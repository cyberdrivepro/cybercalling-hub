"""
================================================================================
  🧠 Unified Conversational Memory Store (OmniDimension Shared Memory)
================================================================================
  Maintains continuous memory across phone calls and WhatsApp chats.
================================================================================
"""

import os
import json
import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".conversation_memory.json")


def load_memory_store():
    """Load customer conversational memory."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_memory_store(store):
    """Save customer conversational memory."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
    except Exception as e:
        print("Memory save error:", e)


def get_customer_memory(phone_number):
    """Retrieve memory context for a specific phone number."""
    store = load_memory_store()
    clean_num = ("+" + phone_number.lstrip("+0")) if not phone_number.startswith("+") else phone_number
    return store.get(clean_num, {
        "phone_number": clean_num,
        "customer_name": "Valued Customer",
        "total_calls": 0,
        "lead_sentiment": "Neutral",
        "last_interaction": None,
        "history": [],
        "variables": {}
    })


def update_customer_memory(phone_number, call_summary="", sentiment="Positive", variables=None, bot_name="cyber"):
    """Update customer memory after a call or message."""
    store = load_memory_store()
    clean_num = ("+" + phone_number.lstrip("+0")) if not phone_number.startswith("+") else phone_number
    mem = store.get(clean_num, {
        "phone_number": clean_num,
        "customer_name": "Valued Customer",
        "total_calls": 0,
        "lead_sentiment": sentiment,
        "last_interaction": None,
        "history": [],
        "variables": {}
    })

    mem["total_calls"] += 1
    mem["lead_sentiment"] = sentiment
    mem["last_interaction"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if variables:
        mem["variables"].update(variables)

    mem["history"].append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "Voice Call",
        "bot_name": bot_name,
        "summary": call_summary or "Voice call completed."
    })

    # Keep last 15 interaction turns
    mem["history"] = mem["history"][-15:]
    store[clean_num] = mem
    save_memory_store(store)
    return mem
