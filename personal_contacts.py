"""
================================================================================
  📇 Personal Speed-Dial Contact Book with Auto Country Detection
================================================================================
  Store nicknames and speed-dial phone numbers for instant calling.
================================================================================
"""

import os
import json
from phone_normalizer import normalize_and_detect_country

CONTACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".personal_contacts.json")


def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "office": "+919876543210",
        "support": "+919811122233"
    }


def save_contacts(contacts):
    try:
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2)
    except Exception as e:
        print("Contacts save error:", e)


def add_contact(name, phone_number):
    contacts = load_contacts()
    clean_name = name.strip().lower()
    norm = normalize_and_detect_country(phone_number)
    clean_num = norm["clean_number"]
    contacts[clean_name] = clean_num
    save_contacts(contacts)
    return clean_name, clean_num, norm["country_name"], norm["flag"]


def resolve_phone_or_nickname(input_str):
    """If input is a nickname (e.g. 'Rahul'), resolve to phone. Otherwise auto-detect country code!"""
    contacts = load_contacts()
    clean = input_str.strip().lower()
    if clean in contacts:
        num = contacts[clean]
        norm = normalize_and_detect_country(num)
        return norm["clean_number"], clean.title(), norm["country_name"], norm["flag"]

    norm = normalize_and_detect_country(input_str)
    return norm["clean_number"], "Valued Contact", norm["country_name"], norm["flag"]
