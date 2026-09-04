"""
================================================================================
  📊 OmniDimension Dynamic CSV & Template Variables Campaign Engine
================================================================================
  Parses CSV with custom columns (e.g. name, amount, date, city, service)
  and injects personalized spoken first messages for each recipient.
================================================================================
"""

import os
import csv
import io
import re
from phone_normalizer import normalize_and_detect_country


def parse_csv_contacts_with_variables(csv_content_or_path, default_template="Hello {name}, calling regarding {service}."):
    """
    Parse CSV text or filepath, detecting headers and row values.
    Returns list of personalized contact dispatch objects.
    """
    rows = []
    if os.path.exists(csv_content_or_path):
        with open(csv_content_or_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            raw_rows = list(reader)
    else:
        f = io.StringIO(csv_content_or_path)
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    if not raw_rows:
        return []

    for row in raw_rows:
        # Find phone column
        phone_key = next((k for k in row.keys() if k and any(x in k.lower() for x in ["phone", "mobile", "number", "tel", "contact"])), None)
        if not phone_key:
            # Fallback to first column
            phone_key = list(row.keys())[0] if row.keys() else None

        if not phone_key or not row.get(phone_key):
            continue

        raw_phone = str(row[phone_key]).strip()
        norm = normalize_and_detect_country(raw_phone)
        if not norm.get("is_valid"):
            continue

        # Find name column
        name_key = next((k for k in row.keys() if k and any(x in k.lower() for x in ["name", "customer", "person", "client"])), None)
        name = str(row.get(name_key, "Valued Customer")).strip() if name_key else "Valued Customer"

        # Interpolate variables into message template
        personalized_msg = default_template
        for k, v in row.items():
            if k:
                personalized_msg = personalized_msg.replace(f"{{{k}}}", str(v or "").strip())
                personalized_msg = personalized_msg.replace(f"{{{k.lower()}}}", str(v or "").strip())

        # Cleanup any unreplaced placeholders
        personalized_msg = re.sub(r'\{[a-zA-Z0-9_]+\}', '', personalized_msg).strip()

        rows.append({
            "phone": norm.get("clean_number"),
            "raw_phone": raw_phone,
            "country": norm.get("country_name"),
            "flag": norm.get("flag"),
            "name": name,
            "custom_message": personalized_msg,
            "raw_variables": row
        })

    return rows


def generate_sample_csv():
    """Return a ready-to-use sample CSV with variable placeholders."""
    return (
        "phone,name,service,due_amount,meeting_time\n"
        "+919876543210,Aman Gupta,Web Development,$250,Friday 4:00 PM\n"
        "+919811122233,Priya Sharma,Cloud AI Demo,$0,Tomorrow 11:30 AM\n"
        "+919899988877,Rahul Verma,Enterprise Telephony,$500,Monday 3:00 PM\n"
    )
