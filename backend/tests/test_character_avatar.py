"""Tests for character avatar system and state management."""
import pytest
import shutil
from datetime import datetime, UTC
from pathlib import Path

from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR
from app.models.story_character import StoryCharacter, AvatarShape, CharacterState


@pytest.fixture
def test_story():
    """Fixture to create and clean up test story."""
    test_story_id = "test_character_avatar_story"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story for Character Avatar",
        description="A test story for character avatar testing",
        genre="Test",
        user_id="test_user_1",
        start_segment_id="start_segment_1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    yield story
    
    # Clean up after tests
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)


class TestAvatarSystem:
    """Test avatar shape and color system."""
    
    def test_avatar_shape_enum(self):
        """Test that all avatar shapes are defined."""
        expected_shapes = {"square", "circle", "triangle", "diamond", "star", "pentagon"}
        actual_shapes = {shape.value for shape in AvatarShape}
        assert actual_shapes == expected_shapes
    
    def test_character_creation_with_default_avatar(self, test_story):
        """Test creating a character with default avatar."""
        char = StoryCharacter(
            story=test_story,
            id="char_1",
            story_id=test_story.id,
            name="Test Character",
            description="A test character",
            background="Test background"
        )
        
        assert char.avatar_shape == AvatarShape.CIRCLE
        assert char.avatar_color == "#FF6B6B"
    
    def test_character_creation_with_custom_avatar(self, test_story):
        """Test creating a character with custom avatar."""
        char = StoryCharacter(
            story=test_story,
            id="char_2",
            story_id=test_story.id,
            name="Custom Avatar Character",
            description="A character with custom avatar",
            background="Background",
            avatar_shape=AvatarShape.SQUARE,
            avatar_color="#4ECDC4"
        )
        
        assert char.avatar_shape == AvatarShape.SQUARE
        assert char.avatar_color == "#4ECDC4"
    
    def test_avatar_shape_validation(self, test_story):
        """Test that invalid avatar shapes are rejected."""
        # Note: Pydantic will handle the enum validation
        with pytest.raises(ValueError):
            StoryCharacter(
                story=test_story,
                id="char_3",
                story_id=test_story.id,
                name="Invalid Avatar",
                description="A character with invalid avatar",
                background="Background",
                avatar_shape="invalid_shape"
            )
    
    def test_avatar_color_validation_6digit_hex(self, test_story):
        """Test 6-digit hex color validation."""
        char = StoryCharacter(
            story=test_story,
            id="char_4",
            story_id=test_story.id,
            name="Hex Color Test",
            description="Test hex colors",
            background="Background",
            avatar_color="#AABBCC"
        )
        assert char.avatar_color == "#AABBCC"
    
    def test_avatar_color_validation_3digit_hex(self, test_story):
        """Test 3-digit hex color validation."""
        char = StoryCharacter(
            story=test_story,
            id="char_5",
            story_id=test_story.id,
            name="3-Digit Hex Test",
            description="Test 3-digit hex",
            background="Background",
            avatar_color="#ABC"
        )
        assert char.avatar_color == "#ABC"
    
    def test_avatar_color_validation_adds_hash(self, test_story):
        """Test that # is added if missing."""
        char = StoryCharacter(
            story=test_story,
            id="char_6",
            story_id=test_story.id,
            name="Hash Test",
            description="Test hash addition",
            background="Background",
            avatar_color="FF6B6B"
        )
        assert char.avatar_color.startswith("#")
    
    def test_avatar_color_validation_invalid_hex(self, test_story):
        """Test that invalid hex colors are rejected."""
        with pytest.raises(ValueError):
            StoryCharacter(
                story=test_story,
                id="char_7",
                story_id=test_story.id,
                name="Invalid Color",
                description="Invalid hex color",
                background="Background",
                avatar_color="#GGGGGG"
            )
    
    def test_avatar_color_validation_wrong_length(self, test_story):
        """Test that wrong-length hex colors are rejected."""
        with pytest.raises(ValueError):
            StoryCharacter(
                story=test_story,
                id="char_8",
                story_id=test_story.id,
                name="Wrong Length",
                description="Wrong length hex",
                background="Background",
                avatar_color="#FF00"
            )
    
    def test_get_short_overview_includes_avatar(self, test_story):
        """Test that short overview includes avatar info."""
        char = StoryCharacter(
            story=test_story,
            id="char_9",
            story_id=test_story.id,
            name="Overview Test",
            description="Test avatar in overview",
            background="Background",
            avatar_shape=AvatarShape.STAR,
            avatar_color="#FFD700"
        )
        
        overview = char.get_short_overview()
        assert "Overview Test" in overview
        assert "star" in overview
        assert "#FFD700" in overview


