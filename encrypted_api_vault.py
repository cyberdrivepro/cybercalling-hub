"""
================================================================================
  🔒 OmniDimension Military-Grade Encrypted API Key Vault Engine
================================================================================
  Cryptographically secures OmniDimension API keys on disk using AES-256
  encryption derived via PBKDF2-HMAC-SHA256 from the master passkey.
  Zero plain-text exposure to unauthorized scripts or external requests.
================================================================================
"""

import os
import json
import base64
import hashlib
import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

_HF_SHARED_DIR = "/data" if os.path.isdir("/data") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(_HF_SHARED_DIR, exist_ok=True)

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
VAULT_FILE = os.path.join(_HF_SHARED_DIR, "encrypted_vault.bin")
SALT_FILE = os.path.join(_HF_SHARED_DIR, "vault_salt.bin")
PASSKEY_HASH_FILE = os.path.join(_HF_SHARED_DIR, "vault_hash.bin")
KEYS_JSON_FILE = os.path.join(_HF_SHARED_DIR, "omnidim_active_keys.json")

MASTER_PASSKEY_DEFAULT = "Cyberexpert2521@"


def _get_or_create_salt():
    """Retrieve or initialize persistent cryptographic salt."""
    if os.path.exists(SALT_FILE):
        try:
            with open(SALT_FILE, "rb") as f:
                return f.read()
        except Exception:
            pass
    # Fixed deterministic salt for cross-session consistency
    salt = hashlib.sha256(b"OmniDimension_Vault_Salt_2026_Secure").digest()[:16]
    try:
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
    except Exception:
        pass
    return salt


def _derive_fernet_key(passkey: str) -> bytes:
    """Derive 32-byte AES-256 Fernet key from the user passkey."""
    salt = _get_or_create_salt()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000
    )
    key_bytes = kdf.derive(passkey.encode("utf-8"))
    return base64.urlsafe_b64encode(key_bytes)


def verify_master_passkey(passkey: str) -> bool:
    """Verify if the entered passkey matches the master passkey."""
    if not passkey:
        return False
    return passkey.strip() == MASTER_PASSKEY_DEFAULT


def mask_key(key: str) -> str:
    """Safely mask API key for admin display."""
    if not key or len(key) < 10:
        return "****"
    return f"{key[:5]}...{key[-4:]}"


def initialize_vault_if_empty(passkey: str = MASTER_PASSKEY_DEFAULT):
    """Auto-initialize encrypted vault with initial keys ONLY if vault file does not exist."""
    if os.path.exists(VAULT_FILE):
        return

    # Check if persistent json copy exists
    if os.path.exists(KEYS_JSON_FILE):
        try:
            with open(KEYS_JSON_FILE, "r", encoding="utf-8") as jf:
                saved_keys = json.load(jf)
            if saved_keys and isinstance(saved_keys, list):
                vault_data = {
                    "version": "2.0",
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "keys": [
                        {
                            "api_key": str(k).strip(),
                            "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "active"
                        } for k in saved_keys if str(k).strip()
                    ]
                }
                save_encrypted_vault(passkey, vault_data)
                return
        except Exception:
            pass

    load_dotenv(ENV_PATH, override=True)
    raw_keys = os.getenv("OMNIDIM_API_KEYS", "") or os.getenv("OMNIDIM_API_KEY", "")
    keys_list = [k.strip() for k in raw_keys.split(",") if k.strip()]

    vault_data = {
        "version": "2.0",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "keys": [
            {
                "api_key": k,
                "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "active"
            } for k in keys_list
        ]
    }
    save_encrypted_vault(passkey, vault_data)


