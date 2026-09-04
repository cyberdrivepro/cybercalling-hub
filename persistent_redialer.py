"""
================================================================================
  🔄 OmniDimension Autonomous Persistent Redial Engine ("Ziddi Caller")
================================================================================
  Complete, robust autonomous redial worker:
  - Clean lifecycle: clears stop signals, monitors live carrier ringing state.
  - Waits quietly while phone is ringing.
  - On 'no-answer' / 'busy': immediately sends Attempt notification & redials.
  - On 'completed': immediately sends Full Summary Report + MP3 Recording & stops.
  - On /stopretry or Stop button: halts immediately across all replicas.
================================================================================
"""

import os
import time
import threading
import datetime

ACTIVE_REDIAL_TASKS = {}
_tasks_lock = threading.Lock()


def mask_phone_number(phone: str) -> str:
    """Half-mask phone numbers for privacy (e.g. +91 8287***432)."""
    if not phone:
        return ""
    p = str(phone).strip()
    import re
    cleaned = re.sub(r'[\s\-()]', '', p)
    if len(cleaned) >= 12:
        return f"{cleaned[:7]}***{cleaned[-3:]}"
    elif len(cleaned) >= 10:
        return f"{cleaned[:4]}***{cleaned[-3:]}"
    elif len(cleaned) > 5:
        return f"{cleaned[:2]}***{cleaned[-2:]}"
    return "***"


def snapshot_existing_cids(clients_pool):
    """Snapshot all currently existing call log IDs across all accounts to avoid matching stale logs."""
    seen = set()
    for entry in clients_pool:
        try:
            cl = entry.get("client")
            if not cl:
                continue
            r = cl.call.get_call_logs(page=1, page_size=20)
            logs = r.get("json", {}).get("call_log_data", []) if isinstance(r, dict) else []
            for item in logs:
                cid = item.get("id") or item.get("call_id")
                if cid:
                    seen.add(str(cid))
        except Exception:
            pass
    return seen


