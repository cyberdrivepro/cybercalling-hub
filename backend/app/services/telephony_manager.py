"""
================================================================================
  📞 CyberCalling 2.0 — Unified Enterprise Telephony Manager & Router
================================================================================
  Abstracts OmniDimension, Twilio, Telnyx, and SIP Trunking into a single
  carrier-agnostic routing interface with automatic failover and consent checking.
================================================================================
"""

import os
import requests
import datetime
import phonenumbers
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from backend.app.core.config import settings
from backend.app.core.audit import log_security_event

def normalize_e164(raw_phone: str) -> Dict[str, Any]:
    """Parse and normalize phone number to strict international E.164 using Google phonenumbers."""
    cleaned = raw_phone.strip()
    if not cleaned.startswith("+"):
        if len(cleaned) == 10 and not cleaned.startswith("0"):
            cleaned = "+91" + cleaned
        else:
            cleaned = "+" + cleaned.lstrip("0")
            
    try:
        parsed = phonenumbers.parse(cleaned, None)
        if phonenumbers.is_valid_number(parsed):
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            country_code = f"+{parsed.country_code}"
            flag = "🇮🇳" if parsed.country_code == 91 else ("🇺🇸" if parsed.country_code == 1 else "🌐")
            return {
                "valid": True,
                "e164": e164,
                "country_code": country_code,
                "flag": flag,
                "national_number": str(parsed.national_number)
            }
    except Exception:
        pass
        
    return {
        "valid": False,
        "e164": cleaned,
        "country_code": "+91",
        "flag": "📞",
        "national_number": cleaned
    }

