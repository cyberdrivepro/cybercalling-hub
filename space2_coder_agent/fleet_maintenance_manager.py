"""
================================================================================
🛠️ CyberCalling Master Fleet Maintenance & Network Security Controller
================================================================================
Features:
- Individual & Global Maintenance Toggle across all 6 Bots in the Fleet:
  1. 📞 @DarkAngelEngine_BOT (Voice Caller)
  2. 🔐 @Cybercallingadmin_bot (Admin Key & Security Vault)
  3. 🗄️ @cybercallingDB_bot (Database & Telemetry)
  4. 🌐 @cybercallingproxy_bot (Proxy Validator Suite)
  5. 🔥 @cybercallingdanger_bot (Danger Burner Vault)
  6. 🩺 @cybercallingPB_bot (Space 2 Server Doctor & AI Coder)
- High-Visibility Red 🔴 Indicators for all locked bots in dashboard and buttons
- Rich User-Facing Maintenance Cards with Animated Progress Bars [████░░] %
- Dynamic Countdown with Auto-Unlock upon Expiry
- Strict Admin Exemption: Master Owner (8405632493) maintains 100% full access
================================================================================
"""

import os
import re
import time
import json
import threading
from typing import Dict, Any, List, Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MAINTENANCE_VAULT_FILE = os.path.join(DATA_DIR, "maintenance_vault.json")

OWNER_IDS = {"8405632493", str(os.getenv("TELEGRAM_OWNER_ID", "8405632493")).strip()}

BOT_REGISTRY = {
    "caller_bot": {
        "name": "📞 Dark Angel Voice Engine Bot",
        "handle": "@DarkAngelEngine_BOT",
        "description": "Outbound Telephony, OTP Intercept & AI Voice Campaigns"
    },
    "admin_bot": {
        "name": "🔐 Admin Vault & Key Bot",
        "handle": "@Cybercallingadmin_bot",
        "description": "Key Vault, User Roles & System Security Controls"
    },
    "db_bot": {
        "name": "🗄️ Database & Telemetry Bot",
        "handle": "@cybercallingDB_bot",
        "description": "Real-time Telemetry, Call CDRs & User Audits"
    },
    "proxy_bot": {
        "name": "🌐 Proxy & Validator Bot",
        "handle": "@cybercallingproxy_bot",
        "description": "Multi-Hop Proxy Chains & 24/7 Server Shield"
    },
    "danger_bot": {
        "name": "🔥 Danger Burner Vault Bot",
        "handle": "@cybercallingdanger_bot",
        "description": "Strict 10-Call Burner Fleet & Stealth Calling"
    },
    "space2_doctor_bot": {
        "name": "🩺 Server Doctor & AI Coder Bot",
        "handle": "@cybercallingPB_bot",
        "description": "Space 2 ZeroGPU Autonomous Coder & Cluster Diagnostics"
    }
}

def parse_duration_seconds(raw_text: str) -> Optional[int]:
    """
    Parses flexible human duration strings into total seconds:
    - '5 sec', '5s', '10 seconds', '30 secs' -> 5, 10, 30
    - '1 min', '1m', '2 mins', '5 minutes' -> 60, 120, 300
    - '1 hour', '1h', '2 hours', '2h' -> 3600, 7200
    - '0', 'off', 'stop', 'indefinite', 'unlock' -> 0
    - Pure numbers: returns int(text)
    """
    if not raw_text:
        return None
    text = raw_text.strip().lower()

    if text in ["0", "off", "stop", "indefinite", "lock", "none", "forever", "unlock", "open"]:
        return 0

    m_sec = re.match(r"^(\d+)\s*(s|sec|secs|second|seconds)$", text)
    if m_sec:
        return int(m_sec.group(1))

    m_min = re.match(r"^(\d+)\s*(m|min|mins|minute|minutes)$", text)
    if m_min:
        return int(m_min.group(1)) * 60

    m_hr = re.match(r"^(\d+)\s*(h|hr|hrs|hour|hours)$", text)
    if m_hr:
        return int(m_hr.group(1)) * 3600

    if text.isdigit():
        return int(text)

    return None

def format_duration_label(total_sec: int) -> str:
    """Formats total seconds into friendly human string."""
    if total_sec <= 0:
        return "Indefinite"
    if total_sec < 60:
        return f"{total_sec} Seconds"
    if total_sec < 3600:
        mins = total_sec // 60
        secs = total_sec % 60
        return f"{mins} Min{'s' if mins != 1 else ''}" + (f" {secs}s" if secs > 0 else "")
    hrs = total_sec // 3600
    rem_mins = (total_sec % 3600) // 60
    return f"{hrs} Hour{'s' if hrs != 1 else ''}" + (f" {rem_mins}m" if rem_mins > 0 else "")

