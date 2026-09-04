"""
================================================================================
  👥 CyberCalling 2.0 — Telegram User & Multi-Tenant Credit Manager
================================================================================
  Handles user onboarding, credit limits, access control (RBAC), and masking
  internal infrastructure details from normal Telegram users.
================================================================================
"""

import os
import json
import datetime
import requests
from typing import Dict, Any, Tuple, List, Optional
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal, Base, engine
from backend.app.models.models import TelegramUser, CreditTransaction, UserCallLog
from backend.app.core.audit import log_security_event

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

def _auto_migrate_db():
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE telegram_users ADD COLUMN assistant_settings JSON;"))
            conn.commit()
        except Exception:
            pass

_auto_migrate_db()

# Master Owner Telegram IDs (Dark Angel Super Admin)
OWNER_IDS = ["8405632493"]
env_owner = os.getenv("TELEGRAM_OWNER_ID", "").strip()
if env_owner and env_owner not in OWNER_IDS:
    OWNER_IDS.append(env_owner)

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
USERS_VAULT_FILE = os.path.join(_ROOT_DIR, "data", "users_vault.json")

class UserManager:
    def __init__(self):
        self.default_signup_credits = float(os.getenv("DEFAULT_USER_CREDITS", "5.0"))
        self.default_daily_limit = int(os.getenv("DEFAULT_DAILY_LIMIT", "10"))
        self.cost_per_call = float(os.getenv("COST_PER_CALL_CREDITS", "1.0"))
        self._tos_cache = set()
        self._load_tos_cache()
        self._restore_from_vault()
        self._sync_vault()

    def _restore_from_vault(self):
        """Restores users from persistent JSON vault into SQLite if missing."""
        if not os.path.exists(USERS_VAULT_FILE):
            return
        db: Session = SessionLocal()
        try:
            with open(USERS_VAULT_FILE, "r", encoding="utf-8") as f:
                vault_data = json.load(f)
            
            existing_ids = {r[0] for r in db.query(TelegramUser.telegram_id).all()}
            restored = 0
            for tid, u_data in vault_data.items():
                if tid not in existing_ids:
                    is_owner = tid in OWNER_IDS
                    new_u = TelegramUser(
                        telegram_id=str(tid),
                        username=u_data.get("username"),
                        first_name=u_data.get("first_name", "User"),
                        role=u_data.get("role", "owner" if is_owner else "user"),
                        plan_tier=u_data.get("plan_tier", "Enterprise" if is_owner else "Free"),
                        language=u_data.get("language", "en"),
                        credit_balance=float(u_data.get("credit_balance", 999999.0 if is_owner else self.default_signup_credits)),
                        daily_limit=int(u_data.get("daily_limit", 999999 if is_owner else self.default_daily_limit)),
                        hourly_limit=int(u_data.get("hourly_limit", 999999 if is_owner else 5)),
                        max_bulk_batch_size=int(u_data.get("max_bulk_batch_size", 500 if is_owner else 50)),
                        can_call=bool(u_data.get("can_call", True)),
                        can_bulk=bool(u_data.get("can_bulk", True)),
                        can_webcall=bool(u_data.get("can_webcall", True)),
                        can_callback=bool(u_data.get("can_callback", True)),
                        is_banned=bool(u_data.get("is_banned", False)),
                        ban_reason=u_data.get("ban_reason"),
                        is_suspended=bool(u_data.get("is_suspended", False)),
                        calls_today=int(u_data.get("calls_today", 0)),
                        calls_this_hour=int(u_data.get("calls_this_hour", 0)),
                        total_calls=int(u_data.get("total_calls", 0)),
                        assistant_settings=u_data.get("assistant_settings"),
                        status=u_data.get("status", "ACTIVE"),
                        admin_notes=u_data.get("admin_notes")
                    )
                    db.add(new_u)
                    restored += 1
            if restored > 0:
                db.commit()
                print(f"[UserManager] Restored {restored} users from permanent vault into SQLite.")
        except Exception as e_res:
            print(f"[UserManager Vault Restore Note]: {e_res}")
        finally:
            db.close()

    def _sync_vault(self):
        """Dumps all SQLite users into data/users_vault.json to guarantee 100% persistence across reboots."""
        db: Session = SessionLocal()
        try:
            users = db.query(TelegramUser).all()
            vault_dict = {}
            for u in users:
                vault_dict[u.telegram_id] = {
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "first_name": u.first_name,
                    "role": u.role,
                    "plan_tier": u.plan_tier,
                    "language": u.language,
                    "credit_balance": u.credit_balance,
                    "daily_limit": u.daily_limit,
                    "hourly_limit": u.hourly_limit,
                    "max_bulk_batch_size": u.max_bulk_batch_size,
                    "can_call": u.can_call,
                    "can_bulk": u.can_bulk,
                    "can_webcall": u.can_webcall,
                    "can_callback": u.can_callback,
                    "is_banned": u.is_banned,
                    "ban_reason": u.ban_reason,
                    "is_suspended": u.is_suspended,
                    "calls_today": u.calls_today,
                    "calls_this_hour": u.calls_this_hour,
                    "total_calls": u.total_calls,
                    "assistant_settings": getattr(u, "assistant_settings", None),
                    "status": u.status,
                    "admin_notes": u.admin_notes
                }
            os.makedirs(os.path.dirname(USERS_VAULT_FILE), exist_ok=True)
            with open(USERS_VAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(vault_dict, f, indent=2)
        except Exception as e_sync:
            print(f"[UserManager Vault Sync Note]: {e_sync}")
        finally:
            db.close()

    def _load_tos_cache(self):
        """Seed accepted ToS cache from SQLite on initialization."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import ToSAcceptance
            recs = db.query(ToSAcceptance.telegram_id).all()
            for r in recs:
                if r[0]:
                    self._tos_cache.add(str(r[0]).strip())
        except Exception:
            pass
        finally:
            db.close()

    def get_or_create_user(self, telegram_id: Any, username: Optional[str] = None, first_name: Optional[str] = None, via_command: Optional[str] = None) -> Dict[str, Any]:
        """Fetch, register, or update a user with live drift-detection and real-time admin push alerts."""
        tg_id = str(telegram_id).strip()
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            is_new = False
            
            if not user:
                is_new = True
                is_owner = tg_id in OWNER_IDS
                role = "owner" if is_owner else "user"
                credits = 999999.0 if is_owner else self.default_signup_credits
                daily_lim = 999999 if is_owner else self.default_daily_limit
                hourly_lim = 999999 if is_owner else 5
                
                user = TelegramUser(
                    telegram_id=tg_id,
                    username=username,
                    first_name=first_name,
                    role=role,
                    plan_tier="Enterprise" if is_owner else "Free",
                    language="en",
                    credit_balance=credits,
                    daily_limit=daily_lim,
                    hourly_limit=hourly_lim,
                    max_bulk_batch_size=500 if is_owner else 50,
                    can_call=True,
                    can_bulk=True,
                    can_webcall=True,
                    can_callback=True,
                    is_banned=False,
                    is_suspended=False,
                    calls_today=0,
                    calls_this_hour=0,
                    total_calls=0,
                    status="ACTIVE",
                    admin_notes=None
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Log Signup Bonus
                if not is_owner and self.default_signup_credits > 0:
                    tx = CreditTransaction(
                        telegram_id=tg_id,
                        amount=self.default_signup_credits,
                        transaction_type="SIGNUP_BONUS",
                        notes="Welcome Trial Credits",
                        performed_by="system"
                    )
                    db.add(tx)
                    db.commit()
                    
                log_security_event("USER_REGISTERED", actor=f"tg_{tg_id}", status="SUCCESS", details={"username": username, "role": role, "via": via_command})
                
                # Dispatch real-time proactive Telegram notification to Admin
                if not is_owner:
                    self._dispatch_new_user_alert(tg_id, username, first_name, via_command)
            else:
                # Update username drift, name & active timestamp
                user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
                if username and user.username != username:
                    user.username = username
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                # Ensure owner privileges if in OWNER_IDS
                if tg_id in OWNER_IDS and user.role != "owner":
                    user.role = "owner"
                    user.credit_balance = 999999.0
                    user.daily_limit = 999999
                    user.hourly_limit = 999999
                db.commit()
                db.refresh(user)
                
            self._sync_vault()
            return {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "role": user.role,
                "plan_tier": user.plan_tier,
                "language": user.language,
                "credit_balance": user.credit_balance,
                "daily_limit": user.daily_limit,
                "hourly_limit": user.hourly_limit,
                "max_bulk_batch_size": user.max_bulk_batch_size,
                "can_call": user.can_call,
                "can_bulk": user.can_bulk,
                "can_webcall": user.can_webcall,
                "can_callback": user.can_callback,
                "is_banned": user.is_banned,
                "ban_reason": user.ban_reason,
                "is_suspended": user.is_suspended,
                "calls_today": user.calls_today,
                "calls_this_hour": user.calls_this_hour,
                "total_calls": user.total_calls,
                "assistant_settings": getattr(user, "assistant_settings", None),
                "status": user.status,
                "admin_notes": user.admin_notes,
                "is_owner": user.role == "owner",
                "is_new": is_new
            }
        finally:
            db.close()

    def _dispatch_new_user_alert(self, tg_id: str, username: Optional[str], first_name: Optional[str], via_command: Optional[str]):
        """Proactively notify master Admin on Telegram when a new user joins."""
        try:
            admin_token = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "8925368015:AAHYm1fHDRNPYhPIqdraVFMBrP5SAHico0k")
            uname_str = f"@{username}" if username else "No username"
            cmd_str = via_command or "/start"
            text = (
                "🆕 *[New User Joined Main Voice Bot!]*\n\n"
                f"• *User:* `{first_name or 'User'}` ({uname_str})\n"
                f"• *Telegram ID:* `{tg_id}`\n"
                f"• *Triggered Via:* `{cmd_str}`\n"
                f"• *Trial Balance:* `5.0 Credits (10 calls/day cap)`\n"
                f"• *Status:* `ACTIVE 🟢`\n\n"
                "👇 *1-Tap Admin Quick Actions:*"
            )
            buttons = [
                [
                    {"text": "🎁 Grant +10 Credits", "callback_data": f"do_topup_{tg_id}_10"},
                    {"text": "🚫 Instant Ban", "callback_data": f"act_ban_user_{tg_id}"}
                ],
                [
                    {"text": "👤 Inspect User Card", "callback_data": f"view_user_{tg_id}"}
                ]
            ]
            for admin_chat_id in OWNER_IDS:
                requests.post(
                    f"https://api.telegram.org/bot{admin_token}/sendMessage",
                    json={"chat_id": int(admin_chat_id), "text": text, "parse_mode": "Markdown", "reply_markup": {"inline_keyboard": buttons}},
                    timeout=5
                )
        except Exception as ex:
            print("Failed to dispatch new user alert:", ex)

    def check_call_permission(self, telegram_id: Any, permission_key: str = "can_call", cost: float = 1.0) -> Tuple[bool, str, Dict[str, Any]]:
        """Centralized Permission Enforcement Gate for all outbound telephony actions."""
        user_info = self.get_or_create_user(telegram_id)
        
        # 1. Owner always permitted
        if user_info["is_owner"]:
            return True, "Owner Access Granted (Unlimited)", user_info
            
        # 2. Check Banned Status
        if user_info.get("is_banned"):
            reason = user_info.get("ban_reason") or "Violation of terms."
            return False, f"🚫 *Access Denied:* Your account has been permanently blocked by Administrator.\n• *Reason:* _{reason}_", user_info
            
        # 3. Check Suspended Status
        if user_info.get("is_suspended") or user_info["status"] == "SUSPENDED":
            return False, "⏸️ *Account Temporarily Suspended:* Outbound calling is currently restricted. Please contact Admin at `@Cybercallingadmin_bot`.", user_info
            
        # 4. Check Feature Permission Flag
        if not user_info.get(permission_key, True):
            feature_name = permission_key.replace("can_", "").title()
            return False, f"🚫 *Feature Restricted:* You do not have permission to use the *{feature_name}* feature. Request access from Admin.", user_info
            
        # 5. Check Hourly Rate Cap
        if user_info.get("calls_this_hour", 0) >= user_info.get("hourly_limit", 5):
            return False, f"⏳ *Hourly Rate Limit Reached ({user_info['calls_this_hour']}/{user_info['hourly_limit']} calls)*. Please wait until next hour window.", user_info

        # 6. Check Daily Limit
        if user_info["calls_today"] >= user_info["daily_limit"]:
            return False, f"⚠️ *Daily call limit reached ({user_info['calls_today']}/{user_info['daily_limit']})*. Limit resets daily at midnight.", user_info
            
        # 7. Check Credit Balance
        required = cost or self.cost_per_call
        if user_info["credit_balance"] < required:
            return False, f"💳 *Insufficient Voice Credits!* Current balance: `{user_info['credit_balance']:.1f} Credits` (Required: `{required:.1f} Credits`).\n\n👉 Use `/topup` or message Admin to recharge.", user_info
            
        return True, "Authorized", user_info

    def admin_list_users(self, page: int = 1, page_size: int = 50, limit: int = 50) -> List[Dict[str, Any]]:
        """List registered users with roles, balances, active status, and call counts."""
        effective_limit = page_size if page_size != 50 else limit
        offset = max(0, (page - 1) * effective_limit)
        db: Session = SessionLocal()
        try:
            users = db.query(TelegramUser).order_by(TelegramUser.last_active_at.desc(), TelegramUser.created_at.desc()).offset(offset).limit(effective_limit).all()
            result = []
            for u in users:
                status_str = "BANNED 🚫" if u.is_banned else ("SUSPENDED ⏸️" if u.is_suspended else "ACTIVE 🟢")
                result.append({
                    "telegram_id": u.telegram_id,
                    "username": u.username or "",
                    "first_name": u.first_name or "User",
                    "role": u.role,
                    "plan_tier": u.plan_tier or "Free",
                    "credit_balance": u.credit_balance,
                    "daily_limit": u.daily_limit,
                    "hourly_limit": u.hourly_limit,
                    "calls_today": u.calls_today,
                    "total_calls": u.total_calls,
                    "status": status_str,
                    "is_banned": u.is_banned,
                    "is_suspended": u.is_suspended,
                    "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else "Recent",
                    "joined": u.created_at.strftime("%Y-%m-%d") if u.created_at else "Recent",
                    "last_active": u.last_active_at.strftime("%Y-%m-%d %H:%M") if u.last_active_at else "Recent"
                })
            return result
        finally:
            db.close()

    def admin_get_user_card(self, target_id_or_username: str) -> Optional[Dict[str, Any]]:
        """Lookup a user by numeric ID or by @username."""
        query_str = str(target_id_or_username).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == query_str) | (TelegramUser.username == query_str)
            ).first()
            if not user:
                return None
            return {
                "telegram_id": user.telegram_id,
                "username": user.username or "N/A",
                "first_name": user.first_name or "User",
                "role": user.role,
                "plan_tier": user.plan_tier or "Free",
                "credit_balance": user.credit_balance,
                "daily_limit": user.daily_limit,
                "hourly_limit": user.hourly_limit,
                "max_bulk_batch_size": user.max_bulk_batch_size,
                "can_call": user.can_call,
                "can_bulk": user.can_bulk,
                "can_webcall": user.can_webcall,
                "can_callback": user.can_callback,
                "is_banned": user.is_banned,
                "ban_reason": user.ban_reason,
                "is_suspended": user.is_suspended,
                "calls_today": user.calls_today,
                "calls_this_hour": user.calls_this_hour,
                "total_calls": user.total_calls,
                "status": "BANNED 🚫" if user.is_banned else ("SUSPENDED ⏸️" if user.is_suspended else "ACTIVE 🟢"),
                "admin_notes": user.admin_notes or "No notes",
                "joined": user.created_at.strftime("%Y-%m-%d") if user.created_at else "Recent",
                "last_active": user.last_active_at.strftime("%Y-%m-%d %H:%M") if user.last_active_at else "Recent"
            }
        finally:
            db.close()

    def admin_set_balance(self, target_id: str, new_balance: float, admin_id: Any = "owner") -> Dict[str, Any]:
        """Admin directly sets user balance to an exact amount."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            old_bal = user.credit_balance
            user.credit_balance = max(0.0, new_balance)
            
            diff = user.credit_balance - old_bal
            tx = CreditTransaction(
                telegram_id=user.telegram_id,
                amount=diff,
                transaction_type="ADMIN_SET",
                notes=f"Balance set from {old_bal:.1f} to {new_balance:.1f}",
                performed_by=str(admin_id)
            )
            db.add(tx)
            db.commit()
            self._sync_vault()
            return {"success": True, "telegram_id": user.telegram_id, "before": old_bal, "after": user.credit_balance, "first_name": user.first_name}
        finally:
            db.close()

    def admin_deduct_credits(self, target_id: str, amount: float, admin_id: Any = "owner", reason: str = "") -> Dict[str, Any]:
        """Admin deducts credits from user account."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            old_bal = user.credit_balance
            user.credit_balance = max(0.0, user.credit_balance - amount)
            
            tx = CreditTransaction(
                telegram_id=user.telegram_id,
                amount=-amount,
                transaction_type="ADMIN_DEDUCT",
                notes=f"Deduction: {reason}" if reason else f"Deducted by Admin {admin_id}",
                performed_by=str(admin_id)
            )
            db.add(tx)
            db.commit()
            self._sync_vault()
            return {"success": True, "telegram_id": user.telegram_id, "before": old_bal, "after": user.credit_balance, "first_name": user.first_name, "deducted": amount}
        finally:
            db.close()

    def admin_set_limits(self, target_id: str, daily_limit: Optional[int] = None, hourly_limit: Optional[int] = None, bulk_cap: Optional[int] = None, admin_id: Any = "owner") -> Dict[str, Any]:
        """Update multiple telephony rate caps at once."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            if daily_limit is not None:
                user.daily_limit = daily_limit
            if hourly_limit is not None:
                user.hourly_limit = hourly_limit
            if bulk_cap is not None:
                user.max_bulk_batch_size = bulk_cap
            db.commit()
            self._sync_vault()
            return {
                "success": True,
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "daily_limit": user.daily_limit,
                "hourly_limit": user.hourly_limit,
                "max_bulk_batch_size": user.max_bulk_batch_size
            }
        finally:
            db.close()

    def admin_toggle_permission(self, target_id: str, perm_key: str, admin_id: Any = "owner") -> Dict[str, Any]:
        """Toggle a specific feature permission for a user."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            if not hasattr(user, perm_key):
                return {"success": False, "message": f"Invalid permission `{perm_key}`."}
            curr = getattr(user, perm_key, True)
            setattr(user, perm_key, not curr)
            db.commit()
            self._sync_vault()
            return {"success": True, "telegram_id": user.telegram_id, "permission": perm_key, "is_enabled": not curr, "first_name": user.first_name}
        finally:
            db.close()

    def admin_ban_user(self, target_id: str, ban: bool = True, reason: Optional[str] = None, admin_id: Any = "owner") -> Dict[str, Any]:
        """Permanently ban or unban a user."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            user.is_banned = ban
            user.ban_reason = reason if ban else None
            user.status = "BANNED" if ban else "ACTIVE"
            db.commit()
            self._sync_vault()
            log_security_event("USER_BAN_TOGGLE", actor=f"admin_{admin_id}", status="SUCCESS", details={"target_id": user.telegram_id, "banned": ban, "reason": reason})
            return {"success": True, "telegram_id": user.telegram_id, "is_banned": ban, "first_name": user.first_name, "reason": reason}
        finally:
            db.close()

    def admin_set_role(self, target_id: str, new_role: str, admin_id: Any = "owner") -> Dict[str, Any]:
        """Promote or demote user role (owner, admin, user)."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            user.role = new_role.lower()
            if user.role == "owner":
                user.credit_balance = 999999.0
            db.commit()
            self._sync_vault()
            return {"success": True, "telegram_id": user.telegram_id, "role": user.role, "first_name": user.first_name}
        finally:
            db.close()

    def admin_add_note(self, target_id: str, note_text: str, admin_id: Any = "owner") -> Dict[str, Any]:
        """Save internal admin note on user."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found."}
            user.admin_notes = note_text.strip()
            db.commit()
            self._sync_vault()
            return {"success": True, "telegram_id": user.telegram_id, "notes": user.admin_notes, "first_name": user.first_name}
        finally:
            db.close()

    def admin_get_category2_summary(self) -> Dict[str, Any]:
        """Aggregate summary for Category 2 User Lifecycle."""
        db: Session = SessionLocal()
        try:
            total_users = db.query(TelegramUser).count()
            banned_count = db.query(TelegramUser).filter(TelegramUser.is_banned == True).count()
            suspended_count = db.query(TelegramUser).filter(TelegramUser.is_suspended == True).count()
            users = db.query(TelegramUser).all()
            total_circ = sum(u.credit_balance for u in users if u.role != "owner")
            
            today_start = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            active_today = db.query(TelegramUser).filter(TelegramUser.last_active_at >= today_start).count()
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "banned_count": banned_count,
                "suspended_count": suspended_count,
                "total_credits_circulation": round(total_circ, 1),
                "roles_breakdown": "Owner (∞), Admin (Staff), User (Standard)"
            }
        finally:
            db.close()

    def deduct_call_credits(self, telegram_id: Any, recipient: str, customer_name: str = "Contact", duration_seconds: float = 30.0) -> Dict[str, Any]:
        """Deduct credits after dispatching a call and record log."""
        tg_id = str(telegram_id).strip()
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
                
            spent = self.cost_per_call
            if user.role != "owner":
                user.credit_balance = max(0.0, user.credit_balance - spent)
                
            user.calls_today += 1
            user.total_calls += 1
            user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
            
            # Log Call
            call_log = UserCallLog(
                telegram_id=tg_id,
                recipient=recipient,
                customer_name=customer_name,
                duration_seconds=duration_seconds,
                credits_spent=spent,
                status="DISPATCHED"
            )
            db.add(call_log)
            
            # Log Transaction
            if user.role != "owner":
                tx = CreditTransaction(
                    telegram_id=tg_id,
                    amount=-spent,
                    transaction_type="CALL_DEDUCT",
                    notes=f"Voice call to {recipient[:4]}****{recipient[-3:]}",
                    performed_by="system"
                )
                db.add(tx)
                
            db.commit()
            self._sync_vault()
            return {
                "success": True,
                "remaining_credits": user.credit_balance,
                "spent": spent,
                "total_calls": user.total_calls
            }
        finally:
            db.close()

    def admin_topup_user(self, target_id: Any, amount: float, admin_id: Any = "owner") -> Dict[str, Any]:
        """Admin credits a user's account."""
        clean_q = str(target_id).strip().lstrip("@")
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(
                (TelegramUser.telegram_id == clean_q) | (TelegramUser.username == clean_q)
            ).first()
            if not user:
                return {"success": False, "message": f"User `{clean_q}` not found in database."}
                
            user.credit_balance += amount
            tx = CreditTransaction(
                telegram_id=user.telegram_id,
                amount=amount,
                transaction_type="ADMIN_TOPUP",
                notes=f"Recharge by Admin {admin_id}",
                performed_by=str(admin_id)
            )
            db.add(tx)
            db.commit()
            self._sync_vault()
            
            log_security_event("ADMIN_TOPUP", actor=f"admin_{admin_id}", status="SUCCESS", details={"target_id": user.telegram_id, "amount": amount, "new_balance": user.credit_balance})
            return {
                "success": True,
                "telegram_id": user.telegram_id,
                "first_name": user.first_name,
                "username": user.username,
                "added_amount": amount,
                "new_balance": user.credit_balance
            }
        finally:
            db.close()

    def get_user_recent_calls(self, target_id: Any = None, telegram_id: Any = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve isolated call history for a specific user, or global recent calls if no ID given."""
        tid = target_id or telegram_id
        db: Session = SessionLocal()
        try:
            if tid:
                tg_id = str(tid).strip()
                logs = db.query(UserCallLog).filter(UserCallLog.telegram_id == tg_id).order_by(UserCallLog.id.desc()).limit(limit).all()
            else:
                logs = db.query(UserCallLog).order_by(UserCallLog.id.desc()).limit(limit).all()

            return [{
                "id": l.id,
                "telegram_id": l.telegram_id,
                "recipient": l.recipient,
                "customer_name": l.customer_name or "Contact",
                "user_name": l.customer_name or "User",
                "duration_seconds": l.duration_seconds or 0.0,
                "cost_credits": l.credits_spent or 1.0,
                "status": l.status or "COMPLETED",
                "created_at": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "Recent"
            } for l in logs]
        finally:
            db.close()

    def admin_set_limit(self, target_id: Any, daily_limit: int, admin_id: Any = "owner") -> Dict[str, Any]:
        """Admin modifies daily call limit for a user."""
        tg_id = str(target_id).strip()
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not user:
                return {"success": False, "message": f"User `{tg_id}` not found."}
                
            user.daily_limit = daily_limit
            db.commit()
            return {"success": True, "telegram_id": tg_id, "new_limit": daily_limit}
        finally:
            db.close()

    def admin_toggle_suspend(self, target_id: Any, suspend: bool, admin_id: Any = "owner") -> Dict[str, Any]:
        """Admin suspends or unsuspends a user."""
        tg_id = str(target_id).strip()
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not user:
                return {"success": False, "message": f"User `{tg_id}` not found."}
                
            user.status = "SUSPENDED" if suspend else "ACTIVE"
            db.commit()
            log_security_event("USER_SUSPEND_TOGGLE", actor=f"admin_{admin_id}", status="SUCCESS", details={"target_id": tg_id, "status": user.status})
            return {"success": True, "telegram_id": tg_id, "status": user.status}
        finally:
            db.close()

    def set_user_language(self, telegram_id: Any, lang: str) -> bool:
        """Switch language between en and hi."""
        tg_id = str(telegram_id).strip()
        db: Session = SessionLocal()
        try:
            u = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if u:
                u.language = lang
                db.commit()
                return True
            return False
        finally:
            db.close()

    def set_user_plan(self, target_id: Any, plan_tier: str, admin_id: Any = "owner") -> Dict[str, Any]:
        """Upgrade user to Free, Pro, or Enterprise tier."""
        tg_id = str(target_id).strip()
        db: Session = SessionLocal()
        try:
            u = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not u:
                return {"success": False, "message": f"User `{tg_id}` not found."}
            u.plan_tier = plan_tier
            if plan_tier.lower() == "pro":
                u.daily_limit = 50
            elif plan_tier.lower() == "enterprise":
                u.daily_limit = 500
            db.commit()
            return {"success": True, "telegram_id": tg_id, "plan_tier": plan_tier, "daily_limit": u.daily_limit}
        finally:
            db.close()

    def create_support_ticket(self, telegram_id: Any, message: str, user_name: str = "User") -> Dict[str, Any]:
        """Create a user support ticket."""
        tg_id = str(telegram_id).strip()
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import SupportTicket
            t = SupportTicket(
                telegram_id=tg_id,
                user_name=user_name,
                message=message,
                status="OPEN"
            )
            db.add(t)
            db.commit()
            db.refresh(t)
            return {"success": True, "ticket_id": t.id, "message": message}
        finally:
            db.close()

    def admin_list_tickets(self, status: str = "OPEN") -> List[Dict[str, Any]]:
        """List support tickets for Admin review."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import SupportTicket
            tickets = db.query(SupportTicket).filter(SupportTicket.status == status).order_by(SupportTicket.id.desc()).all()
            return [{
                "id": t.id,
                "telegram_id": t.telegram_id,
                "user_name": t.user_name,
                "message": t.message,
                "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "Recent"
            } for t in tickets]
        finally:
            db.close()

    def add_contact_tag_or_note(self, phone: str, note_text: str, tag: Optional[str] = None, created_by: str = "admin") -> bool:
        """Attach a CRM tag or note to a customer number."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import ContactNote
            cn = ContactNote(
                phone=phone.strip(),
                note_text=note_text,
                tag=tag,
                created_by=created_by
            )
            db.add(cn)
            db.commit()
            return True
        finally:
            db.close()

    def rate_call_quality(self, telegram_id: Any, rating: int, call_id: Optional[str] = None) -> bool:
        """Submit a 1 to 5 star call quality rating."""
        tg_id = str(telegram_id).strip()
        db: Session = SessionLocal()
        try:
            log = db.query(UserCallLog).filter(UserCallLog.telegram_id == tg_id).order_by(UserCallLog.id.desc()).first()
            if log:
                log.quality_rating = min(5, max(1, rating))
                db.commit()
                return True
            return False
        finally:
            db.close()

    def toggle_killswitch(self, enabled: bool) -> bool:
        """Global system killswitch to immediately freeze all outbound calling."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import SystemSetting
            s = db.query(SystemSetting).filter(SystemSetting.key == "GLOBAL_KILLSWITCH").first()
            if not s:
                s = SystemSetting(key="GLOBAL_KILLSWITCH", value=str(enabled))
                db.add(s)
            else:
                s.value = str(enabled)
                s.updated_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            return enabled
        finally:
            db.close()

    def get_killswitch_status(self) -> bool:
        """Check if global emergency killswitch is active."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import SystemSetting
            s = db.query(SystemSetting).filter(SystemSetting.key == "GLOBAL_KILLSWITCH").first()
            return s.value.lower() == "true" if s else False
        finally:
            db.close()

    def bulk_grant_credits(self, target_ids: List[str], amount: float, admin_id: Any = "owner") -> int:
        """Credit multiple users at once."""
        count = 0
        for tid in target_ids:
            res = self.admin_topup_user(tid, amount, admin_id=admin_id)
            if res.get("success"):
                count += 1
        return count

    def bulk_suspend_users(self, target_ids: List[str], suspend: bool = True, admin_id: Any = "owner") -> int:
        """Suspend multiple users at once."""
        count = 0
        for tid in target_ids:
            res = self.admin_toggle_suspend(tid, suspend=suspend, admin_id=admin_id)
    def get_financial_reconciliation(self) -> Dict[str, Any]:
        """Cross-checks credit transactions, user balances, and telephony consumption."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import TelegramUser, CreditTransaction, UserCallLog
            total_users = db.query(TelegramUser).count()
            users = db.query(TelegramUser).all()
            total_balance = sum(u.credit_balance for u in users if u.role != "owner")
            
            topups = db.query(CreditTransaction).filter(CreditTransaction.transaction_type.in_(["ADMIN_TOPUP", "STRIPE_TOPUP"])).all()
            total_credited = sum(t.amount for t in topups)
            
            calls = db.query(UserCallLog).all()
            total_calls = len(calls)
            total_call_credits = sum(c.credits_spent for c in calls)
            
            # Dollar calculation: 1 credit ~ $0.05 wholesale cost
            est_carrier_cost = total_call_credits * 0.0575
            est_revenue = total_credited * 0.10
            margin = est_revenue - est_carrier_cost
            
            return {
                "total_users": total_users,
                "total_user_balances": round(total_balance, 2),
                "total_credits_granted": round(total_credited, 2),
                "total_calls_placed": total_calls,
                "total_credits_consumed": round(total_call_credits, 2),
                "est_revenue_usd": round(est_revenue, 2),
                "est_carrier_cost_usd": round(est_carrier_cost, 2),
                "gross_margin_usd": round(margin, 2),
                "reconciliation_status": "BALANCED 🟢" if total_balance <= total_credited else "ANOMALOUS ⚠️"
            }
        finally:
            db.close()

    def refund_user_credits(self, target_id: Any, amount: float, reason: str = "Customer Request", admin_id: Any = "owner") -> Dict[str, Any]:
        """Refund / adjust credits with audit ledger record."""
        tg_id = str(target_id).strip()
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import TelegramUser, CreditTransaction
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not user:
                return {"success": False, "message": f"User `{tg_id}` not found."}
            
            old_balance = user.credit_balance
            user.credit_balance += amount
            
            tx = CreditTransaction(
                telegram_id=tg_id,
                amount=amount,
                transaction_type="REFUND_ADJUST",
                notes=f"Refund: {reason}",
                performed_by=str(admin_id)
            )
            db.add(tx)
            db.commit()
            
            log_security_event("CREDIT_REFUND", actor=f"admin_{admin_id}", status="SUCCESS", details={"target_id": tg_id, "amount": amount, "before": old_balance, "after": user.credit_balance, "reason": reason})
            return {
                "success": True,
                "telegram_id": tg_id,
                "first_name": user.first_name,
                "before": old_balance,
                "after": user.credit_balance,
                "amount": amount,
                "reason": reason
            }
        finally:
            db.close()

    def get_churn_risk_users(self, days_inactive: int = 7) -> List[Dict[str, Any]]:
        """Identify inactive users who might churn."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import TelegramUser
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_inactive)
            users = db.query(TelegramUser).filter(TelegramUser.last_active_at < cutoff, TelegramUser.role != "owner").limit(15).all()
            return [{
                "telegram_id": u.telegram_id,
                "name": u.first_name or "User",
                "username": u.username or "N/A",
                "credits": u.credit_balance,
                "last_active": u.last_active_at.strftime("%Y-%m-%d") if u.last_active_at else "Never"
            } for u in users]
        finally:
            db.close()

    def get_security_anomalies(self) -> List[Dict[str, Any]]:
        """Detect automated spikes, high-frequency calling, or credit anomalies."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import TelegramUser, UserCallLog
            anomalies = []
            users = db.query(TelegramUser).all()
            for u in users:
                if u.calls_today >= u.daily_limit and u.role != "owner":
                    anomalies.append({
                        "type": "QUOTA_EXHAUSTED",
                        "severity": "MEDIUM 🟨",
                        "user": f"{u.first_name} (`{u.telegram_id}`)",
                        "details": f"Hit daily limit ({u.calls_today}/{u.daily_limit} calls today)"
                    })
                if u.credit_balance < 0:
                    anomalies.append({
                        "type": "NEGATIVE_BALANCE",
                        "severity": "HIGH 🟥",
                        "user": f"{u.first_name} (`{u.telegram_id}`)",
                        "details": f"Negative credit balance ({u.credit_balance:.2f} Credits)"
                    })
            return anomalies
        finally:
            db.close()

    def toggle_maintenance_mode(self, enabled: bool, message: str = "System is undergoing scheduled maintenance.") -> bool:
        """Toggle maintenance mode on main calling bot."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import SystemSetting
            s = db.query(SystemSetting).filter(SystemSetting.key == "MAINTENANCE_MODE").first()
            if not s:
                s = SystemSetting(key="MAINTENANCE_MODE", value=json.dumps({"enabled": enabled, "message": message}))
                db.add(s)
            else:
                s.value = json.dumps({"enabled": enabled, "message": message})
                s.updated_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            return enabled
        finally:
            db.close()

    def get_maintenance_status(self) -> Tuple[bool, str]:
        """Check if maintenance mode is active."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import SystemSetting
            s = db.query(SystemSetting).filter(SystemSetting.key == "MAINTENANCE_MODE").first()
            if s:
                data = json.loads(s.value)
                return data.get("enabled", False), data.get("message", "Maintenance active.")
            return False, ""
        except Exception:
            return False, ""
        finally:
            db.close()

    def create_invite_code(self, code: Optional[str] = None, bonus_credits: float = 20.0, target_plan: str = "Pro", max_uses: int = 1, expires_days: int = 30, created_by: str = "owner") -> Dict[str, Any]:
        """Generate a new promotional invite code for onboarding users."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import InviteCode
            import random, string
            if not code:
                suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                code = f"CYBER-{suffix}"
            else:
                code = code.strip().upper()

            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_days) if expires_days else None
            inv = InviteCode(
                code=code,
                created_by=str(created_by),
                bonus_credits=bonus_credits,
                target_plan=target_plan,
                max_uses=max_uses,
                used_count=0,
                is_active=True,
                expires_at=expires_at
            )
            db.add(inv)
            db.commit()
            return {
                "success": True,
                "code": code,
                "bonus_credits": bonus_credits,
                "target_plan": target_plan,
                "max_uses": max_uses,
                "expires_at": expires_at.strftime("%Y-%m-%d") if expires_at else "Never"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def redeem_invite_code(self, telegram_id: Any, code_str: str) -> Dict[str, Any]:
        """User redeems an invite code to claim bonus credits & tier upgrade."""
        tg_id = str(telegram_id).strip()
        code_clean = code_str.strip().upper()
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import InviteCode, TelegramUser, CreditTransaction
            inv = db.query(InviteCode).filter(InviteCode.code == code_clean, InviteCode.is_active == True).first()
            if not inv:
                return {"success": False, "message": "❌ Invalid or inactive invite code."}

            if inv.max_uses and inv.used_count >= inv.max_uses:
                return {"success": False, "message": "❌ This invite code has already reached its maximum redemption limit."}

            if inv.expires_at:
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                exp = inv.expires_at.replace(tzinfo=datetime.timezone.utc) if inv.expires_at.tzinfo is None else inv.expires_at
                if now_utc > exp:
                    return {"success": False, "message": "❌ This invite code has expired."}

            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not user:
                user = TelegramUser(telegram_id=tg_id, credit_balance=5.0)
                db.add(user)
                db.flush()

            # Apply Bonus
            user.credit_balance += inv.bonus_credits
            if inv.target_plan and user.role != "owner":
                user.plan_tier = inv.target_plan
                if inv.target_plan.lower() in ["pro", "vip", "enterprise"]:
                    user.daily_limit = max(user.daily_limit, 50)
                    user.hourly_limit = max(user.hourly_limit, 15)
                    user.can_bulk = True

            inv.used_count += 1
            if inv.max_uses and inv.used_count >= inv.max_uses:
                inv.is_active = False

            tx = CreditTransaction(
                telegram_id=tg_id,
                amount=inv.bonus_credits,
                transaction_type="INVITE_REDEEM",
                notes=f"Redeemed invite code {inv.code}",
                performed_by="user"
            )
            db.add(tx)
            db.commit()

            return {
                "success": True,
                "code": inv.code,
                "bonus_credits": inv.bonus_credits,
                "new_balance": user.credit_balance,
                "plan_tier": user.plan_tier,
                "daily_limit": user.daily_limit
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"❌ Redemption error: {str(e)}"}
        finally:
            db.close()

    def list_invite_codes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List active and recent invite codes."""
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import InviteCode
            codes = db.query(InviteCode).order_by(InviteCode.created_at.desc()).limit(limit).all()
            return [{
                "code": c.code,
                "bonus_credits": c.bonus_credits,
                "target_plan": c.target_plan,
                "used_count": c.used_count,
                "max_uses": c.max_uses,
                "is_active": c.is_active,
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
            } for c in codes]
        finally:
            db.close()

    CURRENT_TOS_VERSION = "v1.0"

    def has_accepted_tos(self, telegram_id: Any, version: str = CURRENT_TOS_VERSION) -> bool:
        """Check if user has accepted the specific version of Terms of Service."""
        tg_id = str(telegram_id).strip()
        if tg_id in OWNER_IDS:
            return True
        if tg_id in self._tos_cache:
            return True
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import ToSAcceptance
            rec = db.query(ToSAcceptance).filter(
                ToSAcceptance.telegram_id == tg_id,
                ToSAcceptance.tos_version == version
            ).first()
            if rec:
                self._tos_cache.add(tg_id)
                return True
            return False
        except Exception:
            return True
        finally:
            db.close()

    def record_tos_acceptance(self, telegram_id: Any, version: str = CURRENT_TOS_VERSION, channel: str = "Telegram Bot") -> Dict[str, Any]:
        """Record an immutable timestamped acceptance of the platform ToS & Disclaimer."""
        tg_id = str(telegram_id).strip()
        self._tos_cache.add(tg_id)
        db: Session = SessionLocal()
        try:
            from backend.app.models.models import ToSAcceptance, TelegramUser
            rec = db.query(ToSAcceptance).filter(
                ToSAcceptance.telegram_id == tg_id,
                ToSAcceptance.tos_version == version
            ).first()
            if not rec:
                rec = ToSAcceptance(
                    telegram_id=tg_id,
                    tos_version=version,
                    disclaimer_text="Self-Responsibility, Recipient Consent, TRAI/TCPA Compliance, Immutable Audit & Anti-Abuse Terms.",
                    accepted_at=datetime.datetime.now(datetime.timezone.utc),
                    channel=channel
                )
                db.add(rec)
                
                # Log to Security Audit Trail
                log_security_event(
                    "TOS_DISCLAIMER_ACCEPTED",
                    actor=f"tg_{tg_id}",
                    status="SUCCESS",
                    details={"version": version, "channel": channel}
                )
                db.commit()
            return {"success": True, "telegram_id": tg_id, "tos_version": version}
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def get_tos_disclaimer_card(self) -> Tuple[str, Dict[str, Any]]:
        """Generate the rich bilingual Terms of Service & Disclaimer message and acceptance button."""
        text = (
            "⚖️ *[CYBERCALLING TERMS OF SERVICE & LEGAL DISCLAIMER]*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ *Pehle Yeh Zaroori Shartein & Disclaimer Padhein:* ⚠️\n\n"
            "1. 👤 *Khood Ki Marzi Aur Poori Zimmedari (Sole Responsibility):*\n"
            "   • CyberCalling Voice AI ke through ki jaane wali har call aap **apni marzi aur niji zimmedari** se kar rahe hain.\n"
            "   • Call recipient se pehle consent lena aur call ka purpose legal hona aapki poori responsibility hai.\n\n"
            "2. 📜 *Telecom & Regulatory Compliance (TRAI / TCPA):*\n"
            "   • Aap sabhi telecom regulations (India TRAI/DLT & US TCPA) ko maanne ke liye baadhya hain.\n"
            "   • DND (Do Not Disturb) numbers par unauthorized promotional calls lagana sakht mana hai.\n\n"
            "3. 🚫 *Zero Tolerance on Misuse / Strict Ban:*\n"
            "   • Harassment, fraud, impersonation, emergency numbers (112, 100, 911), ya illegal activities ke liye use karna sakht varjit hai.\n"
            "   • Rules todne par bina warning ke aapka account **Permanently Ban & Block** kar diya jayega.\n\n"
            "4. 🔍 *Audit Logging & Activity Records:*\n"
            "   • Sabhi call timestamps aur activities immutable audit ledger me record hoti hain.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👉 *Bot use karne ke liye neeche diye gaye button par tap karke agree karein:*"
        )
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "✅ I Agree & Accept Terms (Main Sehmat Hoon)", "callback_data": "accept_tos_v1"}
                ]
            ]
        }
        return text, buttons

    def get_user_assistant_settings(self, telegram_id: Any) -> Dict[str, Any]:
        """Fetch user-specific Voice AI assistant configuration with guaranteed fallback to defaults."""
        tg_id = str(telegram_id).strip()
        from assistant_settings_catalog import DEFAULT_ASSISTANT_SETTINGS
        base_defaults = dict(DEFAULT_ASSISTANT_SETTINGS)

        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if user and user.assistant_settings and isinstance(user.assistant_settings, dict):
                base_defaults.update(user.assistant_settings)
            return base_defaults
        except Exception as e:
            print(f"[UserManager get_user_assistant_settings error]: {e}")
            return base_defaults
        finally:
            db.close()

    def update_user_assistant_setting(self, telegram_id: Any, key: str, value: Any) -> Dict[str, Any]:
        """Update a specific persona setting for a single user (100% user-isolated)."""
        tg_id = str(telegram_id).strip()
        from assistant_settings_catalog import DEFAULT_ASSISTANT_SETTINGS
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if not user:
                # Auto-create user if missing
                self.get_or_create_user(tg_id)
                user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()

            current_settings = dict(DEFAULT_ASSISTANT_SETTINGS)
            if user and user.assistant_settings and isinstance(user.assistant_settings, dict):
                current_settings.update(user.assistant_settings)

            current_settings[key] = value
            if user:
                user.assistant_settings = current_settings
                db.commit()
                db.refresh(user)
                self._sync_vault()

            log_security_event(
                "USER_ASSISTANT_SETTING_UPDATED",
                actor=f"tg_{tg_id}",
                status="SUCCESS",
                details={"key": key, "value": value}
            )
            return current_settings
        except Exception as e:
            db.rollback()
            print(f"[UserManager update_user_assistant_setting error]: {e}")
            return self.get_user_assistant_settings(tg_id)
        finally:
            db.close()

    def reset_user_assistant_settings(self, telegram_id: Any) -> Dict[str, Any]:
        """Reset a user's voice assistant settings back to factory defaults."""
        tg_id = str(telegram_id).strip()
        from assistant_settings_catalog import DEFAULT_ASSISTANT_SETTINGS
        db: Session = SessionLocal()
        try:
            user = db.query(TelegramUser).filter(TelegramUser.telegram_id == tg_id).first()
            if user:
                user.assistant_settings = dict(DEFAULT_ASSISTANT_SETTINGS)
                db.commit()
                self._sync_vault()
            log_security_event(
                "USER_ASSISTANT_SETTINGS_RESET",
                actor=f"tg_{tg_id}",
                status="SUCCESS",
                details={"reset": True}
            )
            return dict(DEFAULT_ASSISTANT_SETTINGS)
        except Exception as e:
            db.rollback()
            print(f"[UserManager reset_user_assistant_settings error]: {e}")
            return dict(DEFAULT_ASSISTANT_SETTINGS)
        finally:
            db.close()

user_manager = UserManager()

