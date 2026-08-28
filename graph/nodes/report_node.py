import os
from typing import Dict, Any
from graph.state_schema import GraphState
from report_generator import generate_report

def report_node(state: GraphState) -> Dict[str, Any]:
    """
    Node: Generate the final PDF report.
    """
    job_id = state.get("job_id", "unknown")
    results = state.get("validation_results", [])
    
    # Define report names
    filename = f"report_{job_id}.pdf"
    report_path = os.path.join("jobs", job_id, filename)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    print(f"[report] Generating PDF: {report_path}")

    # Results expected by generator as a dict with 'results' key
    results_payload = {"results": results}
    
    try:
        generate_report(results_payload, report_path, filename)
    except Exception as e:
        print(f"[report] Error generating PDF: {e}")
        return {"status": "failed", "error": f"PDF generation error: {e}"}

    print(f"[report] Successfully generated report for job {job_id}")

    return {
        "status": "complete",
        "metadata": {**state.get("metadata", {}), "report_url": report_path}
    }
