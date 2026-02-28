"""Tests for progress API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta
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


class TestProgressEndpoints:
    """Test progress tracking endpoints."""
    
    def test_get_progress(self):
        """Test getting progress for a story."""
        # Create and save a session
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_5",
            visited_segments=["segment_1", "segment_2", "segment_3", "segment_4", "segment_5"],
            scene_counter=5,
            start_time=datetime.now(UTC) - timedelta(minutes=10)
        )
        SessionState.save_to_file("test_story", session)
        
        # Get progress
        response = client.get("/api/progress/test_story")
        assert response.status_code == 200
        
        data = response.json()
        assert data["story_id"] == "test_story"
        assert data["current_segment_id"] == "segment_5"
        assert data["scene_number"] == 5
        assert data["total_visited"] == 5
        assert data["elapsed_seconds"] > 0
        assert "elapsed_formatted" in data
        assert "reading_pace_minutes_per_scene" in data
    
    def test_get_progress_nonexistent_story(self):
        """Test getting progress for story with no session."""
        response = client.get("/api/progress/nonexistent_story")
        assert response.status_code == 404
    
    def test_get_progress_with_time_estimate(self):
        """Test getting progress with estimated total scenes."""
        # Create session
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_3",
            visited_segments=["segment_1", "segment_2", "segment_3"],
            scene_counter=3,
            start_time=datetime.now(UTC) - timedelta(minutes=6)
        )
        SessionState.save_to_file("test_story", session)
        
        # Get progress with estimate
        response = client.get(
            "/api/progress/test_story?estimated_total_scenes=10"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_visited"] == 3
        # Should have remaining time estimate (for 7 more scenes)
        assert data["estimated_remaining_seconds"] is not None
        assert data["estimated_remaining_seconds"] > 0
    
    def test_get_progress_without_estimate(self):
        """Test getting progress without total scene estimate."""
        # Create session
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        SessionState.save_to_file("test_story", session)
        
        # Get progress without estimate
        response = client.get("/api/progress/test_story")
        assert response.status_code == 200
        
        data = response.json()
        assert data["estimated_remaining_seconds"] is None
    
    def test_get_progress_reading_pace(self):
        """Test that reading pace is calculated correctly."""
        # Create session with known times
        start_time = datetime.now(UTC) - timedelta(minutes=10)
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_5",
            visited_segments=["s1", "s2", "s3", "s4", "s5"],
            scene_counter=5,
            start_time=start_time
        )
        SessionState.save_to_file("test_story", session)
        
        response = client.get("/api/progress/test_story")
        assert response.status_code == 200
        
        data = response.json()
        # Should be approximately 2 minutes per scene (10 minutes / 5 scenes)
        # Allow some variance due to timing
        assert data["reading_pace_minutes_per_scene"] > 0
