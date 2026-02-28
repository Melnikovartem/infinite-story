"""Tests for auto-save system."""

import pytest
import time
from pathlib import Path
from datetime import datetime, UTC
from app.models.session_state import SessionState
from app.services.auto_save_manager import AutoSaveManager


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up and reset auto-save state."""
    AutoSaveManager.clear_all_debounce()
    yield
    # Cleanup after
    AutoSaveManager.clear_all_debounce()
    test_story_dir = Path(".infinite_story_data") / "test_story"
    if test_story_dir.exists():
        for f in test_story_dir.glob("*.json"):
            f.unlink()


class TestAutoSaveDebouncing:
    """Test debouncing functionality."""
    
    def test_should_save_first_time(self):
        """Test that first save is always allowed."""
        assert AutoSaveManager.should_save("story_1") is True
    
    def test_should_save_after_debounce(self):
        """Test that saves are debounced initially."""
        # First save should be allowed
        assert AutoSaveManager.should_save("story_1") is True
        
        # Record it
        AutoSaveManager._last_saves["story_1"] = datetime.now(UTC)
        
        # Immediate second save should be denied
        assert AutoSaveManager.should_save("story_1") is False
    
    def test_debounce_resets_after_time(self):
        """Test that debounce resets after enough time."""
        import datetime as dt_module
        
        # Set last save to 15 seconds ago (debounce is 10 seconds)
        past_time = datetime.now(UTC) - dt_module.timedelta(seconds=15)
        AutoSaveManager._last_saves["story_1"] = past_time
        
        # Should allow save now
        assert AutoSaveManager.should_save("story_1") is True


class TestAutoSaveSync:
    """Test synchronous auto-save."""
    
    def test_auto_save_sync_success(self):
        """Test successful auto-save."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        result = AutoSaveManager.auto_save_sync("test_story", session)
        assert result is True
        
        # Verify it was saved
        loaded = SessionState.load_from_file("test_story")
        assert loaded is not None
        assert loaded.story_id == "test_story"
    
    def test_auto_save_sync_debounced(self):
        """Test that debounced saves return False."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        # First save succeeds
        result1 = AutoSaveManager.auto_save_sync("test_story", session)
        assert result1 is True
        
        # Second save immediately after is debounced
        session.add_segment("segment_2")
        result2 = AutoSaveManager.auto_save_sync("test_story", session)
        assert result2 is False
    
    def test_auto_save_sync_updates_timestamp(self):
        """Test that auto-save updates timestamp."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        before = datetime.now(UTC)
        AutoSaveManager.auto_save_sync("test_story", session)
        after = datetime.now(UTC)
        
        saved_time = AutoSaveManager._last_saves["test_story"]
        assert before <= saved_time <= after


class TestAutoSaveAsync:
    """Test asynchronous auto-save."""
    
    @pytest.mark.asyncio
    async def test_auto_save_async_success(self):
        """Test successful async auto-save."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        result = await AutoSaveManager.auto_save_async("test_story", session)
        assert result is True
        
        # Verify it was saved
        loaded = SessionState.load_from_file("test_story")
        assert loaded is not None


class TestAutoSaveInfo:
    """Test getting auto-save information."""
    
    def test_get_auto_save_info_no_prior_save(self):
        """Test getting info for story with no prior save."""
        info = AutoSaveManager.get_auto_save_info("story_1")
        
        assert info["story_id"] == "story_1"
        assert info["last_save"] is None
        assert info["next_save_ready_in_seconds"] == 0
    
    def test_get_auto_save_info_after_save(self):
        """Test getting info after a save."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        AutoSaveManager.auto_save_sync("test_story", session)
        info = AutoSaveManager.get_auto_save_info("test_story")
        
        assert info["story_id"] == "test_story"
        assert info["last_save"] is not None
        assert info["next_save_ready_in_seconds"] > 0


class TestAutoSaveCleanup:
    """Test cleanup functionality."""
    
    def test_cleanup_old_saves(self):
        """Test cleaning up old saves."""
        # Create multiple saves
        for i in range(3):
            session = SessionState(
                story_id=f"story_{i}",
                current_segment_id="segment_1",
                visited_segments=["segment_1"]
            )
            SessionState.save_to_file(f"story_{i}", session)
        
        # Run cleanup (with very old cutoff to not actually delete)
        stats = AutoSaveManager.cleanup_old_saves(days_old=365)
        
        assert stats["total_stories_checked"] >= 3
        assert stats["sessions_deleted"] == 0  # All are recent
    
    def test_cleanup_returns_stats(self):
        """Test that cleanup returns valid statistics."""
        stats = AutoSaveManager.cleanup_old_saves()
        
        assert "total_stories_checked" in stats
        assert "sessions_deleted" in stats
        assert "errors" in stats
        assert isinstance(stats["errors"], list)


class TestAutoSaveDebounceManagement:
    """Test debounce timer management."""
    
    def test_reset_debounce(self):
        """Test resetting debounce for a story."""
        # Set a debounce
        AutoSaveManager._last_saves["story_1"] = datetime.now(UTC)
        assert AutoSaveManager.should_save("story_1") is False
        
        # Reset it
        AutoSaveManager.reset_debounce("story_1")
        assert AutoSaveManager.should_save("story_1") is True
    
    def test_clear_all_debounce(self):
        """Test clearing all debounce timers."""
        # Set multiple debounces
        AutoSaveManager._last_saves["story_1"] = datetime.now(UTC)
        AutoSaveManager._last_saves["story_2"] = datetime.now(UTC)
        
        # Clear all
        AutoSaveManager.clear_all_debounce()
        
        # All should allow saves now
        assert AutoSaveManager.should_save("story_1") is True
        assert AutoSaveManager.should_save("story_2") is True