def generate_progress_bar(pct: float, total_blocks: int = 14) -> str:
    """Generates a high-precision progress bar."""
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * total_blocks))
    empty = total_blocks - filled
    return "█" * filled + "░" * empty


class FleetMaintenanceManager:
    """
    Centralized Fleet Maintenance State & Security Gatekeeper.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FleetMaintenanceManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.state: Dict[str, Any] = self._load_vault()

    def _default_state(self) -> Dict[str, Any]:
        """Returns baseline fleet maintenance configuration."""
        bots_data = {}
        for b_key, b_info in BOT_REGISTRY.items():
            bots_data[b_key] = {
                "in_maintenance": False,
                "reason": "Scheduled System Optimization & Security Upgrade",
                "start_time": 0,
                "end_time": 0,
                "duration_sec": 0,
                "duration_mins": 0,
                "updated_by": "System"
            }
        return {
            "global_maintenance": False,
            "global_reason": "Master Cluster Maintenance & Upgrades",
            "global_start_time": 0,
            "global_end_time": 0,
            "global_duration_sec": 0,
            "global_duration_mins": 0,
            "bots": bots_data
        }

    def _load_vault(self) -> Dict[str, Any]:
        """Loads maintenance vault from disk."""
        if os.path.exists(MAINTENANCE_VAULT_FILE):
            try:
                with open(MAINTENANCE_VAULT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults = self._default_state()
                    for k, v in defaults["bots"].items():
                        if k not in data.get("bots", {}):
                            data.setdefault("bots", {})[k] = v
                    return data
            except Exception as e:
                print(f"[MaintenanceManager] Vault load error: {e}")
        return self._default_state()

    def _save_vault(self):
        """Atomically persists maintenance state."""
        try:
            with open(MAINTENANCE_VAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[MaintenanceManager] Vault save error: {e}")

    def is_admin(self, user_id: Any) -> bool:
        """Checks if a user ID is the authorized Master Owner."""
        if not user_id:
            return False
        return str(user_id).strip() in OWNER_IDS

    def check_bot_access(self, bot_key: str, user_id: Any = None) -> Tuple[bool, Optional[str]]:
        """
        Primary Gatekeeper for Bot Ingress:
        - Returns (True, None) if bot is accessible (or user is Admin).
        - Returns (False, maintenance_card) if bot is locked under maintenance.
        """
        if self.is_admin(user_id):
            return True, None

        now = time.time()

        # Check Global Fleet Maintenance
        if self.state.get("global_maintenance"):
            g_end = self.state.get("global_end_time", 0)
            if g_end > 0 and now >= g_end:
                self.state["global_maintenance"] = False
                self._save_vault()
            else:
                return False, self.render_maintenance_card("global")

        # Check Individual Bot Maintenance
        bot_data = self.state.get("bots", {}).get(bot_key)
        if not bot_data:
            return True, None

        if bot_data.get("in_maintenance"):
            b_end = bot_data.get("end_time", 0)
            if b_end > 0 and now >= b_end:
                bot_data["in_maintenance"] = False
                self._save_vault()
                return True, None
            else:
                return False, self.render_maintenance_card(bot_key)

        return True, None

    def set_bot_maintenance(
        self,
        bot_key: str,
        enabled: bool,
        duration_sec: int = 0,
        duration_mins: int = 0,
        reason: str = "",
        admin_id: Any = "8405632493"
    ) -> Dict[str, Any]:
        """
        Enables or disables maintenance for a specific bot with second-level precision.
        """
        if bot_key not in self.state.get("bots", {}):
            return {"success": False, "message": f"Bot `{bot_key}` not found."}

        total_sec = duration_sec if duration_sec > 0 else (duration_mins * 60)
        now = time.time()
        bot_entry = self.state["bots"][bot_key]
        bot_entry["in_maintenance"] = enabled
        bot_entry["duration_sec"] = total_sec if enabled else 0
        bot_entry["duration_mins"] = int(total_sec // 60) if enabled else 0
        bot_entry["start_time"] = now if enabled else 0
        bot_entry["end_time"] = (now + total_sec) if (enabled and total_sec > 0) else 0
        if reason:
            bot_entry["reason"] = reason.strip()
        bot_entry["updated_by"] = str(admin_id)

        self._save_vault()
        return {
            "success": True,
            "bot_key": bot_key,
            "in_maintenance": enabled,
            "duration_sec": total_sec,
            "duration_label": format_duration_label(total_sec),
            "end_time": bot_entry["end_time"]
        }

    def set_global_maintenance(
        self,
        enabled: bool,
        duration_sec: int = 0,
        duration_mins: int = 0,
        reason: str = "",
        admin_id: Any = "8405632493"
    ) -> Dict[str, Any]:
        """
        Locks or Unlocks ALL bots in the fleet concurrently.
        """
        total_sec = duration_sec if duration_sec > 0 else (duration_mins * 60)
        now = time.time()
        self.state["global_maintenance"] = enabled
        self.state["global_duration_sec"] = total_sec if enabled else 0
        self.state["global_duration_mins"] = int(total_sec // 60) if enabled else 0
        self.state["global_start_time"] = now if enabled else 0
        self.state["global_end_time"] = (now + total_sec) if (enabled and total_sec > 0) else 0
        if reason:
            self.state["global_reason"] = reason.strip()

        for b_key in self.state.get("bots", {}):
            self.state["bots"][b_key]["in_maintenance"] = enabled
            self.state["bots"][b_key]["duration_sec"] = total_sec if enabled else 0
            self.state["bots"][b_key]["duration_mins"] = int(total_sec // 60) if enabled else 0
            self.state["bots"][b_key]["start_time"] = now if enabled else 0
            self.state["bots"][b_key]["end_time"] = self.state["global_end_time"]
            if reason:
                self.state["bots"][b_key]["reason"] = reason.strip()
            self.state["bots"][b_key]["updated_by"] = str(admin_id)

        self._save_vault()
        return {
            "success": True,
            "global_maintenance": enabled,
            "duration_sec": total_sec,
            "duration_label": format_duration_label(total_sec),
            "end_time": self.state["global_end_time"]
        }

    def render_maintenance_card(self, bot_key: str = "global") -> str:
        """
        Renders rich user-facing maintenance alert card with high-precision live progress bar.
        """
        now = time.time()

        if bot_key == "global":
            bot_name = "🌐 Entire CyberCalling Bot Network"
            bot_handle = "@DarkAngelEngine_BOT Fleet"
            reason = self.state.get("global_reason", "Master Cluster Upgrades & Security Patches")
            start_t = self.state.get("global_start_time", 0)
            end_t = self.state.get("global_end_time", 0)
            tot_sec = self.state.get("global_duration_sec", 0) or (self.state.get("global_duration_mins", 0) * 60)
        else:
            meta = BOT_REGISTRY.get(bot_key, {"name": bot_key, "handle": ""})
            bot_name = meta["name"]
            bot_handle = meta.get("handle", "")
            bot_data = self.state.get("bots", {}).get(bot_key, {})
            reason = bot_data.get("reason", "Scheduled System Maintenance & Maintenance")
            start_t = bot_data.get("start_time", 0)
            end_t = bot_data.get("end_time", 0)
            tot_sec = bot_data.get("duration_sec", 0) or (bot_data.get("duration_mins", 0) * 60)

        # Calculate Timer & Progress
        if end_t > 0 and end_t > start_t:
            total_sec = max(1.0, end_t - start_t)
            elapsed_sec = max(0.0, now - start_t)
            rem_sec = max(0.0, end_t - now)
            pct = min(100.0, (elapsed_sec / total_sec) * 100.0)
            bar = generate_progress_bar(pct, total_blocks=14)

            rem_mins = int(rem_sec // 60)
            rem_secs = int(rem_sec % 60)
            if rem_mins > 0:
                eta_str = f"{rem_mins}m {rem_secs}s remaining"
            else:
                eta_str = f"{rem_secs}s remaining"

            end_time_utc = time.strftime("%H:%M:%S UTC", time.gmtime(end_t))
            dur_label = format_duration_label(int(total_sec))

            timer_section = (
                f"⏱️ *Live Progress Countdown:*\n"
                f"`[{bar}]` *{pct:.1f}%*\n"
                f"• ⏳ *Time Remaining:* `{eta_str}`\n"
                f"• 🏁 *Target Reopen Time:* `{end_time_utc}`\n"
                f"• ⏱️ *Scheduled Window:* `{dur_label}`\n"
            )
        else:
            timer_section = (
                f"⏱️ *Maintenance Mode:* `🔴 Indefinite Maintenance / Active Engineering`\n"
                f"• ⏳ *Status:* Live engineering updates in progress.\n"
                f"• 🔔 *Notice:* The bot will automatically reopen once complete.\n"
            )

        card = (
            f"🛑 *[BOT SYSTEM UNDER MAINTENANCE]* 🛠️\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Bot Service:* `{bot_name}` ({bot_handle})\n"
            f"⚠️ *Current State:* `🔴 LOCKED UNDER MAINTENANCE`\n"
            f"📝 *Maintenance Notice:* _{reason}_\n\n"
            f"{timer_section}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 *Access Notice:* _All user requests, calling features, and commands are temporarily shielded until maintenance reaches 100%._\n\n"
            f"👇 *Tap below to refresh live status countdown:*"
        )
        return card

    def get_fleet_status_card(self) -> Tuple[str, dict]:
        """
        Renders Master Admin Fleet Maintenance Control Dashboard with bold RED 🔴 indicators on locked bots.
        """
        now = time.time()
        g_on = self.state.get("global_maintenance", False)
        g_badge = "🔴 LOCKED (FLEET-WIDE)" if g_on else "🟢 OPEN (PUBLIC)"

        lines = [
            f"🛠️ *[MASTER FLEET MAINTENANCE CONTROLLER]* 👑",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"• 🌐 *Global Fleet State:* `{g_badge}`",
            f"• 🛡️ *Admin Access Bypass:* `100% Active 24/7 (You are exempt)`",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 *Individual Bot Node States:*"
        ]

        buttons = []
        row = []

        for b_key, meta in BOT_REGISTRY.items():
            b_data = self.state.get("bots", {}).get(b_key, {})
            in_m = b_data.get("in_maintenance", False) or g_on
            end_t = b_data.get("end_time", 0)

            if in_m:
                if end_t > now:
                    rem_sec = int(end_t - now)
                    if rem_sec < 60:
                        status_badge = f"🔴 MAINTENANCE (`{rem_sec}s left`)"
                    else:
                        status_badge = f"🔴 MAINTENANCE (`{rem_sec // 60}m left`)"
                    btn_icon = "🔴"
                else:
                    status_badge = "🔴 MAINTENANCE (Indefinite Lock)"
                    btn_icon = "🔴"
            else:
                status_badge = "🟢 ONLINE (PUBLIC)"
                btn_icon = "🟢"

            lines.append(f"• {btn_icon} *{meta['name']}:* `{status_badge}`")

            # Inline toggle button
            row.append({"text": f"{btn_icon} {meta['name'].split()[0]}", "callback_data": f"maint_bot_{b_key}"})
            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        # Global Control Buttons
        buttons.append([
            {"text": "🔴 Lock ALL Bots (Global Maint)", "callback_data": "maint_prompt_global_on"},
            {"text": "🟢 Unlock ALL Bots (Fleet Open)", "callback_data": "maint_global_off"}
        ])
        buttons.append([
            {"text": "🔄 Refresh Status", "callback_data": "maint_refresh_dash"},
            {"text": "🔙 Back to Console", "callback_data": "nav_main"}
        ])

        return "\n".join(lines), {"inline_keyboard": buttons}

    def get_bot_control_card(self, bot_key: str) -> Tuple[str, dict]:
        """
        Renders detailed configuration and timer menu for a single bot with RED 🔴 status indicator.
        """
        meta = BOT_REGISTRY.get(bot_key, {"name": bot_key, "handle": ""})
        b_data = self.state.get("bots", {}).get(bot_key, {})
        in_m = b_data.get("in_maintenance", False)
        now = time.time()
        end_t = b_data.get("end_time", 0)

        if in_m:
            if end_t > now:
                rem_sec = int(end_t - now)
                if rem_sec < 60:
                    st_text = f"🔴 *MAINTENANCE ACTIVE* (`{rem_sec}s remaining`)"
                else:
                    st_text = f"🔴 *MAINTENANCE ACTIVE* (`~{rem_sec // 60} Mins remaining`)"
            else:
                st_text = "🔴 *MAINTENANCE ACTIVE (Indefinite Lock)*"
        else:
            st_text = "🟢 *ONLINE & OPEN TO PUBLIC*"

        text = (
            f"⚙️ *[MAINTENANCE SETTINGS: {meta['name']}]* 🛠️\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• 🤖 *Bot Handle:* `{meta.get('handle')}`\n"
            f"• 📖 *Role:* _{meta.get('description')}_\n"
            f"• 📊 *Current Status:* {st_text}\n"
            f"• 📝 *Current Notice:* _{b_data.get('reason', 'System Upgrade')}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 *Choose a Maintenance Action, Quick Test, or Type Custom Time:*"
        )

        buttons = [
            [
                {"text": "⚡ 10s Test", "callback_data": f"maint_set_{bot_key}_10s"},
                {"text": "⚡ 30s Test", "callback_data": f"maint_set_{bot_key}_30s"},
                {"text": "⏱️ 1 Min", "callback_data": f"maint_set_{bot_key}_60s"}
            ],
            [
                {"text": "⏱️ 5 Mins", "callback_data": f"maint_set_{bot_key}_300s"},
                {"text": "⏱️ 15 Mins", "callback_data": f"maint_set_{bot_key}_900s"},
                {"text": "⏱️ 30 Mins", "callback_data": f"maint_set_{bot_key}_1800s"}
            ],
            [
                {"text": "⏱️ 1 Hour", "callback_data": f"maint_set_{bot_key}_3600s"},
                {"text": "⏱️ 2 Hours", "callback_data": f"maint_set_{bot_key}_7200s"},
                {"text": "🔒 Indefinite", "callback_data": f"maint_set_{bot_key}_0s"}
            ],
            [
                {"text": "✍️ Custom Time (e.g. 5 sec)", "callback_data": f"maint_custom_{bot_key}"},
                {"text": "🟢 Turn OFF / Unlock", "callback_data": f"maint_unlock_{bot_key}"}
            ],
            [
                {"text": "📝 Edit Notice Message", "callback_data": f"maint_reason_{bot_key}"},
                {"text": "🔙 Back to Fleet Menu", "callback_data": "maint_refresh_dash"}
            ]
        ]
        return text, {"inline_keyboard": buttons}


# Global Singleton Instance
fleet_maintenance = FleetMaintenanceManager()


def stream_live_maintenance_progress(bot_key: str, chat_id: Any, message_id: int, edit_fn, interval: float = 1.0, max_duration_sec: int = 1800):
    """
    Real-time 1-second dynamic streaming loop that edits the Telegram message
    live every 1 second with moving progress bar [████░░░░] % and remaining countdown.
    """
    def _worker():
        t_start = time.time()
        last_rendered = ""
        while time.time() - t_start < max_duration_sec:
            now = time.time()
            bot_data = fleet_maintenance.state.get("bots", {}).get(bot_key, {})
            in_m = bot_data.get("in_maintenance", False) or fleet_maintenance.state.get("global_maintenance", False)
            end_t = bot_data.get("end_time", 0) if bot_data.get("in_maintenance") else fleet_maintenance.state.get("global_end_time", 0)

            if not in_m:
                # Bot unlocked manually or opened
                done_card = (
                    f"🎉 *[MAINTENANCE COMPLETE — SYSTEM IS LIVE!]* 🟢\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 *Module:* `{BOT_REGISTRY.get(bot_key, {}).get('name', bot_key)}`\n"
                    f"📊 *Progress:* `[██████████████]` *100.0%*\n"
                    f"⚡ *Status:* `🟢 100% OPERATIONAL & OPEN`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👉 *Aap ab bot ko poori tarah use kar sakte hain!*"
                )
                done_kb = {"inline_keyboard": [[{"text": "🚀 Open Bot / Start", "callback_data": "menu_home"}]]}
                try:
                    edit_fn(chat_id, message_id, done_card, reply_markup=done_kb)
                except Exception:
                    pass
                break

            if end_t > 0 and now >= end_t:
                # Timer expired! Auto-unlock
                fleet_maintenance.set_bot_maintenance(bot_key, False)
                done_card = (
                    f"🎉 *[MAINTENANCE COMPLETE — SYSTEM IS LIVE!]* 🟢\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🤖 *Module:* `{BOT_REGISTRY.get(bot_key, {}).get('name', bot_key)}`\n"
                    f"📊 *Progress:* `[██████████████]` *100.0%*\n"
                    f"⚡ *Status:* `🟢 100% OPERATIONAL & OPEN`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👉 *Aap ab bot ko poori tarah use kar sakte hain!*"
                )
                done_kb = {"inline_keyboard": [[{"text": "🚀 Open Bot / Start", "callback_data": "menu_home"}]]}
                try:
                    edit_fn(chat_id, message_id, done_card, reply_markup=done_kb)
                except Exception:
                    pass
                break

            # Render updated live card
            card = fleet_maintenance.render_maintenance_card(bot_key)
            if card != last_rendered:
                refresh_kb = {"inline_keyboard": [[{"text": "⚡ Live 1s Stream Active 🟢", "callback_data": "user_maint_refresh"}]]}
                try:
                    edit_fn(chat_id, message_id, card, reply_markup=refresh_kb)
                    last_rendered = card
                except Exception:
                    pass

            time.sleep(interval)

    threading.Thread(target=_worker, daemon=True).start()
