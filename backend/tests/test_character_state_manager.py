"""Tests for character state management utilities."""
import pytest
import shutil
from datetime import datetime, UTC
from pathlib import Path

from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR
from app.models.story_character import StoryCharacter, AvatarShape
from app.utils.character_state_manager import CharacterStateManager


@pytest.fixture
def test_story():
    """Fixture to create and clean up test story."""
    test_story_id = "test_character_state_story"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story for State Manager",
        description="A test story for character state manager testing",
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


@pytest.fixture
def test_character(test_story):
    """Fixture to create a test character."""
    char = StoryCharacter(
        story=test_story,
        id="test_char_1",
        story_id=test_story.id,
        name="Test Hero",
        description="A brave adventurer",
        background="Born in the mountains",
        avatar_shape=AvatarShape.SQUARE,
        avatar_color="#FF6B6B"
    )
    return char


class TestCharacterStateManager:
    """Test character state manager functionality."""
    
    def test_update_character_state(self, test_character):
        """Test updating character state."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="curious",
            status="present",
            notes="Just started the adventure"
        )
        
        assert len(test_character.running_status) == 1
        assert test_character.running_status[0]["emotion"] == "curious"
        assert test_character.running_status[0]["status"] == "present"
    
    def test_get_character_context(self, test_character):
        """Test building character context for generation."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="curious",
            status="present",
            notes="Exploring"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_2",
            emotion="afraid",
            status="present",
            notes="Encountered danger"
        )
        
        context = CharacterStateManager.get_character_context(test_character)
        
        assert "Test Hero" in context
        assert "A brave adventurer" in context
        assert "square" in context
        assert "#FF6B6B" in context
        assert "curious" in context
        assert "afraid" in context
        assert "Character Arc:" in context
    
    def test_get_character_context_without_emotions(self, test_character):
        """Test building character context excluding emotions."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="curious",
            status="present",
            notes="Exploring"
        )
        
        context = CharacterStateManager.get_character_context(
            test_character,
            include_emotions=False
        )
        
        # Emotion should not be in the context
        assert "curious" not in context.split("Character Arc:")[1]  # Check in arc section
        assert "Test Hero" in context
    
    def test_get_character_context_without_notes(self, test_character):
        """Test building character context excluding notes."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="curious",
            status="present",
            notes="Exploring the ruins"
        )
        
        context = CharacterStateManager.get_character_context(
            test_character,
            include_notes=False
        )
        
        # Notes should not be in the context
        assert "Exploring the ruins" not in context
        assert "Test Hero" in context
    
    def test_get_characters_for_generation(self, test_story):
        """Test building context for multiple characters."""
        char1 = StoryCharacter(
            story=test_story,
            id="char_1",
            story_id=test_story.id,
            name="Character One",
            description="First character",
            background="Background 1"
        )
        
        char2 = StoryCharacter(
            story=test_story,
            id="char_2",
            story_id=test_story.id,
            name="Character Two",
            description="Second character",
            background="Background 2"
        )
        
        CharacterStateManager.update_character_state(char1, "seg_1", emotion="happy")
        CharacterStateManager.update_character_state(char2, "seg_1", emotion="sad")
        
        context = CharacterStateManager.get_characters_for_generation(
            [char1, char2],
            "seg_1"
        )
        
        assert "Character One" in context
        assert "Character Two" in context
        assert "happy" in context
        assert "sad" in context
    
    def test_extract_character_updates_from_response(self):
        """Test extracting character updates from AI response."""
        response = {
            "character_updates": {
                "char_1": {
                    "emotion": "excited",
                    "status": "present",
                    "notes": "Found treasure"
                },
                "char_2": {
                    "emotion": "afraid",
                    "status": "absent",
                    "notes": "Fled the scene"
                }
            }
        }
        
        updates = CharacterStateManager.extract_character_updates_from_response(
            response,
            segment_id="seg_2"
        )
        
        assert len(updates) == 2
        assert updates["char_1"]["emotion"] == "excited"
        assert updates["char_1"]["segment_id"] == "seg_2"
        assert updates["char_2"]["status"] == "absent"
    
    def test_extract_character_updates_no_updates(self):
        """Test extracting updates when none exist."""
        response = {
            "content": "Some generated text"
        }
        
        updates = CharacterStateManager.extract_character_updates_from_response(
            response,
            segment_id="seg_2"
        )
        
        assert len(updates) == 0
    
    def test_apply_character_updates(self, test_story):
        """Test applying character updates."""
        char1 = StoryCharacter(
            story=test_story,
            id="char_1",
            story_id=test_story.id,
            name="Character One",
            description="First character",
            background="Background 1"
        )
        
        char2 = StoryCharacter(
            story=test_story,
            id="char_2",
            story_id=test_story.id,
            name="Character Two",
            description="Second character",
            background="Background 2"
        )
        
        updates = {
            "char_1": {
                "segment_id": "seg_1",
                "emotion": "determined",
                "status": "present",
                "notes": "Ready for action"
            },
            "char_2": {
                "segment_id": "seg_1",
                "emotion": "confused",
                "status": "present",
                "notes": "Not sure what's happening"
            }
        }
        
        characters = {"char_1": char1, "char_2": char2}
        CharacterStateManager.apply_character_updates(characters, updates)
        
        assert len(char1.running_status) == 1
        assert char1.running_status[0]["emotion"] == "determined"
        assert len(char2.running_status) == 1
        assert char2.running_status[0]["emotion"] == "confused"
    
    def test_get_character_arc_summary_no_states(self, test_character):
        """Test arc summary for character with no states."""
        summary = CharacterStateManager.get_character_arc_summary(test_character)
        assert "not appeared" in summary
    
    def test_get_character_arc_summary_with_states(self, test_character):
        """Test arc summary for character with states."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="hopeful"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_2",
            emotion="determined"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_3",
            emotion="triumphant"
        )
        
        summary = CharacterStateManager.get_character_arc_summary(test_character)
        
        assert "Test Hero" in summary
        assert "hopeful" in summary
        assert "triumphant" in summary
        assert "3 scenes" in summary
    
    def test_validate_character_states_no_states(self, test_character):
        """Test validation for character with no states."""
        messages = CharacterStateManager.validate_character_states(test_character)
        
        assert len(messages) == 1
        assert "no state history" in messages[0]
    
    def test_validate_character_states_uniform_emotion(self, test_character):
        """Test validation warning for uniform emotions."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="sad"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_2",
            emotion="sad"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_3",
            emotion="sad"
        )
        
        messages = CharacterStateManager.validate_character_states(test_character)
        
        assert any("same emotion" in msg for msg in messages)
    
    def test_validate_character_states_varied_emotion(self, test_character):
        """Test validation for character with varied emotions."""
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_1",
            emotion="curious"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_2",
            emotion="afraid"
        )
        CharacterStateManager.update_character_state(
            test_character,
            segment_id="seg_3",
            emotion="brave"
        )
        
        messages = CharacterStateManager.validate_character_states(test_character)
        
        # Should not have emotion variety warning
        assert not any("same emotion" in msg for msg in messages)
    
    def test_character_persistence_with_state_updates(self, test_story):
        """Test that state updates persist through save/load cycle."""
        char = StoryCharacter(
            story=test_story,
            id="persist_test_char",
            story_id=test_story.id,
            name="Persistent Character",
            description="A character that persists",
            background="Persistent background"
        )
        
        # Add states
        CharacterStateManager.update_character_state(
            char,
            segment_id="seg_1",
            emotion="curious",
            status="present",
            notes="Started here"
        )
        CharacterStateManager.update_character_state(
            char,
            segment_id="seg_2",
            emotion="afraid",
            status="present",
            notes="Found danger"
        )
        
        # Save
        char.save()
        
        # Load
        loaded = StoryCharacter.load(test_story.id, char.id, story=test_story)
        
        # Verify
        assert len(loaded.running_status) == 2
        assert loaded.running_status[0]["emotion"] == "curious"
        assert loaded.running_status[1]["emotion"] == "afraid"
        assert loaded.running_status[0]["notes"] == "Started here"
        assert loaded.running_status[1]["notes"] == "Found danger"
