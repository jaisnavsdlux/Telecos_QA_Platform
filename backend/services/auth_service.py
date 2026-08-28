"""
Authentication & User Management Service.
Features NIST SP 800-132 compliant PBKDF2-HMAC-SHA256 password hashing with salt,
legacy SHA-256 compatibility auto-upgrade, and thread-safe persistence.
"""
import os
import json
import uuid
import hashlib
import secrets
import threading
from typing import Dict, Any, Optional
from backend.config import USERS_FILE

_AUTH_LOCK = threading.RLock()

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a 16-byte random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a password against the stored hash.
    Supports PBKDF2-HMAC-SHA256 and legacy unsalted SHA-256.
    """
    if not stored_hash:
        return False
    
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, key_hex = stored_hash.split("$")
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                int(iterations)
            )
            return secrets.compare_digest(new_key.hex(), key_hex)
        except Exception:
            return False
    
    # Legacy SHA-256 fallback
    legacy_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return secrets.compare_digest(legacy_hash, stored_hash)

class AuthService:
    @staticmethod
    def load_users() -> Dict[str, Any]:
        """Thread-safe retrieval of all users from persistent storage."""
        default_users = {
            "admin": {
                "username": "admin",
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "display_name": "Lead QA Administrator",
                "email": "admin@strelza.telecos.com.au",
                "is_admin": True
            }
        }
        with _AUTH_LOCK:
            if os.path.exists(USERS_FILE):
                try:
                    with open(USERS_FILE, "r", encoding="utf-8") as f:
                        users = json.load(f)
                        if "admin" not in users:
                            users["admin"] = default_users["admin"]
                            AuthService.save_users(users)
                        return users
                except Exception:
                    return default_users
            else:
                AuthService.save_users(default_users)
                return default_users

    @staticmethod
    def save_users(users: Dict[str, Any]) -> None:
        """Thread-safe persistence of user data."""
        with _AUTH_LOCK:
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2)

    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates user. If valid and using legacy hash, automatically upgrades to PBKDF2.
        """
        u = username.lower().strip()
        users = AuthService.load_users()
        user = users.get(u)
        if not user:
            return None

        stored_hash = user.get("password_hash", "")
        if verify_password(password, stored_hash):
            # Auto-upgrade legacy hash to PBKDF2 if needed
            if not stored_hash.startswith("pbkdf2_sha256$"):
                user["password_hash"] = hash_password(password)
                AuthService.save_users(users)
            return user
        return None

    @staticmethod
    def register(username: str, password: str, display_name: str = "", email: str = "", role: str = "engineer") -> Dict[str, Any]:
        """Registers a new user account."""
        u = username.lower().strip()
        p = password.strip()
        if not u or not p:
            raise ValueError("Username and password are required.")
        
        users = AuthService.load_users()
        if u in users:
            raise ValueError("Username already exists. Please choose another.")
        
        valid_roles = ["admin", "engineer", "reviewer", "lead"]
        clean_role = role.lower().strip() if role.lower().strip() in valid_roles else "engineer"
        
        new_user = {
            "username": u,
            "password_hash": hash_password(p),
            "role": clean_role,
            "display_name": display_name.strip() or u.capitalize(),
            "email": email.strip(),
            "is_admin": (clean_role == "admin")
        }
        users[u] = new_user
        AuthService.save_users(users)
        return new_user
