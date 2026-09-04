"""
================================================================================
  Telegram Shared State — Cross-Replica Deduplication & Stop Signals
================================================================================
  On Hugging Face Spaces, /data is the shared persistent disk mounted on ALL
  replicas simultaneously. We store:
    1. processed_updates   — update_id dedup (prevents double replies)
    2. redial_stop_signals — stop signals written by any replica, read by all
================================================================================
"""

import os
import time
import uuid
import sqlite3
import threading

_lock = threading.Lock()
_SEEN_IN_MEMORY = {}
_INSTANCE_ID = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"

_HF_SHARED_DIR = "/data" if os.path.isdir("/data") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_DB_PATH = os.path.join(_HF_SHARED_DIR, "shared_state.db")


def _get_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_updates (
            update_id TEXT,
            bot_name TEXT,
            processed_at REAL,
            PRIMARY KEY (update_id, bot_name)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS redial_stop (
            recipient TEXT PRIMARY KEY,
            stopped_at REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shared_wizard_state (
            chat_id TEXT,
            scope TEXT,
            state_json TEXT,
            updated_at REAL,
            PRIMARY KEY (chat_id, scope)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS poller_leases (
            bot_name TEXT PRIMARY KEY,
            holder_id TEXT,
            expires_at REAL
        )
    """)
    conn.commit()
    return conn


def acquire_bot_poller_lease(bot_name: str = "caller", lease_sec: int = 15) -> bool:
    """
    Distributed leader election for multi-replica Hugging Face Spaces.
    Guarantees ONLY ONE replica runs polling/background daemons per bot.
    Returns True if this replica holds the active lease, False if in standby.
    """
    now = time.time()
    with _lock:
        for attempt in range(4):
            try:
                conn = _get_db()
                cur = conn.cursor()
                cur.execute("SELECT holder_id, expires_at FROM poller_leases WHERE bot_name = ?", (str(bot_name),))
                row = cur.fetchone()
                if not row or row[1] < now or row[0] == _INSTANCE_ID:
                    cur.execute(
                        "INSERT OR REPLACE INTO poller_leases (bot_name, holder_id, expires_at) VALUES (?, ?, ?)",
                        (str(bot_name), _INSTANCE_ID, now + lease_sec)
                    )
                    conn.commit()
                    conn.close()
                    return True
                else:
                    conn.close()
                    return False
            except sqlite3.OperationalError:
                time.sleep(0.05)
            except Exception as e:
                return False
        return False


def is_duplicate_update(update_id, bot_name: str = "caller") -> bool:
    """
    Atomic cross-process and cross-replica update deduplication.
    Returns True if this update_id has already been processed by any replica/worker.
    """
    if not update_id:
        return False

    u_key = f"{bot_name}_{update_id}"
    now = time.time()

    with _lock:
        # 1. Fast In-Memory Check
        if u_key in _SEEN_IN_MEMORY:
            if now - _SEEN_IN_MEMORY[u_key] < 600:
                return True

        # Prune old in-memory items
        if len(_SEEN_IN_MEMORY) > 3000:
            cutoff_mem = now - 600
            for k in list(_SEEN_IN_MEMORY.keys()):
                if _SEEN_IN_MEMORY[k] < cutoff_mem:
                    _SEEN_IN_MEMORY.pop(k, None)

        _SEEN_IN_MEMORY[u_key] = now

        # 2. Shared Cross-Replica Database Sync
        for attempt in range(4):
            try:
                conn = _get_db()
                cur = conn.cursor()
                try:
                    cur.execute(
                        "INSERT INTO processed_updates (update_id, bot_name, processed_at) VALUES (?, ?, ?)",
                        (str(update_id), str(bot_name), now)
                    )
                    conn.commit()
                    conn.close()
                    return False
                except sqlite3.IntegrityError:
                    conn.close()
                    return True
            except sqlite3.OperationalError:
                time.sleep(0.05)
            except Exception:
                # Fail-safe on unexpected error: if already seen in memory, reject
                return True
        return True


def is_duplicate_alert(alert_key: str) -> bool:
    """Prevent duplicate call status and notification alerts across replicas."""
    return is_duplicate_update(str(alert_key), bot_name="alert")


def signal_stop_redial(recipient: str):
    """Write a stop signal for a recipient into the shared DB."""
    with _lock:
        try:
            conn = _get_db()
            conn.execute(
                "INSERT OR REPLACE INTO redial_stop (recipient, stopped_at) VALUES (?, ?)",
                (str(recipient).strip(), time.time())
            )
            conn.commit()
            conn.close()
        except Exception:
            pass


def signal_stop_all_redials():
    """Write a global stop signal (recipient='ALL') to stop every active redial."""
    signal_stop_redial("ALL")


def is_redial_stopped(recipient: str) -> bool:
    """Check shared DB if a stop signal was written for this recipient (or 'ALL')."""
    try:
        conn = _get_db()
        cur = conn.cursor()
        cutoff = time.time() - 600
        cur.execute(
            "SELECT COUNT(*) FROM redial_stop WHERE (recipient = ? OR recipient = 'ALL') AND stopped_at > ?",
            (str(recipient).strip(), cutoff)
        )
        count = cur.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def clear_redial_stop(recipient: str):
    """Clear stop signal for a recipient (e.g. when starting a new call)."""
    with _lock:
        try:
            conn = _get_db()
            conn.execute("DELETE FROM redial_stop WHERE recipient = ? OR recipient = 'ALL'", (str(recipient).strip(),))
            conn.commit()
            conn.close()
        except Exception:
            pass


def get_shared_wizard_state(chat_id: str, scope: str = "call"):
    """Fetch wizard state JSON from shared persistent SQLite across replicas."""
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("SELECT state_json FROM shared_wizard_state WHERE chat_id = ? AND scope = ?", (str(chat_id), str(scope)))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            import json
            return json.loads(row[0])
        return None
    except Exception:
        return None


def set_shared_wizard_state(chat_id: str, state_dict: dict, scope: str = "call"):
    """Write wizard state JSON to shared persistent SQLite across replicas."""
    try:
        import json
        conn = _get_db()
        raw = json.dumps(state_dict)
        conn.execute(
            "INSERT OR REPLACE INTO shared_wizard_state (chat_id, scope, state_json, updated_at) VALUES (?, ?, ?, ?)",
            (str(chat_id), str(scope), raw, time.time())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def pop_shared_wizard_state(chat_id: str, scope: str = "call"):
    """Atomically pop wizard state from shared persistent SQLite."""
    val = get_shared_wizard_state(chat_id, scope)
    try:
        conn = _get_db()
        conn.execute("DELETE FROM shared_wizard_state WHERE chat_id = ? AND scope = ?", (str(chat_id), str(scope)))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return val


class SharedWizardStateDict:
    """A dictionary-like interface that seamlessly reads/writes wizard state to cross-replica SQLite."""
    def __init__(self, scope="call"):
        self.scope = scope

    def __getitem__(self, chat_id):
        val = get_shared_wizard_state(str(chat_id), self.scope)
        if val is None:
            raise KeyError(chat_id)
        return val

    def __setitem__(self, chat_id, value):
        set_shared_wizard_state(str(chat_id), value, self.scope)

    def __contains__(self, chat_id):
        return get_shared_wizard_state(str(chat_id), self.scope) is not None

    def get(self, chat_id, default=None):
        val = get_shared_wizard_state(str(chat_id), self.scope)
        return val if val is not None else default

    def pop(self, chat_id, default=None):
        val = pop_shared_wizard_state(str(chat_id), self.scope)
        return val if val is not None else default
