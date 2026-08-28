"""
Tests for Checkpoint Catalog, Rules Filtering, and Evidence Observations.
"""
import pytest

def test_get_checkpoints_catalog(client):
    """Tests GET /api/checkpoints returns all active Optus BA rules."""
    res = client.get("/api/checkpoints")
    assert res.status_code == 200
    rules = res.json()
    assert isinstance(rules, list)
    assert len(rules) >= 71

    # Check key rule codes exist
    codes = [r["code"] for r in rules]
    assert "R002" in codes
    assert "R010" in codes
    assert "R014" in codes
    assert "R030" in codes
    assert "R064" in codes

def test_checkpoints_data_compatibility(client):
    """Tests legacy GET /checkpoints_data endpoint."""
    res = client.get("/checkpoints_data")
    assert res.status_code == 200
    assert len(res.json()) >= 71

def test_filter_rules_by_category(client):
    """Tests filtering rules by category."""
    res_cad = client.get("/api/rules?category=CAD%20Standard")
    assert res_cad.status_code == 200
    for r in res_cad.json():
        assert r["category"].lower() == "cad standard"
