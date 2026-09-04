"""
================================================================================
  📜 CyberCalling 2.0 — Structured Security & Operations Audit Logger
================================================================================
"""

import os
import json
import time
import datetime
from typing import Optional, Dict, Any, List

AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIT_LOG_FILE = os.path.join(AUDIT_DIR, "audit_trail.jsonl")

def log_security_event(
    action: str,
    actor: str = "system",
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    channel: str = "API"
) -> Dict[str, Any]:
    """
    Append an immutable security audit event to the audit trail log.
    Actions: AUTH_SUCCESS, AUTH_FAILED, KEY_ADDED, KEY_REPLACED, KEY_DELETED,
             CAMPAIGN_DISPATCHED, DND_BLOCKED, BUDGET_EXCEEDED, WEBHOOK_RECEIVED
    """
    event = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "unix_time": time.time(),
        "action": action.upper(),
        "actor": actor,
        "status": status.upper(),
        "channel": channel,
        "ip_address": ip_address or "127.0.0.1",
        "details": details or {}
    }
    
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Audit log write error: {e}")
        
    return event

def get_recent_audit_events(limit: int = 50, action_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve the most recent audit events with optional filtering."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
        
    events = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        ev = json.loads(line_str)
                        if action_filter and ev.get("action") != action_filter.upper():
                            continue
                        events.append(ev)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Audit log read error: {e}")
        
    return events[-limit:][::-1]  # Most recent first
