"""
================================================================================
  💬 OmniDimension WhatsApp Post-Call Instant Follow-up Engine
================================================================================
  Formats and dispatches automated WhatsApp follow-ups after phone calls.
================================================================================
"""

import os
import json
import datetime
from phone_normalizer import normalize_and_detect_country

from backend.app.db.session import SessionLocal
from backend.app.models.models import WhatsAppFollowup


def load_whatsapp_logs():
    """Load WhatsApp followup logs from SQLite database."""
    try:
        db = SessionLocal()
        items = db.query(WhatsAppFollowup).all()
        res = []
        for w in items:
            res.append({
                "recipient": w.recipient,
                "customer_name": w.customer_name,
                "message": w.message,
                "status": w.status,
                "retry_count": w.retry_count,
                "timestamp": w.created_at.strftime("%Y-%m-%d %H:%M:%S") if w.created_at else ""
            })
        db.close()
        return res
    except Exception as e:
        print("WhatsApp load error:", e)
        return []


def save_whatsapp_logs(logs):
    """Save WhatsApp followups into SQLite database."""
    try:
        db = SessionLocal()
        for w in logs:
            db.add(WhatsAppFollowup(
                recipient=w.get("recipient", ""),
                customer_name=w.get("customer_name", "Valued Contact"),
                message=w.get("message", ""),
                status=w.get("status", "QUEUED"),
                retry_count=w.get("retry_count", 0)
            ))
        db.commit()
        db.close()
    except Exception as e:
        print("WhatsApp save error:", e)


def create_post_call_whatsapp_followup(to_number, customer_name="Valued Contact", call_summary="Thank you for taking our call.", meeting_link=None, payment_link=None):
    """Generate and queue post-call WhatsApp message."""
    norm = normalize_and_detect_country(to_number)
    clean_num = norm["clean_number"]

    body = f"Hello {customer_name}! 🎙️\n\nThank you for speaking with our Voice AI assistant.\n\n📌 *Summary of our call:* {call_summary}\n"
    if meeting_link:
        body += f"\n🎥 *Your Confirmed Meeting:* {meeting_link}\n"
    if payment_link:
        body += f"\n💳 *Your Secure Payment Link:* {payment_link}\n"
    body += "\nIf you have any questions, feel free to reply directly to this chat! Have a wonderful day."

    record = {
        "recipient": clean_num,
        "customer_name": customer_name,
        "message": body,
        "status": "queued",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    logs = load_whatsapp_logs()
    logs.append(record)
    save_whatsapp_logs(logs)

    # Return deep link for 1-click opening on web/phone
    encoded_msg = body.replace("\n", "%0A").replace(" ", "%20")
    wa_link = f"https://wa.me/{clean_num.replace('+', '')}?text={encoded_msg}"

    return {
        "recipient": clean_num,
        "message": body,
        "wa_link": wa_link,
        "status": "queued"
    }
