"""
Example: how to wire this package into your TWO existing bots.
Copy the relevant half into your existing telegram_bot.py / admin_telegram_bot.py
startup code — don't run this file as-is, it's a reference.
"""
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from user_system.db import init_db

# =====================================================================
# MAIN BOT  (@DarkAngelEngine_BOT)
# =====================================================================
from user_system.main_bot_handlers import (
    start_handler, profile_handler, balance_handler, mylimits_handler,
    help_handler, requestupgrade_handler, appeal_handler,
    notifications_handler, history_handler, call_handler_example,
)


async def _post_init_main(app):
    await init_db()


def build_main_bot() -> Application:
    app = Application.builder().token(os.environ["MAIN_BOT_TOKEN"]).post_init(_post_init_main).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("balance", balance_handler))
    app.add_handler(CommandHandler("credits", balance_handler))  # alias
    app.add_handler(CommandHandler("mylimits", mylimits_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("requestupgrade", requestupgrade_handler))
    app.add_handler(CommandHandler("appeal", appeal_handler))
    app.add_handler(CommandHandler("notifications", notifications_handler))
    app.add_handler(CommandHandler("history", history_handler))
    # Replace this with your real /call handler wrapped in @gated(...) — see
    # main_bot_handlers.call_handler_example for the pattern to copy.
    app.add_handler(CommandHandler("call", call_handler_example))
    return app


# =====================================================================
# ADMIN BOT  (@Cybercallingadmin_bot)
# =====================================================================
from user_system.admin_bot_handlers import (
    users_handler, userinfo_handler, whois_handler, topup_handler,
    setlimits_handler, ban_handler, unban_handler, suspend_handler,
    unsuspend_handler, promote_handler, invite_handler, auditlog_handler,
    callback_router,
)


async def _post_init_admin(app):
    await init_db()


def build_admin_bot() -> Application:
    app = Application.builder().token(os.environ["ADMIN_BOT_TOKEN"]).post_init(_post_init_admin).build()
    app.add_handler(CommandHandler("users", users_handler))
    app.add_handler(CommandHandler("userinfo", userinfo_handler))
    app.add_handler(CommandHandler("whois", whois_handler))
    app.add_handler(CommandHandler("topup", topup_handler))
    app.add_handler(CommandHandler("setlimits", setlimits_handler))
    app.add_handler(CommandHandler("ban", ban_handler))
    app.add_handler(CommandHandler("unban", unban_handler))
    app.add_handler(CommandHandler("suspend", suspend_handler))
    app.add_handler(CommandHandler("unsuspend", unsuspend_handler))
    app.add_handler(CommandHandler("promote", promote_handler))
    app.add_handler(CommandHandler("invite", invite_handler))
    app.add_handler(CommandHandler("auditlog", auditlog_handler))
    app.add_handler(CallbackQueryHandler(callback_router))  # handles ✅/❌ confirm buttons
    return app


if __name__ == "__main__":
    # Run ONE of these per process — main bot and admin bot are two
    # separate long-running processes/services, both pointing at the
    # same DATABASE_URL. That shared DB is what keeps them "live"-synced.
    which = os.environ.get("BOT", "main")
    app = build_main_bot() if which == "main" else build_admin_bot()
    app.run_polling()
