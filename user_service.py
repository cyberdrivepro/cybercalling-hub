"""
User System — Core Service Layer
==================================
Every function here takes an AsyncSession so it can be called from
either bot's handlers, or from a script/admin panel later. Nothing in
this file talks to Telegram directly — that keeps it reusable.
"""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, CreditTransaction, UsageLog, AuditLog, InviteCode, Role, UserStatus

DEFAULT_STARTER_CREDITS = 10.0


# ---------------------------------------------------------------------------
# Identity capture — the "fetch new users" part
# ---------------------------------------------------------------------------

async def get_or_create_user(session: AsyncSession, tg_user, owner_tg_id: Optional[int] = None) -> User:
    """
    Called on EVERY incoming update from EITHER bot. On first contact,
    inserts a new row (this is what makes a user "known" to the system).
    On every later contact, refreshes username/last_active — Telegram
    usernames can change, so we keep it current instead of trusting the
    value we captured on day one.
    """
    result = await session.execute(select(User).where(User.tg_id == tg_user.id))
    user = result.scalar_one_or_none()

    is_new = user is None
    if user is None:
        role = Role.OWNER.value if (owner_tg_id and tg_user.id == owner_tg_id) else Role.USER.value
        user = User(
            tg_id=tg_user.id,
            tg_username=tg_user.username,
            first_name=tg_user.first_name,
            role=role,
            status=UserStatus.ACTIVE.value,
            credit_balance=DEFAULT_STARTER_CREDITS if role == Role.USER.value else 0.0,
        )
        session.add(user)
        await session.flush()  # get user.id without a full commit
    else:
        user.tg_username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_active = datetime.utcnow()

    return user


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    username = username.lstrip("@")
    result = await session.execute(select(User).where(User.tg_username == username))
    return result.scalar_one_or_none()


async def resolve_user(session: AsyncSession, identifier: str) -> Optional[User]:
    """Accepts either a numeric tg_id or an @username — used by /whois, /userinfo etc."""
    identifier = identifier.strip()
    if identifier.lstrip("-").isdigit():
        return await get_user_by_tg_id(session, int(identifier))
    return await get_user_by_username(session, identifier)


async def list_users(
    session: AsyncSession, page: int = 1, page_size: int = 10, status_filter: Optional[str] = None
) -> tuple[Sequence[User], int]:
    stmt = select(User)
    if status_filter:
        stmt = stmt.where(User.status == status_filter)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).scalars().all()
    return rows, total


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

async def check_rate_limit(
    session: AsyncSession, user: User, limit_field: str, window: str
) -> tuple[bool, int, Optional[int]]:
    """
    window: 'day' or 'hour'. Returns (allowed, used_count, cap).
    cap of None means unlimited (typically owner/admin).
    """
    cap = getattr(user, limit_field, None)
    if cap is None:
        return True, 0, None

    since = datetime.utcnow() - (timedelta(hours=1) if window == "hour" else timedelta(days=1))
    stmt = select(func.count()).select_from(UsageLog).where(
        and_(UsageLog.user_id == user.id, UsageLog.action == "call", UsageLog.timestamp >= since)
    )
    used = (await session.execute(stmt)).scalar_one()
    return used < cap, used, cap


async def record_usage(session: AsyncSession, user: User, action: str, cost: float = 0.0, detail: str = "") -> None:
    session.add(UsageLog(user_id=user.id, action=action, cost=cost, detail=detail))
    user.last_active = datetime.utcnow()


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------

async def adjust_credits(
    session: AsyncSession, user: User, amount: float, type_: str,
    performed_by: Optional[int] = None, reason: str = ""
) -> User:
    """amount is signed: positive = add, negative = deduct."""
    user.credit_balance = round(user.credit_balance + amount, 4)
    session.add(CreditTransaction(
        user_id=user.id, amount=amount, balance_after=user.credit_balance,
        type=type_, performed_by=performed_by, reason=reason,
    ))
    return user


async def set_balance(
    session: AsyncSession, user: User, new_balance: float,
    performed_by: Optional[int] = None, reason: str = "manual set"
) -> User:
    delta = round(new_balance - user.credit_balance, 4)
    return await adjust_credits(session, user, delta, "admin_grant" if delta >= 0 else "admin_deduct",
                                 performed_by, reason)


async def check_and_deduct(session: AsyncSession, user: User, cost: float) -> bool:
    """Gate a paid action. Returns False (no deduction) if insufficient balance."""
    if user.credit_balance < cost:
        return False
    await adjust_credits(session, user, -cost, "usage_deduct", performed_by=None, reason="call cost")
    return True


# ---------------------------------------------------------------------------
# Ban / Suspend
# ---------------------------------------------------------------------------

async def ban_user(session: AsyncSession, user: User, reason: str, actor_tg_id: int) -> User:
    user.is_banned = True
    user.status = UserStatus.BANNED.value
    user.ban_reason = reason
    user.banned_at = datetime.utcnow()
    user.banned_by = actor_tg_id
    await log_audit(session, actor_tg_id, "ban", user.id, reason)
    return user


