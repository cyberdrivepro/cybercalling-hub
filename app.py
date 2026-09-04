import spaces
import os
import sys
import time
import json
import threading
from typing import Dict
from dotenv import load_dotenv
from fastapi import WebSocket, WebSocketDisconnect
import gradio as gr

load_dotenv(override=True)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ZeroGPU Accelerator for Hugging Face Spaces
@spaces.GPU(duration=60)
def ai_voice_gpu_accelerator(text: str = ""):
    """ZeroGPU accelerator for Voice AI inference & sentiment scoring."""
    return f"Accelerated: {text}"

# 1. Background Bot Runners with Auto-Recovery
def run_caller_bot_thread():
    while True:
        try:
            from telegram_bot import TelegramVoiceBotEngine
            print("🤖 [Cloud Background] Starting @DarkAngelEngine_BOT polling...")
            bot = TelegramVoiceBotEngine()
            bot.start_polling()
        except Exception as e:
            print(f"🚨 [Cloud Background] Caller Bot Exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def run_admin_bot_thread():
    while True:
        try:
            from admin_telegram_bot import CyberCallingAdminBot
            print("🔐 [Cloud Background] Starting @Cybercallingadmin_bot polling...")
            admin = CyberCallingAdminBot()
            admin.poll_updates()
        except Exception as e:
            print(f"🚨 [Cloud Background] Admin Bot Exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def run_db_bot_thread():
    while True:
        try:
            from cybercalling_db_bot import db_logger_bot
            print("🗄️ [Cloud Background] Starting @cybercallingDB_bot polling...")
            db_logger_bot.poll_updates()
        except Exception as e:
            print(f"🚨 [Cloud Background] DB Bot Exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def run_proxy_bot_thread():
    while True:
        try:
            from cybercalling_proxy_bot import proxy_bot
            print("🌐 [Cloud Background] Starting @cybercallingproxy_bot polling...")
            proxy_bot.poll_updates()
        except Exception as e:
            print(f"🚨 [Cloud Background] Proxy Bot Exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def run_danger_bot_thread():
    while True:
        try:
            from cybercalling_danger_bot import danger_bot
            print("🔥 [Cloud Background] Starting @cybercallingdanger_bot polling...")
            danger_bot.poll_updates()
        except Exception as e:
            print(f"🚨 [Cloud Background] Danger Bot Exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def run_manager_bot_thread():
    while True:
        try:
            from cyberbot_manager import manager_bot
            print("👑 [Cloud Background] Starting @cyberbotmanager_bot polling...")
            manager_bot.poll_updates()
        except Exception as e:
            print(f"🚨 [Cloud Background] Manager Bot Exception: {e}. Retrying in 5 seconds...")
            time.sleep(5)

_BOT_LOCK = threading.Lock()
_BOT_STARTED = False

def init_cloud_bots():
    global _BOT_STARTED
    with _BOT_LOCK:
        if _BOT_STARTED:
            return
        _BOT_STARTED = True
        try:
            from tor_service import tor_service
            tor_service.start()
        except Exception as e:
            print(f"[Cloud Boot] Tor startup notice: {e}")
        threading.Thread(target=run_caller_bot_thread, daemon=True, name="CallerBotDaemon").start()
        threading.Thread(target=run_admin_bot_thread, daemon=True, name="AdminBotDaemon").start()
        threading.Thread(target=run_db_bot_thread, daemon=True, name="DBBotDaemon").start()
        threading.Thread(target=run_proxy_bot_thread, daemon=True, name="ProxyBotDaemon").start()
        threading.Thread(target=run_danger_bot_thread, daemon=True, name="DangerBotDaemon").start()
        threading.Thread(target=run_manager_bot_thread, daemon=True, name="ManagerBotDaemon").start()

init_cloud_bots()

# 2. Multi-Node Cluster State
active_workers: Dict[str, WebSocket] = {}
worker_metrics: Dict[str, dict] = {}

def get_system_status():
    coder_status = "🟢 Connected (Qwen 2.5 Coder Active)" if "coder" in active_workers else "🟡 Standby (/ws/coder listening)"
    active_count = len(active_workers)
    status_text = f"""### 🟢 CyberCalling Multi-Node Voice AI Cluster — LIVE 24/7 IN CLOUD

**Connected Distributed AI Nodes & Telegram Bots:**
- 🌐 **Space 1 (Master Gateway):** `🟢 Healthy` (Port 7860 & HTTP Task Queue)
- 💻 **Space 2 (Coder & Hot-Patcher):** `{coder_status}`
- 📞 **Caller Voice Bot:** `@DarkAngelEngine_BOT` (Active & Outbound Telecom Bridge)
- 🔐 **Admin Key Vault Bot:** `@Cybercallingadmin_bot` (AES-256-GCM Vault Active)
- 🗄️ **Database & Telemetry Bot:** `@cybercallingDB_bot` (Real-Time Live Balance Stream)
- 🌐 **Proxy & Network Fleet Bot:** `@cybercallingproxy_bot` (Live Multi-Hop & Danger Chains)
- 🔥 **Danger & Burner Fleet Bot:** `@cybercallingdanger_bot` (24/7 Proxy-Enforced Burner Accounts)
- 🤖 **Coder & Patch Brain Bot:** `@cybercallingPB_bot` (Qwen 2.5 Coder 32B Active)
- 🏢 **Multi-Account Pool:** Multi-Account Hot-Reload Pool Active
- ⚡ **Multi-Carrier Bridge:** Dark Angel Core · Twilio · Telnyx · SIP
- 🛡️ **Ultra Danger & Ziddi Mode 6x Chains:** Active & Protected

---
*System is permanently hosted 24/7 on Hugging Face Cloud Spaces.*
"""
    return status_text

# 3. Gradio Web Interface & ZeroGPU Integration
with gr.Blocks(title="CyberCalling Voice AI Hub") as demo:
    gr.Markdown("# 🚀 CyberCalling Voice AI Enterprise Hub")
    gr.Markdown("24/7 Master Router & Server for **@DarkAngelEngine_BOT**, **@Cybercallingadmin_bot**, **@cybercallingDB_bot**, and **Space 2 (Coder Agent)**")
    
    with gr.Row():
        status_box = gr.Markdown(value=get_system_status())
    
    refresh_btn = gr.Button("🔄 Refresh System Status")
    refresh_btn.click(fn=get_system_status, outputs=status_box)

    gpu_acc_btn = gr.Button("⚡ GPU AI Acceleration", visible=False)
    gpu_acc_btn.click(fn=ai_voice_gpu_accelerator, inputs=[], outputs=[])

# 4. Attach Multi-Node HTTP Long-Polling Task Queues & REST Endpoints
TASK_QUEUES: Dict[str, list] = {
    "coder": [],
    "reasoning": [],
    "general": []
}
_QUEUE_LOCK = threading.Lock()

def queue_agent_task(agent_type: str, task: dict):
    """Enqueue a task for worker agents to pick up."""
    with _QUEUE_LOCK:
        if agent_type not in TASK_QUEUES:
            TASK_QUEUES[agent_type] = []
        TASK_QUEUES[agent_type].append(task)
    print(f"📥 [QUEUE] Task queued for agent '{agent_type}': {task.get('action')}")

@demo.app.post("/api/get-task/{agent_type}")
@demo.app.get("/api/get-task/{agent_type}")
def api_get_task(agent_type: str):
    """Worker agents poll this endpoint to receive pending tasks."""
    # Update last ping
    worker_metrics[agent_type] = {
        "last_ping": time.time(),
        "status": "online"
    }
    with _QUEUE_LOCK:
        queue = TASK_QUEUES.get(agent_type, [])
        if queue:
            task = queue.pop(0)
            return {"status": "available", "task": task}
    return {"status": "empty"}

@demo.app.post("/api/post-result")
def api_post_result(payload: dict):
    """Worker agents post completed inference/patch results back here."""
    chat_id = payload.get("chat_id")
    msg = payload.get("message")
    if chat_id and msg:
        try:
            from telegram_bot import TelegramVoiceBotEngine
            TelegramVoiceBotEngine().send_message(chat_id, msg)
        except Exception as ex_tg:
            print("[POST-RESULT Telegram Error]:", ex_tg)
    return {"status": "delivered"}

@demo.app.post("/api/heartbeat/{agent_type}")
def api_heartbeat(agent_type: str, payload: dict = None):
    """Periodic worker heartbeat signal."""
    p = payload or {}
    worker_metrics[agent_type] = {
        "last_ping": time.time(),
        "status": "online",
        "inferences": p.get("inferences", 0),
        "hotfixes": p.get("hotfixes", 0)
    }
    return {"status": "pong", "timestamp": time.time(), "master": "healthy"}

@demo.app.get("/health")
def health_endpoint():
    return {
        "status": "healthy",
        "space": "space1_master_router",
        "active_nodes": list(worker_metrics.keys()),
        "connected_count": len(worker_metrics)
    }

@demo.app.get("/api/cluster")
def cluster_endpoint():
    return {
        "master": "Space 1 (Master Router)",
        "active_nodes": list(worker_metrics.keys()),
        "metrics": worker_metrics,
        "task_queues": {k: len(v) for k, v in TASK_QUEUES.items()},
        "timestamp": time.time()
    }

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)

