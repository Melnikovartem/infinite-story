"""Basic tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint returns 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data


def test_status_endpoint(client):
    """Test status endpoint returns server info."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "timestamp" in data
    assert "debug" in data
    assert "data_dir" in data


def test_docs_available(client):
    """Test that API docs are available."""
    response = client.get("/api/docs")
    assert response.status_code == 200
