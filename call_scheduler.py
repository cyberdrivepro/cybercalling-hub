"""
================================================================================
  ⏰ CyberCalling 2.0 — Enterprise SQLite Call Scheduler & Daily Alarms Engine
================================================================================
  Features:
  • 📅 Natural Language & Multi-Format Time Parsing (10m, 1h, 8:00 PM, Tomorrow 9 AM)
  • 🗄️ Full SQLite Persistence (Survives server reboots & container lifecycles)
  • ⚡ High-Precision Background Daemon (Polls due calls with sub-5s accuracy)
  • 🔄 Auto-Redial & Per-Call Dynamic Spoken Message Injection on Trigger
  • 🗄️ Live Real-Time Telemetry to @cybercallingDB_bot
================================================================================
"""

import os
import re
import time
import uuid
import datetime
import threading
from typing import Dict, Any, List, Optional, Tuple

from backend.app.db.session import SessionLocal, Base, engine
from backend.app.models.models import ScheduledCall
from phone_normalizer import normalize_and_detect_country

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)


def parse_schedule_time(time_input: str) -> Optional[Dict[str, Any]]:
    """
    Parse a user's schedule time input into an exact execution timestamp.
    Supports:
      • Relative offsets: '5m', '10m', '15m', '30m', '1h', '2h', 'in 10 mins', 'after 30 minutes'
      • Time today: '8:00 PM', '20:30', '9:15 am', '14:00' (rolls to tomorrow if past)
      • Tomorrow time: 'tomorrow 9:00 AM', 'tomorrow 20:00'
      • ISO format: '2026-09-01 10:00'
    """
    if not time_input:
        return None

    raw = time_input.strip().lower()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # India Standard Time (UTC + 5:30) for human display
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now_ist = datetime.datetime.utcnow() + ist_offset

    target_dt_utc = None
    human_desc = ""

    # 1. Relative Minutes / Hours Pattern: '5m', '15m', '1h', '2h', 'in 10 min'
    rel_match = re.search(r'(?:in|after)?\s*(\d+)\s*(m|min|mins|minute|minutes|h|hr|hrs|hour|hours)\b', raw)
    if rel_match:
        val = int(rel_match.group(1))
        unit = rel_match.group(2)
        if unit.startswith('h'):
            delta = datetime.timedelta(hours=val)
            human_desc = f"In {val} hour{'s' if val > 1 else ''}"
        else:
            delta = datetime.timedelta(minutes=val)
            human_desc = f"In {val} minute{'s' if val > 1 else ''}"
        target_dt_utc = now_utc + delta
        target_ist = now_ist + delta
        human_desc += f" (at {target_ist.strftime('%I:%M %p IST')})"

    # 2. Tomorrow Pattern: 'tomorrow 09:00 am', 'tomorrow 8pm'
    elif "tomorrow" in raw:
        clean_time = raw.replace("tomorrow", "").strip()
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', clean_time)
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == 'pm' and hr < 12:
                hr += 12
            elif ampm == 'am' and hr == 12:
                hr = 0
            
            tomorrow_ist = (now_ist + datetime.timedelta(days=1)).replace(hour=hr, minute=mn, second=0, microsecond=0)
            target_dt_utc = tomorrow_ist - ist_offset
            target_dt_utc = target_dt_utc.replace(tzinfo=datetime.timezone.utc)
            human_desc = f"Tomorrow at {tomorrow_ist.strftime('%I:%M %p IST')}"

    # 3. Today Clock Time: '8:00 pm', '20:00', '9:30 am', '14:30'
    else:
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', raw)
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == 'pm' and hr < 12:
                hr += 12
            elif ampm == 'am' and hr == 12:
                hr = 0

            cand_ist = now_ist.replace(hour=hr, minute=mn, second=0, microsecond=0)
            # If the time is in the past for today, schedule for tomorrow
            if cand_ist <= now_ist:
                cand_ist += datetime.timedelta(days=1)
                human_desc = f"Tomorrow at {cand_ist.strftime('%I:%M %p IST')}"
            else:
                diff_sec = int((cand_ist - now_ist).total_seconds())
                diff_min = diff_sec // 60
                hrs_rem = diff_min // 60
                mins_rem = diff_min % 60
                rem_str = f"in {hrs_rem}h {mins_rem}m" if hrs_rem > 0 else f"in {mins_rem} mins"
                human_desc = f"Today at {cand_ist.strftime('%I:%M %p IST')} ({rem_str})"

            target_dt_utc = cand_ist - ist_offset
            target_dt_utc = target_dt_utc.replace(tzinfo=datetime.timezone.utc)

    if not target_dt_utc:
        return None

    unix_timestamp = target_dt_utc.timestamp()
    sec_left = max(0, int(unix_timestamp - time.time()))

    return {
        "due_at_utc": target_dt_utc,
        "due_timestamp_unix": unix_timestamp,
        "human_str": human_desc,
        "seconds_remaining": sec_left
    }