class TestCharacterState:
    """Test character state tracking."""
    
    def test_character_state_creation(self):
        """Test creating a character state."""
        state = CharacterState(
            segment_id="seg_1",
            emotion="happy",
            status="present",
            notes="Character is happy and present"
        )
        
        assert state.segment_id == "seg_1"
        assert state.emotion == "happy"
        assert state.status == "present"
        assert state.notes == "Character is happy and present"
    
    def test_character_state_default_values(self):
        """Test character state with default values."""
        state = CharacterState(segment_id="seg_2")
        
        assert state.segment_id == "seg_2"
        assert state.emotion is None
        assert state.status == "present"
        assert state.notes == ""
    
    def test_character_state_to_dict(self):
        """Test converting character state to dictionary."""
        state = CharacterState(
            segment_id="seg_3",
            emotion="sad",
            status="absent",
            notes="Character left the scene"
        )
        
        state_dict = state.to_dict()
        assert state_dict["segment_id"] == "seg_3"
        assert state_dict["emotion"] == "sad"
        assert state_dict["status"] == "absent"
        assert state_dict["notes"] == "Character left the scene"
    
    def test_character_state_from_dict(self):
        """Test creating character state from dictionary."""
        data = {
            "segment_id": "seg_4",
            "emotion": "angry",
            "status": "mentioned",
            "notes": "Character mentioned in passing"
        }
        
        state = CharacterState.from_dict(data)
        assert state.segment_id == "seg_4"
        assert state.emotion == "angry"
        assert state.status == "mentioned"
        assert state.notes == "Character mentioned in passing"
    
    def test_add_state_to_character(self, test_story):
        """Test adding state to a character."""
        char = StoryCharacter(
            story=test_story,
            id="char_10",
            story_id=test_story.id,
            name="State Test",
            description="Test character states",
            background="Background"
        )
        
        char.add_state(
            segment_id="seg_1",
            emotion="curious",
            status="present",
            notes="Just arrived"
        )
        
        assert len(char.running_status) == 1
        assert char.running_status[0]["segment_id"] == "seg_1"
        assert char.running_status[0]["emotion"] == "curious"
    
    def test_add_multiple_states(self, test_story):
        """Test adding multiple states to a character."""
        char = StoryCharacter(
            story=test_story,
            id="char_11",
            story_id=test_story.id,
            name="Multi State Test",
            description="Test multiple states",
            background="Background"
        )
        
        char.add_state("seg_1", emotion="curious", status="present", notes="Arrived")
        char.add_state("seg_2", emotion="afraid", status="present", notes="Discovered danger")
        char.add_state("seg_3", emotion="determined", status="present", notes="Ready to fight")
        
        assert len(char.running_status) == 3
        assert char.running_status[0]["emotion"] == "curious"
        assert char.running_status[1]["emotion"] == "afraid"
        assert char.running_status[2]["emotion"] == "determined"
    
    def test_update_existing_state(self, test_story):
        """Test updating an existing state."""
        char = StoryCharacter(
            story=test_story,
            id="char_12",
            story_id=test_story.id,
            name="Update State Test",
            description="Test state updates",
            background="Background"
        )
        
        # Add initial state
        char.add_state("seg_1", emotion="happy", status="present", notes="Initial")
        
        # Update the same state
        char.add_state("seg_1", emotion="very happy", status="present", notes="Updated")
        
        assert len(char.running_status) == 1
        assert char.running_status[0]["emotion"] == "very happy"
        assert char.running_status[0]["notes"] == "Updated"
    
    def test_get_state_at_segment(self, test_story):
        """Test retrieving character state at a segment."""
        char = StoryCharacter(
            story=test_story,
            id="char_13",
            story_id=test_story.id,
            name="Get State Test",
            description="Test getting states",
            background="Background"
        )
        
        char.add_state("seg_1", emotion="happy")
        char.add_state("seg_2", emotion="sad")
        
        state_1 = char.get_state_at_segment("seg_1")
        state_2 = char.get_state_at_segment("seg_2")
        state_3 = char.get_state_at_segment("seg_3")
        
        assert state_1 is not None
        assert state_1["emotion"] == "happy"
        assert state_2 is not None
        assert state_2["emotion"] == "sad"
        assert state_3 is None
    
    def test_get_state_arc(self, test_story):
        """Test getting character's state arc."""
        char = StoryCharacter(
            story=test_story,
            id="char_14",
            story_id=test_story.id,
            name="Arc Test",
            description="Test state arc",
            background="Background"
        )
        
        char.add_state("seg_1", emotion="confused")
        char.add_state("seg_2", emotion="determined")
        char.add_state("seg_3", emotion="triumphant")
        
        arc = char.get_state_arc()
        assert len(arc) == 3
        emotions = [state["emotion"] for state in arc]
        assert emotions == ["confused", "determined", "triumphant"]


