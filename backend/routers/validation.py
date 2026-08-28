"""
Validation & Inference Controls Router.
Provides endpoints to trigger, poll, pause, resume, and stop validation runs.
"""
from fastapi import APIRouter, BackgroundTasks
from backend.services.validation_service import ValidationService

router = APIRouter(tags=["Validation Controls"])

@router.get("/trigger_local_audit")
async def trigger_local_audit(background_tasks: BackgroundTasks):
    """Triggers the full 71-rule audit using the host PC's resources and Gemma-4 model."""
    state = ValidationService.get_state()
    if state["status"] == "running":
        return {"status": "already_running", "message": "Audit is already in progress on the host PC."}

    background_tasks.add_task(ValidationService.run_audit_background)
    return {"status": "started", "message": "Audit initiated on host PC."}

@router.get("/audit_status")
def get_audit_status():
    """Polls real-time inference execution status."""
    return ValidationService.get_state()

@router.post("/api/execution/pause")
@router.get("/api/execution/pause")
def pause_execution():
    """Pauses the active validation runner."""
    return ValidationService.pause()

@router.post("/api/execution/resume")
@router.get("/api/execution/resume")
def resume_execution():
    """Resumes a paused validation runner."""
    return ValidationService.resume()

@router.post("/api/execution/stop")
@router.get("/api/execution/stop")
def stop_execution():
    """Stops and resets the execution state."""
    return ValidationService.stop()
