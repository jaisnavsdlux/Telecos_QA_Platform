"""
Validation & Inference Runner Service.
Manages the real-time AI compliance audit execution state, pause/resume lifecycle,
and background execution threads.
"""
import time
import threading
from typing import Dict, Any, Optional

_AUDIT_LOCK = threading.RLock()
EXECUTION_PAUSE_EVENT = threading.Event()
EXECUTION_PAUSE_EVENT.set()

LOCAL_AUDIT_STATE: Dict[str, Any] = {
    "status": "idle",
    "progress": 0,
    "current_rule": 0,
    "total_rules": 72,
    "current_rule_code": "",
    "current_rule_name": "",
    "elapsed_seconds": 0.0,
    "latest_result": None,
    "verdicts": {"PASS": 0, "FAIL": 0, "UNCLEAR": 0, "NOT_APPLICABLE": 0},
    "rule_results": {},
    "error": None,
    "latest_report_file": None
}

class ValidationService:
    @staticmethod
    def get_state() -> Dict[str, Any]:
        """Returns the current execution state snapshot."""
        with _AUDIT_LOCK:
            return dict(LOCAL_AUDIT_STATE)

    @staticmethod
    def pause() -> Dict[str, Any]:
        """Pauses the active validation runner."""
        with _AUDIT_LOCK:
            if LOCAL_AUDIT_STATE["status"] == "running":
                LOCAL_AUDIT_STATE["status"] = "paused"
                EXECUTION_PAUSE_EVENT.clear()
                return {"status": "paused", "message": "Audit execution paused."}
            return {"status": LOCAL_AUDIT_STATE["status"], "message": "Runner is not currently running."}

    @staticmethod
    def resume() -> Dict[str, Any]:
        """Resumes a paused validation runner."""
        with _AUDIT_LOCK:
            if LOCAL_AUDIT_STATE["status"] == "paused":
                LOCAL_AUDIT_STATE["status"] = "running"
                EXECUTION_PAUSE_EVENT.set()
                return {"status": "running", "message": "Audit execution resumed."}
            return {"status": LOCAL_AUDIT_STATE["status"], "message": "Runner is not currently paused."}

    @staticmethod
    def stop() -> Dict[str, Any]:
        """Stops and resets the validation runner state."""
        with _AUDIT_LOCK:
            LOCAL_AUDIT_STATE["status"] = "idle"
            LOCAL_AUDIT_STATE["progress"] = 0
            EXECUTION_PAUSE_EVENT.set()
            return {"status": "idle", "message": "Execution reset to idle."}

    @staticmethod
    def run_audit_background(project_id: str = "H8097") -> None:
        """Executes full validation in background thread."""
        with _AUDIT_LOCK:
            LOCAL_AUDIT_STATE["status"] = "running"
            LOCAL_AUDIT_STATE["progress"] = 0
            LOCAL_AUDIT_STATE["current_rule"] = 0
            LOCAL_AUDIT_STATE["rule_results"] = {}
            LOCAL_AUDIT_STATE["error"] = None
        EXECUTION_PAUSE_EVENT.set()

        try:
            def progress_callback(current, total, current_res=None, elapsed=0.0):
                EXECUTION_PAUSE_EVENT.wait()
                with _AUDIT_LOCK:
                    LOCAL_AUDIT_STATE["current_rule"] = current
                    LOCAL_AUDIT_STATE["total_rules"] = total
                    LOCAL_AUDIT_STATE["progress"] = round((current / total) * 100, 1)
                    LOCAL_AUDIT_STATE["elapsed_seconds"] = round(elapsed, 1)

                    if current_res:
                        r_id = current_res.get("rule_id", f"R{current:03d}")
                        r_verdict = current_res.get("verdict", "PASS").upper()
                        r_obs = current_res.get("reasoning") or current_res.get("observation") or current_res.get("reason", "")
                        LOCAL_AUDIT_STATE["current_rule_code"] = r_id
                        LOCAL_AUDIT_STATE["current_rule_name"] = current_res.get("rule_text", r_id)
                        LOCAL_AUDIT_STATE["latest_result"] = {
                            "code": r_id,
                            "verdict": r_verdict,
                            "observation": r_obs,
                            "confidence": current_res.get("confidence", 0.95)
                        }
                        LOCAL_AUDIT_STATE["rule_results"][r_id] = LOCAL_AUDIT_STATE["latest_result"]

                        v_counts = {"PASS": 0, "FAIL": 0, "UNCLEAR": 0, "NOT_APPLICABLE": 0}
                        for r in LOCAL_AUDIT_STATE["rule_results"].values():
                            v = r.get("verdict", "PASS")
                            if v in v_counts:
                                v_counts[v] += 1
                            else:
                                v_counts["PASS"] += 1
                        LOCAL_AUDIT_STATE["verdicts"] = v_counts

            from backend.run_full_package_validation import main as run_pkg
            run_pkg(project_id=project_id, progress_callback=progress_callback)

            with _AUDIT_LOCK:
                LOCAL_AUDIT_STATE["status"] = "completed"
                LOCAL_AUDIT_STATE["progress"] = 100
                LOCAL_AUDIT_STATE["latest_report_file"] = "report_full_package.pdf"
        except Exception as e:
            with _AUDIT_LOCK:
                LOCAL_AUDIT_STATE["status"] = "error"
                LOCAL_AUDIT_STATE["error"] = str(e)