def create_scheduled_call(
    telegram_id: str,
    recipient: str,
    time_input: str,
    customer_name: str = "Valued Contact",
    custom_message: str = "",
    spoken_scenario: str = "CUSTOM",
    auto_redial: bool = True,
    is_recurring: bool = False
) -> Dict[str, Any]:
    """
    Create and persist a new scheduled call in SQLite with live audit logging.
    """
    norm = normalize_and_detect_country(recipient)
    if not norm["is_valid"]:
        return {"success": False, "error": "Invalid phone number format."}

    parsed_time = parse_schedule_time(time_input)
    if not parsed_time:
        return {"success": False, "error": f"Could not understand schedule time '{time_input}'. Try '10m', '30m', '8:00 PM', or 'Tomorrow 9 AM'."}

    task_id = f"sch_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        sch = ScheduledCall(
            task_id=task_id,
            telegram_id=str(telegram_id).strip(),
            recipient=norm["clean_number"],
            customer_name=customer_name or "Valued Contact",
            custom_message=custom_message.strip() if custom_message else "",
            spoken_scenario=spoken_scenario,
            due_at=parsed_time["due_at_utc"],
            due_timestamp_unix=parsed_time["due_timestamp_unix"],
            human_time_str=parsed_time["human_str"],
            status="PENDING",
            auto_redial=auto_redial,
            is_recurring=is_recurring
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)

        # Telemetry stream to DB Bot
        try:
            from notify import notify_db_call_dispatched
            from backend.app.services.user_manager import user_manager
            u_info = user_manager.get_or_create_user(telegram_id)
            # Send live scheduling event
            from cybercalling_db_bot import db_logger_bot
            sched_msg = (
                "⏰ *[CALL SCHEDULED IN DATABASE — LIVE LOG]*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *User:* `{u_info.get('first_name', 'User')}` (`{telegram_id}`)\n"
                f"• *Recipient:* `{norm['clean_number']}` ({norm['flag']} {norm['country_name']})\n"
                f"• *Customer:* `{customer_name}`\n"
                f"• *Execution Time:* `{parsed_time['human_str']}`\n"
                f"• *Spoken Message:* _{custom_message or 'Standard AI Voice Greeting'}_\n"
                f"• *Auto-Redial:* `Active 🔄`\n"
                f"• *Task ID:* `{task_id}`"
            )
            db_logger_bot.send_message(db_logger_bot.owner_id, sched_msg)
        except Exception:
            pass

        return {
            "success": True,
            "task_id": task_id,
            "recipient": norm["clean_number"],
            "country": norm["country_name"],
            "flag": norm["flag"],
            "customer_name": customer_name,
            "custom_message": custom_message,
            "human_time": parsed_time["human_str"],
            "seconds_remaining": parsed_time["seconds_remaining"]
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def list_user_scheduled_calls(telegram_id: Optional[str] = None, is_owner: bool = False) -> List[Dict[str, Any]]:
    """List all active pending scheduled calls with live countdowns."""
    db = SessionLocal()
    try:
        query = db.query(ScheduledCall).filter(ScheduledCall.status == "PENDING")
        if not is_owner and telegram_id:
            query = query.filter(ScheduledCall.telegram_id == str(telegram_id).strip())
        
        recs = query.order_by(ScheduledCall.due_timestamp_unix.asc()).limit(20).all()
        now_ts = time.time()
        results = []
        for r in recs:
            sec_left = max(0, int(r.due_timestamp_unix - now_ts))
            mins_left = sec_left // 60
            hrs_left = mins_left // 60
            rem_str = f"{hrs_left}h {mins_left % 60}m" if hrs_left > 0 else f"{mins_left}m {sec_left % 60}s"
            
            results.append({
                "task_id": r.task_id,
                "telegram_id": r.telegram_id,
                "recipient": r.recipient,
                "customer_name": r.customer_name,
                "custom_message": r.custom_message,
                "human_time": r.human_time_str,
                "seconds_left": sec_left,
                "countdown_str": rem_str,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""
            })
        return results
    finally:
        db.close()


def cancel_scheduled_call(task_id_or_number: str, telegram_id: Optional[str] = None, is_owner: bool = False) -> Dict[str, Any]:
    """Cancel a pending scheduled call."""
    db = SessionLocal()
    try:
        query = db.query(ScheduledCall).filter(ScheduledCall.status == "PENDING")
        if not is_owner and telegram_id:
            query = query.filter(ScheduledCall.telegram_id == str(telegram_id).strip())
        
        target = query.filter(
            (ScheduledCall.task_id == task_id_or_number) |
            (ScheduledCall.recipient.contains(task_id_or_number))
        ).first()

        if not target:
            return {"success": False, "error": f"No pending scheduled call found for `{task_id_or_number}`."}

        target.status = "CANCELLED"
        db.commit()
        return {
            "success": True,
            "task_id": target.task_id,
            "recipient": target.recipient,
            "customer_name": target.customer_name
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def start_scheduler_daemon(dispatcher_func):
    """
    High-precision background scheduler daemon (3-second resolution).
    Pulls due calls from SQLite and executes via Voice AI engine with atomic lock.
    """
    def scheduler_loop():
        while True:
            try:
                time.sleep(3)
                now_ts = time.time()
                db = SessionLocal()
                try:
                    due_calls = db.query(ScheduledCall).filter(
                        ScheduledCall.status == "PENDING",
                        ScheduledCall.due_timestamp_unix <= now_ts
                    ).all()

                    for call_task in due_calls:
                        # Atomic row update to prevent duplicate execution across replicas
                        updated = db.query(ScheduledCall).filter(
                            ScheduledCall.task_id == call_task.task_id,
                            ScheduledCall.status == "PENDING"
                        ).update({
                            "status": "COMPLETED",
                            "executed_at": datetime.datetime.now(datetime.timezone.utc)
                        })
                        db.commit()

                        if updated == 0:
                            # Already claimed and executed by another replica/worker thread
                            continue

                        task_payload = {
                            "task_id": call_task.task_id,
                            "telegram_id": call_task.telegram_id,
                            "recipient": call_task.recipient,
                            "name": call_task.customer_name,
                            "custom_msg": call_task.custom_message,
                            "auto_redial": call_task.auto_redial
                        }

                        # Execute live call once in dedicated thread
                        def execute_task(payload=task_payload):
                            try:
                                if dispatcher_func:
                                    dispatcher_func(payload)
                            except Exception as ex:
                                print(f"[Scheduler Dispatch Error on {payload.get('recipient')}]:", ex)

                        threading.Thread(target=execute_task, daemon=True).start()
                finally:
                    db.close()
            except Exception as e:
                time.sleep(5)

    threading.Thread(target=scheduler_loop, daemon=True, name="CallSchedulerDaemon").start()
