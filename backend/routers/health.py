"""
Health & Uptime Keep-Alive Router.
Lightweight ping endpoint for UptimeRobot and deployment health checks.
"""
import time
from fastapi import APIRouter

router = APIRouter(tags=["Health & Monitoring"])
START_TIME = time.time()

@router.get("/api/health")
def health_check():
    """Returns uptime telemetry to keep the Render free tier container active."""
    return {
        "status": "healthy",
        "service": "strelza-telecos-backend",
        "uptime_seconds": round(time.time() - START_TIME, 1)
    }
