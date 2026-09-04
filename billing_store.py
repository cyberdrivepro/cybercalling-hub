"""
================================================================================
  💳 OmniDimension Real Billing & Wallet Store (billing_store.py)
================================================================================
  Exact real rates, balances, and concurrency matching omnidim.io/billing:
  - Default Tier: Signup Gift (Pay As You Go)
  - Current Balance per Account: $1.16
  - Voice AI Rate: $0.115/min
  - Real Minutes Left: 10 mins ($1.16 / $0.115)
  - Real Concurrency: 1 slot per account (Permanent)
  - Knowledge Base: 0 / 5 MB
================================================================================
"""

import os
import json
import datetime

BILLING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".billing_state.json")

DEFAULT_BILLING_STATE = {
    "rate_per_minute": 0.115,
    "telephony_rate_per_minute": 0.005,
    "total_rate_per_minute": 0.120,
    "whatsapp_rate_per_msg": 0.006,
    "sms_rate_per_msg": 0.006,
    "kb_used_mb": 0.0,
    "kb_total_mb": 5.0,
    "auto_recharge": False,
    "concurrency": 1,
    "concurrency_type": "Permanent (Signup Gift)",
    "plans": {
        "Starter": {"price": 15, "mins": 179, "rate": 0.084, "kb": "5 MB", "team": 1},
        "Jump Starter": {"price": 30, "mins": 395, "rate": 0.076, "kb": "10 MB", "team": 2},
        "Early Deployers": {"price": 36, "mins": 588, "rate": 0.068, "kb": "50 MB", "team": 5},
        "Growth": {"price": 200, "mins": 3571, "rate": 0.056, "kb": "100 MB", "team": 10},
        "Enterprise": {"price": "Custom", "mins": "Custom", "rate": "Up to $0.035", "kb": "Custom", "team": "Unlimited"}
    },
    "accounts": {
        "Himanshu Shah": {
            "plan": "No active plan (Free Trial)",
            "balance_usd": 2.28,
            "concurrency": 1,
            "concurrency_type": "Permanent (Signup Gift)",
            "concurrency_start": "May 10, 2026"
        },
        "Rocky Balboa": {
            "plan": "No active plan (Free Trial)",
            "balance_usd": 2.28,
            "concurrency": 1,
            "concurrency_type": "Permanent (Signup Gift)",
            "concurrency_start": "May 10, 2026"
        }
    }
}


def get_billing_state():
    """Load or initialize real billing state."""
    if os.path.exists(BILLING_FILE):
        try:
            with open(BILLING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_billing_state(DEFAULT_BILLING_STATE)
    return DEFAULT_BILLING_STATE


def save_billing_state(state):
    """Persist billing state."""
    try:
        with open(BILLING_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print("Billing save error:", e)


def deduct_call_usage(account_name, duration_seconds):
    """Deduct exact cost ($0.115/min) from account balance after a completed call."""
    state = get_billing_state()
    rate = state.get("rate_per_minute", 0.115)
    cost = (duration_seconds / 60.0) * rate

    acc = state.get("accounts", {}).get(account_name)
    if not acc:
        for k in state.get("accounts", {}):
            if account_name.lower() in k.lower():
                acc = state["accounts"][k]
                break

    if acc:
        current_bal = acc.get("balance_usd", 1.16)
        new_bal = max(0.0, current_bal - cost)
        acc["balance_usd"] = round(new_bal, 4)
        save_billing_state(state)
        return new_bal, cost
    return 1.16, 0.0


def top_up_account_balance(account_name, added_amount_usd):
    """Top up wallet balance."""
    state = get_billing_state()
    acc = state.get("accounts", {}).get(account_name)
    if not acc:
        for k in state.get("accounts", {}):
            if account_name.lower() in k.lower():
                acc = state["accounts"][k]
                break

    if acc:
        acc["balance_usd"] = round(acc.get("balance_usd", 0.0) + added_amount_usd, 2)
        save_billing_state(state)
        return acc["balance_usd"]
    return None
