"""
CyberCalling User System — Database Models
============================================
SQLAlchemy 2.0 async models shared by BOTH bots (main bot + admin bot).

Because both bots point at the same DATABASE_URL and read/write these
exact tables, "live sync" between the two bots is automatic — there is
no separate sync job, no polling, no message-passing needed for the
user data itself. See notify.py for the one place we DO push a live
Telegram message proactively (new-user alerts).
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, enum.Enum):
    PENDING = "pending"     # awaiting admin approval (if approval-gated onboarding is on)
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- Identity (auto-captured on first contact, refreshed every message) ---
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    tg_username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    role: Mapped[str] = mapped_column(String(16), default=Role.USER.value)
    status: Mapped[str] = mapped_column(String(16), default=UserStatus.ACTIVE.value)

    # --- Wallet ---
    credit_balance: Mapped[float] = mapped_column(Float, default=0.0)

    # --- Rate limits (None = unlimited, meant for owner/admin) ---
    max_calls_per_day: Mapped[Optional[int]] = mapped_column(Integer, default=20)
    max_calls_per_hour: Mapped[Optional[int]] = mapped_column(Integer, default=5)
    max_bulk_batch_size: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # --- Feature flags ---
    can_call: Mapped[bool] = mapped_column(Boolean, default=True)
    can_bulk: Mapped[bool] = mapped_column(Boolean, default=False)
    can_webcall: Mapped[bool] = mapped_column(Boolean, default=True)
    can_callback: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_bulk_approval: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Ban (permanent) ---
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    banned_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # actor's tg_id

    # --- Suspend (temporary or indefinite-until-lifted) ---
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    suspended_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    suspend_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Misc ---
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # admin's internal notes

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[List["CreditTransaction"]] = relationship(back_populates="user")
    usage_logs: Mapped[List["UsageLog"]] = relationship(back_populates="user")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Float)              # signed: +topup, -deduct
    balance_after: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(32))              # topup | admin_grant | usage_deduct | refund
    performed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # tg_id, null = system
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")


class UsageLog(Base):
    __tablename__ = "usage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))            # call | bulk | webcall | callback
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="usage_logs")


class AuditLog(Base):
    """Every admin/owner action that changes another user's access or wallet."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    target_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class InviteCode(Base):
    """Admin-generated, expiring, max-use invite codes — controlled onboarding
    instead of an open public referral link."""
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ToSAcceptance(Base):
    """Immutable record of a user accepting the platform Terms of Service & Disclaimer."""
    __tablename__ = "tos_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    tos_version: Mapped[str] = mapped_column(String(20), default="v1.0")
    disclaimer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    channel: Mapped[str] = mapped_column(String(32), default="telegram")

