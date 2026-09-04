"""
================================================================================
  ⚙️ CyberCalling 2.0 — Pydantic Settings & Dynamic Configuration
================================================================================
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "CyberCalling Enterprise Voice AI Hub"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server & Host
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./cybercalling_enterprise.db"
    
    # Security & Encryption
    MASTER_VAULT_PASSKEY: str = os.getenv("MASTER_VAULT_PASSKEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "cybercalling-jwt-secret-key-2026-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    
    # Rate Accounting (OmniDimension Rates)
    VOICE_AI_RATE_PER_MIN: float = 0.115
    TELEPHONY_RATE_PER_MIN: float = 0.005
    TOTAL_RATE_PER_MIN: float = 0.120
    
    # Telephony Provider Defaults
    OMNIDIM_API_KEY: str = os.getenv("OMNIDIM_API_KEY", "")
    OMNIDIM_API_KEYS: str = os.getenv("OMNIDIM_API_KEYS", "")
    
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_BOT_TOKEN: str = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "")
    
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "+18645168900")
    
    TELNYX_PHONE_NUMBER: str = os.getenv("TELNYX_PHONE_NUMBER", "+15863601284")
    TELNYX_SIP_DOMAIN: str = os.getenv("TELNYX_SIP_DOMAIN", "sip.telnyx.com")
    
    # Compliance & Timing
    DEFAULT_CALLING_WINDOW: str = "09:00-20:00"
    ENFORCE_CONSENT_CHECK: bool = True
    MAX_AUTO_RETRIES: int = 3
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
