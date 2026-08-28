"""
Pytest configuration and test client fixtures.
"""
import os
import pytest
from fastapi.testclient import TestClient

from api import app

@pytest.fixture(scope="session")
def client():
    """Provides a TestClient fixture for FastAPI endpoints."""
    with TestClient(app) as c:
        yield c
