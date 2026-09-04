"""
================================================================================
  🗄️ CyberCalling Master Real-Time Database & Telemetry Logger Bot
================================================================================
  Bot Username: @cybercallingDB_bot
  Token: 8880109988:AAFQ-zJwZmWI--iAJbjU0_QHMmNuxHXrQhY
  
  Streams all real-time events to Super Admin:
  • 👤 New User Registrations (Full Name, Username, Telegram ID, Initial credits)
  • 📞 Call Dispatches (Initiator Username/ID, Destination Number, Spoken AI message, Carrier)
  • 🔔 Call Status & Results (Duration, Cost, Final Status, AI Sentiment, Quality Score)
  • 🎧 Call Audio Recordings (.mp3)
  • 🌐 Web Call & API Requests (Real Caller IP, User-Agent, Session Details)
  • 💳 Balance & Credit Transactions
  • ⚖️ Terms of Service & Disclaimer Agreements
================================================================================
"""

import os
import sys
import time
import json
import sqlite3
import datetime
import threading
import requests
from dotenv import load_dotenv

from backend.app.services.user_manager import user_manager
from proxy_manager import proxy_manager

load_dotenv(override=True)

DB_BOT_TOKEN = os.getenv("TELEGRAM_DB_BOT_TOKEN", "8880109988:AAFQ-zJwZmWI--iAJbjU0_QHMmNuxHXrQhY").strip()
OWNER_CHAT_ID = str(os.getenv("TELEGRAM_OWNER_ID", "8405632493")).strip()
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cybercalling_enterprise.db")


