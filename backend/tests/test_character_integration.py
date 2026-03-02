"""Tests for character integration in the generation pipeline."""

import pytest
from app.models.story import Story
from app.models.story_character import StoryCharacter, AvatarShape
from app.models.story_segment import StorySegment
from app.utils.character_context_builder import CharacterContextBuilder
from app.utils.character_state_manager import CharacterStateManager


@pytest.fixture
def sample_story():
    """Create a test story with characters."""
    story = Story(
        id="test_story",
        title="Test Story",
        description="A test story for character integration",
        genre="fantasy"
    )
    return story


@pytest.fixture
def sample_characters(sample_story):
    """Create test characters."""
    eira = StoryCharacter(
        story=sample_story,
        id="eira",
        story_id="test_story",
        name="Eira",
        description="A mysterious elf archer",
        background="Lost her family in the northern wastes",
        avatar_shape=AvatarShape.CIRCLE,
        avatar_color="#FF6B6B"
    )
    
    thorne = StoryCharacter(
        story=sample_story,
        id="thorne",
        story_id="test_story",
        name="Thorne",
        description="A gruff dwarf warrior",
        background="Former mining overseer",
        avatar_shape=AvatarShape.SQUARE,
        avatar_color="#4ECDC4"
    )
    
    return {"eira": eira, "thorne": thorne}


@pytest.fixture
def sample_segment(sample_story):
    """Create a test segment."""
    segment = StorySegment(
        id="segment_001",
        story_id="test_story",
        short_description="The journey begins",
        long_description="The party gathers at the tavern",
    )
    sample_story.add_segment(segment)
    return segment


class TestCharacterContextBuilding:
    """Tests for building character context."""
    
    def test_build_character_section(self, sample_characters):
        """Test building a character section for prompts."""
        characters = list(sample_characters.values())
        
        section = CharacterContextBuilder.build_character_section(
            characters,
            "segment_001",
            include_arcs=True
        )
        
        assert "CHARACTER INFORMATION" in section
        assert "Eira" in section
        assert "Thorne" in section
        assert "circle" in section.lower()
        assert "square" in section.lower()
    
    def test_build_character_instructions(self, sample_characters):
        """Test building character consistency instructions."""
        characters = list(sample_characters.values())
        
        instructions = CharacterContextBuilder.build_character_instructions(characters)
        
        assert "CHARACTER CONSISTENCY INSTRUCTIONS" in instructions
        assert "Eira" in instructions
        assert "Thorne" in instructions
        assert "character names" in instructions.lower()
    
    def test_integrate_character_context_into_prompt(self, sample_characters):
        """Test integrating character context into a base prompt."""
        characters = list(sample_characters.values())
        base_prompt = "Continue the story from here:"
        
        enhanced_prompt = CharacterContextBuilder.integrate_character_context_into_prompt(
            base_prompt,
            characters,
            "segment_001",
            include_instructions=True
        )
        
        assert "Continue the story from here:" in enhanced_prompt
        assert "CHARACTER INFORMATION" in enhanced_prompt
        assert "CHARACTER CONSISTENCY INSTRUCTIONS" in enhanced_prompt
        assert "Eira" in enhanced_prompt
        assert "Thorne" in enhanced_prompt


class TestCharacterStateUpdates:
    """Tests for updating character states after generation."""
    
    def test_extract_character_updates_from_text(self, sample_characters):
        """Test extracting character updates from generated text."""
        text = """
        Eira enters the tavern, her face filled with determination.
        She looks worried about what's to come.
        Thorne sits in the corner, looking angry at the situation.
        He seems determined to join the quest.
        """
        
        updates = CharacterContextBuilder.extract_character_updates_from_text(
            text,
            sample_characters,
            "segment_002"
        )
        
        # Should have updates for both characters
        assert "eira" in updates or "thorne" in updates
        
        # Check that updates have proper structure
        for char_id, update in updates.items():
            assert "segment_id" in update
            assert update["segment_id"] == "segment_002"
            assert "status" in update
            assert update["status"] in ["present", "absent", "mentioned"]
    
    def test_validate_and_apply_character_updates(self, sample_characters):
        """Test validating and applying character updates."""
        updates = {
            "eira": {
                "segment_id": "segment_002",
                "emotion": "determined",
                "status": "present",
                "notes": "Leading the charge"
            },
            "thorne": {
                "segment_id": "segment_002",
                "emotion": "angry",
                "status": "present",
                "notes": "Fighting hard"
            }
        }
        
        warnings = CharacterContextBuilder.validate_and_apply_character_updates(
            sample_characters,
            updates,
            max_emotional_change=5
        )
        
        # Check that updates were applied
        assert sample_characters["eira"].get_state_at_segment("segment_002") is not None
        assert sample_characters["thorne"].get_state_at_segment("segment_002") is not None
        
        # Check the applied states
        eira_state = sample_characters["eira"].get_state_at_segment("segment_002")
        assert eira_state["emotion"] == "determined"
        assert eira_state["status"] == "present"
        assert eira_state["notes"] == "Leading the charge"


