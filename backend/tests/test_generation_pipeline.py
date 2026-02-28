"""Tests for the complete AI generation pipeline."""

import pytest
from unittest.mock import AsyncMock, patch
from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice
from app.models.story_context import StoryContext
from app.models.text_types import TextType, TextBlock, SceneTextGeneratorResponse
from app.engine.generator import TextGenerator


class MockSceneGenerator(TextGenerator):
    """Mock generator for testing scene generation."""
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.last_user_prompt = None
    
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Return a consistent mock scene response."""
        self.call_count += 1
        self.last_user_prompt = user_prompt
        
        return '''{
            "short_description": "A mystical chamber appears before you",
            "text_blocks": [
                {
                    "type": "narrator_describing",
                    "content": "The air shimmers with magical energy.",
                    "emotion": "mystical"
                },
                {
                    "type": "character_speech",
                    "content": "This is where it all begins...",
                    "character": "char_wizard",
                    "emotion": "knowing"
                }
            ],
            "atmosphere": "magical",
            "time_of_day": "midnight",
            "weather": "clear",
            "key_items": ["crystal", "ancient tome"],
            "characters_present": ["char_wizard"],
            "locations_present": ["loc_tower"],
            "character_status_change": {"char_wizard": "casting a spell"},
            "location_status_change": {"loc_tower": "glowing with magic"},
            "choice_1": "Touch the crystal",
            "choice_2": "Open the ancient tome"
        }'''


@pytest.fixture
def generation_test_story():
    """Create a complete test story for generation pipeline testing."""
    story = Story(
        id="gen_pipeline_test",
        title="Generation Pipeline Test",
        description="Test story for generation pipeline",
        genre="Fantasy",
        user_id="test_user"
    )
    
    # Add context
    context = StoryContext(
        story=story,
        id="gen_context",
        story_id=story.id,
        fundamental_truths=["Magic is real", "Prophecy guides fate"],
        worldbuilding={"magic": "elemental", "age": "ancient times"}
    )
    story._context = context
    
    # Add entities
    wizard = StoryCharacter(
        story=story,
        id="char_wizard",
        story_id=story.id,
        name="Merlin",
        description="Ancient wizard",
        background="Keeper of secrets"
    )
    
    tower = StoryLocation(
        story=story,
        id="loc_tower",
        story_id=story.id,
        name="Crystal Tower",
        description="A tower of pure crystal"
    )
    
    return story, wizard, tower


@pytest.fixture
def initial_segment(generation_test_story):
    """Create initial segment for generation testing."""
    story, wizard, tower = generation_test_story
    
    segment = StorySegment(
        story=story,
        id="segment_start",
        story_id=story.id,
        short_description="The beginning of your journey",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="You stand at the entrance of an ancient tower."
            )
        ],
        characters_present=["char_wizard"],
        locations_present=["loc_tower"]
    )
    
    return segment


class TestGenerationPipeline:
    """Tests for the complete generation pipeline."""
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_creates_new_segment(self, initial_segment, generation_test_story):
        """Test that generate_next_scene creates a new segment."""
        story, wizard, tower = generation_test_story
        
        # Create choice that needs generation
        choice = StoryChoice(
            story=story,
            id="choice_gen_1",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Enter the tower"
        )
        
        # Mock generator
        generator = MockSceneGenerator()
        
        # Generate next scene
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # Verify new segment was created
        assert new_segment is not None
        assert new_segment.id != initial_segment.id
        assert new_segment.short_description == "A mystical chamber appears before you"
        assert len(new_segment.text_blocks) > 0
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_creates_new_choices(self, initial_segment, generation_test_story):
        """Test that generate_next_scene creates new choices."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_2",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Search the area"
        )
        
        generator = MockSceneGenerator()
        
        # Count choices before
        choices_before = len(story.get_all_choices())
        
        # Generate next scene
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # Count choices after (should add 2 new choices)
        choices_after = len(story.get_all_choices())
        assert choices_after == choices_before + 2
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_updates_choice_destination(self, initial_segment, generation_test_story):
        """Test that generating updates the connecting choice's destination."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_3",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Climb to the top"
        )
        
        assert choice.to_segment_id is None
        
        generator = MockSceneGenerator()
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # Choice should now point to new segment
        assert choice.to_segment_id == new_segment.id
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_preserves_character_states(self, initial_segment, generation_test_story):
        """Test that character running status is preserved and updated."""
        story, wizard, tower = generation_test_story
        
        # Add initial character status
        initial_segment.characters_running_status.append(
            CharacterStatus(character_id="char_wizard", current_status="watching")
        )
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_4",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Ask the wizard for help"
        )
        
        generator = MockSceneGenerator()
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # New segment should have previous status plus new one
        assert len(new_segment.characters_running_status) >= 1
        # Should have the "casting a spell" status from mock
        statuses = [s.current_status for s in new_segment.characters_running_status]
        assert "casting a spell" in statuses
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_includes_context_in_prompt(self, initial_segment, generation_test_story):
        """Test that generation includes story context in the prompt."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_5",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Use magic"
        )
        
        generator = MockSceneGenerator()
        await initial_segment.generate_next_scene(choice, generator)
        
        # Check that prompt was generated
        assert generator.last_user_prompt is not None
        # Should include the choice text
        assert "Use magic" in generator.last_user_prompt
        # Should include current scene description
        assert "beginning of your journey" in generator.last_user_prompt
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_links_segments(self, initial_segment, generation_test_story):
        """Test that segments are properly linked after generation."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_6",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Move forward"
        )
        
        generator = MockSceneGenerator()
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # Check incoming choices on new segment
        assert len(new_segment.incoming_choices) == 1
        assert choice.id in new_segment.incoming_choices
        
        # Check outgoing choices on original segment
        assert len(initial_segment.outgoing_choices) == 1
        assert choice.id in initial_segment.outgoing_choices
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_creates_proper_text_blocks(self, initial_segment, generation_test_story):
        """Test that generated segment has proper text block structure."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_7",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Explore"
        )
        
        generator = MockSceneGenerator()
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # Check text blocks
        assert len(new_segment.text_blocks) > 0
        
        # Should have narrator block and character speech
        block_types = [block.type for block in new_segment.text_blocks]
        assert TextType.NARRATOR_DESCRIBING in block_types
        assert TextType.CHARACTER_SPEECH in block_types
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_handles_entity_present_tracking(self, initial_segment, generation_test_story):
        """Test that generated segment properly tracks characters and locations present."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_8",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Look around"
        )
        
        generator = MockSceneGenerator()
        new_segment = await initial_segment.generate_next_scene(choice, generator)
        
        # Mock response says char_wizard and loc_tower are present
        assert "char_wizard" in new_segment.characters_present
        assert "loc_tower" in new_segment.locations_present
    
    @pytest.mark.asyncio
    async def test_generate_next_scene_error_handling(self, initial_segment, generation_test_story):
        """Test that generation handles errors gracefully."""
        story, wizard, tower = generation_test_story
        
        choice = StoryChoice(
            story=story,
            id="choice_gen_9",
            story_id=story.id,
            from_segment_id="segment_start",
            to_segment_id=None,
            text="Try something"
        )
        
        # Create a generator that returns a valid error response
        class ErrorGenerator(TextGenerator):
            async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
                # Return valid JSON with error field
                return '''{
                    "short_description": "Error scene",
                    "text_blocks": [],
                    "choice_1": "Retry",
                    "choice_2": "Cancel",
                    "error": "API Error occurred"
                }'''
        
        generator = ErrorGenerator()
        
        # Should raise ValueError when error is in response
        with pytest.raises(ValueError, match="Scene generation failed"):
            await initial_segment.generate_next_scene(choice, generator)