def register_redial_task(
    task_id,
    recipient,
    name,
    custom_msg,
    client,
    agent_id,
    uname,
    chat_id,
    notifier_func,
    max_retries=6,
    retry_delay_sec=6,
    clients_pool=None,
    audio_sender_func=None
):
    """Register and launch an autonomous persistent redial thread for a phone number."""
    clean_target = str(recipient).strip()

    # Cancel existing in-memory task without triggering DB stop signal
    with _tasks_lock:
        if clean_target in ACTIVE_REDIAL_TASKS:
            ACTIVE_REDIAL_TASKS[clean_target]["status"] = "stopped"
            del ACTIVE_REDIAL_TASKS[clean_target]

    # Clear shared DB stop signal so this fresh session can run seamlessly
    try:
        from telegram_dedup import clear_redial_stop
        clear_redial_stop(clean_target)
    except Exception:
        pass

    pool = clients_pool or [{"client": client, "user": uname}]
    # Snapshot historical calls so past calls are NEVER matched
    seen_cids = snapshot_existing_cids(pool)

    task = {
        "task_id": str(task_id),
        "recipient": clean_target,
        "name": name or "Valued Customer",
        "custom_msg": custom_msg or "",
        "client": client,
        "clients_pool": pool,
        "agent_id": agent_id,
        "uname": uname,
        "chat_id": chat_id,
        "notifier_func": notifier_func,
        "audio_sender_func": audio_sender_func,
        "max_retries": max_retries,
        "retry_delay_sec": retry_delay_sec,
        "attempts": 1,
        "status": "active",
        "registered_at": time.time(),
        "seen_cids": seen_cids,
        "last_call_time": time.time()
    }

    with _tasks_lock:
        ACTIVE_REDIAL_TASKS[clean_target] = task

    def _redial_worker():
        from telegram_dedup import is_redial_stopped
        processed_cids = set(seen_cids)

        # Realistic initial wait: wait 12s for carrier trunk to establish and begin ringing
        time.sleep(12)

        while True:
            # 1. Check if user clicked Stop or sent stop signal
            if is_redial_stopped(clean_target):
                print(f"[Ziddi Redialer] Stop signal detected for {clean_target}. Halting.")
                with _tasks_lock:
                    ACTIVE_REDIAL_TASKS.pop(clean_target, None)
                break

            with _tasks_lock:
                current_task = ACTIVE_REDIAL_TASKS.get(clean_target)
                if not current_task or current_task.get("status") != "active":
                    print(f"[Ziddi Redialer] Task for {clean_target} inactive. Halting.")
                    break

            # 2. Check call logs across all pool accounts strictly for NEW calls
            is_answered = False
            is_missed = False
            last_status = "ringing"
            last_duration = "0:0"
            matched_cid = None
            matched_item = None
            found_new_call = False

            pool_list = current_task.get("clients_pool", pool)

            for c_entry in pool_list:
                try:
                    c_cl = c_entry.get("client")
                    if not c_cl:
                        continue
                    logs_res = c_cl.call.get_call_logs(page=1, page_size=10)
                    call_logs = logs_res.get("json", {}).get("call_log_data", []) if isinstance(logs_res, dict) else []
                    for item in call_logs:
                        cid = str(item.get("id") or item.get("call_id") or "")
                        # Strictly ignore all historical calls from before this session!
                        if not cid or cid in processed_cids:
                            continue

                        to_num = str(item.get("to_number") or item.get("phone_number") or "")
                        if clean_target in to_num or to_num in clean_target:
                            found_new_call = True
                            st = str(item.get("status") or item.get("call_status") or "").lower().strip()
                            dur_str = str(item.get("duration") or item.get("call_duration") or "0").strip()
                            last_status = st or "ringing"
                            matched_cid = cid
                            matched_item = item

                            # Check if completed / answered with actual talk time or recording URL
                            rec_cand = item.get("internal_recording_url") or item.get("recording_url")
                            is_zero_talk = dur_str in ["0", "-", "0:0", "0.00:0.00", ""]
                            if (not is_zero_talk) or (rec_cand and rec_cand != False):
                                is_answered = True
                                last_duration = dur_str if not is_zero_talk else "1.00:10.00"
                                break
                            elif "no-answer" in st or "busy" in st or "fail" in st or "cancel" in st:
                                is_missed = True
                                break
                            elif st in ["in-progress", "ringing", "queued", "pending", ""]:
                                # Phone is still ringing on the telecom carrier — keep monitoring
                                pass
                    if is_answered or is_missed:
                        break
                except Exception as e_poll:
                    print(f"[Ziddi Redialer] Polling error for {clean_target}: {e_poll}")

            # 3. IF ANSWERED: Send Completed Report + MP3 Voice Note & Finish!
            if is_answered:
                if matched_cid:
                    processed_cids.add(matched_cid)
                with _tasks_lock:
                    ACTIVE_REDIAL_TASKS.pop(clean_target, None)

                dur_sec = 10.0
                try:
                    from telegram_bot import parse_duration_seconds
                    dur_sec = parse_duration_seconds(str(last_duration))
                except Exception:
                    dur_sec = 10.0
                cost_usd = dur_sec * (0.120 / 60.0)

                # Stream to DB
                try:
                    from notify import notify_db_call_completed
                    notify_db_call_completed({
                        "user_name": name,
                        "telegram_id": str(chat_id),
                        "recipient": clean_target,
                        "duration": str(last_duration),
                        "status": "completed",
                        "cost_credits": 1.0,
                        "cost_usd": cost_usd,
                        "score": 90,
                        "sentiment": "Connected & Answered"
                    })
                except Exception:
                    pass

                # Telegram Completed Card
                success_msg = (
                    f"🔔 *[LIVE CALL ALERT — CALL COMPLETED]* 🟢\n\n"
                    f"🟢 *Recipient:* `{clean_target}`\n"
                    f"• *Customer:* `{name}`\n"
                    f"• *Answered On:* `Attempt #{current_task['attempts']}` 🟢\n"
                    f"• *Talk Duration:* `{last_duration}` ({dur_sec:.1f}s)\n"
                    f"• *Status:* `completed 🟢`\n"
                    f"• *Call Cost:* `${cost_usd:.3f}` (@ $0.120/min)\n"
                    f"• *Account:* `{uname}`\n"
                    f"• *Recording:* `▶️ Audio Voice Note Dispatched below!`"
                )
                if notifier_func:
                    try:
                        from telegram_bot import create_post_call_whatsapp_followup
                        wa_data = create_post_call_whatsapp_followup(clean_target, customer_name=name, call_summary=f"Call completed ({last_duration} duration).")
                        kb = {"inline_keyboard": [
                            [{"text": "⏺️ Get Call Recording / Audio 🎙️", "callback_data": f"get_rec_{clean_target}"}],
                            [{"text": "💬 1-Click WhatsApp Follow-up", "url": wa_data["wa_link"]}]
                        ]}
                        notifier_func(chat_id, success_msg, reply_markup=kb)
                    except Exception:
                        try:
                            notifier_func(chat_id, success_msg)
                        except Exception:
                            pass

                # Push Playable MP3 Audio Recording
                rec_url = matched_item.get("internal_recording_url") or matched_item.get("recording_url") if matched_item else None
                audio_sender = current_task.get("audio_sender_func")
                if not rec_url or rec_url == False:
                    for _ in range(6):
                        time.sleep(2)
                        try:
                            r_fresh = c_cl.call.get_call_logs(page=1, page_size=5)
                            l_fresh = r_fresh.get("json", {}).get("call_log_data", []) if isinstance(r_fresh, dict) else []
                            for f_it in l_fresh:
                                if str(f_it.get("id") or "") == str(matched_cid):
                                    f_rec = f_it.get("internal_recording_url") or f_it.get("recording_url")
                                    if f_rec and f_rec != False:
                                        rec_url = f_rec
                                        break
                        except Exception:
                            pass
                        if rec_url and rec_url != False:
                            break

                if rec_url and rec_url != False and audio_sender:
                    try:
                        if not str(rec_url).startswith("http"):
                            rec_url = f"https://omnidim.io{rec_url}"
                        cap = (
                            f"🎧 *Call Audio Recording:*\n\n"
                            f"• *Recipient:* `{mask_phone_number(clean_target)}`\n"
                            f"• *Talk Duration:* `{last_duration}`\n"
                            f"• *Cost:* `${cost_usd:.3f}`\n\n"
                            f"▶️ _Tap play button above to listen!_"
                        )
                        # Instant cloud URL audio push to Telegram
                        res_aud = audio_sender(chat_id, rec_url, caption=cap, title=f"Call Recording - {mask_phone_number(clean_target)}")
                        if not res_aud:
                            from proxy_manager import proxy_manager
                            s_aud = proxy_manager.get_session()
                            audio_resp = s_aud.get(rec_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                            if audio_resp.status_code == 200 and len(audio_resp.content) > 500:
                                audio_sender(chat_id, audio_resp.content, caption=cap, title=f"Call Recording - {mask_phone_number(clean_target)}")
                    except Exception as ex_aud:
                        print("[Ziddi Redialer Audio Push Error]:", ex_aud)
                break

            # 4. IF STILL RINGING / IN-PROGRESS / WAITING FOR CARRIER: Wait quietly (do NOT redial yet!)
            if not is_missed:
                # Check if attempt has exceeded carrier timeout (120 seconds to allow active calls)
                time_since_last = time.time() - current_task.get("last_call_time", time.time())
                if time_since_last > 120:
                    print(f"[Ziddi Redialer] Carrier ringing timeout (120s) reached for {clean_target}. Marking as missed.")
                    is_missed = True
                    last_status = "no-answer (timeout)"
                else:
                    time.sleep(5)
                    continue

            # 5. IF MISSED / NO-ANSWER: Mark CID as processed
            if matched_cid:
                processed_cids.add(matched_cid)

            # Check if max retries reached
            current_attempts = current_task["attempts"]
            if current_attempts >= max_retries:
                with _tasks_lock:
                    ACTIVE_REDIAL_TASKS.pop(clean_target, None)
                if notifier_func:
                    try:
                        notifier_func(
                            chat_id,
                            f"⚠️ *[Max Retries Reached]* Dialed `{mask_phone_number(clean_target)}` {current_attempts} times (Status: `{last_status}`). Redial loop finished."
                        )
                    except Exception:
                        pass
                break

            # Redial Cooldown: Give receiver and telecom carrier a 6-second breathing window
            time.sleep(6)

            # Advance attempt count
            with _tasks_lock:
                current_task["attempts"] += 1
                current_task["last_call_time"] = time.time()
                attempt_num = current_task["attempts"]

            # Send Attempt Notification to Telegram
            masked_target = mask_phone_number(clean_target)
            retry_alert = (
                f"🔄 *[PERSISTENT REDIAL — ATTEMPT #{attempt_num} of {max_retries}]*\n\n"
                f"• *Recipient:* `{masked_target}` (Previous call was `{last_status}`)\n"
                f"• *Customer:* `{name}`\n"
                f"• *Action:* Ringing again right now...\n"
                f"• *Stop Command:* `/stopretry {masked_target}` or reply `stop`"
            )
            stop_kb = {"inline_keyboard": [[{"text": "🛑 Stop Auto-Redial / Loop", "callback_data": f"stop_redial_{clean_target}"}]]}
            if notifier_func:
                try:
                    notifier_func(chat_id, retry_alert, reply_markup=stop_kb)
                except Exception:
                    try:
                        notifier_func(chat_id, retry_alert)
                    except Exception:
                        pass

            # Dispatch next call attempt with dynamic prompt update
            acc_idx = (current_task["attempts"] - 1) % len(pool_list)
            rotated_pool = pool_list[acc_idx:] + pool_list[:acc_idx]
            for c_entry in rotated_pool:
                try:
                    c_cl = c_entry.get("client")
                    if not c_cl:
                        continue
                    
                    target_aid = None
                    for b in c_entry.get("bots", []):
                        b_low = b.get("name", "").strip().lower()
                        if "dark angel" in b_low or "cyber" in b_low:
                            target_aid = b.get("id")
                            break
                    if not target_aid and c_entry.get("bots"):
                        target_aid = c_entry["bots"][0].get("id")
                    if not target_aid:
                        target_aid = agent_id

                    if custom_msg and custom_msg.strip() != "Standard AI Voice Greeting":
                        welcome_text = custom_msg.strip()
                    else:
                        welcome_text = f"Hello {name}! Thank you for answering. How can I assist you today?"

                    task_prompt = (
                        f"# Role & Purpose\n"
                        f"You are calling {name}.\n"
                        f"PRIMARY TASK: \"{welcome_text}\"\n"
                        f"Greet {name} and deliver the message politely."
                    )

                    try:
                        c_cl.agent.update(int(target_aid), {
                            "name": "Dark Angel Voice AI",
                            "welcome_message": welcome_text,
                            "context": task_prompt,
                            "is_welcome_message_dynamic": False
                        })
                    except Exception:
                        pass

                    call_ctx = {
                        "customer_name": name,
                        "welcome_message": welcome_text,
                        "custom_message": welcome_text,
                        "message_to_deliver": welcome_text,
                        "instruction": f"Deliver this message to {name}: {welcome_text}",
                        "task": welcome_text
                    }

                    c_cl.call.dispatch_call(agent_id=int(target_aid), to_number=clean_target, call_context=call_ctx)
                    break
                except Exception as ex_disp:
                    print(f"[Ziddi Redialer] Dispatch attempt #{attempt_num} error for {clean_target}: {ex_disp}")

            # Carrier ringing cooldown before checking next status
            time.sleep(10)

    threading.Thread(target=_redial_worker, daemon=True).start()
    return task


def stop_redial_task(recipient=None):
    """Stop active redialing for a specific number or all active tasks."""
    from telegram_dedup import signal_stop_redial, signal_stop_all_redials
    stopped = []
    with _tasks_lock:
        if recipient:
            clean = str(recipient).strip()
            for k in list(ACTIVE_REDIAL_TASKS.keys()):
                if clean in k or k in clean:
                    ACTIVE_REDIAL_TASKS[k]["status"] = "stopped"
                    del ACTIVE_REDIAL_TASKS[k]
                    stopped.append(k)
            signal_stop_redial(clean)
        else:
            for k in list(ACTIVE_REDIAL_TASKS.keys()):
                ACTIVE_REDIAL_TASKS[k]["status"] = "stopped"
                stopped.append(k)
            ACTIVE_REDIAL_TASKS.clear()
            signal_stop_all_redials()
    return stopped


def get_active_redial_tasks():
    """Return summary of all active redial tasks."""
    with _tasks_lock:
        return list(ACTIVE_REDIAL_TASKS.values())
