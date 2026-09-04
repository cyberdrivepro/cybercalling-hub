"""
================================================================================
  📱 OmniDimension Android Mobile App & REST API Server (v15.0)
================================================================================
  All 20+ Enterprise Superpowers:
  • Single & Bulk Calling Dispatcher with Auto Country Detection
  • In-App MP3 Audio Player & Waveforms
  • Live Telephony Ledger ($0.80 Balance, $0.120/min Rate)
  • Assistant Switcher & Creator (Cyber expert, Sales Support)
  • Deep CRM Customer Inspector & Lead Tagging
  • Native Android Contact Picker API Integration
  • DND Blacklist Manager
  • Multi-Account Pool Failover (Himanshu Shah + Rocky Balboa)
  • Scheduled Callback & Timing Controls
================================================================================
"""

import os
import sys
import socket
import qrcode
import json
import time
import datetime
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
BLACKLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dnd_blacklist.txt")
load_dotenv(ENV_PATH)

from omnidimension import Client
from phone_normalizer import normalize_and_detect_country
from personal_contacts import load_contacts, add_contact
from live_billing_engine import fetch_all_accounts_pool_billing, fetch_account_live_billing
from persistent_redialer import register_redial_task, stop_redial_task
from lead_intelligence_engine import load_lead_records, get_all_hot_leads
from knowledge_rag_engine import load_knowledge_bases, build_system_prompt_from_knowledge
from executive_report_generator import generate_executive_html_report
from audio_digest_engine import generate_executive_morning_digest_text
from live_sync_logger import get_sync_csv_path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "android_app", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "android_app")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['JSON_AS_ASCII'] = False
CORS(app)

@app.after_request
def apply_cors_and_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

# App State
app_state = {
    "selected_agent_name": "Dark Angel Voice AI",
    "selected_agent_id": 247312,
    "caller_id": "+917969006012",
    "calling_window": "09:00 - 20:00"
}

# Initialize OmniDimension Multi-Account Pool
raw_keys = os.getenv("OMNIDIM_API_KEYS", "")
if raw_keys:
    api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
else:
    single = os.getenv("OMNIDIM_API_KEY", "53lx9WsjS8dtsHYV7qhnjOUmwKTJmEZOTYipMKIgNmw").strip()
    api_keys = [single] if single else ["53lx9WsjS8dtsHYV7qhnjOUmwKTJmEZOTYipMKIgNmw"]

clients_pool = []
for i, k in enumerate(api_keys):
    try:
        cl = Client(api_key=k)
        uname = "Himanshu Shah" if i == 0 else "Rocky Balboa"
        bots = cl.agent.list().get("json", {}).get("bots", [])
        clients_pool.append({"index": i, "client": cl, "user": uname, "bots": bots})
    except Exception as e:
        print(f"Error loading client {i}:", e)


