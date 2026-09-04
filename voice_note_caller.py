"""
================================================================================
  🎙️ OmniDimension Voice Note to Call Dispatcher
================================================================================
  Parses spoken voice notes on Telegram and auto-dispatches calls.
================================================================================
"""

import os
import re
import requests
from personal_contacts import load_contacts, resolve_phone_or_nickname


def parse_voice_transcript_intent(transcript_text):
    """
    Extract contact name, phone number, and custom message from voice transcript.
    Example: 'Call Rahul and tell him that meeting is at 4 PM'
    """
    clean = transcript_text.strip()
    contacts = load_contacts()

    target_phone = None
    target_name = "Valued Contact"
    custom_msg = clean

    # 1. Look for phone numbers
    found_nums = re.findall(r'\+?\d{10,15}', clean)
    if found_nums:
        target_phone = found_nums[0]

    # 2. Look for saved contact names
    if not target_phone:
        words = re.findall(r'\b[a-zA-Z]+\b', clean.lower())
        for w in words:
            if w in contacts:
                target_phone = contacts[w]
                target_name = w.title()
                break

    # Default to None if not found
    if not target_phone:
        target_phone = contacts.get("myself", "")
        target_name = "Contact"

    # Extract clean task
    task_match = re.search(r'(?i)(?:tell\s+him|tell\s+her|tell\s+them|say\s+that|bolo|batao|message|msg)\s+(.+)$', clean)
    if task_match:
        custom_msg = task_match.group(1).strip()

    return {
        "phone": target_phone,
        "name": target_name,
        "message": custom_msg
    }