class CyberCallingDBBot:
    def __init__(self, token=None):
        self.token = token or DB_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.owner_id = OWNER_CHAT_ID
        self.is_running = False
        self.offset = 0

    def send_message(self, chat_id, text, reply_markup=None, parse_mode="Markdown"):
        """Send message to user with automatic fallback to plain text on Markdown syntax errors."""
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            s = proxy_manager.get_session()
            r = s.post(f"{self.base_url}/sendMessage", json=payload, timeout=10)
            res = r.json()
            if not res.get("ok") and parse_mode:
                payload.pop("parse_mode", None)
                r2 = s.post(f"{self.base_url}/sendMessage", json=payload, timeout=10)
                return r2.json()
            return res
        except Exception as e:
            print("[DB Bot send_message error]:", e)
            return None

    def send_audio(self, chat_id, audio_bytes_or_url, caption="", title="Call Recording"):
        """Send playable call audio recording."""
        try:
            raw_bytes = None
            if isinstance(audio_bytes_or_url, bytes):
                raw_bytes = audio_bytes_or_url
            elif isinstance(audio_bytes_or_url, str) and audio_bytes_or_url.startswith("http"):
                r = requests.get(audio_bytes_or_url, timeout=25)
                if r.status_code == 200:
                    raw_bytes = r.content
            elif isinstance(audio_bytes_or_url, str) and os.path.exists(audio_bytes_or_url):
                with open(audio_bytes_or_url, "rb") as f:
                    raw_bytes = f.read()

            if not raw_bytes:
                return

            s = proxy_manager.get_session()
            files = {"audio": ("call_recording.mp3", raw_bytes, "audio/mpeg")}
            data = {"chat_id": chat_id, "caption": caption, "title": title, "parse_mode": "Markdown"}
            s.post(f"{self.base_url}/sendAudio", data=data, files=files, timeout=30)
        except Exception as e:
            print("[DB Bot send_audio error]:", e)

    def send_document(self, chat_id, file_path, caption=""):
        """Send file or DB snapshot."""
        try:
            if not os.path.exists(file_path):
                return
            s = proxy_manager.get_session()
            with open(file_path, "rb") as f:
                s.post(
                    f"{self.base_url}/sendDocument",
                    data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
                    files={"document": f},
                    timeout=30
                )
        except Exception as e:
            print("[DB Bot send_document error]:", e)

    def send_location(self, chat_id, latitude: float, longitude: float):
        """Send interactive GPS map location pin."""
        try:
            if not latitude or not longitude:
                return
            s = proxy_manager.get_session()
            data = {"chat_id": chat_id, "latitude": float(latitude), "longitude": float(longitude)}
            s.post(f"{self.base_url}/sendLocation", json=data, timeout=15)
        except Exception as e:
            print("[DB Bot send_location error]:", e)

    # ==========================================
    # Real-Time Event Streamers
    # ==========================================
    def stream_new_user(self, u: dict):
        """Stream new user registration with MTProto intelligence."""
        uname = f"@{u.get('username')}" if u.get('username') else "No Username"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            from telegram_mtproto_engine import mtproto_engine
            mp = mtproto_engine.inspect_user_profile(u)
            dc_str = mp.get("dc_location", "DC 2 — Global")
            prem_str = mp.get("is_premium", "Standard Free")
        except Exception:
            dc_str = "DC 2 (Auto)"
            prem_str = "Standard Free"

        text = (
            "👤 *[NEW USER REGISTERED — DB LOG 🟢]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Name:* `{u.get('first_name', 'User')}`\n"
            f"• *Username:* {uname}\n"
            f"• *Telegram ID:* `{u.get('telegram_id')}`\n"
            f"• *Telegram DC:* `{dc_str}`\n"
            f"• *Account Tier:* `{prem_str}`\n"
            f"• *Role:* `{u.get('role', 'user')}` | *Plan:* `{u.get('plan_tier', 'Free')}`\n"
            f"• *Trial Credits:* `{u.get('credit_balance', 5.0):.1f} Credits`\n"
            f"• *Daily Limit:* `{u.get('daily_limit', 10)} calls/day`\n"
            f"• *Trigger Source:* `{u.get('registered_via', '/start')}`\n"
            f"• *Time:* _{now_str}_"
        )
        self.send_message(self.owner_id, text)

    def stream_call_dispatch(self, caller: dict, recipient: str, carrier: str = "OmniDimension", message: str = "", caller_id: str = "+917969006012"):
        """Stream outbound call dispatch event."""
        uname = f"@{caller.get('username')}" if caller.get('username') else f"ID: {caller.get('telegram_id')}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = (
            "📞 *[OUTBOUND CALL DISPATCHED — LIVE FEED 🚀]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Initiated By:* `{caller.get('first_name', 'User')}` ({uname})\n"
            f"• *Target Recipient:* `{recipient}`\n"
            f"• *Spoken AI Prompt:* _{message or 'Default assistant greeting'}_\n"
            f"• *Carrier Bridge:* `{carrier}`\n"
            f"• *Caller ID:* `{caller_id}`\n"
            f"• *Time:* _{now_str}_"
        )
        self.send_message(self.owner_id, text)

    def stream_call_completed(self, call_data: dict, audio_bytes_or_url=None):
        """Stream call log result and forward audio."""
        icon = "🟢" if call_data.get("status") == "completed" else "🔴"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = (
            f"{icon} *[CALL LOG RECORDED — LIVE DB]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *User:* `{call_data.get('user_name', 'User')}` (`{call_data.get('telegram_id')}`)\n"
            f"• *Recipient:* `{call_data.get('recipient')}`\n"
            f"• *Duration:* `{call_data.get('duration', '0s')}`\n"
            f"• *Final Status:* `{call_data.get('status', 'completed')}`\n"
            f"• *Cost / Deducted:* `{call_data.get('cost_credits', 1.0):.2f} Credits` (${call_data.get('cost_usd', 0.0):.3f})\n"
            f"• *Lead Score:* `{call_data.get('score', 80)}/100` ({call_data.get('sentiment', 'Positive')})\n"
            f"• *Time:* _{now_str}_"
        )
        self.send_message(self.owner_id, text)

        if audio_bytes_or_url:
            cap = f"🎧 *Audio Recording:* `{call_data.get('recipient')}` | Duration: `{call_data.get('duration')}` | User: `{call_data.get('user_name')}`"
            self.send_audio(self.owner_id, audio_bytes_or_url, caption=cap, title=f"Call - {call_data.get('recipient')}")

    def stream_web_visitor(self, ip: str, endpoint: str, user_agent: str = "", extra: str = ""):
        """Stream web visitor and API calls with real client IP, City/Country and Map."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            from geo_ip_engine import lookup_ip_geo
            geo = lookup_ip_geo(ip)
            flag = geo.get("flag", "🌐")
            loc_str = f"{geo.get('city')}, {geo.get('region')} ({geo.get('country')})" if geo.get('region') else f"{geo.get('city')}, {geo.get('country')}"
            isp_str = geo.get("isp", "Unknown ISP")
            sec_badge = "🛡️ VPN / Proxy / Tor Detected" if geo.get("is_proxy") else "🟢 Clean (Residential/Mobile)"
            if geo.get("is_hosting"):
                sec_badge += " | Datacenter"
            map_url = geo.get("google_maps_url") or geo.get("map_url", "")
            map_md = f"[📍 View on Map]({map_url})" if map_url else "N/A"
        except Exception:
            flag = "🌐"
            loc_str = "Global Client"
            isp_str = "Unknown"
            sec_badge = "🟢 Standard"
            map_md = "N/A"

        text = (
            "🌐 *[WEB / API CALLER IP CAPTURED 🔍]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Real Client IP:* `{ip}`\n"
            f"• *Location:* {flag} `{loc_str}`\n"
            f"• *ISP / Network:* `{isp_str}`\n"
            f"• *Security Status:* `{sec_badge}`\n"
            f"• *Endpoint:* `{endpoint}`\n"
            f"• *Details:* `{extra or 'WebRTC Web Call session'}`\n"
            f"• *Map Coordinates:* {map_md}\n"
            f"• *User-Agent:* `{user_agent[:55] if user_agent else 'Browser Client'}`\n"
            f"• *Time:* _{now_str}_"
        )
        self.send_message(self.owner_id, text)
        if isinstance(geo, dict) and geo.get("lat") and geo.get("lon"):
            try:
                self.send_location(self.owner_id, geo["lat"], geo["lon"])
            except Exception:
                pass

    def stream_tos_acceptance(self, tg_id: str, fname: str, uname: str, version: str = "v1.0"):
        """Stream ToS agreement signature."""
        un_str = f"@{uname}" if uname else "No Username"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = (
            "⚖️ *[TERMS OF SERVICE ACCEPTED 📜]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *User:* `{fname}` ({un_str})\n"
            f"• *Telegram ID:* `{tg_id}`\n"
            f"• *Version:* `{version}`\n"
            "• *Status:* `Agreed to Sole Responsibility & Compliance 🟢`\n"
            f"• *Time:* _{now_str}_"
        )
        self.send_message(self.owner_id, text)

    def answer_callback_query(self, cb_id, text=None):
        """Acknowledge Telegram callback query to stop loading spinner."""
        try:
            s = proxy_manager.get_session()
            payload = {"callback_query_id": str(cb_id)}
            if text:
                payload["text"] = text
            s.post(f"{self.base_url}/answerCallbackQuery", json=payload, timeout=5)
        except Exception:
            pass

    # ==========================================
    # Command & Callback Router
    # ==========================================
    def handle_update(self, update):
        # Fleet Maintenance Gate (Admin Bypass Active)
        from fleet_maintenance_manager import fleet_maintenance
        chat_id = None
        if "callback_query" in update:
            chat_id = str(update["callback_query"]["message"]["chat"]["id"])
        elif "message" in update:
            chat_id = str(update["message"]["chat"]["id"])

        if chat_id:
            can_access, maint_card = fleet_maintenance.check_bot_access("db_bot", user_id=chat_id)
            if not can_access:
                self.send_message(chat_id, maint_card)
                return

        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            chat_id = str(cb["message"]["chat"]["id"])
            data = cb.get("data", "")
            self.answer_callback_query(cb_id)

            # Owner-Only Security Gate
            user_info = user_manager.get_or_create_user(chat_id)
            if not user_info.get("is_owner"):
                self.send_message(chat_id, "🚫 *Access Denied:* This database telemetry stream is strictly reserved for the Master Owner.")
                return

            if data in ["menu_fleet_maint", "maint_refresh_dash"]:
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.send_message(chat_id, txt, reply_markup=kb)
                return
            elif data.startswith("maint_bot_"):
                b_key = data[10:]
                txt, kb = fleet_maintenance.get_bot_control_card(b_key)
                self.send_message(chat_id, txt, reply_markup=kb)
                return
            elif data.startswith("maint_set_"):
                raw = data[10:]
                parts = raw.rsplit("_", 1)
                b_key, dur_str = parts[0], parts[1]
                dur = int(dur_str)
                fleet_maintenance.set_bot_maintenance(b_key, True, duration_mins=dur, admin_id=chat_id)
                self.answer_callback_query(cb_id, text=f"✅ {b_key} set to {dur}m maintenance!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.send_message(chat_id, txt, reply_markup=kb)
                return
            elif data.startswith("maint_unlock_"):
                b_key = data[13:]
                fleet_maintenance.set_bot_maintenance(b_key, False, admin_id=chat_id)
                self.answer_callback_query(cb_id, text=f"🟢 {b_key} unlocked to Public!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.send_message(chat_id, txt, reply_markup=kb)
                return
            elif data == "maint_prompt_global_on":
                text_g = (
                    "🚨 *[CONFIRM GLOBAL FLEET LOCKOUT]* ⚠️\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "This will lock **ALL 6 BOTS** concurrently into Maintenance Mode.\n"
                    "• 👑 *Admin (You):* 100% full access remains active.\n"
                    "• 👥 *Users:* All interaction requests will be blocked.\n\n"
                    "👇 *Select Global Maintenance Timer Duration:*"
                )
                buttons_g = [
                    [
                        {"text": "⏱️ 15 Mins", "callback_data": "maint_global_set_15"},
                        {"text": "⏱️ 30 Mins", "callback_data": "maint_global_set_30"}
                    ],
                    [
                        {"text": "⏱️ 1 Hour", "callback_data": "maint_global_set_60"},
                        {"text": "⏱️ 2 Hours", "callback_data": "maint_global_set_120"}
                    ],
                    [
                        {"text": "🔒 Indefinite Lock", "callback_data": "maint_global_set_0"},
                        {"text": "❌ Cancel", "callback_data": "menu_fleet_maint"}
                    ]
                ]
                self.send_message(chat_id, text_g, reply_markup={"inline_keyboard": buttons_g})
                return
            elif data.startswith("maint_global_set_"):
                dur = int(data[17:])
                fleet_maintenance.set_global_maintenance(True, duration_mins=dur, admin_id=chat_id)
                self.answer_callback_query(cb_id, text="🔴 ALL Bots Locked into Maintenance!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.send_message(chat_id, txt, reply_markup=kb)
                return
            elif data == "maint_global_off":
                fleet_maintenance.set_global_maintenance(False, admin_id=chat_id)
                self.answer_callback_query(cb_id, text="🟢 ALL Bots Unlocked to Public!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.send_message(chat_id, txt, reply_markup=kb)
                return

            if data in ["menu_home", "nav_home", "menu_start", "nav_main"]:
                self.cmd_start(chat_id)
                return
            elif data == "db_balance":
                self.cmd_balance(chat_id)
            elif data == "db_stats":
                self.cmd_stats(chat_id)
            elif data == "db_users":
                self.cmd_users(chat_id)
            elif data == "db_calls":
                self.cmd_calls(chat_id)
            elif data == "db_export":
                self.cmd_export(chat_id)
            elif data.startswith("view_user_"):
                self.cmd_user_inspect(chat_id, data[10:].strip())
            elif data.startswith("mtproto_"):
                self.cmd_mtproto_lookup(chat_id, data[8:].strip())
            return

        if "message" in update:
            msg = update["message"]
            chat_id = str(msg["chat"]["id"])
            text = msg.get("text", "").strip()

            # Owner-Only Security Gate
            user_info = user_manager.get_or_create_user(chat_id)
            if not user_info.get("is_owner"):
                self.send_message(chat_id, "🚫 *Access Denied:* This database telemetry stream is strictly reserved for the Master Owner.")
                return

            if not text:
                return

            if text in ["/start", "/help"]:
                self.cmd_start(chat_id)
            elif text in ["/balance", "/trunks", "💰 Carrier Balances"]:
                self.cmd_balance(chat_id)
            elif text in ["/stats", "📊 Platform Stats"]:
                self.cmd_stats(chat_id)
            elif text in ["/users", "👥 View Users"]:
                self.cmd_users(chat_id)
            elif text in ["/calls", "📞 Recent Calls"]:
                self.cmd_calls(chat_id)
            elif text.startswith("/user "):
                self.cmd_user_inspect(chat_id, text[6:].strip())
            elif text.startswith("/ip "):
                self.cmd_ip_lookup(chat_id, text[4:].strip())
            elif text.startswith("/mtproto "):
                self.cmd_mtproto_lookup(chat_id, text[9:].strip())
            elif text.startswith("/search "):
                self.cmd_search(chat_id, text[8:].strip())
            elif text in ["/export", "💾 Export Database"]:
                self.cmd_export(chat_id)
            else:
                self.send_message(chat_id, "💡 Type `/stats`, `/users`, `/calls`, `/balance`, `/user <tg_id>`, `/ip <address>`, `/mtproto <tg_id>`, `/search <phone>`, or `/export`!")

    def cmd_start(self, chat_id):
        from fleet_maintenance_manager import fleet_maintenance
        maint_banner = fleet_maintenance.get_admin_maint_banner("db_bot")
        maint_prefix = f"{maint_banner}\n" if maint_banner else ""
        maint_btn = "🔴 Fleet Maintenance (ACTIVE)" if maint_banner else "🛠️ Fleet Maintenance Control"

        text = (
            f"{maint_prefix}"
            "🗄️ *[CyberCalling Master Database & Telemetry Bot]* 👑\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚡ *LIVE TELEMETRY & AUDIT LOGGER*\n\n"
            "Real-time stream logs only upon events:\n"
            "• 👤 User Registrations & Balances\n"
            "• 📞 Outbound Calls & Audio Recordings (.mp3)\n"
            "• 🔔 Lead Scoring & AI Sentiment Analysis\n"
            "• 🌐 Web Callers Real IP & DC Locations\n"
            "• 💳 Credit Recharges & Voucher Redemptions\n\n"
            "👇 *Database Commands:*\n"
            "• `/balance` — Check Multi-Trunk Pool Balance on-demand\n"
            "• `/stats` — Platform Overview & DB Metrics\n"
            "• `/users` — Registered users list\n"
            "• `/calls` — Recent live call logs\n"
            "• `/user <tg_id>` — Inspect user record\n"
            "• `/export` — Download SQLite DB backup"
        )
        buttons = {
            "inline_keyboard": [
                [
                    {"text": maint_btn, "callback_data": "menu_fleet_maint"}
                ],
                [
                    {"text": "💰 Carrier Balances", "callback_data": "db_balance"},
                    {"text": "📊 Platform Stats", "callback_data": "db_stats"}
                ],
                [
                    {"text": "👥 All Users", "callback_data": "db_users"},
                    {"text": "📞 Recent Calls", "callback_data": "db_calls"}
                ],
                [
                    {"text": "💾 Export DB Backup", "callback_data": "db_export"}
                ]
            ]
        }
        self.send_message(chat_id, text, reply_markup=buttons)

    def cmd_stats(self, chat_id):
        summary = user_manager.admin_get_category2_summary()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            "📊 *[CyberCalling Master Database Statistics]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• *Total Registered Users:* `{summary['total_users']} Accounts`\n"
            f"• *Active Users Today:* `{summary['active_today']}`\n"
            f"• *Banned Users:* `{summary['banned_count']}` | *Suspended:* `{summary['suspended_count']}`\n"
            f"• *Total Voice Credits in Circulation:* `{summary['total_credits_circulation']:.1f} Credits`\n"
            f"• *Active Telephony Proxy Pool:* `{proxy_manager.get_status()['pool_size']} Proxies`\n"
            f"• *Proxy Routing Mode:* `{proxy_manager.get_status()['mode']}`\n"
            f"• *Time:* _{now_str}_"
        )
        self.send_message(chat_id, text)

    def cmd_users(self, chat_id):
        users_list = user_manager.admin_list_users(page=1, page_size=10)
        lines = ["👥 *[All Registered Users in Database]*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        buttons = []
        for u in users_list:
            st = "🟢" if "ACTIVE" in str(u.get("status", "ACTIVE")) else "🔴"
            uname = f"@{u['username']}" if u.get('username') else "No Username"
            lines.append(
                f"{st} *{u['first_name']}* ({uname})\n"
                f"   • ID: `{u['telegram_id']}` | Role: `{u['role']}`\n"
                f"   • Balance: `{u['credit_balance']:.1f} Cr` | Plan: `{u.get('plan_tier', 'Free')}`\n"
                f"   • Calls: `{u.get('total_calls', 0)}` | Joined: _{u.get('created_at', 'Recent')}_\n"
            )
            buttons.append([
                {"text": f"👤 {u['first_name']}", "callback_data": f"view_user_{u['telegram_id']}"},
                {"text": "⚡ MTProto DC", "callback_data": f"mtproto_{u['telegram_id']}"}
            ])
        if not users_list:
            lines.append("_No users in database yet._")
        else:
            lines.append("👉 Tap any user button below to inspect full activity.")

        self.send_message(chat_id, "\n".join(lines), reply_markup={"inline_keyboard": buttons[:8]} if buttons else None)

    def cmd_calls(self, chat_id):
        calls = user_manager.get_user_recent_calls(limit=10)
        lines = ["📞 *[Latest 10 Live Outbound Calls]*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        if not calls:
            lines.append("_No recent calls recorded yet._")
        else:
            for c in calls:
                st_icon = "🟢" if "complete" in str(c.get("status", "")).lower() else "⚪"
                lines.append(
                    f"{st_icon} *Target:* `{c.get('recipient')}` ({c.get('customer_name', 'Client')})\n"
                    f"   • User: `{c.get('user_name', 'User')}` (`{c.get('telegram_id', '-')}`)\n"
                    f"   • Duration: `{c.get('duration_seconds', 0):.1f}s` | Cost: `{c.get('cost_credits', 1.0):.1f} Cr`\n"
                    f"   • Status: `{c.get('status')}` | Time: _{c.get('created_at')}_\n"
                )
        self.send_message(chat_id, "\n".join(lines))

    def cmd_user_inspect(self, chat_id, target_id):
        card = user_manager.admin_get_user_card(target_id)
        if not card:
            self.send_message(chat_id, f"❌ User `{target_id}` not found in database.")
            return

        uname = f"@{card.get('username')}" if card.get('username') else "No Username"
        history = user_manager.get_user_recent_calls(target_id=target_id, limit=5)
        text = (
            f"👤 *[User Database Record — {card.get('first_name')}]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Telegram ID:* `{card.get('telegram_id')}`\n"
            f"• *Username:* {uname}\n"
            f"• *Role:* `{card.get('role')}` | *Status:* `{card.get('status')}`\n"
            f"• *Plan Tier:* `{card.get('plan_tier')}`\n"
            f"• *Credit Balance:* `{card.get('credit_balance'):.1f} Credits`\n"
            f"• *Calls Today:* `{card.get('calls_today')} / {card.get('daily_limit')}`\n"
            f"• *Lifetime Calls:* `{card.get('total_calls')}`\n"
            f"• *Registered:* _{card.get('created_at')}_\n\n"
            "📋 *Recent Call History:*\n"
        )
        if not history:
            text += "_No calls placed by this user yet._"
        else:
            for h in history:
                text += f"• `{h.get('recipient')}` ({h.get('status')}) - `{h.get('duration_seconds', 0):.0f}s` ({h.get('cost_credits')} Cr)\n"
        self.send_message(chat_id, text)

    def cmd_search(self, chat_id, query):
        if not query:
            self.send_message(chat_id, "ℹ️ *Usage:* `/search <phone or username or name>`")
            return
        results = user_manager.admin_list_users(page=1, page_size=50)
        matches = []
        for u in results:
            if query.lower() in u.get("first_name", "").lower() or query.lower() in u.get("username", "").lower() or query in str(u.get("telegram_id")):
                matches.append(u)
        if not matches:
            self.send_message(chat_id, f"🔍 No users found matching `{query}`.")
            return
        lines = [f"🔍 *[Search Results for `{query}` — {len(matches)} found]*\n"]
        for u in matches[:8]:
            uname = f"@{u.get('username')}" if u.get('username') else "No Username"
            lines.append(f"• *{u.get('first_name')}* ({uname}) — ID: `{u.get('telegram_id')}` | Bal: `{u.get('credit_balance', 0.0):.1f} Cr`")
        self.send_message(chat_id, "\n".join(lines))

    def cmd_ip_lookup(self, chat_id, target_ip):
        """Lookup geolocation and security details for any IP on-demand."""
        if not target_ip:
            self.send_message(chat_id, "ℹ️ *Usage:* `/ip <ip_address>` (e.g. `/ip 1.1.1.1`)")
            return
        from geo_ip_engine import lookup_ip_geo, format_geo_card_markdown
        geo = lookup_ip_geo(target_ip)
        card = format_geo_card_markdown(geo)
        text = (
            f"🌍 *[IP Geolocation & Threat Intelligence]*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{card}\n"
        )
        self.send_message(chat_id, text)
        if isinstance(geo, dict) and geo.get("lat") and geo.get("lon"):
            try:
                self.send_location(chat_id, geo["lat"], geo["lon"])
            except Exception:
                pass

    def cmd_mtproto_lookup(self, chat_id, target):
        """Lookup deep Telegram MTProto profile intelligence on-demand."""
        if not target:
            self.send_message(chat_id, "ℹ️ *Usage:* `/mtproto <telegram_id or username>`")
            return
        from telegram_mtproto_engine import mtproto_engine
        profile = mtproto_engine.inspect_user_profile({"telegram_id": target, "first_name": "Target User", "username": target})
        card = mtproto_engine.format_mtproto_card(profile)
        self.send_message(chat_id, card)

    def cmd_export(self, chat_id):
        self.send_message(chat_id, "⏳ *Preparing complete database backup package...*")
        if os.path.exists(DB_FILE):
            self.send_document(chat_id, DB_FILE, caption="💾 *CyberCalling SQLite Enterprise Database Backup*")
        else:
            self.send_message(chat_id, "❌ Database file not found on disk.")

    def cmd_balance(self, chat_id):
        """On-demand OmniDimension carrier balances & platform metrics check."""
        try:
            from encrypted_api_vault import get_all_vault_keys
            from live_billing_engine import fetch_account_live_billing
            from telegram_bot import OmniClient

            keys = get_all_vault_keys()
            account_lines = []
            total_pool_balance = 0.0
            total_pool_mins = 0

            for idx, k_item in enumerate(keys):
                api_key = k_item.get("api_key")
                if not api_key:
                    continue
                try:
                    c = OmniClient(api_key=api_key, base_url="https://backend.omnidim.io/api/v1")
                    bots = c.agent.list().get("json", {}).get("bots", [])
                    uname = bots[0].get("user_name", f"Trunk {idx+1}") if bots else f"Trunk {idx+1}"
                    
                    billing = fetch_account_live_billing(c, account_name=uname)
                    bal = float(billing.get("current_balance_usd", 0.0))
                    mins = int(billing.get("minutes_left", 0))
                    
                    total_pool_balance += bal
                    total_pool_mins += mins
                    
                    if bal > 0:
                        icon = "🟢"
                        note = f"(`{mins}` Mins Left) — *PRIMARY* ⭐" if idx == 0 else f"(`{mins}` Mins Left) — *ACTIVE*"
                    else:
                        icon = "🔴"
                        note = "(`0` Mins / Balance Low)"
                        
                    account_lines.append(f"{idx+1}. {icon} *{uname.title()}*: `${bal:.2f} USD` {note}")
                except Exception as ex_b:
                    account_lines.append(f"{idx+1}. ⚠️ *Trunk {idx+1}*: `Error fetching balance` ({str(ex_b)[:30]})")

            summary = user_manager.admin_get_category2_summary()
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

            balance_text = (
                "⚡ *[CARRIER TRUNKS & POOL BALANCE]* 🟢\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 *Total Multi-Trunk Pool Balance:* `${total_pool_balance:.2f} USD` (`~{total_pool_mins} Mins`)\n"
                f"📊 *Registered Users:* `{summary.get('total_users', 0)}` | *Active Today:* `{summary.get('active_today', 0)}`\n"
                f"📞 *Total Calls Today:* `{summary.get('calls_today', summary.get('total_calls', 0))}`\n\n"
                "🏢 *Live Carrier Trunk Breakdown:*\n" +
                ("\n".join(account_lines) if account_lines else "• No active trunks connected.") +
                f"\n\n🕒 _Timestamp: {now_str}_"
            )
            self.send_message(chat_id, balance_text)
        except Exception as ex:
            self.send_message(chat_id, f"❌ Error checking balance: `{str(ex)}`")

    def poll_updates(self):
        self.is_running = True
        print("🗄️ @cybercallingDB_bot is LIVE (Telemetry & Event Logger Active)!")
        while self.is_running:
            try:
                from telegram_dedup import acquire_bot_poller_lease
                if not acquire_bot_poller_lease(bot_name="db_bot", lease_sec=15):
                    time.sleep(2)
                    continue

                url = self.base_url + f"/getUpdates?offset={self.offset}&timeout=20"
                s = proxy_manager.get_session()
                resp = s.get(url, timeout=25)
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        uid = update.get("update_id")
                        self.offset = uid + 1
                        try:
                            from telegram_dedup import is_duplicate_update
                            if is_duplicate_update(uid, bot_name="db"):
                                continue
                        except Exception:
                            pass
                        try:
                            self.handle_update(update)
                        except Exception as ex:
                            print("[DB Bot handle error]:", ex)
            except Exception as e:
                time.sleep(3)


db_logger_bot = CyberCallingDBBot()