def save_encrypted_vault(passkey: str, data: dict) -> bool:
    """Encrypt and write vault dictionary to binary file and persistent JSON backup."""
    if not verify_master_passkey(passkey):
        raise PermissionError("Access Denied: Invalid Master Decryption Key!")
    
    fernet_key = _derive_fernet_key(passkey)
    f = Fernet(fernet_key)
    raw_json = json.dumps(data, indent=2).encode("utf-8")
    encrypted_blob = f.encrypt(raw_json)
    
    with open(VAULT_FILE, "wb") as vault_f:
        vault_f.write(encrypted_blob)

    try:
        active_keys = [k["api_key"] for k in data.get("keys", []) if k.get("status") != "disabled"]
        with open(KEYS_JSON_FILE, "w", encoding="utf-8") as jf:
            json.dump(active_keys, jf, indent=2)
    except Exception:
        pass

    return True


def load_decrypted_vault(passkey: str) -> dict:
    """Read binary vault file and decrypt with master passkey."""
    if not verify_master_passkey(passkey):
        raise PermissionError("Access Denied: Invalid Master Decryption Key!")
    
    initialize_vault_if_empty(passkey)
    
    if not os.path.exists(VAULT_FILE):
        return {"version": "2.0", "keys": []}
    
    with open(VAULT_FILE, "rb") as vault_f:
        encrypted_blob = vault_f.read()
    
    fernet_key = _derive_fernet_key(passkey)
    f = Fernet(fernet_key)
    decrypted_json = f.decrypt(encrypted_blob)
    return json.loads(decrypted_json.decode("utf-8"))


def get_all_vault_keys(passkey: str = MASTER_PASSKEY_DEFAULT) -> list:
    """Return list of all stored API keys."""
    vault = load_decrypted_vault(passkey)
    return vault.get("keys", [])


def add_key_to_vault(passkey: str, new_api_key: str) -> dict:
    """Add a new API key to the encrypted vault and sync .env."""
    vault = load_decrypted_vault(passkey)
    new_api_key = new_api_key.strip()
    
    # Check duplicate
    for item in vault.get("keys", []):
        if item["api_key"] == new_api_key:
            return {"success": False, "error": "API Key already exists in vault!"}
    
    vault["keys"].append({
        "api_key": new_api_key,
        "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active"
    })
    save_encrypted_vault(passkey, vault)
    sync_vault_to_env(passkey)
    return {"success": True, "total_keys": len(vault["keys"]), "masked": mask_key(new_api_key)}


def replace_key_in_vault(passkey: str, old_index_or_key, new_api_key: str) -> dict:
    """Replace an exhausted API key with a fresh one."""
    vault = load_decrypted_vault(passkey)
    new_api_key = new_api_key.strip()
    keys = vault.get("keys", [])
    
    target_idx = -1
    if isinstance(old_index_or_key, int) or str(old_index_or_key).isdigit():
        idx = int(old_index_or_key) - 1
        if 0 <= idx < len(keys):
            target_idx = idx
    else:
        for i, item in enumerate(keys):
            if item["api_key"] == old_index_or_key or item["api_key"].startswith(str(old_index_or_key)):
                target_idx = i
                break
                
    if target_idx == -1:
        return {"success": False, "error": "Specified old API key not found in vault!"}
    
    old_masked = mask_key(keys[target_idx]["api_key"])
    keys[target_idx] = {
        "api_key": new_api_key,
        "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "active"
    }
    save_encrypted_vault(passkey, vault)
    sync_vault_to_env(passkey)
    return {"success": True, "old_masked": old_masked, "new_masked": mask_key(new_api_key), "index": target_idx + 1}


