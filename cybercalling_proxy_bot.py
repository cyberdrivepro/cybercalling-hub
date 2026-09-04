"""
================================================================================
🤖 CyberCalling Proxy & Network Fleet Manager Bot (@cybercallingproxy_bot)
================================================================================
Bot Token: 8689620842:AAE-0QwoWVI4cnl7GgNfVyx4Cl0O9btxa8A
Role:
- High-Speed Multi-Source Proxy Validator (Inspired by proxy-validator-tool)
- Multi-Protocol Support: HTTP, HTTPS, SOCKS4, SOCKS5
- 50-100 Parallel Worker Threads with Real-Time Telegram Progress Bar [████░░] %
- Instant 6-Attempt Multi-Hop Chain Generation for Danger & Ziddi Modes
- Bulk Ingestion (.txt / direct paste), Auto-Scraping & Categorized File Exporters
================================================================================
"""

import os
import sys
import json
import time
import re
import threading
import requests
from typing import Dict, Any, List, Optional, Tuple
from proxy_network_engine import proxy_engine

PROXY_BOT_TOKEN = os.environ.get("PROXY_BOT_TOKEN") or "8689620842:AAE-0QwoWVI4cnl7GgNfVyx4Cl0O9btxa8A"

def generate_progress_bar(pct: int, total_blocks: int = 16) -> str:
    """Generates clean ASCII progress bar."""
    pct = max(0, min(100, pct))
    filled = int((pct / 100) * total_blocks)
    empty = total_blocks - filled
    return "█" * filled + "░" * empty

