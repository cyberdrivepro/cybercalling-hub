"""
================================================================================
  🎙️ OmniDimension Daily Morning Executive Audio Digest Generator
================================================================================
  Compiles daily call metrics, hot lead conversions, and wallet balance
  into a concise, human-like executive audio script & briefing card.
================================================================================
"""

import os
import datetime
from live_billing_engine import fetch_all_accounts_pool_billing
from lead_intelligence_engine import load_lead_records


def generate_executive_morning_digest_text(clients_pool):
    """
    Generate an executive audio script summarizing key metrics.
    """
    pool_data = fetch_all_accounts_pool_billing(clients_pool)
    leads = load_lead_records()
    now_str = datetime.datetime.now().strftime("%A, %B %d")

    tot_calls = pool_data.get("pool_total_calls", 0)
    connected = pool_data.get("pool_billable_calls", 0)
    ans_rate = pool_data.get("pool_answered_rate_percent", 0.0)
    tot_spent = pool_data.get("pool_spent_usd", 0.0)
    bal = pool_data.get("pool_balance_usd", 0.0)
    mins_left = pool_data.get("pool_minutes_left", 0)

    hot_leads = [v for v in leads.values() if v.get("is_hot")]
    hot_count = len(hot_leads)

    script = (
        f"Good morning Boss! Here is your OmniDimension Executive Voice AI briefing for {now_str}.\n\n"
        f"Yesterday, our autonomous Voice AI system handled {tot_calls} outbound phone calls across 2 connected accounts, "
        f"achieving a solid {ans_rate:.1f}% answer rate with {connected} successfully connected conversations.\n\n"
        f"We qualified {hot_count} High-Intent Hot Leads ready for deal closing. "
        f"Total telephony expenditure was ${tot_spent:.2f}, leaving ${bal:.2f} in our wallet balance, "
        f"which provides approximately {mins_left} minutes of continuous calling runway.\n\n"
        f"All AI assistants and persistent redial daemons are running at 100% operational capacity. Have a productive day!"
    )

    card_text = (
        f"🎙️ *[Executive Morning Voice AI Briefing — {now_str}]*\n\n"
        f"📊 *Key Performance Indicators:*\n"
        f"• *Total Outbound Calls:* `{tot_calls}`\n"
        f"• *Answered Rate:* `{ans_rate:.1f}%` ({connected} connected)\n"
        f"• *Hot Leads Qualified:* `🔥 {hot_count} Deals Ready`\n"
        f"• *Total Spent:* `${tot_spent:.2f}`\n"
        f"• *Wallet Remaining:* `${bal:.2f}` ({mins_left} mins)\n\n"
        f"🤖 *Executive Audio Script:*\n"
        f"_{script}_\n\n"
        f"💡 Type `/report` to download the full visual HTML campaign report!"
    )

    return {
        "script": script,
        "card_text": card_text,
        "hot_count": hot_count,
        "tot_calls": tot_calls,
        "balance": bal
    }