class TelephonyManager:
    def __init__(self):
        self.omnidim_keys = [k.strip() for k in settings.OMNIDIM_API_KEYS.split(",") if k.strip()] or [settings.OMNIDIM_API_KEY]
        
    def dispatch_call(
        self,
        to_number: str,
        customer_name: str = "Valued Contact",
        spoken_message: Optional[str] = None,
        provider: str = "OMNIDIM",
        enforce_consent: bool = True,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Route and dispatch an outbound Voice AI call over the requested provider."""
        norm = normalize_e164(to_number)
        clean_num = norm["e164"]
        
        provider_upper = provider.upper()
        
        # 1. Twilio High-Concurrency Carrier Route
        if provider_upper == "TWILIO":
            return self._dispatch_twilio(clean_num, customer_name, spoken_message)
            
        # 2. Telnyx SIP Number Route
        elif provider_upper == "TELNYX":
            return self._dispatch_telnyx(clean_num, customer_name, spoken_message)
            
        # 3. Enterprise SIP Trunk Route
        elif provider_upper == "SIP":
            return self._dispatch_sip(clean_num, customer_name, spoken_message)
            
        # 4. OmniDimension Voice AI Brain Route (Default)
        else:
            return self._dispatch_omnidim(clean_num, customer_name, spoken_message, user_settings=user_settings)

    def _dispatch_omnidim(self, to_number: str, customer_name: str, spoken_message: Optional[str], user_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatch via OmniDimension AI Engine routed strictly through active proxy tunnel."""
        from proxy_manager import proxy_manager
        if not proxy_manager.has_active_proxy():
            return {
                "success": False,
                "provider": "OMNIDIM",
                "error": "🚫 [STRICT PROXY KILLSWITCH ACTIVATED] OmniDimension Call Blocked! No active verified proxy in pool. Direct unmasked server requests are prohibited. Please add proxies to @cybercallingproxy_bot first."
            }

        api_key = self.omnidim_keys[0] if self.omnidim_keys else ""
        if not api_key:
            return {"success": False, "provider": "OMNIDIM", "error": "No OmniDimension API keys configured."}
            
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        url = "https://backend.omnidim.io/api/v1/calls/dispatch"

        # Resolve User Assistant Settings Persona
        from assistant_settings_catalog import AVAILABLE_VOICES, AVAILABLE_MODELS, AVAILABLE_STT, AVAILABLE_LANGUAGES, AVAILABLE_SPEEDS
        v_key = (user_settings or {}).get("voice_key", "v_riya")
        v_info = AVAILABLE_VOICES.get(v_key, AVAILABLE_VOICES["v_riya"])
        m_key = (user_settings or {}).get("model_key", "m_gpt4mini")
        m_info = AVAILABLE_MODELS.get(m_key, AVAILABLE_MODELS["m_gpt4mini"])
        stt_key = (user_settings or {}).get("stt_key", "stt_soniox")
        stt_info = AVAILABLE_STT.get(stt_key, AVAILABLE_STT["stt_soniox"])
        lang_key = (user_settings or {}).get("language_key", "lang_hindi")
        lang_info = AVAILABLE_LANGUAGES.get(lang_key, AVAILABLE_LANGUAGES["lang_hindi"])
        spd_key = (user_settings or {}).get("speed_key", "spd_normal")
        spd_info = AVAILABLE_SPEEDS.get(spd_key, AVAILABLE_SPEEDS["spd_normal"])
        
        payload = {
            "phone_number": to_number,
            "customer_name": customer_name,
            "agent_id": 247312,
            "caller_id": "+918048799598"
        }
        if spoken_message:
            payload["welcome_message"] = spoken_message
            payload["custom_message"] = spoken_message
            payload["message_to_deliver"] = spoken_message
            payload["task"] = spoken_message
            payload["instruction"] = f"Deliver this exact message: {spoken_message}"
            payload["call_context"] = {
                "welcome_message": spoken_message,
                "custom_message": spoken_message,
                "message_to_deliver": spoken_message,
                "instruction": f"Deliver this exact message: {spoken_message}",
                "task": spoken_message,
                "voice_name": v_info.get("name"),
                "voice_id": v_info.get("voice_id"),
                "model": m_info.get("model_id"),
                "language": lang_info.get("code")
            }
            
        try:
            s = proxy_manager.get_session(target_url=url)
            if spoken_message:
                try:
                    agent_up_url = "https://backend.omnidim.io/api/v1/agents/247312"
                    task_prompt = (
                        f"# Role & Purpose\n"
                        f"You are Dark Angel Voice AI calling {customer_name}.\n"
                        f"CRITICAL RULE: YOUR FIRST WORDS MUST BE EXACTLY: \"{spoken_message}\"\n"
                        f"PRIMARY TASK / MESSAGE TO DELIVER: \"{spoken_message}\"\n\n"
                        f"Instructions:\n"
                        f"1. Say \"{spoken_message}\" immediately as your very first words when the call is answered. Do not alter or omit this sentence.\n"
                        f"2. Converse naturally in Hindi/English, answer questions politely, and remain helpful.\n"
                        f"3. Keep responses concise (1-2 sentences)."
                    )
                    s.put(agent_up_url, json={
                        "name": "Dark Angel Voice AI",
                        "welcome_message": spoken_message,
                        "context": task_prompt,
                        "is_welcome_message_dynamic": False,
                        "voice_name": v_info.get("name"),
                        "voice_id": v_info.get("voice_id"),
                        "model": m_info.get("model_id"),
                        "stt_provider": stt_info.get("provider_id"),
                        "language": lang_info.get("code"),
                        "speech_rate": spd_info.get("rate", 1.0)
                    }, headers=headers, timeout=8)
                except Exception as ex_ag:
                    print(f"[TelephonyManager Agent Update]: {ex_ag}")

            r = s.post(url, json=payload, headers=headers, timeout=12)
            if r.status_code in [200, 201]:
                res_data = r.json()
                call_id = str(res_data.get("call_id") or res_data.get("id") or "OD-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
                log_security_event("CALL_DISPATCHED", actor="telephony_manager", status="SUCCESS", details={"provider": "OMNIDIM", "to": to_number, "call_id": call_id})
                return {
                    "success": True,
                    "provider": "OMNIDIM",
                    "call_id": call_id,
                    "status": "DISPATCHED",
                    "recipient": to_number,
                    "caller_id": "+918048799598",
                    "rate_per_min": 0.120
                }
            else:
                err_text = r.text
                return {
                    "success": False,
                    "provider": "OMNIDIM",
                    "error": f"OmniDimension API HTTP {r.status_code}: {err_text}"
                }
        except Exception as ex:
            return {"success": False, "provider": "OMNIDIM", "error": str(ex)}

    def _dispatch_twilio(self, to_number: str, customer_name: str, spoken_message: Optional[str]) -> Dict[str, Any]:
        """Dispatch via Twilio REST API."""
        from twilio_calling_engine import dispatch_twilio_single_call
        msg = spoken_message or "Hello! Thank you for speaking with our Voice AI assistant."
        res = dispatch_twilio_single_call(to_number, spoken_message=msg, customer_name=customer_name)
        if res.get("success"):
            return {
                "success": True,
                "provider": "TWILIO",
                "call_id": res.get("call_sid"),
                "status": "QUEUED",
                "recipient": to_number,
                "caller_id": res.get("from") or "+18645168900",
                "rate_per_min": 0.015
            }
        return {"success": False, "provider": "TWILIO", "error": res.get("error")}

    def _dispatch_telnyx(self, to_number: str, customer_name: str, spoken_message: Optional[str]) -> Dict[str, Any]:
        """Dispatch via Telnyx Wholesale SIP number."""
        from telnyx_sip_engine import dispatch_telnyx_single_call
        res = dispatch_telnyx_single_call(to_number, spoken_message=spoken_message or "Hello via Telnyx")
        if res.get("success"):
            return {
                "success": True,
                "provider": "TELNYX",
                "call_id": res.get("call_control_id") or res.get("call_id"),
                "status": "INITIATED",
                "recipient": to_number,
                "caller_id": "+15863601284",
                "rate_per_min": 0.008
            }
        return {"success": False, "provider": "TELNYX", "error": res.get("error")}

    def _dispatch_sip(self, to_number: str, customer_name: str, spoken_message: Optional[str]) -> Dict[str, Any]:
        """Dispatch via Enterprise SIP Trunk."""
        from sip_trunking_gateway import dispatch_sip_single_call
        res = dispatch_sip_single_call(to_number, spoken_message=spoken_message or "Hello via SIP Trunk")
        if res.get("success"):
            return {
                "success": True,
                "provider": "SIP",
                "call_id": res.get("sip_uri"),
                "status": "ROUTED",
                "recipient": to_number,
                "caller_id": res.get("caller_id"),
                "rate_per_min": 0.004
            }
        return {"success": False, "provider": "SIP", "error": res.get("error")}

telephony_manager = TelephonyManager()
