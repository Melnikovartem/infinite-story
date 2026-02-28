"""Tests for session API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from pathlib import Path
from app.main import app
from app.models.session_state import SessionState

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up test sessions."""
    yield
    # Cleanup after test
    test_story_dir = Path(".infinite_story_data") / "test_story"
    if test_story_dir.exists():
        for f in test_story_dir.glob("*.json"):
            f.unlink()


class TestSessionEndpoints:
    """Test session management endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_save_session(self):
        """Test saving a session."""
        session_data = {
            "story_id": "test_story",
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session_data)
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "saved_at" in response.json()
    
    def test_load_session(self):
        """Test loading a saved session."""
        # First save a session
        session_data = {
            "story_id": "test_story",
            "current_segment_id": "segment_2",
            "visited_segments": ["segment_1", "segment_2"],
            "scene_counter": 2,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        client.post("/api/sessions/save", json=session_data)
        
        # Now load it
        response = client.get("/api/sessions/test_story")
        assert response.status_code == 200
        assert response.json()["found"] is True
        assert response.json()["session"]["story_id"] == "test_story"
        assert response.json()["session"]["current_segment_id"] == "segment_2"
    
    def test_load_nonexistent_session(self):
        """Test loading a session that doesn't exist."""
        response = client.get("/api/sessions/nonexistent_story")
        assert response.status_code == 200
        assert response.json()["found"] is False
    
    def test_delete_session(self):
        """Test deleting a session."""
        # First save a session
        session_data = {
            "story_id": "test_story",
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        client.post("/api/sessions/save", json=session_data)
        
        # Delete it
        response = client.delete("/api/sessions/test_story")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify it's gone
        response = client.get("/api/sessions/test_story")
        assert response.json()["found"] is False
    
    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        response = client.delete("/api/sessions/nonexistent_story")
        assert response.status_code == 404
