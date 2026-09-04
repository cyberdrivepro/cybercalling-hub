"""
================================================================================
  🔄 CyberCalling 2.0 — n8n Autonomous Workflow Integration Gateway
================================================================================
  Connects local & cloud n8n workflows with CyberCalling's Voice AI engine,
  automated lead scrubbing, instant call dispatching, and webhook notifications.
================================================================================
"""

import time
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.models import CallRecord, Contact
from backend.app.services.telephony_manager import telephony_manager, normalize_e164
from backend.app.core.audit import log_security_event

router = APIRouter(prefix="/api/v1/n8n", tags=["n8n-integration"])

class N8nCallTrigger(BaseModel):
    phone: str
    name: Optional[str] = "Valued Contact"
    message: Optional[str] = None
    provider: Optional[str] = "OMNIDIM"  # OMNIDIM, TWILIO, TELNYX, SIP
    workflow_id: Optional[str] = None
    source: Optional[str] = "n8n-automation"

class N8nBulkTrigger(BaseModel):
    leads: List[Dict[str, Any]]
    provider: Optional[str] = "OMNIDIM"
    campaign_name: Optional[str] = "n8n Automated Campaign"

@router.get("/status")
def get_n8n_bridge_status():
    """Health & capability endpoint for n8n HTTP Request node."""
    return {
        "status": "online",
        "service": "CyberCalling 2.0 n8n Gateway",
        "supported_providers": ["OMNIDIM", "TWILIO", "TELNYX", "SIP"],
        "voice_ai_rate": "$0.115/min",
        "concurrency": "Multi-Carrier High-Concurrency Enabled",
        "timestamp": time.time()
    }

@router.post("/dispatch-call")
def n8n_dispatch_call(payload: N8nCallTrigger, db: Session = Depends(get_db)):
    """
    Endpoint triggered by n8n HTTP Request Node to dispatch an automated Voice AI call.
    Accepts leads from Google Sheets, Webhooks, Typeform, Calendly, or CRM.
    """
    norm = normalize_e164(payload.phone)
    if not norm["valid"] and len(norm["e164"]) < 10:
        raise HTTPException(status_code=400, detail=f"Invalid phone number: {payload.phone}")

    clean_num = norm["e164"]
    res = telephony_manager.dispatch_call(
        to_number=clean_num,
        customer_name=payload.name or "Valued Contact",
        spoken_message=payload.message,
        provider=payload.provider or "OMNIDIM"
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Call dispatch failed"))

    # Record in database
    rec = CallRecord(
        call_sid=res.get("call_id"),
        provider=res.get("provider", payload.provider),
        to_number=clean_num,
        from_number=res.get("caller_id", "+918048799598"),
        customer_name=payload.name,
        spoken_message=payload.message,
        status="DISPATCHED",
        cost_usd=0.044,
        lead_score=85,
        is_hot_lead=True
    )
    db.add(rec)
    db.commit()

    log_security_event(
        "N8N_CALL_TRIGGERED",
        actor=f"n8n_{payload.workflow_id or 'node'}",
        status="SUCCESS",
        details={"to": clean_num, "provider": payload.provider, "call_id": res.get("call_id")}
    )

    return {
        "success": True,
        "call_id": res.get("call_id"),
        "provider": res.get("provider"),
        "recipient": clean_num,
        "customer_name": payload.name,
        "caller_id": res.get("caller_id"),
        "status": "DISPATCHED",
        "lead_score": 85,
        "is_hot_lead": True,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@router.post("/bulk-dispatch")
def n8n_bulk_dispatch(payload: N8nBulkTrigger, db: Session = Depends(get_db)):
    """Dispatch automated parallel campaign directly from an n8n list of records."""
    dispatched = []
    failed = []

    for item in payload.leads:
        raw_phone = str(item.get("phone") or item.get("number") or item.get("mobile") or "")
        name = str(item.get("name") or item.get("full_name") or "Valued Contact")
        msg = item.get("message") or item.get("task")

        if not raw_phone:
            continue

        norm = normalize_e164(raw_phone)
        if not norm["valid"] and len(norm["e164"]) < 10:
            failed.append({"phone": raw_phone, "reason": "Invalid E.164"})
            continue

        res = telephony_manager.dispatch_call(
            to_number=norm["e164"],
            customer_name=name,
            spoken_message=msg,
            provider=payload.provider or "OMNIDIM"
        )
        if res.get("success"):
            dispatched.append({
                "call_id": res.get("call_id"),
                "phone": norm["e164"],
                "name": name,
                "provider": res.get("provider")
            })
        else:
            failed.append({"phone": norm["e164"], "reason": res.get("error")})

    return {
        "success": True,
        "campaign_name": payload.campaign_name,
        "total_received": len(payload.leads),
        "dispatched_count": len(dispatched),
        "failed_count": len(failed),
        "dispatched": dispatched,
        "failed": failed
    }
