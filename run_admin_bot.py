"""
================================================================================
  🔐 Standalone Cloud Runner — Encrypted Key Vault Admin Bot (@Cybercallingadmin_bot)
================================================================================
  Lightweight, high-security standalone daemon for deploying @Cybercallingadmin_bot
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
        self.wfile.write(b'{"status":"healthy","service":"Cybercallingadmin_bot","online":true}')

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        print(f"🌐 Cloud Health Ping listener bound to port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Health server note: {e}")

threading.Thread(target=start_health_server, daemon=True).start()

from admin_telegram_bot import CyberCallingAdminBot

def main():
    print("=" * 70)
    print("  🔐 CyberCalling Encrypted Admin Bot — Standalone Cloud Instance")
    print("=" * 70)
    
    bot = CyberCallingAdminBot()
    print("🤖 @Cybercallingadmin_bot is ONLINE & POLLING with AES-256 Protection!")
    
    while True:
        try:
            bot.poll_updates()
        except KeyboardInterrupt:
            print("\nShutting down admin bot gracefully...")
            break
        except Exception as e:
            print(f"⚠️ Polling exception: {e}. Reconnecting in 3s...")
            time.sleep(3)

if __name__ == "__main__":
    main()
