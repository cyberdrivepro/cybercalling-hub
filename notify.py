"""
================================================================================
  🔔 CyberCalling Real-Time Admin Notification Engine
================================================================================
  Pushes instant real-time Telegram alerts to the Super Admin / Owner chat 
  (ID: 8405632493) via @Cybercallingadmin_bot whenever:
  • A new user registers / contacts the main bot
  • A live call is dispatched
  • Daily / hourly calling rate limits are reached
  • A user submits an appeal or upgrade request
================================================================================
"""

import os
import threading
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

from proxy_manager import proxy_manager

ADMIN_BOT_TOKEN = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "8925368015:AAHYm1fHDRNPYhPIqdraVFMBrP5SAHico0k").strip()
DB_BOT_TOKEN = os.getenv("TELEGRAM_DB_BOT_TOKEN", "8880109988:AAFQ-zJwZmWI--iAJbjU0_QHMmNuxHXrQhY").strip()
OWNER_CHAT_ID = str(os.getenv("TELEGRAM_OWNER_ID", "8405632493")).strip()


def send_push_sync(token: str, text: str, reply_markup: dict = None) -> bool:
    """Send immediate notification to Telegram chat."""
    if not token or not OWNER_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": OWNER_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        s = proxy_manager.get_session()
        r = s.post(url, json=payload, timeout=5)
        res = r.json()
        if not res.get("ok"):
            payload.pop("parse_mode", None)
            s.post(url, json=payload, timeout=5)
        return True
    except Exception as e:
        print(f"[Notify Push Warning] {e}")
        return False


def send_admin_push_sync(text: str, reply_markup: dict = None) -> bool:
    return send_push_sync(ADMIN_BOT_TOKEN, text, reply_markup)


def send_db_push_sync(text: str, reply_markup: dict = None) -> bool:
    return send_push_sync(DB_BOT_TOKEN, text, reply_markup)


def notify_admin(text: str, reply_markup: dict = None):
    """Fire-and-forget background alert push to Owner chat."""
    t = threading.Thread(target=send_admin_push_sync, args=(text, reply_markup), daemon=True)
    t.start()


def notify_new_user_registered(user_info: dict):
    """Push rich alert when a new user registers on @DarkAngelEngine_BOT."""
    tg_id = user_info.get("telegram_id")
    fname = user_info.get("first_name", "New User")
    uname = f"@{user_info.get('username')}" if user_info.get("username") else "No Username"
    credits_bal = user_info.get("credit_balance", 5.0)
    via = user_info.get("registered_via", "Direct Start")

    text = (
        "👤 *[NEW USER REGISTERED ON DARK ANGEL 🟢]*\n\n"
        f"• *Name:* `{fname}` ({uname})\n"
        f"• *Telegram ID:* `{tg_id}`\n"
        f"• *Starter Wallet:* `{credits_bal:.1f} Free Credits`\n"
        f"• *Source:* `{via}`\n"
        f"• *Role:* `Standard User` | *Tier:* `Free`\n\n"
        "👇 *1-Tap Admin Quick Actions:*"
    )

    buttons = {
        "inline_keyboard": [
            [
                {"text": "👤 View User Card", "callback_data": f"view_user_{tg_id}"},
                {"text": "➕ Add Credits", "callback_data": f"prompt_add_cr_{tg_id}"}
            ],
            [
                {"text": "🚫 Ban User", "callback_data": f"act_ban_user_{tg_id}"},
                {"text": "📋 All Users", "callback_data": "act_list_users"}
            ]
        ]
    }

    notify_admin(text, reply_markup=buttons)
    try:
        from cybercalling_db_bot import db_logger_bot
        threading.Thread(target=db_logger_bot.stream_new_user, args=(user_info,), daemon=True).start()
    except Exception:
        pass


def notify_user_call_dispatched(tg_id: str, fname: str, recipient_masked: str, duration: str = "-", status: str = "dispatched"):
    """Push real-time telemetry when any user dispatches a live call."""
    text = (
        "📞 *[LIVE CALL DISPATCHED BY USER 🟢]*\n\n"
        f"• *User:* `{fname}` (ID: `{tg_id}`)\n"
        f"• *Recipient:* `{recipient_masked}`\n"
        f"• *Status:* `{status}`\n"
        f"• *Carrier:* `OmniDimension Enterprise Voice AI`"
    )

    buttons = {
        "inline_keyboard": [
            [
                {"text": f"👤 Manage {fname}", "callback_data": f"view_user_{tg_id}"}
            ]
        ]
    }

    notify_admin(text, reply_markup=buttons)


def notify_db_call_dispatched(caller: dict, recipient: str, carrier: str = "OmniDimension", message: str = "", caller_id: str = "+917969006012"):
    """Push real-time call dispatch alert directly to @cybercallingDB_bot."""
    try:
        from cybercalling_db_bot import db_logger_bot
        threading.Thread(target=db_logger_bot.stream_call_dispatch, args=(caller, recipient, carrier, message, caller_id), daemon=True).start()
    except Exception as e:
        print("[Notify DB call error]:", e)


def notify_db_call_completed(call_data: dict, audio_bytes_or_url=None):
    """Push completed call logs and recording audio directly to @cybercallingDB_bot."""
    try:
        from cybercalling_db_bot import db_logger_bot
        threading.Thread(target=db_logger_bot.stream_call_completed, args=(call_data, audio_bytes_or_url), daemon=True).start()
    except Exception as e:
        print("[Notify DB completed error]:", e)


def notify_db_web_visitor(ip: str, endpoint: str, user_agent: str = "", extra: str = ""):
    """Push WebRTC web caller IP and details directly to @cybercallingDB_bot."""
    try:
        from cybercalling_db_bot import db_logger_bot
        threading.Thread(target=db_logger_bot.stream_web_visitor, args=(ip, endpoint, user_agent, extra), daemon=True).start()
    except Exception as e:
        print("[Notify DB web error]:", e)


def notify_db_tos_accepted(tg_id: str, fname: str, uname: str, version: str = "v1.0"):
    """Push ToS acceptance event directly to @cybercallingDB_bot."""
    try:
        from cybercalling_db_bot import db_logger_bot
        threading.Thread(target=db_logger_bot.stream_tos_acceptance, args=(tg_id, fname, uname, version), daemon=True).start()
    except Exception as e:
        print("[Notify DB ToS error]:", e)

