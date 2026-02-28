"""Tests for character context integration in generation."""
import pytest
import shutil
from datetime import datetime, UTC
from pathlib import Path

from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR
from app.models.story_character import StoryCharacter, AvatarShape
from app.utils.character_context_builder import CharacterContextBuilder
from app.utils.character_state_manager import CharacterStateManager


@pytest.fixture
def test_story():
    """Fixture to create and clean up test story."""
    test_story_id = "test_character_context_story"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story for Context Building",
        description="A test story for character context builder testing",
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
def test_characters(test_story):
    """Fixture to create test characters."""
    char1 = StoryCharacter(
        story=test_story,
        id="hero",
        story_id=test_story.id,
        name="Hero",
        description="A brave adventurer",
        background="Trained since childhood",
        avatar_shape=AvatarShape.CIRCLE,
        avatar_color="#FF6B6B"
    )
    
    char2 = StoryCharacter(
        story=test_story,
        id="companion",
        story_id=test_story.id,
        name="Companion",
        description="A loyal friend",
        background="Childhood friend",
        avatar_shape=AvatarShape.SQUARE,
        avatar_color="#4ECDC4"
    )
    
    char3 = StoryCharacter(
        story=test_story,
        id="villain",
        story_id=test_story.id,
        name="Villain",
        description="The antagonist",
        background="Mysterious origins",
        avatar_shape=AvatarShape.TRIANGLE,
        avatar_color="#95E1D3"
    )
    
    return [char1, char2, char3]


