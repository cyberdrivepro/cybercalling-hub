"""
@Cybercallingadmin_bot — user & access management commands.

All money-moving or access-changing actions go through an inline
Yes/No confirm before they commit (see _confirm_keyboard / callback_router)
so nothing destructive fires from a single mistyped command.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .db import SessionLocal
from .permissions import admin_only, owner_only
from . import user_service as svc
from .notify import notify_admin  # reused if you want admin-bot -> owner escalation later

# In-memory pending-confirm store: {confirm_id: {"action": ..., "params": {...}}}
# Fine for a single-admin-process bot; swap for a DB table if you run >1 admin worker.
_PENDING: dict[str, dict] = {}


def _confirm_keyboard(confirm_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{confirm_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{confirm_id}"),
    ]])


def _stash(action: str, **params) -> str:
    confirm_id = f"{action}:{datetime.utcnow().timestamp()}"
    _PENDING[confirm_id] = {"action": action, "params": params}
    return confirm_id


# ---------------------------------------------------------------------------
# /users — paginated list + live header stats (your "Category 2" screen)
# ---------------------------------------------------------------------------

@admin_only
async def users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1

    async with SessionLocal() as session:
        stats = await svc.get_stats(session)
        rows, total = await svc.list_users(session, page=page, page_size=10)
        await session.commit()

    header = (
        f"👥 *User & Admin Lifecycle Management*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Total Users: {stats['total_users']}\n"
        f"• Active Today: {stats['active_today']}\n"
        f"• Banned: {stats['banned']}  |  Suspended: {stats['suspended']}\n"
        f"• Total Credits in Circulation: {stats['total_credits']}\n\n"
    )
    if not rows:
        await update.effective_message.reply_text(header + "No users on this page.", parse_mode="Markdown")
        return

    lines = []
    for u in rows:
        flag = "🚫" if u.is_banned else ("⏸️" if u.is_suspended else "🟢")
        lines.append(f"{flag} `{u.tg_id}` @{u.tg_username or '—'} — {u.credit_balance} cr — {u.role}")

    total_pages = max(1, -(-total // 10))
    footer = f"\nPage {page}/{total_pages}. /users {page+1} for next."
    await update.effective_message.reply_text(header + "\n".join(lines) + footer, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# /userinfo <id_or_username>, /whois — full per-user detail card
# ---------------------------------------------------------------------------

@admin_only
async def userinfo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /userinfo <tg_id or @username>")
        return

    async with SessionLocal() as session:
        user = await svc.resolve_user(session, context.args[0])
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        _, used_day, cap_day = await svc.check_rate_limit(session, user, "max_calls_per_day", "day")
        _, used_hr, cap_hr = await svc.check_rate_limit(session, user, "max_calls_per_hour", "hour")
        await session.commit()

    flag = "🚫 Banned" if user.is_banned else ("⏸️ Suspended" if user.is_suspended else "🟢 Active")
    text = (
        f"👤 *User Detail — @{user.tg_username or '—'}* (ID `{user.tg_id}`)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Role: {user.role.title()}        Status: {flag}\n"
        f"Joined: {user.created_at:%Y-%m-%d}     Last active: {user.last_active:%Y-%m-%d %H:%M}\n"
        f"Balance: {user.credit_balance} credits\n\n"
        f"📞 Limits\n"
        f"• Today: {used_day}/{cap_day or '∞'}   This hour: {used_hr}/{cap_hr or '∞'}\n"
        f"• Bulk batch cap: {user.max_bulk_batch_size or '∞'}\n"
        f"• Can Bulk: {'✅' if user.can_bulk else '❌'}  Webcall: {'✅' if user.can_webcall else '❌'}  "
        f"Callback: {'✅' if user.can_callback else '❌'}\n"
    )
    if user.notes:
        text += f"\n🗒️ Notes: {user.notes}"

    await update.effective_message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Credits", callback_data=f"ui_add:{user.tg_id}"),
             InlineKeyboardButton("➖ Remove", callback_data=f"ui_sub:{user.tg_id}")],
            [InlineKeyboardButton("🚫 Ban", callback_data=f"ui_ban:{user.tg_id}"),
             InlineKeyboardButton("⏸️ Suspend", callback_data=f"ui_susp:{user.tg_id}")],
        ]),
    )


@admin_only
async def whois_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await userinfo_handler(update, context)


# ---------------------------------------------------------------------------
# /topup <id> <amount>  — confirm-diff before committing
# ---------------------------------------------------------------------------

@admin_only
async def topup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: /topup <tg_id or @username> <amount>")
        return
    identifier, amount_str = context.args[0], context.args[1]
    try:
        amount = float(amount_str)
    except ValueError:
        await update.effective_message.reply_text("Amount must be a number.")
        return

    async with SessionLocal() as session:
        user = await svc.resolve_user(session, identifier)
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        before, after = user.credit_balance, round(user.credit_balance + amount, 4)

    confirm_id = _stash("topup", tg_id=user.tg_id, amount=amount)
    await update.effective_message.reply_text(
        f"Before: {before} → After: {after} credits for @{user.tg_username or user.tg_id}\nConfirm?",
        reply_markup=_confirm_keyboard(confirm_id),
    )


# ---------------------------------------------------------------------------
# /setlimits <id> <calls_day> <calls_hour> <bulk_cap>
# ---------------------------------------------------------------------------

@admin_only
async def setlimits_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.effective_message.reply_text("Usage: /setlimits <id> <calls/day> <calls/hour> <bulk_cap>")
        return
    identifier, day, hour, bulk = context.args[:4]

    async with SessionLocal() as session:
        user = await svc.resolve_user(session, identifier)
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        await svc.set_limits(
            session, user, update.effective_user.id,
            max_calls_per_day=int(day), max_calls_per_hour=int(hour), max_bulk_batch_size=int(bulk),
        )
        await session.commit()

    await update.effective_message.reply_text(f"✅ Limits updated for @{user.tg_username or user.tg_id}.")


# ---------------------------------------------------------------------------
# /ban, /unban, /suspend, /unsuspend, /promote
# ---------------------------------------------------------------------------

@admin_only
async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /ban <id> <reason>")
        return
    identifier, reason = context.args[0], " ".join(context.args[1:]) or "not specified"

    async with SessionLocal() as session:
        user = await svc.resolve_user(session, identifier)
        if not user:
            await update.effective_message.reply_text("User not found.")
            return

    confirm_id = _stash("ban", tg_id=user.tg_id, reason=reason)
    await update.effective_message.reply_text(
        f"Ban @{user.tg_username or user.tg_id}? Reason: {reason}",
        reply_markup=_confirm_keyboard(confirm_id),
    )


@admin_only
async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /unban <id>")
        return
    async with SessionLocal() as session:
        user = await svc.resolve_user(session, context.args[0])
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        await svc.unban_user(session, user, update.effective_user.id)
        await session.commit()
    await update.effective_message.reply_text(f"✅ Unbanned @{user.tg_username or user.tg_id}.")


@admin_only
async def suspend_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /suspend <id> [hours] [reason]")
        return
    identifier = context.args[0]
    hours = None
    reason_parts = context.args[1:]
    if reason_parts and reason_parts[0].isdigit():
        hours = int(reason_parts[0])
        reason_parts = reason_parts[1:]
    reason = " ".join(reason_parts) or "not specified"

    async with SessionLocal() as session:
        user = await svc.resolve_user(session, identifier)
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        until = datetime.utcnow() + timedelta(hours=hours) if hours else None
        await svc.suspend_user(session, user, reason, update.effective_user.id, until=until)
        await session.commit()

    duration = f"{hours}h" if hours else "indefinitely"
    await update.effective_message.reply_text(
        f"⏸️ @{user.tg_username or user.tg_id} suspended {duration}. Reason: {reason}"
    )


@admin_only
async def unsuspend_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /unsuspend <id>")
        return
    async with SessionLocal() as session:
        user = await svc.resolve_user(session, context.args[0])
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        await svc.unsuspend_user(session, user, update.effective_user.id)
        await session.commit()
    await update.effective_message.reply_text(f"✅ Reactivated @{user.tg_username or user.tg_id}.")


@owner_only
async def promote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2 or context.args[1] not in ("owner", "admin", "user"):
        await update.effective_message.reply_text("Usage: /promote <id> <owner|admin|user>")
        return
    async with SessionLocal() as session:
        user = await svc.resolve_user(session, context.args[0])
        if not user:
            await update.effective_message.reply_text("User not found.")
            return
        await svc.set_role(session, user, context.args[1], update.effective_user.id)
        await session.commit()
    await update.effective_message.reply_text(f"✅ @{user.tg_username or user.tg_id} is now {context.args[1]}.")


# ---------------------------------------------------------------------------
# /invite — controlled onboarding code, not an open public link
# ---------------------------------------------------------------------------

@admin_only
async def invite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    max_uses = int(context.args[0]) if context.args else 1
    async with SessionLocal() as session:
        invite = await svc.create_invite_code(session, update.effective_user.id, max_uses=max_uses)
        await session.commit()
    await update.effective_message.reply_text(
        f"🔗 Invite code: `{invite.code}`\nMax uses: {invite.max_uses}\nExpires: {invite.expires_at:%Y-%m-%d}",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# /auditlog — recent admin/vault actions
# ---------------------------------------------------------------------------

@admin_only
async def auditlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limit = int(context.args[0]) if context.args and context.args[0].isdigit() else 20
    async with SessionLocal() as session:
        rows = await svc.recent_audit_log(session, limit=limit)
        await session.commit()

    if not rows:
        await update.effective_message.reply_text("No audit entries yet.")
        return

    lines = ["📜 *Recent Admin Actions*\n"]
    for r in rows:
        lines.append(f"• {r.timestamp:%m-%d %H:%M} — actor `{r.actor_tg_id}` — {r.action} — {r.detail or ''}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Callback router — handles the ✅/❌ buttons from confirm flows above
# ---------------------------------------------------------------------------

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    verb, confirm_id = query.data.split(":", 1)

    if verb == "cancel":
        _PENDING.pop(confirm_id, None)
        await query.edit_message_text("❌ Cancelled.")
        return

    pending = _PENDING.pop(confirm_id, None)
    if not pending:
        await query.edit_message_text("⚠️ This confirmation expired.")
        return

    action, params = pending["action"], pending["params"]
    actor_tg_id = update.effective_user.id

    async with SessionLocal() as session:
        user = await svc.get_user_by_tg_id(session, params["tg_id"])
        if not user:
            await query.edit_message_text("User no longer exists.")
            return

        if action == "topup":
            await svc.adjust_credits(session, user, params["amount"], "admin_grant",
                                      performed_by=actor_tg_id, reason="admin topup")
            await session.commit()
            await query.edit_message_text(f"✅ New balance: {user.credit_balance} credits.")

        elif action == "ban":
            await svc.ban_user(session, user, params["reason"], actor_tg_id)
            await session.commit()
            await query.edit_message_text(f"🚫 @{user.tg_username or user.tg_id} banned.")

        else:
            await query.edit_message_text("Unknown action.")
