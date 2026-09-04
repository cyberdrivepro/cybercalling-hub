"""
@DarkAngelEngine_BOT — user-facing command handlers.

Wire these into your existing bot's Application alongside your current
telephony logic (see register_example.py). These handlers own the
user-system side of things; your existing /call, /bulk etc. dialing
code just needs the @gated(...) decorator added on top — see the
call_handler_example at the bottom for the pattern.
"""
from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from .db import SessionLocal
from .permissions import gated, OWNER_TG_ID
from . import user_service as svc
from .notify import notify_admin

PRODUCT_NAME = "CyberCalling"  # swap freely — every user-facing string routes through this


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        tg_user = update.effective_user
        existing = await svc.get_user_by_tg_id(session, tg_user.id)
        is_new = existing is None

        user = await svc.get_or_create_user(session, tg_user, owner_tg_id=OWNER_TG_ID)
        await session.commit()

        if is_new:
            await notify_admin(
                f"🆕 *New user joined*\n@{user.tg_username or 'no_username'} (ID `{user.tg_id}`)\n"
                f"Starter balance: {user.credit_balance} credits"
            )

        if user.is_banned:
            await update.effective_message.reply_text("🚫 This account is banned.")
            return

        await update.effective_message.reply_text(
            f"👋 Welcome to {PRODUCT_NAME}!\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Account: 🟢 {user.status.title()}\n"
            f"Credits: {user.credit_balance}\n"
            f"Daily Limit: {user.max_calls_per_day or '∞'} calls\n\n"
            f"Try /call <phone>, or /help to see everything you can do."
        )


# ---------------------------------------------------------------------------
# /profile
# ---------------------------------------------------------------------------

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        _, used_today, cap_day = await svc.check_rate_limit(session, user, "max_calls_per_day", "day")
        await session.commit()

        bulk_line = "✅" if user.can_bulk else "🔒 (/requestupgrade)"
        text = (
            f"👤 *My Account*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Role: {user.role.title()}      Status: {user.status.title()}\n"
            f"Balance: {user.credit_balance} credits\n\n"
            f"📞 Today's Usage: {used_today} / {cap_day or '∞'}\n\n"
            f"⚙️ Feature Access\n"
            f"Call: {'✅' if user.can_call else '🔒'}   "
            f"Webcall: {'✅' if user.can_webcall else '🔒'}   "
            f"Callback: {'✅' if user.can_callback else '🔒'}   "
            f"Bulk: {bulk_line}"
        )
        await update.effective_message.reply_text(text, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# /balance, /mylimits
# ---------------------------------------------------------------------------

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        await session.commit()
        await update.effective_message.reply_text(f"💰 Credits: {user.credit_balance}")


async def mylimits_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        _, used_day, cap_day = await svc.check_rate_limit(session, user, "max_calls_per_day", "day")
        _, used_hr, cap_hr = await svc.check_rate_limit(session, user, "max_calls_per_hour", "hour")
        await session.commit()
        await update.effective_message.reply_text(
            f"📞 *Your Limits*\n"
            f"Today: {used_day} / {cap_day or '∞'}\n"
            f"This hour: {used_hr} / {cap_hr or '∞'}\n"
            f"Bulk batch cap: {user.max_bulk_batch_size or '∞'}",
            parse_mode="Markdown",
        )


# ---------------------------------------------------------------------------
# /help — dynamic, only shows what this user can actually do
# ---------------------------------------------------------------------------

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        await session.commit()

    lines = [f"📖 *{PRODUCT_NAME} — Your Commands*\n"]
    lines.append("/balance — Check your credits")
    lines.append("/profile — Your account summary")
    lines.append("/mylimits — Your usage limits")
    lines.append("/history — Your call history")
    lines.append("/call <phone> — Make a call" if user.can_call else "🔒 /call — locked")
    lines.append("/webcall — Get a shareable voice link" if user.can_webcall else "🔒 /webcall — locked")
    lines.append("/callback <phone> <mins> — Schedule a callback" if user.can_callback else "🔒 /callback — locked")
    lines.append("/bulk <numbers/CSV> — Bulk campaign" if user.can_bulk
                 else "🔒 /bulk — locked (/requestupgrade to ask)")
    lines.append("/topup — Add credits")
    lines.append("/requestupgrade — Ask admin for higher limits or bulk access")
    lines.append("/appeal — Appeal a suspension or ban")
    lines.append("/notifications — Toggle your alerts")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# /requestupgrade, /appeal — user -> admin, routed as an audit-logged note
# and pushed live to the owner
# ---------------------------------------------------------------------------

async def requestupgrade_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        note = " ".join(context.args) if context.args else "(no message)"
        await svc.log_audit(session, user.tg_id, "requestupgrade", user.id, note)
        await session.commit()

    await notify_admin(
        f"📩 *Upgrade request*\n@{update.effective_user.username or 'no_username'} "
        f"(ID `{update.effective_user.id}`)\nMessage: {note}"
    )
    await update.effective_message.reply_text("✅ Request sent to the admin. You'll be notified of any changes.")


async def appeal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        note = " ".join(context.args) if context.args else "(no message)"
        await svc.log_audit(session, user.tg_id, "appeal", user.id, note)
        await session.commit()

    await notify_admin(
        f"⚖️ *Appeal submitted*\n@{update.effective_user.username or 'no_username'} "
        f"(ID `{update.effective_user.id}`)\nMessage: {note}"
    )
    await update.effective_message.reply_text("✅ Your appeal was sent to the admin.")


# ---------------------------------------------------------------------------
# /notifications — user's own alert preference
# ---------------------------------------------------------------------------

async def notifications_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        user.notify_enabled = not user.notify_enabled
        await session.commit()
        state = "ON 🔔" if user.notify_enabled else "OFF 🔕"
        await update.effective_message.reply_text(f"Notifications: {state}")


# ---------------------------------------------------------------------------
# /history — the user's OWN usage only, never another user's
# ---------------------------------------------------------------------------

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from sqlalchemy import select
    from .models import UsageLog

    async with SessionLocal() as session:
        user = await svc.get_or_create_user(session, update.effective_user, owner_tg_id=OWNER_TG_ID)
        stmt = (select(UsageLog).where(UsageLog.user_id == user.id)
                .order_by(UsageLog.timestamp.desc()).limit(10))
        rows = (await session.execute(stmt)).scalars().all()
        await session.commit()

    if not rows:
        await update.effective_message.reply_text("No activity yet.")
        return

    lines = ["📜 *Your Recent Activity*\n"]
    for r in rows:
        lines.append(f"• {r.timestamp:%Y-%m-%d %H:%M} — {r.action}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Example: wiring your EXISTING dialing logic behind the gate.
# Replace the body with your real OmniDimension/Twilio/Telnyx dispatch call —
# the gate + usage-recording + credit-deduction is the only new part.
# ---------------------------------------------------------------------------

@gated(permission="can_call", limit_field="max_calls_per_day", action_name="call")
async def call_handler_example(update: Update, context: ContextTypes.DEFAULT_TYPE, user, session):
    if not context.args:
        await update.effective_message.reply_text("Usage: /call <phone> [message]")
        return

    phone = context.args[0]
    estimated_cost = 1.0  # replace with your real per-call credit cost

    if not await svc.check_and_deduct(session, user, estimated_cost):
        await update.effective_message.reply_text("💳 Not enough credits. Use /topup.")
        return

    # ---- your existing dispatch call goes here, e.g.: ----
    # await omnidimension_client.dial(phone, message=" ".join(context.args[1:]))

    await update.effective_message.reply_text(f"📞 Calling {phone}... ({user.credit_balance} credits left)")
