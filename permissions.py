"""
Single gate every user-facing command passes through.

Usage:

    @gated(permission="can_call", limit_field="max_calls_per_day", action_name="call")
    async def call_handler(update, context, user, session):
        phone = context.args[0]
        # ... your existing dialing logic here ...

The decorator injects `user` (the User row) and `session` (an open
AsyncSession, already committing your changes) into the wrapped
function's kwargs. Ban/suspend/permission/rate-limit checks all happen
here, in one place, so adding a new restriction later is a one-line
change instead of touching every handler.
"""
from __future__ import annotations

import functools
import os
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from .db import SessionLocal
from . import user_service as svc

OWNER_TG_ID = int(os.getenv("OWNER_TG_ID", "0")) or None


def gated(permission: Optional[str] = None, limit_field: Optional[str] = None, action_name: Optional[str] = None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            async with SessionLocal() as session:
                user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)

                if user.is_banned:
                    await update.effective_message.reply_text(
                        f"🚫 Access denied.\nReason: {user.ban_reason or 'not specified'}\n"
                        f"If you think this is a mistake, use /appeal."
                    )
                    await session.commit()
                    return

                if user.is_suspended and (not user.suspended_until or user.suspended_until > datetime.utcnow()):
                    await update.effective_message.reply_text(
                        "⏸️ Your account is currently suspended.\nUse /appeal to contact the admin."
                    )
                    await session.commit()
                    return

                if permission and not getattr(user, permission, False):
                    await update.effective_message.reply_text(
                        "🔒 This feature isn't enabled on your account.\n"
                        "Use /requestupgrade to ask for access."
                    )
                    await session.commit()
                    return

                if limit_field:
                    window = "hour" if "hour" in limit_field else "day"
                    ok, used, cap = await svc.check_rate_limit(session, user, limit_field, window)
                    if not ok:
                        reset = "the next hour" if window == "hour" else "midnight"
                        await update.effective_message.reply_text(
                            f"⏳ Daily limit reached ({used}/{cap}).\nResets at {reset}.\n"
                            f"Use /requestupgrade to ask for a higher limit."
                        )
                        await session.commit()
                        return

                result = await func(update, context, user=user, session=session, *args, **kwargs)

                if action_name:
                    await svc.record_usage(session, user, action_name)

                await session.commit()
                return result
        return wrapper
    return decorator


def owner_only(func):
    """For commands even admins shouldn't touch (e.g. /promote to owner, /killswitch)."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != OWNER_TG_ID:
            await update.effective_message.reply_text("🚫 Owner-only command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def admin_only(func):
    """For admin-bot commands — role must be owner or admin."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        async with SessionLocal() as session:
            user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
            await session.commit()
            if user.role not in ("owner", "admin"):
                await update.effective_message.reply_text("🚫 Admins only.")
                return
        return await func(update, context, *args, **kwargs)
    return wrapper
