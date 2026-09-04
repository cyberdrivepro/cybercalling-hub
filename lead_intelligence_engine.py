"""
================================================================================
  🧠 OmniDimension AI Lead Intelligence, Sentiment & Keyword Radar Engine
================================================================================
  Evaluates call transcripts, duration, and keywords to calculate a 0-100
  Lead Qualification Score and trigger Instant High-Priority Hot Lead alerts.
================================================================================
"""

import os
import json
import re
import datetime

from backend.app.db.session import SessionLocal
from backend.app.models.models import LeadIntelligence


def load_lead_records():
    """Load all lead records from SQLite database."""
    try:
        db = SessionLocal()
        leads = db.query(LeadIntelligence).all()
        res = {}
        for l in leads:
            res[l.phone] = {
                "phone": l.phone,
                "name": l.name,
                "score": l.score,
                "classification": l.classification,
                "sentiment": l.sentiment,
                "duration": l.duration,
                "duration_sec": l.duration_sec,
                "matched_hot_keywords": l.matched_hot_keywords or [],
                "matched_cold_keywords": l.matched_cold_keywords or [],
                "is_hot": l.is_hot,
                "timestamp": l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else ""
            }
        db.close()
        return res
    except Exception as e:
        print("Lead load error:", e)
        return {}


def save_lead_records(data):
    """Save or update lead records in SQLite database."""
    try:
        db = SessionLocal()
        for phone, item in data.items():
            existing = db.query(LeadIntelligence).filter(LeadIntelligence.phone == phone).first()
            if existing:
                existing.name = item.get("name", existing.name)
                existing.score = int(item.get("score", existing.score))
                existing.classification = item.get("classification", existing.classification)
                existing.sentiment = item.get("sentiment", existing.sentiment)
                existing.duration = str(item.get("duration", existing.duration))
                existing.duration_sec = float(item.get("duration_sec", existing.duration_sec))
                existing.matched_hot_keywords = item.get("matched_hot_keywords", [])
                existing.matched_cold_keywords = item.get("matched_cold_keywords", [])
                existing.is_hot = bool(item.get("is_hot", False))
            else:
                db.add(LeadIntelligence(
                    phone=phone,
                    name=item.get("name", "Valued Contact"),
                    score=int(item.get("score", 50)),
                    classification=item.get("classification", "WARM"),
                    sentiment=item.get("sentiment", "Neutral"),
                    duration=str(item.get("duration", "0:0")),
                    duration_sec=float(item.get("duration_sec", 0.0)),
                    matched_hot_keywords=item.get("matched_hot_keywords", []),
                    matched_cold_keywords=item.get("matched_cold_keywords", []),
                    is_hot=bool(item.get("is_hot", False))
                ))
        db.commit()
        db.close()
    except Exception as e:
        print("Lead DB save error:", e)


def analyze_lead_quality(phone, name, duration_str, transcript="", status="completed"):
    """
    Score a completed call from 0 to 100 and classify lead intent.
    """
    clean_phone = str(phone).strip()
    st = str(status).lower()
    score = 0
    sentiment = "Neutral ⚪"
    matched_hot = []
    matched_cold = []

    # 1. Duration Scoring
    dur_sec = 0.0
    if duration_str and duration_str != "-":
        parts = str(duration_str).split(":")
        if len(parts) == 2:
            try:
                dur_sec = (float(parts[0]) * 60) + float(parts[1])
            except ValueError:
                dur_sec = 0.0

    if dur_sec >= 45:
        score += 45
    elif dur_sec >= 25:
        score += 35
    elif dur_sec >= 10:
        score += 20
    elif dur_sec > 0:
        score += 10

    # 2. Status Scoring
    if "complete" in st or "success" in st:
        score += 15
    elif "busy" in st:
        score += 5
    elif "no-answer" in st or "fail" in st:
        score += 0

    # 3. Transcript Keyword Matching
    text_lower = (transcript or "").lower()
    for kw in HOT_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            score += 8
            matched_hot.append(kw)

    for kw in COLD_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            score -= 20
            matched_cold.append(kw)

    # Normalize score bounds (0 - 100)
    score = max(0, min(100, score))

    # 4. Classification
    if score >= 75:
        classification = "🔥 Hot Lead / High Intent"
        sentiment = "Positive 🔥"
        is_escalation_worthy = True
    elif score >= 45:
        classification = "⚡ Warm Lead / Follow-Up Required"
        sentiment = "Interested 🟢"
        is_escalation_worthy = False
    else:
        classification = "❄️ Cold Lead / Unqualified"
        sentiment = "Cold / Neutral ⚪"
        is_escalation_worthy = False

    record = {
        "phone": clean_phone,
        "name": name or "Valued Contact",
        "score": score,
        "classification": classification,
        "sentiment": sentiment,
        "duration": duration_str or "0:0",
        "duration_sec": dur_sec,
        "matched_hot_keywords": matched_hot,
        "matched_cold_keywords": matched_cold,
        "is_hot": score >= 75,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    leads = load_lead_records()
    leads[clean_phone] = record
    save_lead_records(leads)

    return record


def get_all_hot_leads():
    """Retrieve all leads marked Hot for instant executive escalation."""
    leads = load_lead_records()
    return [v for v in leads.values() if v.get("is_hot")]
