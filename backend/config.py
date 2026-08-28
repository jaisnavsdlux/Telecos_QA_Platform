"""
Centralized Configuration & Path Management for Strelza Telecos QA Platform.
Supports Render, Vercel, Neon PostgreSQL, Cloudflare R2, and local fallback.
"""
import os
import threading
from typing import List

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# 3-Tier Directory Layout
DB_DIR = os.path.join(BASE_DIR, "db")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Data Stores
USERS_FILE = os.path.join(DB_DIR, "users.json")
TOKEN_LOG_FILE = os.path.join(DB_DIR, "token_usage_log.json")
CACHE_FILE = os.path.join(DB_DIR, "validation_results_cache.json")
PROJECTS_DIR = os.path.join(DB_DIR, "projects")
REPORTS_DIR = os.path.join(DB_DIR, "reports")
CLIENTS_DIR = os.path.join(DB_DIR, "clients")
RULES_DIR = os.path.join(CLIENTS_DIR, "optus", "rules")
REFERENCE_FILES_DIR = os.path.join(DB_DIR, "reference_files")
DRAWINGS_DIR = os.path.join(DB_DIR, "drawings")

# Fallback paths
if not os.path.exists(RULES_DIR):
    alt_rules = os.path.join(BASE_DIR, "clients", "optus", "rules")
    if os.path.exists(alt_rules):
        RULES_DIR = alt_rules

if not os.path.exists(REFERENCE_FILES_DIR):
    alt_refs = os.path.join(BASE_DIR, "reference_files")
    if os.path.exists(alt_refs):
        REFERENCE_FILES_DIR = alt_refs
    elif os.path.exists(os.path.join(BASE_DIR, "qaInput", "reference_package")):
        REFERENCE_FILES_DIR = os.path.join(BASE_DIR, "qaInput", "reference_package")

if not os.path.exists(DRAWINGS_DIR):
    alt_dwg = os.path.join(BASE_DIR, "drawings")
    if os.path.exists(alt_dwg):
        DRAWINGS_DIR = alt_dwg
    elif os.path.exists(os.path.join(BASE_DIR, "qaInput", "primary_drawing")):
        DRAWINGS_DIR = os.path.join(BASE_DIR, "qaInput", "primary_drawing")

# Ensure essential runtime directories exist
for d in [DB_DIR, PROJECTS_DIR, REPORTS_DIR, FRONTEND_DIR, STATIC_DIR]:
    os.makedirs(d, exist_ok=True)

# Security & CORS Settings (includes Vercel domains)
CORS_ORIGIN_ENV = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS: List[str] = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.vercel.app"
]
if CORS_ORIGIN_ENV:
    CORS_ORIGINS.extend([o.strip() for o in CORS_ORIGIN_ENV.split(",") if o.strip()])

# Concurrency & Memory Guard (Render 512MB RAM optimization)
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "2"))
LLM_SEMAPHORE = threading.Semaphore(LLM_CONCURRENCY)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "150"))

# Cloudflare R2 Settings
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_R2_ACCESS_KEY_ID = os.getenv("CF_R2_ACCESS_KEY_ID", "")
CF_R2_SECRET_ACCESS_KEY = os.getenv("CF_R2_SECRET_ACCESS_KEY", "")
CF_R2_BUCKET_NAME = os.getenv("CF_R2_BUCKET_NAME", "telecos-drawings")

# Database Configuration (Neon PostgreSQL or SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# LLM & Inference Settings
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4:cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