class TestCharacterSerialization:
    """Test character serialization and persistence."""
    
    def test_character_save_load_with_avatar(self, test_story):
        """Test saving and loading a character with avatar data."""
        char = StoryCharacter(
            story=test_story,
            id="char_15",
            story_id=test_story.id,
            name="Serialization Test",
            description="Test serialization",
            background="Background",
            avatar_shape=AvatarShape.TRIANGLE,
            avatar_color="#FF1493"
        )
        
        # Save the character
        char.save()
        
        # Load the character
        loaded = StoryCharacter.load(test_story.id, char.id, story=test_story)
        
        assert loaded is not None
        assert loaded.avatar_shape == AvatarShape.TRIANGLE
        assert loaded.avatar_color == "#FF1493"
    
    def test_character_save_load_with_states(self, test_story):
        """Test saving and loading a character with state history."""
        char = StoryCharacter(
            story=test_story,
            id="char_16",
            story_id=test_story.id,
            name="State Serialization Test",
            description="Test state serialization",
            background="Background"
        )
        
        char.add_state("seg_1", emotion="nervous", status="present", notes="Entering")
        char.add_state("seg_2", emotion="confident", status="present", notes="Found courage")
        
        # Save the character
        char.save()
        
        # Load the character
        loaded = StoryCharacter.load(test_story.id, char.id, story=test_story)
        
        assert loaded is not None
        assert len(loaded.running_status) == 2
        assert loaded.running_status[0]["emotion"] == "nervous"
        assert loaded.running_status[1]["emotion"] == "confident"
    
    def test_full_overview_with_avatar(self, test_story):
        """Test full overview includes avatar information."""
        char = StoryCharacter(
            story=test_story,
            id="char_17",
            story_id=test_story.id,
            name="Full Overview Test",
            description="A test character",
            background="Test background",
            avatar_shape=AvatarShape.PENTAGON,
            avatar_color="#8B4513"
        )
        
        overview = char.get_full_overview()
        assert "Full Overview Test" in overview
        assert "pentagon" in overview
        assert "#8B4513" in overview
        assert "Test background" in overview
