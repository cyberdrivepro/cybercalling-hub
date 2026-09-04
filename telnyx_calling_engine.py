"""
================================================================================
  📞 OmniDimension Telnyx & Global SIP Telephony Engine
================================================================================
  Native integration for Telnyx SIP Numbers (+15863601284) & API V2 Call Control.
  Supports high-speed outbound dialing, custom caller IDs, and bulk blasting.
================================================================================
"""

import os
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from proxy_manager import proxy_manager

load_dotenv()

from phone_normalizer import normalize_and_detect_country


def get_telnyx_credentials():
    """Load Telnyx configuration from .env."""
    load_dotenv(override=True)
    return {
        "api_key": os.getenv("TELNYX_API_KEY", "").strip(),
        "phone_number": os.getenv("TELNYX_PHONE_NUMBER", "").strip() or os.getenv("SIP_CALLER_ID", "+15863601284").strip() or "+15863601284",
        "connection_id": os.getenv("TELNYX_CONNECTION_ID", "").strip() or "3037215859656361433",
        "sip_domain": os.getenv("SIP_DOMAIN", "sip.telnyx.com").strip() or "sip.telnyx.com"
    }


def is_telnyx_configured():
    """Check if Telnyx API key or SIP number is provided."""
    creds = get_telnyx_credentials()
    return bool(creds["api_key"] or (creds["phone_number"] and creds["sip_domain"]))


def get_telnyx_summary():
    """Return live status of the Telnyx / SIP Number integration."""
    creds = get_telnyx_credentials()
    has_api = bool(creds["api_key"])
    phone = creds["phone_number"]

    return {
        "configured": is_telnyx_configured(),
        "phone_number": phone,
        "sip_domain": creds["sip_domain"],
        "api_ready": has_api,
        "status": "Active 🟢" if phone else "Needs Setup",
        "instructions": (
            "Add to .env:\n"
            f"TELNYX_PHONE_NUMBER={phone}\n"
            "TELNYX_API_KEY=KEY01...\n"
            "TELNYX_CONNECTION_ID=your_connection_id"
        )
    }


def dispatch_telnyx_call(to_number, spoken_message="Hello! This is a Voice AI message.", voice="Polly.Aditi"):
    """
    Dispatch an outbound call using Telnyx Call Control API V2.
    """
    creds = get_telnyx_credentials()
    api_key = creds["api_key"]
    from_num = creds["phone_number"]

    norm = normalize_and_detect_country(to_number)
    clean_to = norm["clean_number"]

    if not api_key:
        return {
            "success": False,
            "error": "TELNYX_API_KEY is not configured in environment. Please configure TELNYX_API_KEY in .env.",
            "provider": "Telnyx",
            "to": clean_to,
            "from": from_num,
            "status": "unconfigured"
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": clean_to,
        "from": from_num,
        "connection_id": creds["connection_id"] or None
    }
    # Clean None values
    payload = {k: v for k, v in payload.items() if v is not None}

    try:
        url = "https://api.telnyx.com/v2/calls"
        resp = proxy_manager.get_session().post(url, headers=headers, json=payload, timeout=10)
        data = resp.json()

        if resp.status_code in [200, 201]:
            call_id = data.get("data", {}).get("call_control_id", "OK")
            return {
                "success": True,
                "provider": "Telnyx API V2",
                "call_id": call_id,
                "to": clean_to,
                "from": from_num,
                "country": norm["country_name"],
                "flag": norm["flag"],
                "status": "dialing"
            }
        else:
            return {
                "success": False,
                "error": data.get("errors", [{}])[0].get("detail", str(data))
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def dispatch_telnyx_bulk_campaign(numbers_list, spoken_message="Hello! This is a Voice AI announcement.", concurrency=25):
    """
    Parallel bulk calling campaign via Telnyx (+15863601284).
    """
    results = []

    def worker(num):
        return dispatch_telnyx_call(num, spoken_message)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, n) for n in numbers_list]
        for f in futures:
            try:
                results.append(f.result())
            except Exception as ex:
                results.append({"success": False, "error": str(ex)})

    success_count = sum(1 for r in results if r.get("success"))
    failed_count = len(results) - success_count

    return {
        "total": len(numbers_list),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
