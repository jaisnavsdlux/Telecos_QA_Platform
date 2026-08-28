"""
Unit & Integration tests for Authentication & Password Security.
"""
import uuid
import pytest
from backend.services.auth_service import hash_password, verify_password

def test_password_hashing_pbkdf2():
    """Verifies that password hashing produces salted PBKDF2-HMAC-SHA256 hashes."""
    pwd = "SecretPassword123!"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)

    # Salted hashes must be unique
    assert h1 != h2
    assert h1.startswith("pbkdf2_sha256$100000$")
    assert verify_password(pwd, h1) is True
    assert verify_password("WrongPassword", h1) is False

def test_legacy_sha256_verification_and_upgrade():
    """Verifies backward compatibility with legacy unsalted SHA-256 hashes."""
    import hashlib
    pwd = "legacyPassword123"
    legacy_hash = hashlib.sha256(pwd.encode("utf-8")).hexdigest()

    assert verify_password(pwd, legacy_hash) is True
    assert verify_password("wrong", legacy_hash) is False

def test_api_login_success(client):
    """Tests POST /api/auth/login with valid admin credentials."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_admin"] is True

def test_api_login_failure(client):
    """Tests POST /api/auth/login with invalid password."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "invalid_wrong_password"})
    assert res.status_code == 401

def test_api_register_and_login(client):
    """Tests registering a new QA Engineer account and authenticating with it."""
    random_user = f"engineer_{uuid.uuid4().hex[:6]}"
    res_reg = client.post("/api/auth/register", json={
        "username": random_user,
        "password": "Password2026!",
        "display_name": "Test Engineer",
        "email": f"{random_user}@telecos.com.au",
        "role": "engineer"
    })
    assert res_reg.status_code == 200
    data_reg = res_reg.json()
    assert data_reg["user"]["username"] == random_user
    assert data_reg["user"]["role"] == "engineer"

    # Now login with the newly created account
    res_login = client.post("/api/auth/login", json={
        "username": random_user,
        "password": "Password2026!"
    })
    assert res_login.status_code == 200
    assert res_login.json()["user"]["username"] == random_user
