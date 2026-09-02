"""
Strelza Telecos Drawing QA Validator — Main FastAPI Application.
Modular, layered architecture with decoupled routers, Neon Postgres DB, and Cloudflare R2 / Backblaze B2 storage.
"""
import os
import sys
import types

# Ensure module resolution when running inside /app container or root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

if "backend" not in sys.modules and os.path.exists(os.path.join(current_dir, "config.py")):
    backend_pkg = types.ModuleType("backend")
    backend_pkg.__path__ = [current_dir]
    sys.modules["backend"] = backend_pkg

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import Response, RedirectResponse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.config import FRONTEND_DIR, STATIC_DIR, CORS_ORIGINS, BASE_DIR
from backend.database.init_db import init_db
from backend.services.project_service import classify_file
from backend.routers.health import router as health_router
from backend.routers.auth import router as auth_router
from backend.routers.projects import router as projects_router
from backend.routers.checkpoints import router as checkpoints_router
from backend.routers.validation import router as validation_router
from backend.routers.reports import router as reports_router
from backend.routers.telemetry import router as telemetry_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQL database tables on startup
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization notice: {e}")
    yield

class NoCacheStaticFiles(StaticFiles):
    """Static file handler that enforces immediate cache invalidation for frontend assets."""
    def file_response(self, *args, **kwargs) -> Response:
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

app = FastAPI(
    title="Strelza Telecos Drawing QA & Compliance API",
    version="2.3.0",
    description="Production-grade AI compliance audit suite for For-Construction telecom drawings.",
    lifespan=lifespan
)

# Production CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(checkpoints_router)
app.include_router(validation_router)
app.include_router(reports_router)
app.include_router(telemetry_router)

# Mount frontend UI assets if present locally
for static_candidate in [STATIC_DIR, FRONTEND_DIR, os.path.join(BASE_DIR, "static"), os.path.join(BASE_DIR, "frontend")]:
    if os.path.exists(static_candidate):
        app.mount("/static", NoCacheStaticFiles(directory=static_candidate, html=True), name="static")
        app.mount("/assets", NoCacheStaticFiles(directory=static_candidate, html=True), name="assets")
        break

@app.get("/")
@app.head("/")
def root():
    """API Gateway root status endpoint — redirects to login/dashboard UI."""
    return RedirectResponse(url="/static/index.html")

# Backward compatibility exports
__all__ = ["app", "classify_file"]