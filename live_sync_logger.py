"""
================================================================================
  🔄 OmniDimension Google Sheets & Outgoing Webhook 2-Way Sync Engine
================================================================================
  Logs completed calls, duration, sentiment, and recording URLs to local CSV/JSON
  and dispatches outgoing webhooks to Google Sheets, Zapier, Make, and HubSpot.
================================================================================
"""

import os
import csv
import json
import datetime
import requests

SYNC_CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_call_sync.csv")
WEBHOOK_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".webhook_config.json")


def load_webhook_urls():
    if os.path.exists(WEBHOOK_CONFIG_FILE):
        try:
            with open(WEBHOOK_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"webhooks": []}


def save_webhook_url(url):
    cfg = load_webhook_urls()
    if url not in cfg["webhooks"]:
        cfg["webhooks"].append(url)
    try:
        with open(WEBHOOK_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("Webhook save error:", e)


def log_call_to_sync_storage(record):
    """
    Append record to live CSV and dispatch to configured webhooks.
    """
    file_exists = os.path.exists(SYNC_CSV_FILE)
    fieldnames = ["timestamp", "phone", "name", "status", "duration", "cost_usd", "sentiment", "score", "recording_url"]

    try:
        with open(SYNC_CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            row = {
                "timestamp": record.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "phone": record.get("phone", ""),
                "name": record.get("name", "Valued Contact"),
                "status": record.get("status", "completed"),
                "duration": record.get("duration", "0:0"),
                "cost_usd": record.get("cost_usd", 0.0),
                "sentiment": record.get("sentiment", "Neutral"),
                "score": record.get("score", 0),
                "recording_url": record.get("recording_url", "")
            }
            writer.writerow(row)
    except Exception as e:
        print("Live sync CSV write error:", e)

    # Dispatch to external webhooks (e.g. Google Sheets / Zapier / HubSpot)
    webhooks = load_webhook_urls().get("webhooks", [])
    for wh in webhooks:
        try:
            requests.post(wh, json=record, timeout=5)
        except Exception:
            pass


def get_sync_csv_path():
    return SYNC_CSV_FILE
