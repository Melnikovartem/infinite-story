"""Tests for SessionState model."""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime, UTC
from app.models.session_state import SessionState


class TestSessionStateModel:
    """Test SessionState model creation and validation."""
    
    def test_session_creation(self):
        """Test that a session can be created with valid data."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        assert session.story_id == "test_story"
        assert session.current_segment_id == "segment_1"
        assert session.visited_segments == ["segment_1"]
        assert session.scene_counter >= 1
    
    def test_session_auto_updates_visited_segments(self):
        """Test that current segment is automatically added to visited if not present."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1"
        )
        assert "segment_1" in session.visited_segments
    
    def test_session_validates_visited_segments(self):
        """Test that duplicate segments are removed from visited_segments."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_3",
            visited_segments=["segment_1", "segment_2", "segment_1", "segment_3"]
        )
        assert session.visited_segments == ["segment_1", "segment_2", "segment_3"]
    
    def test_session_add_segment(self):
        """Test adding a new segment to the session."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        session.add_segment("segment_2")
        assert session.current_segment_id == "segment_2"
        assert "segment_2" in session.visited_segments
        assert session.visited_segments == ["segment_1", "segment_2"]
    
    def test_session_add_duplicate_segment(self):
        """Test that adding a duplicate segment doesn't create duplicates."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        session.add_segment("segment_1")
        assert session.visited_segments == ["segment_1"]
    
    def test_session_scene_counter_updated(self):
        """Test that scene counter is updated when adding segments."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        assert session.scene_counter >= 1
        initial_counter = session.scene_counter
        
        session.add_segment("segment_2")
        assert session.scene_counter == initial_counter + 1


class TestSessionStateTime:
    """Test time tracking functionality."""
    
    def test_elapsed_seconds(self):
        """Test elapsed time calculation."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"],
            start_time=datetime.now(UTC)
        )
        
        time.sleep(0.1)
        elapsed = session.get_elapsed_seconds()
        assert elapsed >= 0
    
    def test_elapsed_formatted(self):
        """Test formatted elapsed time."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        formatted = session.get_elapsed_formatted()
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        # Should contain at least "s" for seconds
        assert "s" in formatted or "m" in formatted or "h" in formatted


class TestSessionStateSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"],
            scene_counter=5
        )
        
        data = session.to_dict()
        assert isinstance(data, dict)
        assert data["story_id"] == "test_story"
        assert data["current_segment_id"] == "segment_1"
        assert data["visited_segments"] == ["segment_1"]
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "story_id": "test_story",
            "current_segment_id": "segment_2",
            "visited_segments": ["segment_1", "segment_2"],
            "scene_counter": 2,
            "start_time": datetime.now(UTC).isoformat(),
            "last_updated": datetime.now(UTC).isoformat()
        }
        
        session = SessionState.from_dict(data)
        assert session.story_id == "test_story"
        assert session.current_segment_id == "segment_2"
        assert len(session.visited_segments) == 2


class TestSessionStateFileIO:
    """Test file save/load functionality."""
    
    def setup_method(self):
        """Clean up any test files before each test."""
        test_story_dir = Path(".infinite_story_data") / "test_story"
        if test_story_dir.exists():
            for file in test_story_dir.glob("*.json"):
                file.unlink()
    
    def teardown_method(self):
        """Clean up test files after each test."""
        test_story_dir = Path(".infinite_story_data") / "test_story"
        if test_story_dir.exists():
            for file in test_story_dir.glob("*.json"):
                file.unlink()
    
    def test_save_to_file(self):
        """Test saving session to file."""
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        file_path = SessionState.save_to_file("test_story", session)
        assert file_path.exists()
        assert file_path.name == "runner_state.json"
        
        # Verify the file contains valid JSON
        with open(file_path, "r") as f:
            data = json.load(f)
        assert data["story_id"] == "test_story"
    
    def test_load_from_file(self):
        """Test loading session from file."""
        # First save a session
        session_original = SessionState(
            story_id="test_story",
            current_segment_id="segment_3",
            visited_segments=["segment_1", "segment_2", "segment_3"],
            scene_counter=3
        )
        SessionState.save_to_file("test_story", session_original)
        
        # Now load it
        session_loaded = SessionState.load_from_file("test_story")
        assert session_loaded is not None
        assert session_loaded.story_id == "test_story"
        assert session_loaded.current_segment_id == "segment_3"
        assert session_loaded.visited_segments == ["segment_1", "segment_2", "segment_3"]
    
    def test_load_nonexistent_session(self):
        """Test loading a session that doesn't exist returns None."""
        session = SessionState.load_from_file("nonexistent_story")
        assert session is None
    
    def test_delete_from_file(self):
        """Test deleting session from file."""
        # First save a session
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        SessionState.save_to_file("test_story", session)
        
        # Verify it exists
        assert SessionState.exists("test_story")
        
        # Delete it
        deleted = SessionState.delete_from_file("test_story")
        assert deleted is True
        assert not SessionState.exists("test_story")
    
    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        deleted = SessionState.delete_from_file("nonexistent_story")
        assert deleted is False
    
    def test_exists(self):
        """Test checking if a session exists."""
        # Should not exist initially
        assert not SessionState.exists("test_story")
        
        # Save a session
        session = SessionState(
            story_id="test_story",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        SessionState.save_to_file("test_story", session)
        
        # Should exist now
        assert SessionState.exists("test_story")
