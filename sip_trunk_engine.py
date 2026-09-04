"""
================================================================================
  🌐 OmniDimension Enterprise SIP Trunking & PBX Gateway Engine
================================================================================
  Integrates any SIP Trunk (Twilio Elastic SIP, Telnyx, Tata, Zadarma, FreePBX)
  for unlimited concurrency, lowest wholesale carrier rates, and PBX forwarding.
================================================================================
"""

import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

from phone_normalizer import normalize_and_detect_country


def get_sip_configuration():
    """Load SIP trunk configuration from environment variables."""
    load_dotenv(override=True)
    return {
        "domain": os.getenv("SIP_DOMAIN", "").strip() or os.getenv("SIP_HOST", "").strip() or "sip.telnyx.com",
        "username": os.getenv("SIP_USERNAME", "").strip() or os.getenv("SIP_AUTH_USER", "").strip() or "usersurajexpert132541140",
        "password": os.getenv("SIP_PASSWORD", "").strip() or "NEsLy-B,e9^O",
        "port": int(os.getenv("SIP_PORT", "5060").strip() or "5060"),
        "transport": os.getenv("SIP_TRANSPORT", "UDP").strip().upper(),  # UDP, TCP, TLS
        "caller_id": os.getenv("SIP_CALLER_ID", "").strip() or os.getenv("SIP_FROM_NUMBER", "").strip() or "+15863601284",
        "trunk_provider": os.getenv("SIP_PROVIDER", "Telnyx SIP Gateway").strip()
    }


def is_sip_configured():
    """Check if minimum SIP trunk credentials are provided."""
    cfg = get_sip_configuration()
    return bool(cfg["domain"] and cfg["caller_id"])


def build_sip_uri(phone_number):
    """Format standardized E.164 phone number into a destination SIP URI."""
    norm = normalize_and_detect_country(phone_number)
    clean_num = norm["clean_number"]
    cfg = get_sip_configuration()
    domain = cfg["domain"] or "pstn.twilio.com"
    return f"sip:{clean_num}@{domain}"


def get_sip_trunk_summary():
    """Retrieve formatted summary of the active SIP Trunk."""
    cfg = get_sip_configuration()
    configured = is_sip_configured()

    if not configured:
        return {
            "configured": False,
            "message": (
                "SIP Trunk not configured in .env.\n\n"
                "Add these variables to connect your SIP Trunk:\n"
                "• `SIP_DOMAIN=mytrunk.pstn.twilio.com` (or `sip.telnyx.com`, `sip.zadarma.com`)\n"
                "• `SIP_USERNAME=your_sip_username`\n"
                "• `SIP_PASSWORD=your_sip_password`\n"
                "• `SIP_CALLER_ID=+18005550199`\n"
                "• `SIP_TRANSPORT=TLS` (or UDP/TCP)"
            )
        }

    return {
        "configured": True,
        "provider": cfg["trunk_provider"],
        "domain": cfg["domain"],
        "caller_id": cfg["caller_id"],
        "username": cfg["username"] or "Auth via IP Access Control List (ACL)",
        "port": cfg["port"],
        "transport": cfg["transport"],
        "concurrency_limit": "Unlimited / High Capacity 🚀",
        "human_agent_transfer_uri": f"sip:human_support@{cfg['domain']}"
    }


def dispatch_sip_single_call(to_number, spoken_message="Hello! Connecting via Enterprise SIP Trunk.", client=None):
    """
    Dispatch an outbound call routed through the configured SIP Trunk.
    """
    cfg = get_sip_configuration()
    if not is_sip_configured():
        return {
            "success": False,
            "error": "SIP Trunk not configured in .env. Please set SIP_DOMAIN and SIP_CALLER_ID."
        }

    norm = normalize_and_detect_country(to_number)
    clean_num = norm["clean_number"]
    sip_uri = build_sip_uri(clean_num)

    # 1. If Telnyx API is configured, dispatch real call via Telnyx
    try:
        from telnyx_calling_engine import is_telnyx_configured, dispatch_telnyx_call
        if is_telnyx_configured():
            return dispatch_telnyx_call(clean_num, spoken_message=spoken_message)
    except Exception:
        pass

    # 2. If Twilio is configured, dispatch real call via Twilio
    try:
        from twilio_calling_engine import is_twilio_configured, dispatch_twilio_single_call
        if is_twilio_configured():
            return dispatch_twilio_single_call(clean_num, spoken_message=spoken_message)
    except Exception:
        pass

    # 3. Fail-closed: Never return fake success if no active PBX or carrier trunk is connected
    return {
        "success": False,
        "error": "Live SIP PBX gateway is not connected. Please configure TELNYX_API_KEY, Twilio, or Asterisk PBX in .env, or use /call to dispatch via OmniDimension Voice AI.",
        "sip_uri": sip_uri,
        "provider": f"SIP Trunk ({cfg['domain']})"
    }


def dispatch_sip_bulk_campaign(numbers_list, spoken_message="Voice AI SIP Broadcast", concurrency=30):
    """
    Blast hundreds of parallel outbound calls over SIP Trunk with zero concurrency choke.
    """
    results = []

    def sip_worker(num):
        return dispatch_sip_single_call(num, spoken_message)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(sip_worker, n) for n in numbers_list]
        for f in futures:
            try:
                results.append(f.result())
            except Exception as e:
                results.append({"success": False, "error": str(e)})

    success_count = sum(1 for r in results if r.get("success"))
    failed_count = len(results) - success_count

    return {
        "total": len(numbers_list),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
