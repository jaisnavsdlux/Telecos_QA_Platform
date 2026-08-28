"""
Authentication Router.
Handles login, registration, role resolution, and session tokens.
"""
import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str
    passkey: Optional[str] = ""

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = ""
    email: Optional[str] = ""
    role: Optional[str] = "engineer"

class UserResponse(BaseModel):
    username: str
    display_name: str
    role: str
    email: str
    is_admin: bool

class AuthResponse(BaseModel):
    token: str
    user: UserResponse
    status: str = "success"

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Authenticates a user and returns a session token."""
    user = AuthService.authenticate(req.username, req.password)
    if not user:
        # Fallback tolerance for demo admin credentials if passkey provided
        if req.username.lower().strip() == "admin" and (req.password == "admin123" or req.passkey == "admin123"):
            user = {
                "username": "admin",
                "role": "admin",
                "display_name": "Lead QA Administrator",
                "email": "admin@strelza.telecos.com.au",
                "is_admin": True
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials. Please enter a valid account or admin / admin123.")

    token = "telecos-jwt-" + uuid.uuid4().hex[:16]
    return {
        "status": "success",
        "token": token,
        "user": {
            "username": user["username"],
            "display_name": user.get("display_name", user["username"].capitalize()),
            "role": user.get("role", "engineer"),
            "email": user.get("email", ""),
            "is_admin": user.get("is_admin", user.get("role") == "admin")
        }
    }

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """Registers a new QA Engineer, Lead Auditor, or Reviewer account."""
    try:
        new_user = AuthService.register(
            username=req.username,
            password=req.password,
            display_name=req.display_name or "",
            email=req.email or "",
            role=req.role or "engineer"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = "telecos-jwt-" + uuid.uuid4().hex[:16]
    return {
        "status": "success",
        "token": token,
        "user": {
            "username": new_user["username"],
            "display_name": new_user["display_name"],
            "role": new_user["role"],
            "email": new_user["email"],
            "is_admin": new_user["is_admin"]
        }
    }

@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Returns basic session context."""
    return {"status": "authenticated", "authenticated": True}
