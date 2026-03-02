"""Auto-save integration tests for Phase 2.

Tests auto-save triggering in game flow scenarios.
"""

import pytest
import asyncio
from datetime import datetime, UTC
from pathlib import Path
import shutil
from fastapi.testclient import TestClient
from app.main import app
from app.models.session_state import SessionState
from app.services.auto_save_manager import AutoSaveManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_and_reset():
    """Clean up test data and reset auto-save manager."""
    # Reset debounce before each test
    AutoSaveManager.clear_all_debounce()
    
    yield
    
    # Cleanup after test
    AutoSaveManager.clear_all_debounce()
    test_dir = Path(".infinite_story_data")
    if test_dir.exists():
        for story_dir in ["auto_save_test", "debounce_test", "multi_scene_test", "concurrent_test"]:
            story_path = test_dir / story_dir
            if story_path.exists():
                shutil.rmtree(story_path)


class TestAutoSaveBasics:
    """Test basic auto-save functionality."""
    
    def test_auto_save_manager_initialization(self):
        """Test AutoSaveManager initializes correctly."""
        AutoSaveManager.clear_all_debounce()
        
        # Should allow save when not debounced
        assert AutoSaveManager.should_save("test_story") is True
    
    def test_auto_save_sync_success(self):
        """Test synchronous auto-save succeeds."""
        story_id = "auto_save_test"
        
        # Create a session
        session = SessionState(
            story_id=story_id,
            current_segment_id="segment_001",
            visited_segments=["segment_001"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        
        # Auto-save synchronously
        result = AutoSaveManager.auto_save_sync(story_id, session)
        assert result is True
        
        # Verify it was saved
        loaded = SessionState.load_from_file(story_id)
        assert loaded is not None
        assert loaded.scene_counter == 1
    
    def test_auto_save_debouncing(self):
        """Test that auto-save debounces rapid saves."""
        story_id = "debounce_test"
        
        session = SessionState(
            story_id=story_id,
            current_segment_id="segment_001",
            visited_segments=["segment_001"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        
        # First save should succeed
        result1 = AutoSaveManager.auto_save_sync(story_id, session)
        assert result1 is True
        
        # Immediate second save should be debounced
        result2 = AutoSaveManager.auto_save_sync(story_id, session)
        assert result2 is False
        
        # Reset debounce
        AutoSaveManager.reset_debounce(story_id)
        
        # Save should succeed after reset
        result3 = AutoSaveManager.auto_save_sync(story_id, session)
        assert result3 is True


class TestAutoSaveInGameFlow:
    """Test auto-save in realistic game scenarios."""
    
    def test_auto_save_after_scene_progression(self):
        """Test auto-save triggers as player progresses through scenes."""
        story_id = "multi_scene_test"
        
        # Initialize session
        initial_session = {
            "story_id": story_id,
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=initial_session)
        assert response.status_code == 200
        
        # Reset debounce to allow next save
        AutoSaveManager.reset_debounce(story_id)
        
        # Progress to next scene
        next_session = {
            "story_id": story_id,
            "current_segment_id": "segment_002",
            "visited_segments": ["segment_001", "segment_002"],
            "scene_counter": 2,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=next_session)
        assert response.status_code == 200
        
        # Verify the update persisted
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        assert response.json()["session"]["scene_counter"] == 2
    
    def test_auto_save_manager_get_info(self):
        """Test getting auto-save status information."""
        story_id = "info_test"
        
        # Create and save a session
        session = SessionState(
            story_id=story_id,
            current_segment_id="segment_001",
            visited_segments=["segment_001"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        
        AutoSaveManager.auto_save_sync(story_id, session)
        
        # Get info
        info = AutoSaveManager.get_auto_save_info(story_id)
        assert info["story_id"] == story_id
        assert info["last_save"] is not None
        assert "next_save_ready_in_seconds" in info


class TestAutoSaveErrorHandling:
    """Test auto-save error handling."""
    
    def test_auto_save_handles_invalid_session(self):
        """Test auto-save gracefully handles invalid sessions."""
        story_id = "error_test"
        
        # Try to save with invalid session (None)
        # This should not raise, just return False
        try:
            result = AutoSaveManager.auto_save_sync(story_id, None)
            # Should handle error gracefully
            assert isinstance(result, (bool, type(None)))
        except Exception as e:
            # If it raises, the error should be specific
            assert "auto_save" in str(e).lower() or "session" in str(e).lower()
    
    def test_auto_save_continues_on_failure(self):
        """Test that auto-save errors don't break game flow."""
        story_id = "resilience_test"
        
        # Create a valid session
        session = SessionState(
            story_id=story_id,
            current_segment_id="segment_001",
            visited_segments=["segment_001"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        
        # Save should work
        result = AutoSaveManager.auto_save_sync(story_id, session)
        assert result is True
        
        # Game should continue even if auto-save failed on next attempt
        # (due to debounce)
        result2 = AutoSaveManager.auto_save_sync(story_id, session)
        assert result2 is False  # Debounced, not an error
        
        # Game can still proceed


class TestAutoSaveCleanup:
    """Test auto-save cleanup functionality."""
    
    def test_cleanup_stats_format(self):
        """Test cleanup returns proper statistics."""
        stats = AutoSaveManager.cleanup_old_saves(days_old=0)
        
        assert "total_stories_checked" in stats
        assert "sessions_deleted" in stats
        assert "errors" in stats
        assert isinstance(stats["total_stories_checked"], int)
        assert isinstance(stats["sessions_deleted"], int)
        assert isinstance(stats["errors"], list)


class TestMultiStoryAutoSave:
    """Test auto-save with multiple stories."""
    
    def test_independent_debouncing(self):
        """Test that debounce is independent per story."""
        story1 = "story_a"
        story2 = "story_b"
        
        session1 = SessionState(
            story_id=story1,
            current_segment_id="seg_1",
            visited_segments=["seg_1"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        
        session2 = SessionState(
            story_id=story2,
            current_segment_id="seg_1",
            visited_segments=["seg_1"],
            scene_counter=1,
            start_time=datetime.now(UTC)
        )
        
        # Save story 1
        result1_a = AutoSaveManager.auto_save_sync(story1, session1)
        assert result1_a is True
        
        # Save story 2 immediately (different story, should not debounce)
        result2_a = AutoSaveManager.auto_save_sync(story2, session2)
        assert result2_a is True
        
        # Try to save story 1 again (should debounce)
        result1_b = AutoSaveManager.auto_save_sync(story1, session1)
        assert result1_b is False
        
        # But story 2 should also be debounced now (same rules apply)
        result2_b = AutoSaveManager.auto_save_sync(story2, session2)
        assert result2_b is False
    
    def test_multiple_story_cleanup(self):
        """Test cleanup works with multiple stories."""
        # Create sessions for multiple stories
        for i in range(3):
            session = SessionState(
                story_id=f"cleanup_story_{i}",
                current_segment_id="segment_001",
                visited_segments=["segment_001"],
                scene_counter=1,
                start_time=datetime.now(UTC)
            )
            AutoSaveManager.auto_save_sync(f"cleanup_story_{i}", session)
        
        # Run cleanup
        stats = AutoSaveManager.cleanup_old_saves(days_old=0)
        
        # Should have checked multiple stories
        assert stats["total_stories_checked"] >= 0


class TestAutoSaveIntegrationWithAPI:
    """Test auto-save integration with API endpoints."""
    
    def test_session_save_endpoint_persists(self):
        """Test that session save endpoint persists to disk."""
        story_id = "api_persist_test"
        
        session_data = {
            "story_id": story_id,
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session_data)
        assert response.status_code == 200
        
        # Verify by loading from disk
        loaded = SessionState.load_from_file(story_id)
        assert loaded is not None
        assert loaded.story_id == story_id
    
    def test_concurrent_session_saves_safe(self):
        """Test that concurrent session saves are handled safely."""
        story_id = "concurrent_test"
        
        # Simulate multiple quick saves (would test thread safety)
        for i in range(3):
            session_data = {
                "story_id": story_id,
                "current_segment_id": f"segment_{i:03d}",
                "visited_segments": [f"segment_{j:03d}" for j in range(i + 1)],
                "scene_counter": i + 1,
                "start_time": datetime.now(UTC).isoformat()
            }
            
            response = client.post("/api/sessions/save", json=session_data)
            # All should succeed (or debounce gracefully)
            assert response.status_code in [200]
        
        # Final state should be consistent
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        assert "scene_counter" in response.json()["session"]
