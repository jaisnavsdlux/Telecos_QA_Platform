"""
Tests for Telemetry, Token Accounting, and Dashboard Scorecard Metrics.
"""
import pytest

def test_dashboard_metrics_h8097(client):
    """Tests GET /api/dashboard_metrics?project_id=H8097 returns consistent scorecard."""
    res = client.get("/api/dashboard_metrics?project_id=H8097")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"
    assert data["target_site"]["site_id"] == "H8097"
    assert "verdicts" in data
    v = data["verdicts"]
    assert "PASS" in v
    assert "FAIL" in v
    assert "NOT_APPLICABLE" in v
    assert "telemetry" in data
    assert data["telemetry"]["input_tokens"] > 0
    assert data["telemetry"]["output_tokens"] > 0

def test_unvalidated_project_metrics(client):
    """Tests metrics for a newly created clean project return 0% scorecard gracefully."""
    res = client.get("/api/dashboard_metrics?project_id=BRAND_NEW_UNVALIDATED_SITE")
    assert res.status_code == 200
    data = res.json()
    assert data["verdicts"]["PASS"] == 0
    assert data["compliance_score"] == "0.0%"
