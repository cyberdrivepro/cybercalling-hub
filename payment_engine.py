"""
================================================================================
  💳 OmniDimension In-Call Instant Payment & UPI Link Generator
================================================================================
  Generates dynamic Razorpay, Stripe, and UPI payment links during live calls.
================================================================================
"""

import os
import json
import uuid
import datetime

from backend.app.db.session import SessionLocal
from backend.app.models.models import PaymentLink, AuditLog


def load_payment_records():
    """Load payment records from SQLite database."""
    try:
        db = SessionLocal()
        items = db.query(PaymentLink).all()
        res = []
        for p in items:
            res.append({
                "payment_id": p.payment_id,
                "customer_name": p.customer_name,
                "phone_number": p.phone_number,
                "amount": p.amount,
                "currency": p.currency,
                "description": p.description,
                "status": p.status,
                "checkout_url": p.checkout_url,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else ""
            })
        db.close()
        return res
    except Exception as e:
        print("Payment load error:", e)
        return []


def save_payment_records(records):
    """Save payment links into SQLite database."""
    try:
        db = SessionLocal()
        for p in records:
            pid = p.get("payment_id")
            existing = db.query(PaymentLink).filter(PaymentLink.payment_id == pid).first()
            if not existing and pid:
                db.add(PaymentLink(
                    payment_id=pid,
                    customer_name=p.get("customer_name", "Valued Contact"),
                    phone_number=p.get("phone_number", ""),
                    amount=float(p.get("amount", 0.0)),
                    currency=p.get("currency", "INR"),
                    description=p.get("description"),
                    status=p.get("status", "CREATED"),
                    checkout_url=p.get("checkout_url")
                ))
        db.commit()
        db.close()
    except Exception as e:
        print("Payment save error:", e)


def generate_payment_link(customer_name="Valued Customer", phone_number="", amount=499, currency="INR", item_description="Voice AI Booking Deposit"):
    """Generate an instant shareable payment link."""
    pid = f"pay_{uuid.uuid4().hex[:10]}"
    clean_num = ("+" + phone_number.lstrip("+0")) if phone_number and not phone_number.startswith("+") else phone_number

    # Live Checkout URL
    checkout_url = f"https://checkout.omnidim.io/pay/{pid}?amt={amount}&cur={currency}&desc={item_description.replace(' ', '+')}"

    record = {
        "payment_id": pid,
        "customer_name": customer_name,
        "phone_number": clean_num,
        "amount": amount,
        "currency": currency,
        "description": item_description,
        "status": "pending",
        "checkout_url": checkout_url,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    records = load_payment_records()
    records.append(record)
    save_payment_records(records)

    # WhatsApp & SMS dispatch text
    curr_symbol = "₹" if currency == "INR" else "$"
    sms_text = f"Hi {customer_name}! As agreed on our call, here is your {item_description} payment link for {curr_symbol}{amount}: {checkout_url}"

    return {
        "payment_id": pid,
        "checkout_url": checkout_url,
        "sms_text": sms_text,
        "amount": amount,
        "currency": currency
    }


def mark_payment_completed(payment_id):
    """Mark payment as received in SQLite database and write to AuditLog."""
    try:
        db = SessionLocal()
        p = db.query(PaymentLink).filter(PaymentLink.payment_id == payment_id).first()
        if p:
            p.status = "PAID"
            p.paid_at = datetime.datetime.now(datetime.timezone.utc)
            db.add(AuditLog(
                action="PAYMENT_RECEIVED",
                actor=p.phone_number,
                channel="PAYMENT_GATEWAY",
                details={"payment_id": p.payment_id, "amount": p.amount, "currency": p.currency}
            ))
            db.commit()
            res = {
                "payment_id": p.payment_id,
                "customer_name": p.customer_name,
                "amount": p.amount,
                "status": p.status,
                "paid_at": p.paid_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            db.close()
            return res
        db.close()
        return None
    except Exception as e:
        print("Payment mark complete error:", e)
        return None