async def unban_user(session: AsyncSession, user: User, actor_tg_id: int) -> User:
    user.is_banned = False
    user.status = UserStatus.ACTIVE.value
    user.ban_reason = None
    await log_audit(session, actor_tg_id, "unban", user.id, "")
    return user


async def suspend_user(
    session: AsyncSession, user: User, reason: str, actor_tg_id: int, until: Optional[datetime] = None
) -> User:
    user.is_suspended = True
    user.status = UserStatus.SUSPENDED.value
    user.suspend_reason = reason
    user.suspended_until = until
    await log_audit(session, actor_tg_id, "suspend", user.id, reason)
    return user


async def unsuspend_user(session: AsyncSession, user: User, actor_tg_id: int) -> User:
    user.is_suspended = False
    user.status = UserStatus.ACTIVE.value
    user.suspend_reason = None
    user.suspended_until = None
    await log_audit(session, actor_tg_id, "unsuspend", user.id, "")
    return user


# ---------------------------------------------------------------------------
# Limits / feature flags / role
# ---------------------------------------------------------------------------

async def set_limits(
    session: AsyncSession, user: User, actor_tg_id: int,
    max_calls_per_day: Optional[int] = None, max_calls_per_hour: Optional[int] = None,
    max_bulk_batch_size: Optional[int] = None,
) -> User:
    before = (user.max_calls_per_day, user.max_calls_per_hour, user.max_bulk_batch_size)
    if max_calls_per_day is not None:
        user.max_calls_per_day = max_calls_per_day
    if max_calls_per_hour is not None:
        user.max_calls_per_hour = max_calls_per_hour
    if max_bulk_batch_size is not None:
        user.max_bulk_batch_size = max_bulk_batch_size
    await log_audit(session, actor_tg_id, "set_limits", user.id, f"{before} -> "
                     f"({user.max_calls_per_day}, {user.max_calls_per_hour}, {user.max_bulk_batch_size})")
    return user


async def toggle_feature(session: AsyncSession, user: User, feature: str, value: bool, actor_tg_id: int) -> User:
    if feature not in {"can_call", "can_bulk", "can_webcall", "can_callback"}:
        raise ValueError(f"Unknown feature flag: {feature}")
    setattr(user, feature, value)
    await log_audit(session, actor_tg_id, "toggle_feature", user.id, f"{feature}={value}")
    return user


async def set_role(session: AsyncSession, user: User, role: str, actor_tg_id: int) -> User:
    before = user.role
    user.role = role
    await log_audit(session, actor_tg_id, "set_role", user.id, f"{before} -> {role}")
    return user


# ---------------------------------------------------------------------------
# Invite codes (controlled onboarding, not an open public link)
# ---------------------------------------------------------------------------

async def create_invite_code(session: AsyncSession, created_by: int, max_uses: int = 1,
                              expires_in_days: Optional[int] = 7) -> InviteCode:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expires_at = datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
    invite = InviteCode(code=code, created_by=created_by, max_uses=max_uses, expires_at=expires_at)
    session.add(invite)
    await session.flush()
    return invite


async def redeem_invite_code(session: AsyncSession, code: str) -> tuple[bool, str]:
    result = await session.execute(select(InviteCode).where(InviteCode.code == code))
    invite = result.scalar_one_or_none()
    if not invite:
        return False, "Invalid invite code."
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        return False, "This invite code has expired."
    if invite.used_count >= invite.max_uses:
        return False, "This invite code has already been fully used."
    invite.used_count += 1
    return True, "Invite accepted."


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

async def log_audit(session: AsyncSession, actor_tg_id: Optional[int], action: str,
                     target_user_id: Optional[int], detail: str) -> None:
    session.add(AuditLog(actor_tg_id=actor_tg_id, action=action, target_user_id=target_user_id, detail=detail))


async def recent_audit_log(session: AsyncSession, limit: int = 20) -> Sequence[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    return (await session.execute(stmt)).scalars().all()


# ---------------------------------------------------------------------------
# Aggregate stats — for the admin dashboard header
# ---------------------------------------------------------------------------

async def get_stats(session: AsyncSession) -> dict:
    total = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    banned = (await session.execute(
        select(func.count()).select_from(User).where(User.is_banned == True))).scalar_one()  # noqa: E712
    suspended = (await session.execute(
        select(func.count()).select_from(User).where(User.is_suspended == True))).scalar_one()  # noqa: E712
    since = datetime.utcnow() - timedelta(days=1)
    active_today = (await session.execute(
        select(func.count()).select_from(User).where(User.last_active >= since))).scalar_one()
    total_credits = (await session.execute(select(func.coalesce(func.sum(User.credit_balance), 0.0)))).scalar_one()
    return {
        "total_users": total, "banned": banned, "suspended": suspended,
        "active_today": active_today, "total_credits": round(total_credits, 2),
    }
