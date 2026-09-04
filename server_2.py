"""
================================================================================
  🚀 CyberCalling 2.0 — Enterprise Master Server & Multi-Daemon Supervisor
================================================================================
  Single-command launcher that runs:
  1. FastAPI Async Core Gateway (WebSockets, REST API, Glassmorphism Dashboard)
  2. Background Voice AI Telegram Bot (@DarkAngelEngine_BOT)
  3. Background Encrypted Vault & TOTP Admin Bot (@Cybercallingadmin_bot)
================================================================================
"""

import os
import sys
import time
import threading
import uvicorn
from dotenv import load_dotenv

load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_caller_bot():
    try:
        from bot.caller_bot import CyberCallerBot
        bot = CyberCallerBot()
        bot.poll_updates()
    except Exception as e:
        print(f"Caller Bot Thread Exception: {e}")

def run_admin_bot():
    try:
        from bot.admin_bot import CyberAdminBot
        admin = CyberAdminBot()
        admin.poll_updates()
    except Exception as e:
        print(f"Admin Bot Thread Exception: {e}")

def main():
    print("=" * 75)
    print("  🚀 Starting CyberCalling 2.0 Enterprise Platform")
    print("=" * 75)
    print("  • Web Dashboard:    http://localhost:8000")
    print("  • Voice AI Bot:     @DarkAngelEngine_BOT")
    print("  • Encrypted Vault:  @Cybercallingadmin_bot (AES-256-GCM + TOTP)")
    print("  • Live WebSockets:  ws://localhost:8000/ws/calls")
    print("=" * 75)
    
    # 0. Start Tor Daemon (if on Linux / Hugging Face Spaces)
    try:
        from tor_service import tor_service
        tor_service.start()
        print("  • Tor SOCKS5 Proxy: socks5h://127.0.0.1:9050 (Initializing)")
    except Exception as ex_tor:
        print(f"  • Tor Daemon:       Offline/Unavailable ({ex_tor})")

    # 1. Start Background Telegram Bots
    t_caller = threading.Thread(target=run_caller_bot, daemon=True)
    t_caller.start()
    
    t_admin = threading.Thread(target=run_admin_bot, daemon=True)
    t_admin.start()
    
    # 2. Launch FastAPI Async Server
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
