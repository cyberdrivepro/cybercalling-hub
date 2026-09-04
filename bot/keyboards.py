"""
================================================================================
  ⌨️ CyberCalling 2.0 — Telegram Inline Keyboard Builders
================================================================================
"""

from typing import Dict, Any, List

def build_main_caller_keyboard() -> Dict[str, Any]:
    """Build modern interactive inline keyboard for @DarkAngelEngine_BOT."""
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ 1-Tap Call", "callback_data": "call_quick"},
                {"text": "📞 Twilio Bulk", "callback_data": "menu_twilio"}
            ],
            [
                {"text": "📢 Bulk Campaign", "callback_data": "menu_bulk"},
                {"text": "💳 Balance", "callback_data": "menu_balance"}
            ],
            [
                {"text": "📋 Live Call Logs", "callback_data": "menu_logs"},
                {"text": "🤖 AI Assistants", "callback_data": "menu_bots"}
            ],
            [
                {"text": "🌐 Web Dashboard", "url": "https://huggingface.co/spaces/cyberexpert29/cybercalling-hub"},
                {"text": "💳 Recharge Credits", "callback_data": "menu_topup"}
            ]
        ]
    }

def build_admin_dashboard_keyboard() -> Dict[str, Any]:
    """Build modern interactive inline keyboard for @Cybercallingadmin_bot."""
    return {
        "inline_keyboard": [
            [
                {"text": "🔑 View Connected Keys", "callback_data": "admin_view_keys"},
                {"text": "➕ Add New Key", "callback_data": "admin_add_key"}
            ],
            [
                {"text": "🔄 Hot-Swap Key", "callback_data": "admin_swap_key"},
                {"text": "💳 Quota & Balance", "callback_data": "admin_balance"}
            ],
            [
                {"text": "📜 Security Audit Log", "callback_data": "admin_audit_log"},
                {"text": "🔒 Lock Vault", "callback_data": "admin_lock"}
            ]
        ]
    }