class TestCharacterContextBuilder:
    """Test character context building functionality."""
    
    def test_build_character_section_empty(self):
        """Test building section with no characters."""
        section = CharacterContextBuilder.build_character_section([], current_segment_id="seg_1")
        assert section == ""
    
    def test_build_character_section_basic(self, test_characters):
        """Test building basic character section."""
        section = CharacterContextBuilder.build_character_section(
            test_characters[:1],
            current_segment_id="seg_1"
        )
        
        assert "CHARACTER INFORMATION" in section
        assert "Hero" in section
        assert "A brave adventurer" in section
        assert "circle" in section
        assert "#FF6B6B" in section
    
    def test_build_character_section_with_states(self, test_characters):
        """Test building section with character states."""
        char = test_characters[0]
        CharacterStateManager.update_character_state(
            char,
            segment_id="seg_1",
            emotion="determined",
            status="present",
            notes="Starting the quest"
        )
        
        section = CharacterContextBuilder.build_character_section(
            [char],
            current_segment_id="seg_1"
        )
        
        assert "determined" in section
        assert "Starting the quest" in section
        assert "present" in section
    
    def test_build_character_section_max_chars(self, test_characters):
        """Test limiting number of characters in section."""
        section = CharacterContextBuilder.build_character_section(
            test_characters,
            current_segment_id="seg_1",
            max_chars=2
        )
        
        assert "Hero" in section
        assert "Companion" in section
        assert "Villain" not in section
    
    def test_build_character_instructions(self, test_characters):
        """Test building character consistency instructions."""
        instructions = CharacterContextBuilder.build_character_instructions(test_characters)
        
        assert "CHARACTER CONSISTENCY INSTRUCTIONS" in instructions
        assert "Hero" in instructions
        assert "Companion" in instructions
        assert "Villain" in instructions
    
    def test_build_character_instructions_with_emotions(self, test_characters):
        """Test instructions include emotional consistency."""
        char = test_characters[0]
        CharacterStateManager.update_character_state(
            char,
            segment_id="seg_1",
            emotion="afraid"
        )
        
        instructions = CharacterContextBuilder.build_character_instructions([char])
        
        assert "Emotional consistency" in instructions
        assert "Hero" in instructions
    
    def test_extract_character_updates_from_text(self, test_characters):
        """Test extracting character updates from generated text."""
        characters_dict = {char.id: char for char in test_characters}
        
        text = """
        Hero walked into the room, feeling very happy about the discovery.
        Companion seemed happy by what they found.
        Villain appeared, looking angry and determined to stop them.
        """
        
        updates = CharacterContextBuilder.extract_character_updates_from_text(
            text,
            characters_dict,
            "seg_2"
        )
        
        # Check that all characters are recognized
        assert "hero" in updates
        assert "companion" in updates
        assert "villain" in updates
        
        # All should have some status (emotion extraction is simplified)
        assert updates["hero"]["status"] == "present"
        assert updates["companion"]["status"] == "present"
        assert updates["villain"]["status"] == "present"
    
    def test_extract_character_updates_partial_mentions(self, test_characters):
        """Test extracting updates when only some characters are mentioned."""
        characters_dict = {char.id: char for char in test_characters}
        
        text = "Hero and Companion arrived at the castle."
        
        updates = CharacterContextBuilder.extract_character_updates_from_text(
            text,
            characters_dict,
            "seg_2"
        )
        
        # Hero and Companion should have updates (mentioned in text)
        assert "hero" in updates
        assert "companion" in updates
        # Villain should not have updates (not mentioned)
        assert "villain" not in updates
    
    def test_extract_character_updates_no_mentions(self, test_characters):
        """Test extracting updates when characters aren't mentioned."""
        characters_dict = {char.id: char for char in test_characters}
        
        text = "The forest was quiet and still."
        
        updates = CharacterContextBuilder.extract_character_updates_from_text(
            text,
            characters_dict,
            "seg_2"
        )
        
        # No updates since no characters mentioned
        assert len(updates) == 0
    
    def test_integrate_character_context_into_prompt(self, test_characters):
        """Test integrating character context into prompt."""
        base_prompt = "Generate a scene where the hero makes a choice."
        
        enhanced = CharacterContextBuilder.integrate_character_context_into_prompt(
            base_prompt,
            test_characters,
            "seg_1",
            include_instructions=True
        )
        
        assert "Generate a scene where the hero makes a choice." in enhanced
        assert "CHARACTER INFORMATION" in enhanced
        assert "CHARACTER CONSISTENCY INSTRUCTIONS" in enhanced
        assert "Hero" in enhanced
    
    def test_integrate_character_context_without_instructions(self, test_characters):
        """Test integrating without consistency instructions."""
        base_prompt = "Generate a scene."
        
        enhanced = CharacterContextBuilder.integrate_character_context_into_prompt(
            base_prompt,
            test_characters,
            "seg_1",
            include_instructions=False
        )
        
        assert "CHARACTER INFORMATION" in enhanced
        assert "CHARACTER CONSISTENCY INSTRUCTIONS" not in enhanced
    
    def test_validate_and_apply_character_updates(self, test_characters):
        """Test validating and applying character updates."""
        characters_dict = {char.id: char for char in test_characters}
        
        updates = {
            "hero": {
                "segment_id": "seg_2",
                "emotion": "triumphant",
                "status": "present",
                "notes": "Defeated the enemy"
            },
            "companion": {
                "segment_id": "seg_2",
                "emotion": "grateful",
                "status": "present",
                "notes": "Hero saved the day"
            }
        }
        
        warnings = CharacterContextBuilder.validate_and_apply_character_updates(
            characters_dict,
            updates
        )
        
        assert len(warnings) == 0
        assert len(test_characters[0].running_status) == 1
        assert test_characters[0].running_status[0]["emotion"] == "triumphant"
    
    def test_validate_and_apply_unknown_character(self, test_characters):
        """Test warning for unknown character."""
        characters_dict = {char.id: char for char in test_characters}
        
        updates = {
            "unknown_char": {
                "segment_id": "seg_2",
                "emotion": "happy",
                "status": "present"
            }
        }
        
        warnings = CharacterContextBuilder.validate_and_apply_character_updates(
            characters_dict,
            updates
        )
        
        assert len(warnings) == 1
        assert "Unknown character ID" in warnings[0]
    
    def test_validate_excessive_changes(self, test_characters):
        """Test warning for excessive character changes."""
        characters_dict = {char.id: char for char in test_characters}
        
        # Create updates for all characters (more than default max)
        updates = {
            char.id: {
                "segment_id": "seg_2",
                "emotion": "very_emotional",
                "status": "present"
            }
            for char in test_characters
        }
        
        warnings = CharacterContextBuilder.validate_and_apply_character_updates(
            characters_dict,
            updates,
            max_emotional_change=2
        )
        
        # Should have warning about high volatility
        assert any("High character volatility" in w for w in warnings)
    
    def test_character_context_persistence(self, test_story):
        """Test that character context persists through save/load."""
        char = StoryCharacter(
            story=test_story,
            id="persistent_char",
            story_id=test_story.id,
            name="Persistent",
            description="A persistent character",
            background="Background",
            avatar_shape=AvatarShape.STAR,
            avatar_color="#FFD700"
        )
        
        # Add states
        CharacterStateManager.update_character_state(
            char,
            segment_id="seg_1",
            emotion="hopeful"
        )
        CharacterStateManager.update_character_state(
            char,
            segment_id="seg_2",
            emotion="determined"
        )
        
        # Save character
        char.save()
        
        # Load and rebuild context
        loaded = StoryCharacter.load(test_story.id, char.id, story=test_story)
        
        # Build context from loaded character
        section = CharacterContextBuilder.build_character_section(
            [loaded],
            current_segment_id="seg_2"
        )
        
        assert "Persistent" in section
        assert "determined" in section
        assert "#FFD700" in section
