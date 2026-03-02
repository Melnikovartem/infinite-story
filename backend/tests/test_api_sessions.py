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
    # Cleanup after test - check both old and new locations
    test_story_dir = Path(".infinite_story_data") / "test_story"
    if test_story_dir.exists():
        # Clean old location (runner_state.json)
        old_file = test_story_dir / "runner_state.json"
        if old_file.exists():
            old_file.unlink()
        
        # Clean new location (sessionstate/*.json)
        sessionstate_dir = test_story_dir / "sessionstate"
        if sessionstate_dir.exists():
            for f in sessionstate_dir.glob("*.json"):
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
            "id": "session_1",
            "story_id": "test_story",
            "user_id": "user_1",
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "visited_choices": []
        }
        
        response = client.post("/api/sessions/save", json=session_data)
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "saved_at" in response.json()
    
    def test_load_session(self):
        """Test loading a saved session."""
        # First save a session
        session_data = {
            "id": "session_2",
            "story_id": "test_story",
            "user_id": "user_1",
            "current_segment_id": "segment_2",
            "visited_segments": ["segment_1", "segment_2"],
            "visited_choices": ["choice_1"]
        }
        
        client.post("/api/sessions/save", json=session_data)
        
        # Now load it
        response = client.get("/api/sessions/test_story/session_2")
        assert response.status_code == 200
        assert response.json()["found"] is True
        assert response.json()["session"]["story_id"] == "test_story"
        assert response.json()["session"]["current_segment_id"] == "segment_2"
        assert response.json()["session"]["user_id"] == "user_1"
    
    def test_load_nonexistent_session(self):
        """Test loading a session that doesn't exist."""
        response = client.get("/api/sessions/test_story/nonexistent_session")
        assert response.status_code == 200
        assert response.json()["found"] is False
    
    def test_delete_session(self):
        """Test deleting a session."""
        # First save a session
        session_data = {
            "id": "session_3",
            "story_id": "test_story",
            "user_id": "user_1",
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "visited_choices": []
        }
        
        client.post("/api/sessions/save", json=session_data)
        
        # Delete it
        response = client.delete("/api/sessions/test_story/session_3")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify it's gone
        response = client.get("/api/sessions/test_story/session_3")
        assert response.json()["found"] is False
    
    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        response = client.delete("/api/sessions/test_story/nonexistent_session")
        assert response.status_code == 404
