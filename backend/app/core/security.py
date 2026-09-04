"""
================================================================================
  🔒 CyberCalling 2.0 — Enterprise Cryptographic & Security Engine
================================================================================
  1. Authenticated Encryption: AES-256-GCM (256-bit key, 96-bit random nonce, 128-bit auth tag)
  2. Key Derivation: PBKDF2-HMAC-SHA256 (600,000 rounds) with dynamic cryptographic salt
  3. Two-Factor Authentication: RFC 6238 TOTP (Time-based One-Time Password via pyotp)
  4. Passkey Verification: Constant-time comparison to prevent timing attacks
================================================================================
"""

import os
import hmac
import json
import base64
import hashlib
import secrets
from typing import Optional, Tuple, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import pyotp

# Dynamic Salt Location
VAULT_DIR = os.path.dirname(os.path.abspath(__file__))
SALT_FILE = os.path.join(VAULT_DIR, ".vault_salt_gcm.bin")
TOTP_SECRET_FILE = os.path.join(VAULT_DIR, ".vault_totp_secret.bin")

def get_or_create_salt() -> bytes:
    """Retrieve or generate secure 32-byte cryptographic salt."""
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "rb") as f:
            return f.read()
    salt = secrets.token_bytes(32)
    with open(SALT_FILE, "wb") as f:
        f.write(salt)
    return salt

def get_or_create_totp_secret() -> str:
    """Retrieve or initialize persistent base32 TOTP secret."""
    if os.path.exists(TOTP_SECRET_FILE):
        with open(TOTP_SECRET_FILE, "r", encoding="utf-8") as f:
            sec = f.read().strip()
            if sec:
                return sec
    new_sec = pyotp.random_base32()
    with open(TOTP_SECRET_FILE, "w", encoding="utf-8") as f:
        f.write(new_sec)
    return new_sec

def derive_aes_gcm_key(passkey: str, salt: Optional[bytes] = None) -> bytes:
    """Derive a 256-bit (32 bytes) key from passkey using PBKDF2-HMAC-SHA256 with 600,000 iterations."""
    if not passkey:
        raise ValueError("Passkey cannot be empty")
    s = salt or get_or_create_salt()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=s,
        iterations=600000
    )
    return kdf.derive(passkey.encode("utf-8"))

def encrypt_aes_gcm(plaintext: str, passkey: str) -> Dict[str, str]:
    """
    Encrypt plaintext string using AES-256-GCM.
    Returns dictionary with base64-encoded ciphertext, nonce, and tag.
    """
    key = derive_aes_gcm_key(passkey)
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # Standard 96-bit nonce for GCM
    # AESGCM.encrypt in cryptography appends the 16-byte tag to the ciphertext
    encrypted_data = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    
    return {
        "ciphertext": base64.b64encode(encrypted_data).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "version": "AES-256-GCM-v2"
    }

def decrypt_aes_gcm(encrypted_payload: Dict[str, str], passkey: str) -> str:
    """
    Decrypt AES-256-GCM ciphertext payload with authentication tag validation.
    Raises exception if data was tampered with or passkey is incorrect.
    """
    key = derive_aes_gcm_key(passkey)
    aesgcm = AESGCM(key)
    nonce = base64.b64decode(encrypted_payload["nonce"])
    data = base64.b64decode(encrypted_payload["ciphertext"])
    
    decrypted_bytes = aesgcm.decrypt(nonce, data, None)
    return decrypted_bytes.decode("utf-8")

def generate_totp_uri(account_name: str = "CyberCalling_Admin", issuer_name: str = "CyberCalling Enterprise") -> str:
    """Generate standard otpauth:// provisioning URI for Google Authenticator / 1Password / Authy."""
    secret = get_or_create_totp_secret()
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer_name)

def verify_totp_code(code: str) -> bool:
    """Verify 6-digit TOTP token against current time window (+/- 1 step window drift tolerance)."""
    if not code:
        return False
    clean_code = str(code).strip().replace(" ", "")
    secret = get_or_create_totp_secret()
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(clean_code, valid_window=1))

def constant_time_compare(val1: str, val2: str) -> bool:
    """Constant-time string comparison preventing side-channel timing attacks."""
    if not isinstance(val1, str) or not isinstance(val2, str):
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))
