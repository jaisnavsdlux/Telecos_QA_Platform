"""
Tests for Compliance Reports Stack, High-Res Page Rendering, and PDF Downloads.
"""
import pytest

def test_get_reports_stack_h8097(client):
    """Tests GET /api/reports?project_id=H8097 returns reports in LIFO order."""
    res = client.get("/api/reports?project_id=H8097")
    assert res.status_code == 200
    reports = res.json()
    assert isinstance(reports, list)
    assert len(reports) >= 1

    top = reports[0]
    assert "filename" in top
    assert "verdict_summary" in top
    assert "pages" in top
    assert top["pages"] >= 1

def test_get_report_page_image(client):
    """Tests GET /api/reports/{id}/page/1 renders PNG bytes at 150 DPI."""
    reports = client.get("/api/reports?project_id=H8097").json()
    top_id = reports[0]["id"]

    res_page = client.get(f"/api/reports/{top_id}/page/1?project_id=H8097")
    assert res_page.status_code == 200
    assert res_page.headers["content-type"] == "image/png"
    assert len(res_page.content) > 10000

def test_download_latest_report(client):
    """Tests GET /download_latest_report streams a valid PDF."""
    res_dl = client.get("/download_latest_report?project_id=H8097")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    assert len(res_dl.content) > 5000