class TestCharacterArcTracking:
    """Tests for tracking character emotional arcs."""
    
    def test_get_character_arc_summary(self, sample_characters):
        """Test getting a character's emotional arc summary."""
        eira = sample_characters["eira"]
        
        # Add some states
        eira.add_state("segment_001", emotion="hopeful", status="present", notes="Starting the journey")
        eira.add_state("segment_002", emotion="worried", status="present", notes="First setback")
        eira.add_state("segment_003", emotion="determined", status="present", notes="Rallying the team")
        
        arc_summary = CharacterStateManager.get_character_arc_summary(eira)
        
        assert arc_summary is not None
        assert len(arc_summary) > 0
        # The summary should mention emotional progression
        assert any(emotion in arc_summary.lower() for emotion in ["hopeful", "worried", "determined"])
    
    def test_character_consistency_across_segments(self, sample_characters):
        """Test that character presence is tracked consistently."""
        eira = sample_characters["eira"]
        
        # Track presence across segments
        eira.add_state("segment_001", emotion="hopeful", status="present")
        eira.add_state("segment_002", emotion=None, status="absent")
        eira.add_state("segment_003", emotion="determined", status="present")
        eira.add_state("segment_004", emotion=None, status="mentioned")
        
        # Get the arc
        arc = eira.get_state_arc()
        
        assert len(arc) == 4
        assert arc[0]["status"] == "present"
        assert arc[1]["status"] == "absent"
        assert arc[2]["status"] == "present"
        assert arc[3]["status"] == "mentioned"


class TestCharacterDataIntegration:
    """Tests for character data endpoints integration."""
    
    def test_character_serialization_for_api(self, sample_characters):
        """Test that characters serialize properly for API responses."""
        eira = sample_characters["eira"]
        eira.add_state("segment_001", emotion="hopeful", status="present", notes="Starting")
        
        # Get the data that would be returned by the API
        api_response = {
            "id": eira.id,
            "name": eira.name,
            "description": eira.description,
            "background": eira.background,
            "avatar_shape": eira.avatar_shape.value,
            "avatar_color": eira.avatar_color,
            "running_status": [state for state in eira.running_status]
        }
        
        # Verify it can be serialized
        assert api_response["id"] == "eira"
        assert api_response["name"] == "Eira"
        assert api_response["avatar_shape"] == "circle"
        assert api_response["avatar_color"] == "#FF6B6B"
        assert len(api_response["running_status"]) > 0
        assert api_response["running_status"][0]["emotion"] == "hopeful"


class TestCharacterPromptIntegration:
    """Tests for character integration in prompt building."""
    
    def test_character_context_with_state_history(self, sample_characters):
        """Test that character state history is included in prompt context."""
        characters = list(sample_characters.values())
        
        # Add some state history
        for char in characters:
            char.add_state("segment_001", emotion="hopeful", status="present")
            char.add_state("segment_002", emotion="determined", status="present")
        
        # Build context
        context = CharacterContextBuilder.build_character_section(
            characters,
            "segment_002",
            include_arcs=True
        )
        
        # Should include current state
        assert "determined" in context.lower()
        # Should include arc information
        assert "Arc:" in context or "arc" in context.lower()
    
    def test_empty_character_list_handling(self):
        """Test that empty character list is handled gracefully."""
        section = CharacterContextBuilder.build_character_section([], "segment_001")
        assert section == ""
        
        instructions = CharacterContextBuilder.build_character_instructions([])
        assert instructions == ""
