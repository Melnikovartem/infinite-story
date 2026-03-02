"""Tests for SessionState model."""

import pytest
import shutil
from pathlib import Path
from datetime import datetime, UTC
from app.models.session_state import SessionState
from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR


@pytest.fixture
def test_data():
    """Fixture to set up and tear down test data for SessionState tests."""
    test_story_id = "test_session_story"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story for Sessions",
        description="A test story for session testing",
        genre="Test",
        user_id="test_user_1",
        start_segment_id="seg_1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    yield {
        "story": story,
        "story_id": test_story_id,
        "test_data_dir": test_data_dir
    }
    
    # Clean up after test
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)


class TestSessionStateModel:
    """Test SessionState model creation and validation."""
    
    def test_session_creation(self, test_data):
        """Test that a session can be created with valid data."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_1",
            user_id="user_1",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        assert session.id == "session_1"
        assert session.story_id == test_data["story_id"]
        assert session.user_id == "user_1"
        assert session.current_segment_id == "segment_1"
        assert session.visited_segments == ["segment_1"]
    
    def test_session_auto_updates_visited_segments(self, test_data):
        """Test that current segment is automatically added to visited if not present."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_2",
            user_id="user_1",
            current_segment_id="segment_1"
        )
        assert "segment_1" in session.visited_segments
    
    def test_session_validates_visited_segments(self, test_data):
        """Test that duplicate segments are removed from visited_segments."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_3",
            user_id="user_1",
            current_segment_id="segment_3",
            visited_segments=["segment_1", "segment_2", "segment_1", "segment_3"]
        )
        assert session.visited_segments == ["segment_1", "segment_2", "segment_3"]
    
    def test_session_validates_visited_choices(self, test_data):
        """Test that duplicate choices are removed from visited_choices."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_4",
            user_id="user_1",
            current_segment_id="segment_3",
            visited_choices=["choice_1", "choice_2", "choice_1"]
        )
        assert session.visited_choices == ["choice_1", "choice_2"]
    
    def test_session_add_visited(self, test_data):
        """Test adding visited segments and choices to the session."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_5",
            user_id="user_1",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        session.add_visited("segment_2", "choice_1")
        assert "segment_2" in session.visited_segments
        assert "choice_1" in session.visited_choices
        assert session.visited_segments == ["segment_1", "segment_2"]
    
    def test_session_add_visited_duplicate_segment(self, test_data):
        """Test that adding a duplicate segment doesn't create duplicates."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_6",
            user_id="user_1",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        session.add_visited("segment_1")
        assert session.visited_segments == ["segment_1"]
    
    def test_session_move_to(self, test_data):
        """Test moving to a new segment."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_7",
            user_id="user_1",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        
        session.move_to("segment_2", "choice_1")
        assert session.current_segment_id == "segment_2"
        assert "segment_2" in session.visited_segments
        assert "choice_1" in session.visited_choices


class TestSessionStateSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self, test_data):
        """Test conversion to dictionary."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_8",
            user_id="user_1",
            current_segment_id="segment_1",
            visited_segments=["segment_1"],
            visited_choices=["choice_1"]
        )
        
        data = session.to_dict()
        assert isinstance(data, dict)
        assert data["story_id"] == test_data["story_id"]
        assert data["user_id"] == "user_1"
        assert data["current_segment_id"] == "segment_1"
        assert data["visited_segments"] == ["segment_1"]
        assert data["visited_choices"] == ["choice_1"]
    
    def test_from_dict(self, test_data):
        """Test creation from dictionary."""
        story = test_data["story"]
        story_id = test_data["story_id"]
        
        data = {
            "id": "session_9",
            "story_id": story_id,
            "user_id": "user_1",
            "current_segment_id": "segment_2",
            "visited_segments": ["segment_1", "segment_2"],
            "visited_choices": ["choice_1"]
        }
        
        session = SessionState.from_dict(data)
        assert session.id == "session_9"
        assert session.story_id == story_id
        assert session.user_id == "user_1"
        assert session.current_segment_id == "segment_2"
        assert len(session.visited_segments) == 2
        assert len(session.visited_choices) == 1


class TestSessionStatePersistence:
    """Test save/load functionality using StoryBase."""
    
    def test_save_and_load(self, test_data):
        """Test saving and loading session."""
        story = test_data["story"]
        story_id = test_data["story_id"]
        
        session = SessionState(
            story=story,
            id="session_10",
            user_id="user_1",
            current_segment_id="segment_3",
            visited_segments=["segment_1", "segment_2", "segment_3"],
            visited_choices=["choice_1", "choice_2"]
        )
        
        # Save the session
        session.save()
        
        # Load it back
        loaded = SessionState.load(story_id, "session_10")
        
        assert loaded is not None
        assert loaded.id == session.id
        assert loaded.user_id == session.user_id
        assert loaded.current_segment_id == session.current_segment_id
        assert loaded.visited_segments == session.visited_segments
        assert loaded.visited_choices == session.visited_choices
    
    def test_load_nonexistent_session(self, test_data):
        """Test loading a session that doesn't exist returns None."""
        story_id = test_data["story_id"]
        
        session = SessionState.load(story_id, "nonexistent_session")
        assert session is None
    
    def test_delete_session(self, test_data):
        """Test deleting session from disk."""
        story = test_data["story"]
        story_id = test_data["story_id"]
        
        # Create and save a session
        session = SessionState(
            story=story,
            id="session_11",
            user_id="user_1",
            current_segment_id="segment_1",
            visited_segments=["segment_1"]
        )
        session.save()
        
        # Verify it exists
        loaded = SessionState.load(story_id, "session_11")
        assert loaded is not None
        
        # Delete it
        session.delete()
        
        # Verify it's gone
        loaded = SessionState.load(story_id, "session_11")
        assert loaded is None
    
    def test_list_all_sessions(self, test_data):
        """Test listing all sessions for a story."""
        story = test_data["story"]
        story_id = test_data["story_id"]
        
        # Create and save multiple sessions
        for i in range(3):
            session = SessionState(
                story=story,
                id=f"session_list_{i}",
                user_id=f"user_{i}",
                current_segment_id="segment_1",
                visited_segments=["segment_1"]
            )
            session.save()
        
        # List all sessions
        session_ids = SessionState.list_all(story_id)
        
        assert len(session_ids) >= 3
        assert "session_list_0" in session_ids
        assert "session_list_1" in session_ids
        assert "session_list_2" in session_ids


class TestSessionStateDefaults:
    """Test default values for SessionState."""
    
    def test_session_defaults(self, test_data):
        """Test that SessionState has proper defaults."""
        story = test_data["story"]
        
        session = SessionState(
            story=story,
            id="session_12",
            user_id="user_1",
            current_segment_id="segment_1"
        )
        
        assert session.visited_segments == ["segment_1"]
        assert session.visited_choices == []
        assert session.created_at is not None
        assert session.updated_at is not None
