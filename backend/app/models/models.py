"""
================================================================================
  🗄️ CyberCalling 2.0 — Enterprise Database Entities & Schemas
================================================================================
"""

import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="admin")  # admin, operator, viewer
    totp_secret = Column(String(64), nullable=True)
    is_totp_enabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    phone = Column(String(50), unique=True, index=True, nullable=False)  # Normalized E.164
    country_code = Column(String(10), default="+91")
    flag = Column(String(10), default="🇮🇳")
    nickname = Column(String(100), nullable=True, index=True)
    tags = Column(String(255), default="lead")  # e.g. "vip,hot_lead,customer"
    
    # Compliance & Consent
    consent_status = Column(String(50), default="OPTED_IN")  # OPTED_IN, UNKNOWN, BLOCKED, DND
    dnd_registered = Column(Boolean, default=False)
    consent_proof = Column(Text, nullable=True)
    last_called_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    provider = Column(String(50), default="OMNIDIM")  # OMNIDIM, TWILIO, TELNYX, SIP
    status = Column(String(50), default="DRAFT")       # DRAFT, RUNNING, PAUSED, COMPLETED, CANCELLED
    budget_cap_usd = Column(Float, default=10.0)
    current_spend_usd = Column(Float, default=0.0)
    
    total_contacts = Column(Integer, default=0)
    dialed_count = Column(Integer, default=0)
    answered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    
    task_prompt = Column(Text, nullable=True)
    calling_window = Column(String(50), default="09:00-20:00")
    created_at = Column(DateTime, default=lambda: datetime.timezone.utc)
    completed_at = Column(DateTime, nullable=True)
    
    calls = relationship("CallRecord", back_populates="campaign")

class CallRecord(Base):
    __tablename__ = "call_records"
    
    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(100), unique=True, index=True, nullable=True)  # Provider SID
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    provider = Column(String(50), default="OMNIDIM")
    
    to_number = Column(String(50), index=True, nullable=False)
    from_number = Column(String(50), default="+918048799598")
    customer_name = Column(String(150), default="Valued Contact")
    spoken_message = Column(Text, nullable=True)
    
    status = Column(String(50), default="QUEUED")  # QUEUED, RINGING, IN_PROGRESS, COMPLETED, BUSY, FAILED
    duration_seconds = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    
    recording_url = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    lead_score = Column(Integer, default=50)  # 0 to 100
    sentiment = Column(String(50), default="Neutral")  # Positive, Neutral, Negative
    is_hot_lead = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    campaign = relationship("Campaign", back_populates="calls")

class VaultKey(Base):
    __tablename__ = "vault_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(100), nullable=False)
    provider = Column(String(50), default="OMNIDIMENSION")
    
    # AES-256-GCM Envelope Encryption
    encrypted_key = Column(Text, nullable=False)
    nonce = Column(String(64), nullable=False)
    tag = Column(String(64), nullable=True)
    key_preview = Column(String(50), nullable=False)  # e.g. "Iw82u...Hz0"
    
    balance_usd = Column(Float, default=0.0)
    quota_limit = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), index=True, nullable=False)
    actor = Column(String(100), default="system")
    channel = Column(String(50), default="API")
    ip_address = Column(String(50), default="127.0.0.1")
    status = Column(String(50), default="SUCCESS")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

# ==============================================================================
#  👥 Telegram User & Multi-Tenant Credit System
# ==============================================================================
class TelegramUser(Base):
    __tablename__ = "telegram_users"
    
    telegram_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(150), nullable=True)
    role = Column(String(20), default="user")  # owner, admin, user
    plan_tier = Column(String(20), default="Free") # Free, Pro, Enterprise
    language = Column(String(10), default="en")    # en, hi
    
    credit_balance = Column(Float, default=5.0)  # 5.0 Free Trial credits
    daily_limit = Column(Integer, default=10)     # Max 10 calls/day
    hourly_limit = Column(Integer, default=5)     # Max 5 calls/hour
    max_bulk_batch_size = Column(Integer, default=50) # Bulk campaign batch size cap
    
    # Feature Permissions
    can_call = Column(Boolean, default=True)
    can_bulk = Column(Boolean, default=True)
    can_webcall = Column(Boolean, default=True)
    can_callback = Column(Boolean, default=True)
    
    # Ban & Suspension
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String(255), nullable=True)
    is_suspended = Column(Boolean, default=False)
    suspended_until = Column(DateTime, nullable=True)
    
    # Live Velocity Tracking
    calls_today = Column(Integer, default=0)
    calls_this_hour = Column(Integer, default=0)
    total_calls = Column(Integer, default=0)
    
    admin_notes = Column(Text, nullable=True)
    assistant_settings = Column(JSON, nullable=True)  # Per-user Persona: TTS, Model, STT, Language, Speed
    status = Column(String(20), default="ACTIVE") # ACTIVE, SUSPENDED, BANNED, PENDING
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    last_active_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), ForeignKey("telegram_users.telegram_id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), default="CALL_DEDUCT")  # SIGNUP_BONUS, CALL_DEDUCT, ADMIN_TOPUP, ADMIN_ADJUST
    notes = Column(String(255), nullable=True)
    performed_by = Column(String(50), default="system")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class UserCallLog(Base):
    __tablename__ = "user_call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), ForeignKey("telegram_users.telegram_id"), index=True, nullable=False)
    recipient = Column(String(50), index=True, nullable=False)
    customer_name = Column(String(150), default="Contact")
    duration_seconds = Column(Float, default=0.0)
    credits_spent = Column(Float, default=1.0)
    status = Column(String(50), default="DISPATCHED")
    quality_rating = Column(Integer, nullable=True) # 1 to 5 stars
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), ForeignKey("telegram_users.telegram_id"), index=True, nullable=False)
    user_name = Column(String(150), default="User")
    message = Column(Text, nullable=False)
    admin_reply = Column(Text, nullable=True)
    status = Column(String(20), default="OPEN") # OPEN, RESOLVED, CLOSED
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

