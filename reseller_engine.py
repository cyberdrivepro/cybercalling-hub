"""
================================================================================
  🏷️ OmniDimension White-Label Agency & Reseller Profit Markup Engine
================================================================================
  Manages client organizations, retail markup ($0.115 -> $0.25/min), and invoices.
================================================================================
"""

import os
import json
import uuid
import datetime

RESELLER_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".reseller_agency.json")


def load_reseller_data():
    if os.path.exists(RESELLER_CONFIG_FILE):
        try:
            with open(RESELLER_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "agency_name": "CyberVoice AI Solutions",
        "wholesale_rate_usd": 0.115,
        "retail_rate_usd": 0.250,
        "clients": [
            {"id": "cl_101", "name": "Apex Real Estate Ltd", "contact": "+919876543210", "minutes_allocated": 500, "minutes_used": 120, "rate_charged": 0.250, "balance_usd": 95.0},
            {"id": "cl_102", "name": "Horizon E-commerce Store", "contact": "+919811122233", "minutes_allocated": 1000, "minutes_used": 450, "rate_charged": 0.220, "balance_usd": 121.0}
        ]
    }


def save_reseller_data(data):
    try:
        with open(RESELLER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Reseller save error:", e)


def calculate_agency_profit_metrics():
    """Calculate wholesale costs, retail revenues, and net agency profit."""
    data = load_reseller_data()
    wholesale = data.get("wholesale_rate_usd", 0.115)
    retail = data.get("retail_rate_usd", 0.250)
    clients = data.get("clients", [])

    total_mins_used = sum(c.get("minutes_used", 0) for c in clients)
    total_wholesale_cost = total_mins_used * wholesale
    total_client_revenue = sum(c.get("minutes_used", 0) * c.get("rate_charged", retail) for c in clients)
    net_agency_profit = total_client_revenue - total_wholesale_cost
    margin_percent = (net_agency_profit / total_client_revenue * 100) if total_client_revenue > 0 else 0.0

    return {
        "agency_name": data.get("agency_name", "CyberVoice AI Solutions"),
        "total_clients": len(clients),
        "total_mins_used": total_mins_used,
        "wholesale_cost_usd": round(total_wholesale_cost, 2),
        "client_revenue_usd": round(total_client_revenue, 2),
        "net_profit_usd": round(net_agency_profit, 2),
        "margin_percent": round(margin_percent, 1)
    }


def generate_client_invoice_html(client_id):
    """Generate an official client invoice in HTML format."""
    data = load_reseller_data()
    agency = data.get("agency_name", "CyberVoice AI Solutions")
    client = next((c for c in data.get("clients", []) if c.get("id") == client_id), data.get("clients", [])[0])

    mins = client.get("minutes_used", 100)
    rate = client.get("rate_charged", 0.25)
    total = mins * rate
    inv_num = f"INV-2026-{client.get('id', '101')}"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice {inv_num} - {agency}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; }}
        .box {{ max-width: 650px; margin: auto; background: #1e293b; border-radius: 10px; padding: 30px; border: 1px solid #334155; }}
        .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; }}
        .title {{ font-size: 22px; font-weight: bold; color: #60a5fa; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #334155; text-align: left; }}
        th {{ background: #0f172a; color: #94a3b8; }}
        .total-row {{ font-size: 18px; font-weight: bold; color: #10b981; }}
    </style>
</head>
<body>
    <div class="box">
        <div class="header">
            <div>
                <div class="title">{agency}</div>
                <div style="color:#94a3b8; font-size:12px;">Enterprise Voice AI Telecom Solutions</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:16px; font-weight:bold;">{inv_num}</div>
                <div style="color:#94a3b8; font-size:12px;">{datetime.date.today().strftime('%B %d, %Y')}</div>
            </div>
        </div>

        <p><strong>Billed To:</strong> {client.get('name')}<br><strong>Contact:</strong> {client.get('contact')}</p>

        <table>
            <thead>
                <tr><th>Description</th><th>Talk Minutes</th><th>Rate</th><th>Total</th></tr>
            </thead>
            <tbody>
                <tr>
                    <td>Autonomous Voice AI Calling Consumption</td>
                    <td>{mins} mins</td>
                    <td>${rate:.3f}/min</td>
                    <td>${total:.2f}</td>
                </tr>
                <tr class="total-row">
                    <td colspan="3">Grand Total Due:</td>
                    <td>${total:.2f}</td>
                </tr>
            </tbody>
        </table>

        <div style="margin-top: 30px; text-align: center; color: #64748b; font-size: 11px;">
            Thank you for your business with {agency}. For assistance, contact support@{agency.lower().replace(' ', '')}.com
        </div>
    </div>
</body>
</html>"""
    invoice_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"invoice_{client.get('id')}.html")
    with open(invoice_path, "w", encoding="utf-8") as f:
        f.write(html)
    return invoice_path
