"""Tests for progress API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from pathlib import Path
import shutil
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
        shutil.rmtree(test_story_dir, ignore_errors=True)


class TestProgressEndpoints:
    """Test progress tracking endpoints."""
    
    def test_get_progress(self):
        """Test getting progress for a story."""
        # Create and save a session
        session = SessionState(
            id="session_001",
            story_id="test_story",
            user_id="test_user",
            current_segment_id="segment_5",
            visited_segments=["segment_1", "segment_2", "segment_3", "segment_4", "segment_5"]
        )
        session.save()
        
        # Get progress - endpoint requires both story_id and session_id
        response = client.get("/api/progress/test_story/session_001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["story_id"] == "test_story"
        assert data["current_segment_id"] == "segment_5"
        assert data["scene_number"] == 5
        assert data["total_visited"] == 5
        assert data["elapsed_seconds"] >= 0
        assert "elapsed_formatted" in data
        assert "reading_pace_minutes_per_scene" in data
    
    def test_get_progress_nonexistent_story(self):
        """Test getting progress for story with no session."""
        response = client.get("/api/progress/nonexistent_story/nonexistent_session")
        assert response.status_code == 404
    
    def test_get_progress_with_time_estimate(self):
        """Test getting progress with estimated total scenes."""
        session = SessionState(
            id="session_002",
            story_id="test_story",
            user_id="test_user",
            current_segment_id="segment_3",
            visited_segments=["segment_1", "segment_2", "segment_3"]
        )
        session.save()
        
        response = client.get(
            "/api/progress/test_story/session_002?estimated_total_scenes=10"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_visited"] == 3
    
    def test_get_progress_without_estimate(self):
        """Test getting progress without total scene estimate."""
        session = SessionState(
            id="session_003",
            story_id="test_story",
            user_id="test_user",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        session.save()
        
        response = client.get("/api/progress/test_story/session_003")
        assert response.status_code == 200
        
        data = response.json()
        assert data["estimated_remaining_seconds"] is None
    
    def test_get_progress_reading_pace(self):
        """Test that reading pace is calculated."""
        session = SessionState(
            id="session_004",
            story_id="test_story",
            user_id="test_user",
            current_segment_id="segment_5",
            visited_segments=["s1", "s2", "s3", "s4", "s5"]
        )
        session.save()
        
        response = client.get("/api/progress/test_story/session_004")
        assert response.status_code == 200
        
        data = response.json()
        assert data["reading_pace_minutes_per_scene"] >= 0
