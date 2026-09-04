"""
================================================================================
  🚀 OmniDimension Master Auto-Pilot Launcher (start_all.py)
================================================================================
  Single-command launcher that automatically:
  1. Validates all dependencies & .env credentials
  2. Automatically starts the Telegram Voice Bot Engine (@DarkAngelEngine_BOT) in the background
  3. Synchronizes and replicates bots across all OmniDimension accounts
  4. Launches the Enterprise Desktop GUI Command Center
================================================================================
"""

import os
import sys
import threading
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

print("=" * 75)
print("  🚀 Starting OmniDimension Enterprise Command Center & Telegram Bot")
print("=" * 75)

# 1. Start Android Mobile API Server in Background
def run_mobile_server():
    try:
        from mobile_api_server import app, get_local_ip, print_qr_banner
        host_ip = get_local_ip()
        print_qr_banner(host_ip, 5000)
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as ex_mob:
        print("Mobile Server error:", ex_mob)

threading.Thread(target=run_mobile_server, daemon=True).start()

# 2. Start Encrypted Vault Admin Bot (@Cybercallingadmin_bot) in Background
def run_admin_bot():
    try:
        from admin_telegram_bot import CyberCallingAdminBot
        admin_bot = CyberCallingAdminBot()
        admin_bot.poll_updates()
    except Exception as ex_admin:
        print("Admin Bot error:", ex_admin)

threading.Thread(target=run_admin_bot, daemon=True).start()

# 3. Start Master Database & Telemetry Logger Bot (@cybercallingDB_bot) in Background
def run_db_bot():
    try:
        from cybercalling_db_bot import db_logger_bot
        db_logger_bot.poll_updates()
    except Exception as ex_db:
        print("DB Bot error:", ex_db)

threading.Thread(target=run_db_bot, daemon=True).start()

# 4. Launch Desktop GUI (or Headless 24/7 Multi-Bot Daemon)
try:
    from omnidim_hub import OmniDimensionUltimateApp
    print("✅ [Auto-Pilot] Launching Enterprise Command Center GUI, Android App & 3 Telegram Bots...")
    app = OmniDimensionUltimateApp()
    app.mainloop()
except Exception as e:
    print(f"ℹ️ Headless Server Mode ({e}): Running @DarkAngelEngine_BOT, @Cybercallingadmin_bot & @cybercallingDB_bot 24/7...")
    try:
        from telegram_bot import TelegramVoiceBotEngine
        caller = TelegramVoiceBotEngine()
        caller.start_polling()
    except KeyboardInterrupt:
        print("\nShutdown requested by user.")
    except Exception as ex_call:
        print(f"Caller bot error: {ex_call}")
        while True:
            time.sleep(60)