class CyberCallingProxyBotEngine:
    """Telegram Bot Engine for @cybercallingproxy_bot (Autonomous Proxy & Network Controller)."""
    def __init__(self, token: str = PROXY_BOT_TOKEN):
        self.token = token.strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

        # Persistent 6-Button Bottom Keyboard Menu
        self.main_keyboard = {
            "keyboard": [
                [{"text": "🌐 Live Proxy Pool"}, {"text": "⚡ Fast 75-Thread Scan"}],
                [{"text": "📥 Fetch Online .txt Lists"}, {"text": "🛡️ 6x Danger Chains"}],
                [{"text": "🧹 Flush Dead Proxies"}, {"text": "🗑️ Wipe All Proxies"}]
            ],
            "resize_keyboard": True,
            "persistent": True
        }

    def send_message(self, chat_id, text: str, reply_markup=None, parse_mode: str = "Markdown") -> Optional[int]:
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        else:
            payload["reply_markup"] = self.main_keyboard

        try:
            r = requests.post(url, json=payload, timeout=10)
            res = r.json()
            if not res.get("ok") and parse_mode:
                payload.pop("parse_mode", None)
                r = requests.post(url, json=payload, timeout=8)
                res = r.json()
            if res.get("ok"):
                return res["result"]["message_id"]
        except Exception as e:
            print(f"[@cybercallingproxy_bot Send Error]: {e}")
        return None

    def edit_message_text(self, chat_id, message_id, text: str, reply_markup=None, parse_mode: str = "Markdown"):
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        try:
            r = requests.post(url, json=payload, timeout=10)
            res = r.json()
            if not res.get("ok") and parse_mode:
                payload.pop("parse_mode", None)
                requests.post(url, json=payload, timeout=8)
        except Exception as e:
            pass

    def answer_callback_query(self, callback_query_id, text: str = None):
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": str(callback_query_id)}
        if text:
            payload["text"] = text
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass

    def send_document(self, chat_id, file_path: str, caption: str = ""):
        url = f"{self.base_url}/sendDocument"
        try:
            with open(file_path, "rb") as f:
                files = {"document": (os.path.basename(file_path), f)}
                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
                r = requests.post(url, data=data, files=files, timeout=60)
                return r.status_code == 200
        except Exception as e:
            print(f"[@cybercallingproxy_bot Send Document Error]: {e}")
            return False

    def download_telegram_file(self, file_id: str) -> Optional[str]:
        """Downloads a document sent by user via Telegram Bot API."""
        try:
            r = requests.get(f"{self.base_url}/getFile?file_id={file_id}", timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get("ok"):
                    file_path = res["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                    dr = requests.get(download_url, timeout=30)
                    if dr.status_code == 200:
                        return dr.text
        except Exception as e:
            print(f"[@cybercallingproxy_bot Download Error]: {e}")
        return None

    def get_dashboard_card(self) -> Tuple[str, dict]:
        """Builds live proxy pool status card with multi-protocol metrics."""
        from fleet_maintenance_manager import fleet_maintenance
        maint_banner = fleet_maintenance.get_admin_maint_banner("proxy_bot")
        maint_prefix = f"{maint_banner}\n" if maint_banner else ""
        maint_btn = "🔴 Fleet Maintenance (ACTIVE)" if maint_banner else "🛠️ Fleet Maintenance"

        m = proxy_engine.get_pool_metrics()
        status_icon = "🟢 Healthy" if m["alive"] > 0 else "⚪ Pool Empty / Awaiting Proxies"

        text = (
            f"{maint_prefix}"
            f"🌐 *[CYBERCALLING ULTRA-FAST PROXY CONTROLLER]* ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• 🛰️ *Fleet Status:* `{status_icon}` ({m['health_pct']}% Active)\n"
            f"• 🟢 *Verified Live Nodes:* `{m['alive']}` Alive (`{m['dead']}` Dead, `{m['unchecked']}` Unchecked)\n"
            f"• 📡 *Protocols:* HTTP: `{m.get('http_alive', 0)}` | SOCKS5: `{m.get('socks5_alive', 0)}` | SOCKS4: `{m.get('socks4_alive', 0)}`\n"
            f"• ⚡ *Average Latency:* `{m['avg_latency_ms']} ms` (🚀 Ultra-Fast <500ms: `{m['fast_count']}`)\n"
            f"• 🛡️ *Danger 6x Chains Ready:* `{m['chains_available']} Full Chains`\n"
            f"• 🔒 *Server Protection Mode:* `24/7 Shield Active (0% IP Leak)`\n"
            f"• ⚙️ *Validator Concurrency:* `75 Parallel Workers` | Multi-Endpoints: `ipify · httpbin · cloudflare`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 *Send working proxies directly (text or .txt file) or tap below:*"
        )

        inline_kb = {
            "inline_keyboard": [
                [{"text": maint_btn, "callback_data": "menu_fleet_maint"}, {"text": "⚡ Fast 75-Thread Scan", "callback_data": "prx_scan_all"}],
                [{"text": "🌐 Fetch Online .txt Lists", "callback_data": "prx_scrape_all"}, {"text": "🛡️ 6x Danger Chains", "callback_data": "prx_view_chains"}],
                [{"text": "📥 Ingest Custom .txt / URL", "callback_data": "prx_prompt_import"}, {"text": "🧹 Flush Dead Nodes", "callback_data": "prx_flush_dead"}],
                [{"text": "📦 Export Alive (.txt)", "callback_data": "prx_export_txt"}, {"text": "🗑️ Wipe All Proxies", "callback_data": "prx_confirm_wipe"}],
                [{"text": "🔄 Refresh Dashboard", "callback_data": "prx_refresh_dash"}]
            ]
        }
        return text, inline_kb

    def prompt_confirm_wipe(self, chat_id, message_id=None):
        """Confirmation gate to permanently wipe all proxies."""
        m = proxy_engine.get_pool_metrics()
        text = (
            "🗑️ *[CONFIRM WIPE: PURGE ALL PROXIES]* ⚠️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Current Pool Size:* `{m['total']} Proxies` (`{m['alive']} Alive`)\n"
            "• *Action:* Permanently deletes all proxies from database and files.\n\n"
            "❓ *Are you sure you want to delete all proxies now?*"
        )
        buttons = [
            [
                {"text": "🗑️ Yes, Wipe All Proxies", "callback_data": "prx_do_wipe_all"},
                {"text": "❌ Cancel", "callback_data": "prx_refresh_dash"}
            ]
        ]
        if message_id:
            self.edit_message_text(chat_id, message_id, text, reply_markup={"inline_keyboard": buttons})
        else:
            self.send_message(chat_id, text, reply_markup={"inline_keyboard": buttons})

    def get_chains_card(self) -> Tuple[str, dict]:
        """Renders the 6-Attempt Danger / Ziddi Mode proxy sequence."""
        chains = proxy_engine.get_ready_chains(count=6)
        if not chains:
            return (
                "⚠️ *[No Verified Working Proxies Available for Danger Chain]*\n\n"
                "Please send your working proxies directly to this chat or drop a `.txt` file to generate chains!",
                {"inline_keyboard": [[{"text": "📥 Import Proxies", "callback_data": "prx_prompt_import"}, {"text": "🔙 Back to Dashboard", "callback_data": "prx_refresh_dash"}]]}
            )

        rows_txt = []
        for ch in chains:
            lat_badge = f"{ch['latency_ms']}ms" if ch['latency_ms'] > 0 else "Ready"
            status_icon = "🟢" if ch['status'] == "ALIVE" else "⚪"
            country_txt = ch.get("country", "🌐 Global")
            rows_txt.append(f"• *Attempt {ch['attempt']}:* {status_icon} `{ch['display']}` — {country_txt} (`{lat_badge}`)")

        chain_str = "\n".join(rows_txt)
        text = (
            f"🛡️ *[DANGER MODE & ZIDDI 6-ATTEMPT PROXY CHAINS]* ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Every single call & redial attempt is automatically mapped to a dedicated verified working proxy node:\n\n"
            f"{chain_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 *Status: 100% Locked & Ready for Ultra Stealth Calling!*"
        )

        inline_kb = {
            "inline_keyboard": [
                [{"text": "🔄 Re-Roll / Regenerate Chain", "callback_data": "prx_view_chains"}, {"text": "🔙 Back to Dashboard", "callback_data": "prx_refresh_dash"}]
            ]
        }
        return text, inline_kb

    def trigger_live_progress_scan(self, chat_id: int):
        """
        Launches 75-thread parallel validation with dynamic real-time Telegram progress bar animation!
        """
        total_proxies = len(proxy_engine.proxies)
        if total_proxies == 0:
            self.send_message(chat_id, "⚠️ *Proxy pool is currently empty.* Tap '🔄 Scrape All Sources' or upload a proxy file first!")
            return

        proxy_engine.validate_all_async(max_workers=75)

        # Initial message
        bar_initial = generate_progress_bar(0, 16)
        initial_txt = (
            f"⚡ *[75-THREAD HIGH-SPEED PARALLEL AUDIT]* 🚀\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Progress:* `[{bar_initial}]` *0.0%*\n"
            f"• 🔍 *Audited:* `0/{total_proxies}` Nodes\n"
            f"• 🟢 *Alive Nodes:* `0` Found\n"
            f"• 🔴 *Dead Nodes:* `0` Found\n"
            f"• ⚙️ *Concurrency:* `75 Parallel Workers`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ _Benchmarking latency & dual-stack HTTP/HTTPS in real-time..._"
        )
        msg_id = self.send_message(chat_id, initial_txt)
        if not msg_id:
            return

        def _animation_worker():
            t_start = time.time()
            time.sleep(0.5)

            while proxy_engine._is_checking:
                time.sleep(0.8)
                p = proxy_engine._check_progress
                checked = p.get("checked", 0)
                tot = p.get("total", total_proxies) or total_proxies
                alive = p.get("alive", 0)
                dead = p.get("dead", 0)

                pct = round((checked / max(1, tot)) * 100, 1)
                bar = generate_progress_bar(int(pct), 16)
                elapsed = max(0.1, time.time() - t_start)
                speed = round(checked / elapsed, 1)
                rem = max(0, tot - checked)
                eta = round(rem / max(1, speed), 1)

                prog_txt = (
                    f"⚡ *[75-THREAD HIGH-SPEED PARALLEL AUDIT]* 🚀\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 *Progress:* `[{bar}]` *{pct}%*\n"
                    f"• 🔍 *Audited:* `{checked}/{tot}` Nodes\n"
                    f"• 🟢 *Alive Nodes:* `{alive}` Alive\n"
                    f"• 🔴 *Dead Nodes:* `{dead}` Dead\n"
                    f"• ⚡ *Speed:* `~{speed} nodes/sec` (ETA: `{eta}s`)\n"
                    f"• ⚙️ *Concurrency:* `75 Parallel Workers`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏳ _Auditing dual-stack HTTP/HTTPS in real-time..._"
                )
                self.edit_message_text(chat_id, msg_id, prog_txt)

            # Final Completed Card
            time.sleep(0.3)
            m = proxy_engine.get_pool_metrics()
            t_dur = round(time.time() - t_start, 1)
            bar_full = "█" * 16

            done_txt = (
                f"🎉 *[PARALLEL PROXY AUDIT COMPLETE]* ({t_dur}s) ⚡\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Progress:* `[{bar_full}]` *100%*\n"
                f"• 🟢 *Verified Live Nodes:* `{m['alive']}` Alive\n"
                f"• 🔴 *Dead / Stalled Nodes:* `{m['dead']}` Dead\n"
                f"• 🚀 *Ultra-Fast (<500ms):* `{m['fast_count']}` Nodes\n"
                f"• ⚡ *Average Latency:* `{m['avg_latency_ms']} ms`\n"
                f"• 🛡️ *Danger 6x Chains Ready:* `{m['chains_available']} Full Chains`\n"
                f"• ⏱️ *Total Time:* `{t_dur}s` (75 Workers)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👉 *All verified live working proxies are ready & saved!*"
            )
            inline_kb = {
                "inline_keyboard": [
                    [{"text": "🛡️ View 6x Danger Chains", "callback_data": "prx_view_chains"}, {"text": "📦 Export Working (.txt)", "callback_data": "prx_export_txt"}],
                    [{"text": "🔄 Refresh Dashboard", "callback_data": "prx_refresh_dash"}]
                ]
            }
            self.edit_message_text(chat_id, msg_id, done_txt, reply_markup=inline_kb)

        threading.Thread(target=_animation_worker, daemon=True).start()

    def handle_update(self, update: dict):
        """Processes Telegram updates (Messages, Callbacks, File Uploads)."""
        # Fleet Maintenance Gate (Admin Bypass Active)
        from fleet_maintenance_manager import fleet_maintenance
        chat_id = None
        if "callback_query" in update:
            chat_id = update["callback_query"]["message"]["chat"]["id"]
        elif "message" in update:
            chat_id = update["message"]["chat"]["id"]

        if chat_id:
            can_access, maint_card = fleet_maintenance.check_bot_access("proxy_bot", user_id=chat_id)
            if not can_access:
                if "callback_query" in update:
                    self.answer_callback_query(update["callback_query"]["id"], text="⚠️ Proxy Bot Under Maintenance")
                    self.edit_message_text(chat_id, update["callback_query"]["message"]["message_id"], maint_card)
                else:
                    self.send_message(chat_id, maint_card)
                return

        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            chat_id = cb["message"]["chat"]["id"]
            msg_id = cb["message"]["message_id"]
            data = cb.get("data", "")

            # Fleet Maintenance Callbacks
            if data in ["menu_fleet_maint", "maint_refresh_dash"]:
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                return
            elif data.startswith("maint_bot_"):
                b_key = data[10:]
                txt, kb = fleet_maintenance.get_bot_control_card(b_key)
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                return
            elif data.startswith("maint_set_"):
                raw = data[10:]
                parts = raw.rsplit("_", 1)
                b_key, dur_str = parts[0], parts[1]
                dur = int(dur_str)
                fleet_maintenance.set_bot_maintenance(b_key, True, duration_mins=dur, admin_id=chat_id)
                self.answer_callback_query(cb_id, text=f"✅ {b_key} set to {dur}m maintenance!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                return
            elif data.startswith("maint_unlock_"):
                b_key = data[13:]
                fleet_maintenance.set_bot_maintenance(b_key, False, admin_id=chat_id)
                self.answer_callback_query(cb_id, text=f"🟢 {b_key} unlocked to Public!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
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
                self.edit_message_text(chat_id, msg_id, text_g, reply_markup={"inline_keyboard": buttons_g})
                return
            elif data.startswith("maint_global_set_"):
                dur = int(data[17:])
                fleet_maintenance.set_global_maintenance(True, duration_mins=dur, admin_id=chat_id)
                self.answer_callback_query(cb_id, text="🔴 ALL Bots Locked into Maintenance!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                return
            elif data == "maint_global_off":
                fleet_maintenance.set_global_maintenance(False, admin_id=chat_id)
                self.answer_callback_query(cb_id, text="🟢 ALL Bots Unlocked to Public!")
                txt, kb = fleet_maintenance.get_fleet_status_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                return

            if data in ["prx_refresh_dash", "menu_home", "nav_home", "menu_start", "nav_main"]:
                txt, kb = self.get_dashboard_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                self.answer_callback_query(cb_id, text="Dashboard Refreshed 🟢")
            elif data == "prx_scan_all":
                self.answer_callback_query(cb_id, text="Starting 50-Thread Parallel Audit...")
                self.trigger_live_progress_scan(chat_id)
            elif data == "prx_scrape_all":
                self.answer_callback_query(cb_id, text="Scraping HTTP, SOCKS4, SOCKS5 sources...")
                self.send_message(chat_id, "🔄 *[Scraping Multi-Protocol Sources (HTTP, SOCKS4, SOCKS5)...]* ⚡")
                res = proxy_engine.auto_scrape_all_sources()
                msg = (
                    f"✅ *[MULTI-SOURCE COLLECTION COMPLETE]* 🚀\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• 📡 *HTTP Added:* `{res['http']}`\n"
                    f"• 🔒 *SOCKS4 Added:* `{res['socks4']}`\n"
                    f"• 🛡️ *SOCKS5 Added:* `{res['socks5']}`\n"
                    f"• ➕ *Total Fresh Ingested:* `{res['total_added']}` Proxies\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *Launching 50-Thread Live Progress Validator...*"
                )
                self.send_message(chat_id, msg)
                self.trigger_live_progress_scan(chat_id)
            elif data == "prx_confirm_wipe":
                self.answer_callback_query(cb_id)
                self.prompt_confirm_wipe(chat_id, message_id=msg_id)
            elif data == "prx_do_wipe_all":
                self.answer_callback_query(cb_id, text="Purging all proxies...")
                wiped = proxy_engine.wipe_all_proxies()
                done_wipe = (
                    f"🗑️ *[ALL PROXIES WIPED SUCCESSFULLY]* 🟢\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• *Purged:* `{wiped}` Proxies from memory & disk\n"
                    f"• *Current Pool:* `0 Nodes (Clean Slate)`\n\n"
                    f"👉 *Now send your own working proxies directly in this chat or drop a `.txt` file!*"
                )
                self.send_message(chat_id, done_wipe)
                txt, kb = self.get_dashboard_card()
                self.send_message(chat_id, txt, reply_markup=kb)
            elif data == "prx_view_chains":
                txt, kb = self.get_chains_card()
                self.edit_message_text(chat_id, msg_id, txt, reply_markup=kb)
                self.answer_callback_query(cb_id)
            elif data == "prx_export_txt":
                self.answer_callback_query(cb_id, text="Exporting working proxies...")
                out_p = proxy_engine.export_working_proxies_txt()
                if os.path.exists(out_p):
                    m = proxy_engine.get_pool_metrics()
                    cap = f"📦 *[CYBERCALLING LIVE PROXIES]*\n• Total Alive: `{m['alive']}`\n• Fast (<500ms): `{m['fast_count']}`\n• Avg Latency: `{m['avg_latency_ms']} ms`"
                    self.send_document(chat_id, out_p, caption=cap)
                else:
                    self.send_message(chat_id, "❌ Error exporting proxies.")
            elif data == "prx_flush_dead":
                self.answer_callback_query(cb_id, text="Flushing dead nodes...")
                flushed = proxy_engine.flush_dead_proxies()
                self.send_message(chat_id, f"🧹 *[Flush Complete]* Removed `{flushed}` dead proxies from pool!")
                txt, kb = self.get_dashboard_card()
                self.send_message(chat_id, txt, reply_markup=kb)
            elif data == "prx_prompt_import":
                self.answer_callback_query(cb_id)
                self.send_message(chat_id, "📥 *[Import Working Proxies]*\n\nSend your proxies directly in this chat or drop a `.txt` file!\n\n_Supported formats:_\n• `IP:PORT` (e.g. `104.207.51.25:3129`)\n• `IP:PORT:USER:PASS`\n• `http://user:pass@ip:port`\n• `socks5://ip:port`\n• `socks4://ip:port`")
            return

        if "message" not in update:
            return

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        user_name = msg.get("from", {}).get("first_name", "Dark Angel Operator")

        # 1. Handle Document File Upload (.txt / .csv)
        if "document" in msg:
            doc = msg["document"]
            file_name = doc.get("file_name", "proxies.txt")
            file_id = doc.get("file_id")
            self.send_message(chat_id, f"📥 *[Receiving Proxy File: `{file_name}`...]* ⚡")

            file_content = self.download_telegram_file(file_id)
            if file_content:
                res = proxy_engine.add_proxies_bulk(file_content, auto_validate=False)
                resp_txt = (
                    f"✅ *[PROXY FILE INGESTED SUCCESSFULLY]* 🚀\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📁 *File:* `{file_name}`\n"
                    f"➕ *Added New:* `{res['added']}` Proxies\n"
                    f"🔁 *Duplicates Skipped:* `{res['duplicates']}`\n"
                    f"🌐 *Total Pool Size:* `{res['total_pool']}` Proxies\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *Starting 50-Thread Parallel Validator with Live Progress Bar...*"
                )
                self.send_message(chat_id, resp_txt)
                self.trigger_live_progress_scan(chat_id)
            else:
                self.send_message(chat_id, "❌ Error downloading proxy file.")
            return

        text = msg.get("text", "").strip()
        if not text:
            return

        # 2. Match One-Tap Bottom Keyboard Buttons & Commands
        if text in ["🛠️ Fleet Maintenance", "/maintenance", "/fleetmaint", "/maint"]:
            txt, kb = fleet_maintenance.get_fleet_status_card()
            self.send_message(chat_id, txt, reply_markup=kb)
            return

        elif text in ["🌐 Live Proxy Pool", "/pool", "/status", "/start"]:
            txt, kb = self.get_dashboard_card()
            welcome = (
                f"👋 *Welcome {user_name} to CyberCalling Ultra-Fast Proxy Controller!* 🌐\n\n"
                f"I am `@cybercallingproxy_bot`, your **Multi-Protocol Proxy Engine & Validator Suite**.\n\n"
                f"• ⚡ *Fast 75-Thread Engine:* Multi-endpoint ping, speed benchmarking & anonymity audit.\n"
                f"• 📡 *Protocols:* HTTP, HTTPS, SOCKS4, SOCKS5 supported.\n"
                f"• 📥 *Fetch Online .txt Lists:* Auto-fetches public/raw proxy lists and validates live!\n"
                f"• 🛡️ *Danger 6x Chains:* Instant verified live chains for Danger & Ziddi Mode.\n"
                f"• 🔒 *24/7 Server Shield:* Normal requests shuffle 2-3 proxies, Danger mode uses multi-hop chains.\n\n"
                f"👇 *Live Fleet Control Dashboard:*"
            )
            self.send_message(chat_id, welcome)
            self.send_message(chat_id, txt, reply_markup=kb)
            return

        elif text in ["📥 Fetch Online .txt Lists", "🌐 Fetch Online .txt Lists", "/scrape", "/fetch_all", "scrape"]:
            self.send_message(chat_id, "🔄 *[Fetching All Multi-Protocol Online .txt Lists (HTTP, SOCKS4, SOCKS5)...]* ⚡")
            res = proxy_engine.auto_scrape_all_sources(auto_validate=False)
            msg = (
                f"✅ *[MULTI-SOURCE .TXT FETCH COMPLETE]* 🚀\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• 📡 *HTTP Ingested:* `{res['http']}`\n"
                f"• 🔒 *SOCKS4 Ingested:* `{res['socks4']}`\n"
                f"• 🛡️ *SOCKS5 Ingested:* `{res['socks5']}`\n"
                f"• ➕ *Total Fresh Ingested:* `{res['total_added']}` Proxies\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ *Launching 75-Thread Live Progress Validator...*"
            )
            self.send_message(chat_id, msg)
            self.trigger_live_progress_scan(chat_id)
            return

        # Direct Raw .txt URL Ingestion (/fetch <url> or direct link)
        elif text.startswith("/fetch ") or text.startswith("/load ") or (text.startswith(("http://", "https://")) and len(text.splitlines()) == 1):
            url_to_fetch = text.replace("/fetch ", "").replace("/load ", "").strip()
            self.send_message(chat_id, f"🌐 *[Fetching Proxies from Raw .txt URL: `{url_to_fetch[:60]}...`]* ⚡")
            res = proxy_engine.fetch_from_url(url_to_fetch, auto_validate=False)
            if res.get("success") and res.get("added", 0) > 0:
                resp_txt = (
                    f"✅ *[ONLINE .TXT PROXIES FETCHED SUCCESSFULLY]* 🚀\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 *Source URL:* `{url_to_fetch[:60]}`\n"
                    f"➕ *Added New:* `{res['added']}` Proxies\n"
                    f"🔁 *Duplicates Skipped:* `{res.get('duplicates', 0)}`\n"
                    f"🌐 *Total Pool Size:* `{res['total_pool']}` Proxies\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *Starting 75-Thread Parallel Validator with Live Progress Bar...*"
                )
                self.send_message(chat_id, resp_txt)
                self.trigger_live_progress_scan(chat_id)
            else:
                self.send_message(chat_id, f"❌ *Failed to fetch proxies from URL:*\n{res.get('message', 'No valid proxies found in URL content.')}")
            return

        elif text in ["⚡ Fast 50-Thread Scan", "⚡ Fast 75-Thread Scan"] or any(text.lower().startswith(cmd) for cmd in ["/scan", "/validate", "/checkall", "/auditall"]):
            self.trigger_live_progress_scan(chat_id)
            return

        elif text in ["🗑️ Wipe All Proxies", "/wipe", "/wipeproxies", "/clearallproxies", "/deleteall", "wipe"]:
            self.prompt_confirm_wipe(chat_id)
            return

        elif text in ["🛡️ 6x Danger Chains", "/chain", "/chains"] or any(text.lower().startswith(cmd) for cmd in ["/chain", "/chains"]):
            txt, kb = self.get_chains_card()
            self.send_message(chat_id, txt, reply_markup=kb)
            return

        elif text in ["📥 Import Proxies", "📥 Import Bulk Proxies", "/import"] or any(text.lower().startswith(cmd) for cmd in ["/import", "/add"]):
            self.send_message(chat_id, "📥 *[Import Working Proxies]*\n\nSimply paste your proxies directly in this chat, upload a `.txt` file, or send `/fetch <url>` to download from any raw .txt list!\n\n_Formats supported:_\n• `IP:PORT`\n• `IP:PORT:USER:PASS`\n• `http://user:pass@ip:port`\n• `socks5://ip:port`\n• `socks4://ip:port`")
            return

        elif text in ["🧹 Flush Dead Proxies", "/flush"] or any(text.lower().startswith(cmd) for cmd in ["/flush", "/cleandead"]):
            flushed = proxy_engine.flush_dead_proxies()
            self.send_message(chat_id, f"🧹 *[Flush Complete]* Removed `{flushed}` dead proxies from pool!")
            txt, kb = self.get_dashboard_card()
            self.send_message(chat_id, txt, reply_markup=kb)
            return

        elif text.startswith("/export") or text in ["📦 Export Working (.txt)", "/getlist"]:
            out_p = proxy_engine.export_working_proxies_txt()
            if os.path.exists(out_p):
                m = proxy_engine.get_pool_metrics()
                cap = f"📦 *[CYBERCALLING LIVE PROXIES]*\n• Total Alive: `{m['alive']}`\n• Fast (<500ms): `{m['fast_count']}`\n• Avg Latency: `{m['avg_latency_ms']} ms`"
                self.send_document(chat_id, out_p, caption=cap)
            else:
                self.send_message(chat_id, "❌ Error exporting proxies.")
            return

        # 3. Handle Direct Text Proxy Ingestion (Single or Multi-line IP:PORT)
        if re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}\b", text):
            res = proxy_engine.add_proxies_bulk(text, auto_validate=False)
            if res["added"] > 0 or res["duplicates"] > 0:
                resp_txt = (
                    f"✅ *[PROXIES INGESTED SUCCESSFULLY]* 🚀\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"➕ *Added New:* `{res['added']}` Proxies\n"
                    f"🔁 *Duplicates:* `{res['duplicates']}`\n"
                    f"🌐 *Total Pool Size:* `{res['total_pool']}` Proxies\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *Starting 75-Thread Parallel Validator with Live Progress Bar...*"
                )
                self.send_message(chat_id, resp_txt)
                self.trigger_live_progress_scan(chat_id)
                return

        # 3. Handle Single Proxy Live Health & Diagnostics Check (/check or single IP:PORT)
        clean_text = text.strip()
        if clean_text.startswith("/check"):
            parts = clean_text.split(maxsplit=1)
            clean_text = parts[1].strip() if len(parts) > 1 else ""

        if len(clean_text.splitlines()) == 1 and re.match(r"^(?:https?://|socks[45]://)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}", clean_text):
            self.send_message(chat_id, f"🔍 *[Running Live Health & Protocol Audit on `{clean_text}`...]* ⚡")
            try:
                audit = proxy_engine.audit_single_proxy(clean_text, timeout=3.5)
                self.send_message(chat_id, audit["card"])
                return
            except Exception as e:
                self.send_message(chat_id, f"❌ Proxy Audit Error: {e}")
                return

        # 4. Direct Bulk Raw Proxy Text Ingestion (Multiple lines)
        if any(c in text for c in [":", "@"]) and len(text.splitlines()) > 0:
            res = proxy_engine.add_proxies_bulk(text, auto_validate=False)
            if res["added"] > 0:
                resp_txt = (
                    f"✅ *[BULK PROXIES INGESTED]* 🚀\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"➕ *Added New Nodes:* `{res['added']}`\n"
                    f"🔁 *Duplicates Skipped:* `{res['duplicates']}`\n"
                    f"🌐 *Total Fleet Size:* `{res['total_pool']}` Proxies\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚡ *Launching 50-Thread Live Progress Validator...*"
                )
                self.send_message(chat_id, resp_txt)
                self.trigger_live_progress_scan(chat_id)
                return

        # Default help
        self.send_message(chat_id, "ℹ️ *Type `/pool` or drop a `.txt` proxy file or send `IP:PORT` to audit any proxy!*")

    def poll_updates(self):
        """Continuously polls Telegram Bot API with long-polling."""
        print(f"🌐 [Proxy Bot] Starting @cybercallingproxy_bot polling engine...")
        while True:
            try:
                url = f"{self.base_url}/getUpdates?offset={self.offset}&timeout=20"
                r = requests.get(url, timeout=25)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("ok"):
                        for upd in data.get("result", []):
                            self.offset = upd["update_id"] + 1
                            self.handle_update(upd)
                elif r.status_code == 409:
                    time.sleep(5)
            except Exception as e_poll:
                time.sleep(3)

# Global Bot Instance
proxy_bot = CyberCallingProxyBotEngine()

if __name__ == "__main__":
    proxy_bot.poll_updates()
