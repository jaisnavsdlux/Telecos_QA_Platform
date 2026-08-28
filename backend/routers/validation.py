"""
Validation & Inference Controls Router.
Provides endpoints to trigger, poll, pause, resume, and stop validation runs.
"""
from fastapi import APIRouter, BackgroundTasks
from backend.services.validation_service import ValidationService

router = APIRouter(tags=["Validation Controls"])

@router.get("/trigger_local_audit")
@router.post("/trigger_local_audit")
@router.get("/api/validation/run")
@router.post("/api/validation/run")
async def trigger_local_audit(background_tasks: BackgroundTasks, project_id: str = "H8097"):
    """Triggers the full 71-rule compliance audit with real-time streaming feedback."""
    state = ValidationService.get_state()
    if state["status"] == "running":
        return {"status": "already_running", "message": "Audit is already in progress for this workspace."}

    background_tasks.add_task(ValidationService.run_audit_background, project_id=project_id)
    return {"status": "started", "message": f"Audit initiated for project {project_id}."}

@router.get("/audit_status")
@router.get("/api/validation/status")
def get_audit_status():
    """Polls real-time inference execution status and scorecards."""
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