def get_local_ip():
    """Find local network IP address for Android phone pairing."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_dnd_list():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []


def add_to_dnd(phone):
    clean_num = phone.strip()
    with open(BLACKLIST_FILE, "a") as f:
        f.write(f"\n{clean_num}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(STATIC_DIR, "manifest.json")


@app.route("/sw.js")
def service_worker():
    return send_from_directory(STATIC_DIR, "sw.js")


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({
        "status": "online",
        "assistant": app_state["selected_agent_name"],
        "agent_id": app_state["selected_agent_id"],
        "caller_id": app_state["caller_id"],
        "calling_window": app_state["calling_window"],
        "rate_usd_per_min": 0.120,
        "accounts_connected": len(clients_pool)
    })


@app.route("/api/billing", methods=["GET"])
def api_billing():
    try:
        data = fetch_all_accounts_pool_billing(clients_pool)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync/keys", methods=["POST"])
def api_sync_keys():
    """Cross-host secure API key synchronization endpoint."""
    auth_header = request.headers.get("X-Vault-Auth", "") or request.json.get("auth_passkey", "")
    if auth_header != "Cyberexpert2521@":
        return jsonify({"success": False, "error": "Unauthorized: Invalid Vault Passkey"}), 401
    
    data = request.get_json(silent=True) or {}
    new_keys = data.get("keys", [])
    if not new_keys:
        return jsonify({"success": False, "error": "No keys provided"}), 400
    
    try:
        from encrypted_api_vault import save_encrypted_vault, sync_vault_to_env, MASTER_PASSKEY_DEFAULT
        vault_data = {
            "version": "2.0",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "keys": [{"api_key": k, "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "active"} for k in new_keys]
        }
        save_encrypted_vault(MASTER_PASSKEY_DEFAULT, vault_data)
        sync_vault_to_env(MASTER_PASSKEY_DEFAULT)
        # Reload local clients pool
        init_clients_pool()
        return jsonify({"success": True, "accounts_count": len(clients_pool), "message": "Cross-Host Keys Synced Successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/recordings", methods=["GET"])
def api_recordings():
    """Fetch all playable audio recordings across all connected accounts."""
    recordings = []
    for c_entry in clients_pool:
        cl = c_entry["client"]
        uname = c_entry["user"]
        try:
            r = cl.call.get_call_logs(page=1, page_size=50)
            logs = r.get("json", {}).get("call_log_data", []) if isinstance(r, dict) else []
            for it in logs:
                rec = it.get("internal_recording_url") or it.get("recording_url")
                if rec and rec != False:
                    url = rec if str(rec).startswith("http") else f"https://omnidim.io{rec}"
                    recordings.append({
                        "id": it.get("id"),
                        "to_number": it.get("to_number") or it.get("phone_number"),
                        "call_duration": it.get("call_duration") or it.get("duration") or "0:15",
                        "status": it.get("call_status") or it.get("status") or "completed",
                        "time_of_call": it.get("time_of_call") or it.get("created_at") or "",
                        "account_name": uname,
                        "audio_stream_url": url
                    })
        except Exception as e:
            print("Recordings error on", uname, e)
    return jsonify({"recordings": recordings})


@app.route("/api/call", methods=["POST"])
def api_call():
    """Dispatch outbound call with auto country code & custom greeting."""
    req = request.get_json() or {}
    raw_phone = req.get("phone", "").strip()
    name = req.get("name", "").strip()
    msg = req.get("message", "").strip()
    redial = req.get("persistent_redial", True)

    if not raw_phone:
        return jsonify({"success": False, "error": "Phone number is required"}), 400

    norm = normalize_and_detect_country(raw_phone)
    clean_num = norm.get("clean_number", "")
    country = norm.get("country_name", "India")
    flag = norm.get("flag", "🇮🇳")
    if not clean_num:
        return jsonify({"success": False, "error": "Invalid phone number"}), 400

    # DND Check
    if clean_num in get_dnd_list():
        return jsonify({"success": False, "error": f"Number {clean_num} is in DND Blacklist"}), 403

    if not clients_pool:
        return jsonify({"success": False, "error": "No OmniDimension accounts available"}), 500

    client = clients_pool[0]["client"]
    agent_id = app_state["selected_agent_id"]

    # 1. Update cloud welcome greeting if custom message provided
    if msg:
        try:
            client.agent.update(agent_id, {
                "welcome_message": msg,
                "context": f"You are speaking to {name or 'the customer'}. Your primary instruction: {msg}"
            })
        except Exception as ex:
            print("Greeting update error:", ex)

    # 2. Dispatch Outbound Call
    try:
        res = client.call.dispatch_call(
            agent_id=agent_id,
            to_number=clean_num,
            call_context={"customer_name": name or "Customer", "task": msg or "General Assistant Call"}
        )
        req_id = res.get("json", {}).get("requestId", "OK")

        # 3. Persistent Redial Task
        if redial:
            register_redial_task(
                task_id=str(req_id),
                recipient=clean_num,
                name=name or "Contact",
                custom_msg=msg,
                client=client,
                agent_id=agent_id,
                uname="Himanshu Shah",
                chat_id=None,
                notifier_func=None,
                max_retries=10,
                retry_delay_sec=25
            )

        return jsonify({
            "success": True,
            "requestId": req_id,
            "recipient": clean_num,
            "country": f"{flag} {country}",
            "rate": "$0.120 / min"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/bulk", methods=["POST"])
def api_bulk():
    """Launch multi-API bulk campaign."""
    req = request.get_json() or {}
    numbers_str = req.get("numbers", "")
    numbers = [n.strip() for n in numbers_str.replace("\n", ",").split(",") if n.strip()]

    if not numbers:
        return jsonify({"success": False, "error": "No phone numbers provided"}), 400

    dispatched = []
    dnd_skipped = []
    failed = []

    dnd_list = get_dnd_list()

    for idx, raw_n in enumerate(numbers):
        norm = normalize_and_detect_country(raw_n)
        clean_num = norm.get("clean_number", "")
        country = norm.get("country_name", "India")
        flag = norm.get("flag", "🇮🇳")
        if not clean_num:
            failed.append(raw_n)
            continue
        if clean_num in dnd_list:
            dnd_skipped.append(clean_num)
            continue

        c_entry = clients_pool[idx % len(clients_pool)]
        try:
            res = c_entry["client"].call.dispatch_call(
                agent_id=app_state["selected_agent_id"],
                to_number=clean_num,
                call_context={"customer_name": "Valued Contact", "task": "Bulk Voice Campaign"}
            )
            dispatched.append(clean_num)
            time.sleep(1.5)  # Safe stagger
        except Exception as e:
            failed.append(clean_num)

    return jsonify({
        "success": True,
        "total": len(numbers),
        "dispatched_count": len(dispatched),
        "dispatched": dispatched,
        "dnd_skipped": dnd_skipped,
        "failed": failed
    })


@app.route("/api/bots", methods=["GET", "POST"])
def api_bots():
    """List or select active assistant."""
    if request.method == "POST":
        req = request.get_json() or {}
        aid = req.get("agent_id")
        aname = req.get("agent_name")
        if aid and aname:
            app_state["selected_agent_id"] = int(aid)
            app_state["selected_agent_name"] = str(aname)
            return jsonify({"success": True, "selected": app_state})
        return jsonify({"success": False, "error": "Invalid params"}), 400

    all_bots = []
    for c in clients_pool:
        for b in c.get("bots", []):
            all_bots.append({
                "id": b.get("id"),
                "name": b.get("name"),
                "voice_provider": b.get("voice_provider"),
                "llm": b.get("llm_service"),
                "owner": c.get("user"),
                "is_active": (b.get("id") == app_state["selected_agent_id"])
            })
    return jsonify({"bots": all_bots, "active": app_state})


@app.route("/api/bots/create", methods=["POST"])
@app.route("/api/createbot", methods=["POST"])
def api_create_bot():
    """Create a new Voice AI Assistant directly on OmniDimension cloud platform."""
    req = request.get_json() or {}
    name = req.get("name", "").strip()
    prompt = req.get("prompt", "").strip() or "You are a helpful and polite professional AI voice assistant."
    voice = req.get("voice_provider", "cartesia")

    if not name:
        return jsonify({"success": False, "error": "Bot name is required"}), 400

    if not clients_pool:
        return jsonify({"success": False, "error": "No cloud client connected"}), 500

    try:
        cl = clients_pool[0]["client"]
        res = cl.agent.create({
            "name": name,
            "context": prompt,
            "voice_provider": voice,
            "welcome_message": f"Hello! I am {name}. How may I help you today?"
        })
        new_bot = res.get("json", {}) if isinstance(res, dict) else {}
        bot_id = new_bot.get("id") or new_bot.get("agent_id") or 247312

        # Refresh bots in pool
        clients_pool[0]["bots"] = cl.agent.list().get("json", {}).get("bots", [])
        app_state["selected_agent_id"] = int(bot_id)
        app_state["selected_agent_name"] = str(name)

        return jsonify({
            "success": True,
            "agent_id": bot_id,
            "name": name,
            "message": f"Assistant '{name}' successfully created on cloud platform!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/inspect/<phone>", methods=["GET"])
def api_inspect(phone):
    """Deep CRM lookup for a customer number."""
    try:
        norm = normalize_and_detect_country(phone)
        clean_num = norm.get("clean_number", phone) if isinstance(norm, dict) else phone
        country = norm.get("country_name", "India") if isinstance(norm, dict) else "India"
        flag = norm.get("flag", "🇮🇳") if isinstance(norm, dict) else "🇮🇳"
        call_history = []

        for c in clients_pool:
            try:
                r = c["client"].call.get_call_logs(page=1, page_size=50)
                logs = r.get("json", {}).get("call_log_data", []) if isinstance(r, dict) else []
                for it in logs:
                    t_num = str(it.get("to_number") or it.get("phone_number") or "")
                    if clean_num in t_num or phone in t_num:
                        call_history.append({
                            "duration": str(it.get("call_duration") or it.get("duration") or "0:0"),
                            "status": str(it.get("call_status") or it.get("status") or "completed"),
                            "time": str(it.get("time_of_call") or it.get("created_at") or ""),
                            "recording": bool(it.get("internal_recording_url") or it.get("recording_url"))
                        })
            except Exception as ex:
                print("Error inspecting logs on account:", ex)

        is_hot = any(x["duration"] not in ["-", "0:0", "0", ""] for x in call_history)

        return jsonify({
            "phone": clean_num,
            "country": f"{flag} {country}",
            "total_calls": len(call_history),
            "history": call_history,
            "is_dnd": clean_num in get_dnd_list(),
            "lead_status": "🔥 Hot Lead / Qualified" if is_hot else "❄️ Cold Lead"
        })
    except Exception as e:
        print("api_inspect error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """Get high-level KPI analytics."""
    total_calls = 0
    completed_calls = 0
    total_seconds = 0.0

    for c in clients_pool:
        try:
            r = c["client"].call.get_call_logs(page=1, page_size=100)
            logs = r.get("json", {}).get("call_log_data", []) if isinstance(r, dict) else []
            total_calls += len(logs)
            for it in logs:
                st = str(it.get("call_status") or it.get("status") or "").lower()
                dur = it.get("call_duration") or it.get("duration") or "0:0"
                if "complete" in st or (dur not in ["-", "0:0", "0", ""]):
                    completed_calls += 1
                if dur and dur != "-":
                    parts = str(dur).split(":")
                    if len(parts) == 2:
                        total_seconds += (float(parts[0]) * 60) + float(parts[1])
        except Exception:
            pass

    conv_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    total_cost = total_seconds * (0.120 / 60.0)

    return jsonify({
        "total_calls": total_calls,
        "completed_calls": completed_calls,
        "answered_rate_percent": round(conv_rate, 1),
        "total_talk_minutes": round(total_seconds / 60.0, 2),
        "total_cost_usd": round(total_cost, 4),
        "active_concurrency": len(clients_pool)
    })


@app.route("/api/dnd", methods=["GET", "POST"])
def api_dnd():
    if request.method == "POST":
        req = request.get_json() or {}
        p = req.get("phone", "").strip()
        if p:
            add_to_dnd(p)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Phone required"}), 400
    return jsonify({"dnd_list": get_dnd_list()})


@app.route("/api/contacts", methods=["GET", "POST"])
def api_contacts():
    if request.method == "POST":
        data = request.get_json() or {}
        n = data.get("name", "").strip()
        p = data.get("phone", "").strip()
        if n and p:
            add_contact(n, p)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Invalid fields"}), 400
    return jsonify(load_contacts())


@app.route("/api/timing", methods=["POST"])
def api_timing():
    req = request.get_json() or {}
    w = req.get("window", "").strip()
    if w:
        app_state["calling_window"] = w
        return jsonify({"success": True, "window": w})
    return jsonify({"success": False, "error": "Window required"}), 400


@app.route("/api/reports/html", methods=["GET"])
def api_reports_html():
    """Generate and return the dynamic Executive Campaign HTML Report."""
    try:
        report_path = generate_executive_html_report(clients_pool)
        return send_file(report_path, mimetype="text/html")
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/leads/hot", methods=["GET"])
def api_leads_hot():
    """Get all classified high-intent Hot Leads."""
    return jsonify({"hot_leads": get_all_hot_leads()})


@app.route("/api/digest", methods=["GET"])
def api_digest():
    """Get daily executive morning audio briefing script and metrics."""
    return jsonify(generate_executive_morning_digest_text(clients_pool))


@app.route("/api/knowledge", methods=["GET"])
def api_knowledge():
    """Get all configured AI Knowledge Bases & FAQ matrices."""
    return jsonify(load_knowledge_bases())


@app.route("/api/knowledge/apply", methods=["POST"])
def api_knowledge_apply():
    """Apply a selected knowledge base to the active Voice AI Assistant."""
    req = request.get_json() or {}
    kb_key = req.get("kb_key", "sales_closer")
    prompt = build_system_prompt_from_knowledge(kb_key, agent_name=app_state.get("assistant_name", "Cyber expert"))
    if clients_pool:
        try:
            clients_pool[0]["client"].agent.update(int(app_state["agent_id"]), {"context": prompt})
            return jsonify({"success": True, "applied_kb": kb_key})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "No clients connected"}), 400


@app.route("/api/export/csv", methods=["GET"])
def api_export_csv():
    """Download the live synced call logs CSV file."""
    csv_p = get_sync_csv_path()
    if os.path.exists(csv_p):
        return send_file(csv_p, as_attachment=True, download_name="omnidim_call_logs_live.csv", mimetype="text/csv")
    return jsonify({"success": False, "error": "No calls logged yet"}), 404


def print_qr_banner(host_ip, port):
    """Print connection URLs for Android phone pairing."""
    url = f"http://{host_ip}:{port}"
    print("\n" + "="*60)
    print("  OMNIDIMENSION ANDROID APP LIVE SERVER (v15.0)")
    print("="*60)
    print(f"  Open in Android Phone Browser / Add to Home Screen:")
    print(f"  URL: {url}")
    print(f"  Localhost: http://localhost:{port}")
    print("="*60 + "\n")


if __name__ == "__main__":
    port = 5000
    host_ip = get_local_ip()
    print_qr_banner(host_ip, port)
    app.run(host="0.0.0.0", port=port, debug=False)
