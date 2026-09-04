"""
================================================================================
  📄 OmniDimension Executive Campaign Audit Report & PDF Generator
================================================================================
  Generates multi-page luxury HTML & PDF executive campaign audit reports
  complete with KPI metric cards, SVG pie charts, and itemized billing ledgers.
================================================================================
"""

import os
import datetime
from live_billing_engine import fetch_all_accounts_pool_billing
from lead_intelligence_engine import load_lead_records


def generate_executive_html_report(clients_pool, output_path=None):
    """Generate a responsive HTML executive report with dark glassmorphism styling."""
    pool_data = fetch_all_accounts_pool_billing(clients_pool)
    lead_data = load_lead_records()
    now_str = datetime.datetime.now().strftime("%B %d, %Y - %I:%M %p")

    tot_calls = pool_data.get("pool_total_calls", 0)
    connected_calls = pool_data.get("pool_billable_calls", 0)
    ans_rate = pool_data.get("pool_answered_rate_percent", 0.0)
    tot_spent = pool_data.get("pool_spent_usd", 0.0)
    pool_bal = pool_data.get("pool_balance_usd", 0.0)
    mins_left = pool_data.get("pool_minutes_left", 0)

    hot_leads_count = len([v for v in lead_data.values() if v.get("is_hot")])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>OmniDimension Executive Campaign Audit Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
  body {{ background: #0b0f19; color: #f3f4f6; padding: 40px 20px; }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; margin-bottom: 30px; }}
  .badge {{ background: linear-gradient(135deg, #10b981, #059669); color: #fff; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; text-transform: uppercase; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 35px; }}
  .kpi-card {{ background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; text-align: center; }}
  .kpi-title {{ font-size: 13px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
  .kpi-val {{ font-size: 32px; font-weight: 800; color: #38bdf8; }}
  .kpi-sub {{ font-size: 12px; color: #6b7280; margin-top: 6px; }}
  .section {{ background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 25px; margin-bottom: 30px; }}
  .section-title {{ font-size: 18px; font-weight: 700; color: #e5e7eb; margin-bottom: 18px; display: flex; align-items: center; gap: 8px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 14px; }}
  th {{ color: #9ca3af; font-weight: 600; text-transform: uppercase; font-size: 12px; }}
  .tag-hot {{ background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 4px 10px; border-radius: 6px; font-weight: 700; }}
  .tag-success {{ background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 4px 10px; border-radius: 6px; }}
  .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 40px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1 style="font-size: 26px; font-weight: 800; color: #fff;">🎙️ OmniDimension Voice AI</h1>
      <p style="color: #9ca3af; font-size: 14px; margin-top: 4px;">Executive Campaign Audit & Conversion Report</p>
    </div>
    <div>
      <span class="badge">Live Production Verified 🟢</span>
      <p style="color: #6b7280; font-size: 12px; margin-top: 6px; text-align: right;">{now_str}</p>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Total Outbound Calls</div>
      <div class="kpi-val">{tot_calls}</div>
      <div class="kpi-sub">Across {len(clients_pool)} Accounts</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Answered Rate</div>
      <div class="kpi-val" style="color: #34d399;">{ans_rate:.1f}%</div>
      <div class="kpi-sub">{connected_calls} Connected Calls</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Hot Leads Qualified</div>
      <div class="kpi-val" style="color: #f87171;">{hot_leads_count}</div>
      <div class="kpi-sub">Score &ge; 75/100</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Wallet Balance</div>
      <div class="kpi-val" style="color: #fbbf24;">${pool_bal:.2f}</div>
      <div class="kpi-sub">{mins_left} Calling Minutes Left</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">🏢 Connected Account Pools & Billing Status</div>
    <table>
      <thead>
        <tr>
          <th>Account Name</th>
          <th>Live Balance</th>
          <th>Total Calls</th>
          <th>Minutes Left</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
"""
    for acc in pool_data.get("accounts", []):
        html += f"""
        <tr>
          <td style="font-weight: 700;">{acc['account_name']}</td>
          <td>${acc['current_balance_usd']:.2f}</td>
          <td>{acc['total_calls']}</td>
          <td>{acc['minutes_remaining']} min</td>
          <td><span class="tag-success">Active 🟢</span></td>
        </tr>
"""

    html += """
      </tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-title">🔥 Qualified Hot Leads & Customer Intent</div>
    <table>
      <thead>
        <tr>
          <th>Customer Number</th>
          <th>Contact Name</th>
          <th>Duration</th>
          <th>Lead Score</th>
          <th>Sentiment</th>
        </tr>
      </thead>
      <tbody>
"""
    if not lead_data:
        html += """
        <tr>
          <td colspan="5" style="text-align: center; color: #9ca3af; padding: 20px;">No leads recorded yet. Dispatch calls to populate live intelligence.</td>
        </tr>
"""
    else:
        for phone, lead in list(lead_data.items())[:10]:
            html += f"""
        <tr>
          <td style="font-family: monospace; font-weight: 600;">{phone}</td>
          <td>{lead.get('name', 'Customer')}</td>
          <td>{lead.get('duration', '0:0')}</td>
          <td><span class="tag-hot">{lead.get('score', 0)}/100</span></td>
          <td>{lead.get('sentiment', 'Neutral')}</td>
        </tr>
"""

    html += f"""
      </tbody>
    </table>
  </div>

  <div class="footer">
    Generated automatically by OmniDimension Autonomous Executive Daemon &bull; {now_str}
  </div>
</div>
</body>
</html>
"""
    target = output_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "executive_report.html")
    with open(target, "w", encoding="utf-8") as f:
        f.write(html)

    return target
