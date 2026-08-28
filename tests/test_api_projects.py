"""
Tests for Project Workspaces, Renaming, Deletion, Drawing Ingestion, and Reference Categorization.
"""
import io
import uuid
import pytest
from backend.services.project_service import classify_file

def test_classify_file_rules():
    """Tests file classification taxonomy for companion engineering documents."""
    assert classify_file("H8097_AUSTINS FERRY_FC_05122025_Final PDF After QC validation.pdf") == "FC_Drawing"
    assert classify_file("H8097_Austins Ferry_FR_20251110.pdf") == "FR"
    assert classify_file("H8097_RLM_Phase2.pdf") == "RLM"
    assert classify_file("H8097_Mount_Certificate_SC184419.pdf") == "Mount_Certificate"
    assert classify_file("Pole_Certificate_292920.pdf") == "Pole_Certificate"
    assert classify_file("Structural_Certificate_Optus.pdf") == "Structural_Certificate"
    assert classify_file("SDV_Photo_Antenna_Front.jpg") == "SDV_Photos"
    assert classify_file("Form_A_Radiation_Hazard.pdf") == "Form_A"
    assert classify_file("Form_B_EME_Report.pdf") == "Form_B"
    assert classify_file("OSD-100_Standard_Signage.pdf") == "OSD"

def test_list_projects(client):
    """Tests GET /api/projects returns the baseline projects including H8097."""
    res = client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    p_ids = [p["id"] for p in data]
    assert "H8097" in p_ids

def test_create_rename_and_delete_project(client):
    """Tests creating an isolated workspace, renaming it, and deleting it."""
    test_pid = f"TEST{uuid.uuid4().hex[:4].upper()}"
    
    # 1. Create
    res_create = client.post("/api/projects", json={
        "id": test_pid,
        "name": f"Test Site {test_pid}",
        "structure_type": "ROOFTOP MOUNT",
        "drawing_revision": "FOR CONSTRUCTION (Rev 1.0)"
    })
    assert res_create.status_code == 200
    assert res_create.json()["project"]["id"] == test_pid

    # 2. Rename / Update
    res_rename = client.post(f"/api/projects/{test_pid}/update", json={
        "name": f"Renamed Site {test_pid}",
        "structure_type": "SELF SUPPORTING LATTICE TOWER",
        "drawing_revision": "FOR CONSTRUCTION (Rev 2.0)"
    })
    assert res_rename.status_code == 200
    updated = res_rename.json()["project"]
    assert updated["name"] == f"Renamed Site {test_pid}"
    assert updated["structure_type"] == "SELF SUPPORTING LATTICE TOWER"
    assert updated["drawing_revision"] == "FOR CONSTRUCTION (Rev 2.0)"

    # 3. Verify in project list
    res_list = client.get("/api/projects")
    matched = [p for p in res_list.json() if p["id"] == test_pid]
    assert len(matched) == 1
    assert matched[0]["name"] == f"Renamed Site {test_pid}"

    # 4. Upload a test reference file
    fake_pdf = b"%PDF-1.4 Fake reference content for testing"
    res_up = client.post(
        f"/api/projects/{test_pid}/upload_references",
        files=[("files", ("test_cert_mount.pdf", io.BytesIO(fake_pdf), "application/pdf"))]
    )
    assert res_up.status_code == 200
    assert res_up.json()["total_references"] >= 1

    # Verify package files
    res_pkg = client.get(f"/api/projects/{test_pid}/package_files")
    assert res_pkg.status_code == 200
    assert res_pkg.json()["total_reference_files"] >= 1

    # 5. Delete project
    res_del = client.delete(f"/api/projects/{test_pid}")
    assert res_del.status_code == 200

    # Verify project is gone
    res_list_after = client.get("/api/projects")
    assert not any(p["id"] == test_pid for p in res_list_after.json())

def test_cannot_delete_baseline_h8097(client):
    """Tests that deleting baseline H8097 is safely rejected with HTTP 400."""
    res_del = client.delete("/api/projects/H8097")
    assert res_del.status_code == 400
    assert "Cannot delete baseline project" in res_del.json()["detail"]

def test_get_package_files_h8097(client):
    """Tests GET /api/package_files?project_id=H8097 returns indexed sheets and companion references."""
    res = client.get("/api/package_files?project_id=H8097")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == "H8097"
    assert "primary_drawing" in data
    assert len(data["primary_drawing"]["sheets_detected"]) >= 10
    assert data["total_reference_files"] >= 500
    assert len(data["reference_categories"]) >= 5