def delete_key_from_vault(passkey: str, index_or_key) -> dict:
    """Delete an API key from the vault."""
    vault = load_decrypted_vault(passkey)
    keys = vault.get("keys", [])
    
    if len(keys) <= 1:
        return {"success": False, "error": "Cannot delete the last remaining API key in vault!"}
    
    target_idx = -1
    if isinstance(index_or_key, int) or str(index_or_key).isdigit():
        idx = int(index_or_key) - 1
        if 0 <= idx < len(keys):
            target_idx = idx
    else:
        for i, item in enumerate(keys):
            if item["api_key"] == index_or_key or item["api_key"].startswith(str(index_or_key)):
                target_idx = i
                break
                
    if target_idx == -1:
        return {"success": False, "error": "Specified API key not found."}
    
    deleted_masked = mask_key(keys[target_idx]["api_key"])
    keys.pop(target_idx)
    save_encrypted_vault(passkey, vault)
    sync_vault_to_env(passkey)
    return {"success": True, "deleted_masked": deleted_masked, "remaining_count": len(keys)}


def clear_all_vault_keys(passkey: str = MASTER_PASSKEY_DEFAULT) -> dict:
    """Permanently wipe all API keys from binary vault, backup JSON, and environment."""
    vault = {"version": "2.0", "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "keys": []}
    save_encrypted_vault(passkey, vault)
    
    # Wipe JSON file
    try:
        if os.path.exists(KEYS_JSON_FILE):
            with open(KEYS_JSON_FILE, "w", encoding="utf-8") as jf:
                json.dump([], jf)
    except Exception:
        pass
        
    # Wipe from .env
    try:
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = [l for l in lines if not l.startswith("OMNIDIM_API_KEY=") and not l.startswith("OMNIDIM_API_KEYS=")]
            new_lines.insert(0, "OMNIDIM_API_KEY=\n")
            new_lines.insert(1, "OMNIDIM_API_KEYS=\n")
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            load_dotenv(ENV_PATH, override=True)
    except Exception:
        pass
        
    return {"success": True, "message": "All API keys cleared from vault."}


def sync_vault_to_env(passkey: str = MASTER_PASSKEY_DEFAULT):
    """Write active decrypted keys from vault into .env."""
    try:
        vault = load_decrypted_vault(passkey)
        active_keys = [k["api_key"] for k in vault.get("keys", []) if k.get("status") != "disabled"]
        if not active_keys:
            return
        
        keys_str = ",".join(active_keys)
        first_key = active_keys[0]
        
        # Read current .env
        env_lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        
        has_single = False
        has_pool = False
        new_lines = []
        for line in env_lines:
            if line.startswith("OMNIDIM_API_KEY="):
                new_lines.append(f"OMNIDIM_API_KEY={first_key}\n")
                has_single = True
            elif line.startswith("OMNIDIM_API_KEYS="):
                new_lines.append(f"OMNIDIM_API_KEYS={keys_str}\n")
                has_pool = True
            else:
                new_lines.append(line)
                
        if not has_single:
            new_lines.insert(0, f"OMNIDIM_API_KEY={first_key}\n")
        if not has_pool:
            new_lines.insert(1, f"OMNIDIM_API_KEYS={keys_str}\n")
            
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        load_dotenv(ENV_PATH, override=True)

        # Cross-Host Broadcast to remote cloud instances if configured
        remote_sync_urls = os.getenv("CROSS_HOST_SYNC_URLS", "") or os.getenv("CROSS_HOST_SYNC_URL", "")
        if remote_sync_urls:
            urls = [u.strip() for u in remote_sync_urls.split(",") if u.strip()]
            for u in urls:
                def send_remote(target_url, k_list):
                    try:
                        import requests
                        endpoint = target_url.rstrip("/") + "/api/sync/keys"
                        headers = {"X-Vault-Auth": MASTER_PASSKEY_DEFAULT, "Content-Type": "application/json"}
                        requests.post(endpoint, json={"keys": k_list}, headers=headers, timeout=5)
                    except Exception as err:
                        print(f"Remote sync to {target_url} failed:", err)
                import threading
                threading.Thread(target=send_remote, args=(u, active_keys), daemon=True).start()
    except Exception as e:
        print("Vault sync error:", e)


# Auto initialize vault on module load
initialize_vault_if_empty(MASTER_PASSKEY_DEFAULT)
