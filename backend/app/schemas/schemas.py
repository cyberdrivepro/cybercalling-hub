"""
================================================================================
  📋 CyberCalling 2.0 — Pydantic Validation Schemas & DTOs
================================================================================
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import datetime

# Auth Schemas
class AuthRequest(BaseModel):
    passkey: str
    totp_code: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    token_type: str = "bearer"
    totp_required: bool = False
    message: str

# Call Dispatch Schemas
class CallDispatchRequest(BaseModel):
    to_number: str
    customer_name: Optional[str] = "Valued Contact"
    spoken_message: Optional[str] = None
    provider: Optional[str] = "OMNIDIM"  # OMNIDIM, TWILIO, TELNYX, SIP
    campaign_id: Optional[int] = None

class CallDispatchResponse(BaseModel):
    success: bool
    call_id: Optional[str] = None
    provider: str
    status: str
    recipient: str
    caller_id: str
    cost_usd: float = 0.0
    message: str

# Campaign Schemas
class CampaignCreateRequest(BaseModel):
    name: str
    provider: str = "OMNIDIM"
    numbers: List[str]
    spoken_message: Optional[str] = None
    budget_cap_usd: float = 10.0
    calling_window: str = "09:00-20:00"

# Contact Schemas
class ContactCreateRequest(BaseModel):
    name: str
    phone: str
    nickname: Optional[str] = None
    tags: Optional[str] = "lead"
    consent_status: Optional[str] = "OPTED_IN"

# Vault Key Schemas
class VaultKeyAddRequest(BaseModel):
    label: str
    api_key: str
    provider: str = "OMNIDIMENSION"

class VaultKeyResponse(BaseModel):
    id: int
    label: str
    provider: str
    key_preview: str
    balance_usd: float
    is_active: bool
    added_at: datetime.datetime
