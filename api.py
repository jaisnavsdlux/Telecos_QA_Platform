"""
Strelza Telecos Drawing QA Validator — Main FastAPI Application.
Modular, layered architecture with decoupled routers, Neon Postgres DB, and Cloudflare R2 storage.
"""
import os
import sys
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

from backend.config import FRONTEND_DIR, STATIC_DIR, CORS_ORIGINS
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

# Constrained CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

# Mount frontend UI assets with zero-caching policy
mount_dir = FRONTEND_DIR if os.path.exists(FRONTEND_DIR) else STATIC_DIR
if os.path.exists(mount_dir):
    app.mount("/static", NoCacheStaticFiles(directory=mount_dir, html=True), name="static")
    app.mount("/assets", NoCacheStaticFiles(directory=mount_dir, html=True), name="assets")

@app.get("/")
def root():
    """Redirects root URL to the authentication portal."""
    return RedirectResponse(url="/static/index.html")

# Backward compatibility exports
__all__ = ["app", "classify_file"]