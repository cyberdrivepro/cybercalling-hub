"""
================================================================================
  🚀 Standalone Cloud Runner — Dark Angel Voice Bot (@DarkAngelEngine_BOT)
================================================================================
  Lightweight, high-speed standalone daemon for deploying @DarkAngelEngine_BOT
  independently on cloud containers (justrunmy.app, Render, Railway, VPS).
  Includes built-in HTTP health-check responder for cloud port bindings.
================================================================================
"""

import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 1. Cloud Health Check Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","service":"DarkAngelEngine_BOT","online":true}')

    def log_message(self, format, *args):
        pass  # Suppress health check spam in logs

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Cloud Health Ping listener bound to port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server note: {e}")

threading.Thread(target=start_health_server, daemon=True).start()

from telegram_bot import TelegramVoiceBotEngine

def main():
    print("=" * 70)
    print("  📞 CyberCalling Voice AI Bot Engine — Standalone Cloud Instance")
    print("=" * 70)
    
    bot = TelegramVoiceBotEngine()
    print(f"🤖 @DarkAngelEngine_BOT is ONLINE & POLLING!")
    
    while True:
        try:
            bot.start_polling()
        except KeyboardInterrupt:
            print("\nShutting down bot gracefully...")
            break
        except Exception as e:
            print(f"⚠️ Polling exception: {e}. Reconnecting in 3s...")
            time.sleep(3)

if __name__ == "__main__":
    main()