class ContactNote(Base):
    __tablename__ = "contact_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(50), index=True, nullable=False)
    note_text = Column(Text, nullable=False)
    tag = Column(String(50), nullable=True)
    created_by = Column(String(50), default="admin")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    key = Column(String(50), primary_key=True, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class InviteCode(Base):
    __tablename__ = "invite_codes"
    
    code = Column(String(50), primary_key=True, index=True)
    created_by = Column(String(50), default="owner")
    bonus_credits = Column(Float, default=20.0)
    target_plan = Column(String(20), default="Pro")
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class ToSAcceptance(Base):
    __tablename__ = "tos_acceptances"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), ForeignKey("telegram_users.telegram_id"), index=True, nullable=False)
    tos_version = Column(String(20), default="v1.0", nullable=False)
    disclaimer_text = Column(Text, nullable=True)
    accepted_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    channel = Column(String(50), default="Telegram Bot")


class ScheduledCall(Base):
    __tablename__ = "scheduled_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False)
    telegram_id = Column(String(50), ForeignKey("telegram_users.telegram_id"), index=True, nullable=False)
    recipient = Column(String(50), index=True, nullable=False)
    customer_name = Column(String(150), default="Valued Contact")
    custom_message = Column(Text, nullable=True)
    spoken_scenario = Column(String(100), default="CUSTOM")
    
    # Timing & Execution
    due_at = Column(DateTime, nullable=False, index=True)
    due_timestamp_unix = Column(Float, nullable=False, index=True)
    human_time_str = Column(String(100), nullable=True)
    
    status = Column(String(30), default="PENDING", index=True) # PENDING, EXECUTING, COMPLETED, CANCELLED, FAILED
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(50), nullable=True)
    auto_redial = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    executed_at = Column(DateTime, nullable=True)


class LeadIntelligence(Base):
    __tablename__ = "lead_intelligence"
    
    phone = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), default="Valued Contact")
    score = Column(Integer, default=50)  # 0 to 100
    classification = Column(String(50), default="WARM")  # HOT, WARM, COLD
    sentiment = Column(String(50), default="Neutral")
    duration = Column(String(50), default="0:0")
    duration_sec = Column(Float, default=0.0)
    matched_hot_keywords = Column(JSON, nullable=True)
    matched_cold_keywords = Column(JSON, nullable=True)
    is_hot = Column(Boolean, default=False)
    tenant_id = Column(String(50), default="default", index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))


class CalendarAppointment(Base):
    __tablename__ = "calendar_appointments"
    
    event_id = Column(String(50), primary_key=True, index=True)
    telegram_id = Column(String(50), nullable=True, index=True)
    customer_name = Column(String(150), default="Valued Contact")
    phone_number = Column(String(50), index=True, nullable=False)
    slot_time = Column(String(100), nullable=False)
    topic = Column(String(255), default="Product Demo & Consultation")
    meet_link = Column(Text, nullable=True)
    cal_link = Column(Text, nullable=True)
    status = Column(String(50), default="CONFIRMED")  # CONFIRMED, RESCHEDULED, CANCELLED
    tenant_id = Column(String(50), default="default", index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class WhatsAppFollowup(Base):
    __tablename__ = "whatsapp_followups"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), nullable=True, index=True)
    recipient = Column(String(50), index=True, nullable=False)
    customer_name = Column(String(150), default="Valued Contact")
    message = Column(Text, nullable=False)
    status = Column(String(50), default="QUEUED")  # QUEUED, SENT, FAILED, DELIVERED
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_attempt_at = Column(DateTime, nullable=True)
    tenant_id = Column(String(50), default="default", index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class PaymentLink(Base):
    __tablename__ = "payment_links"
    
    payment_id = Column(String(50), primary_key=True, index=True)
    telegram_id = Column(String(50), nullable=True, index=True)
    customer_name = Column(String(150), default="Valued Contact")
    phone_number = Column(String(50), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    description = Column(String(255), nullable=True)
    status = Column(String(50), default="CREATED")  # CREATED, PAID, EXPIRED, CANCELLED
    checkout_url = Column(Text, nullable=True)
    tenant_id = Column(String(50), default="default", index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    paid_at = Column(DateTime, nullable=True)




