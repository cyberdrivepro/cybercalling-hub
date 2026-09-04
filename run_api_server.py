"""
================================================================================
  🌐 Standalone Cloud Runner — Mobile API & Webhook Bridge Server
================================================================================
  Lightweight REST API backend for mobile dashboard & cross-host synchronization.
================================================================================
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mobile_api_server import app

def main():
    port = int(os.getenv("PORT", 5000))
    print("=" * 70)
    print(f"  🌐 OmniDimension Mobile API & Cloud Bridge Server on port {port}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
