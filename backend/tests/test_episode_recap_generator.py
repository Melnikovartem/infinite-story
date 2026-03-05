"""Tests for EpisodeRecapGenerator (E2-1, E2-2)."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, UTC

from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode as EpisodeRecap, CharacterState
from app.models.text_types import TextBlock, TextType
from app.engine.episode_recap_generator import EpisodeRecapGenerator


@pytest.fixture
def sample_story():
    """Create a test story."""
    return Story(
        id="test_story",
        title="Test Story",
        description="A test story",
        genre="Fantasy"
    )


@pytest.fixture
def sample_arc(sample_story):
    """Create a test arc."""
    arc = StoryArc(
        id="arc_1",
        story_id=sample_story.id,
        title="The First Arc",
        premise="A hero's journey begins",
        narrative_direction="Toward self-discovery",
        start_segment_id="seg_1"
    )
    return arc


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator."""
    gen = AsyncMock()
    
    # Default response for generate
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        response.title = "Test Episode Title"
        response.summary = "A test episode summary"
        response.key_themes = ["theme1", "theme2"]
        response.tone_tags = ["dramatic"]
        response.end_condition = "Test condition met"
        response.narrative_direction = "Story progresses"
        return response
    
    gen.generate = mock_generate
    return gen


class TestEpisodeRecapGeneratorBasics:
    """Tests for basic EpisodeRecapGenerator functionality."""
    
    def test_init(self, sample_story, mock_generator):
        """Initialize EpisodeRecapGenerator."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        assert gen.story == sample_story
        assert gen.generator == mock_generator
    
    def test_walk_episode_segments_empty(self, sample_story, mock_generator):
        """Walk returns empty list when no segments exist."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        segments = gen._walk_episode_segments(1)
        
        assert segments == []
    
    def test_walk_episode_segments_single(self, sample_story, mock_generator):
        """Walk returns single segment when only one exists."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="First scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene")
            ]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        segments = gen._walk_episode_segments(1)
        
        assert len(segments) == 1
        assert segments[0].id == "seg_1"
    
    def test_walk_episode_segments_chain(self, sample_story, mock_generator):
        """Walk collects all segments in episode chain."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="First scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 1")
            ]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            episode_number=1,
            parent_segment_id="seg_1",
            short_description="Second scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 2")
            ]
        )
        
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            episode_number=2,
            parent_segment_id="seg_2",
            short_description="Third scene (ep 2)",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 3")
            ]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        segments = gen._walk_episode_segments(1)
        
        assert len(segments) == 2
        assert segments[0].id == "seg_1"
        assert segments[1].id == "seg_2"
    
    def test_walk_episode_segments_respects_arc(self, sample_story, mock_generator):
        """Walk respects arc_id filter."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            arc_id="arc_1",
            short_description="First scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 1")
            ]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            episode_number=1,
            arc_id="arc_2",
            parent_segment_id="seg_1",
            short_description="Second scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 2")
            ]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        # Without arc filter, should get both
        segments = gen._walk_episode_segments(1)
        assert len(segments) == 2
        
        # With arc_1 filter, should get only seg_1
        segments = gen._walk_episode_segments(1, arc_id="arc_1")
        assert len(segments) == 1
        assert segments[0].id == "seg_1"


class TestEpisodeRecapGeneratorCollection:
    """Tests for data collection methods."""
    
    def test_collect_changes_empty(self, sample_story, mock_generator):
        """Collect returns empty list when no changes."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="Scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            change_notes=[]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        changes = gen._collect_changes([seg])
        
        assert changes == []
    
    def test_collect_changes_multiple(self, sample_story, mock_generator):
        """Collect aggregates change notes from all segments."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ],
            change_notes=["Alice learns a secret", "Bob becomes angry"]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            episode_number=1,
            parent_segment_id="seg_1",
            short_description="Scene 2",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")
            ],
            change_notes=["Alice makes a choice"]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        changes = gen._collect_changes([seg1, seg2])
        
        assert len(changes) == 3
        assert "Alice learns a secret" in changes
        assert "Bob becomes angry" in changes
        assert "Alice makes a choice" in changes
    
    def test_extract_starting_states_empty(self, sample_story, mock_generator):
        """Extract returns empty dict when no states."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="Scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            character_states={}
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        states = gen._extract_starting_states([seg])
        
        assert states == {}
    
    def test_extract_starting_states_from_dict(self, sample_story, mock_generator):
        """Extract converts dict character states to CharacterState objects."""
        char_state_dict = {
            "char_1": {
                "name": "Alice",
                "status": "alive",
                "mood": "hopeful",
                "loyalty": 0.8
            }
        }
        
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="Scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            character_states=char_state_dict
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        states = gen._extract_starting_states([seg])
        
        assert "char_1" in states
        assert isinstance(states["char_1"], CharacterState)
        assert states["char_1"].name == "Alice"
        assert states["char_1"].mood == "hopeful"


class TestEpisodeRecapGeneratorPromptBuilding:
    """Tests for prompt building methods."""
    
    def test_build_recap_prompt_structure(self, sample_story, mock_generator):
        """Build recap prompt contains all required sections."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="First scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        prompt = gen._build_recap_prompt([seg], ["Change 1"], 1, None)
        
        assert "EPISODE 1" in prompt
        assert "KEY SCENES" in prompt
        assert "CHARACTER CHANGES" in prompt
        assert "Change 1" in prompt
        assert "narrative recap" in prompt.lower()
    
    def test_build_episode_generation_prompt_without_recap(self, sample_story, sample_arc, mock_generator):
        """Build episode prompt without previous recap."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        prompt = gen._build_episode_generation_prompt(sample_arc, None)
        
        assert sample_arc.title in prompt
        assert sample_arc.premise in prompt
        assert "NEXT EPISODE" in prompt
        assert "tone_tags" in prompt


class TestEpisodeRecapGeneratorCharacterReconciliation:
    """Tests for character state reconciliation."""
    
    def test_reconcile_character_states_empty(self, sample_story, mock_generator):
        """Reconcile empty states."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        result = gen._reconcile_character_states({}, [])
        
        assert result == {}
    
    def test_reconcile_character_states_copies(self, sample_story, mock_generator):
        """Reconcile creates copies of character states."""
        initial_state = CharacterState(
            id="char_1",
            name="Alice",
            status="alive",
            mood="hopeful",
            loyalty=0.8,
            relationships={"char_2": "trusts"}
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        result = gen._reconcile_character_states({"char_1": initial_state}, [])
        
        assert "char_1" in result
        assert result["char_1"].name == "Alice"
        # Verify it's a copy, not the same object
        assert result["char_1"] is not initial_state
    
    def test_reconcile_preserves_fields(self, sample_story, mock_generator):
        """Reconcile preserves all character state fields."""
        initial_state = CharacterState(
            id="char_1",
            name="Alice",
            status="alive",
            mood="determined",
            loyalty=-0.5,
            location="castle",
            relationships={"char_2": "enemy", "char_3": "ally"},
            goals=["Defeat the villain", "Save the kingdom"],
            custom_data={"wounds": 2}
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        result = gen._reconcile_character_states({"char_1": initial_state}, [])
        
        result_state = result["char_1"]
        assert result_state.location == "castle"
        assert result_state.loyalty == -0.5
        assert len(result_state.relationships) == 2
        assert len(result_state.goals) == 2
        assert result_state.custom_data["wounds"] == 2
    
    @pytest.mark.asyncio
    async def test_generate_new_episode_context_flow(self, sample_story, sample_arc, mock_generator):
        """Full new episode context generation."""
        # Save arc so it can be loaded
        sample_arc.save()
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        context = await gen.generate_new_episode_context(sample_arc.id)
        
        assert "tone_tags" in context
        assert "end_condition" in context
        assert "narrative_direction" in context
        assert isinstance(context["tone_tags"], list)
        assert context["end_condition"]
        assert context["narrative_direction"]
    
    @pytest.mark.asyncio
    async def test_generate_recap_handles_ai_error(self, sample_story, mock_generator):
        """Generate recap handles AI generation errors gracefully."""
        # Mock generator that returns error
        error_gen = AsyncMock()
        async def mock_generate_with_error(system_prompt, user_prompt, context_type):
            response = MagicMock()
            response.error = "AI generation failed"
            return response
        
        error_gen.generate = mock_generate_with_error
        
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="Scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            episode_tone="neutral"
        )
        
        gen = EpisodeRecapGenerator(sample_story, error_gen)
        recap = await gen.generate_recap(1)
        
        # Should still create recap with fallback values
        assert recap.episode_number == 1
        assert "Episode 1" in recap.title
        assert recap.summary != ""


@pytest.mark.asyncio
class TestEpisodeRecapGeneratorFull:
    """Full integration tests for recap generation."""
    
    async def test_generate_recap_full_flow(self, sample_story, mock_generator):
        """Full recap generation flow."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            episode_number=1,
            short_description="Opening scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 1")
            ],
            character_states={
                "char_1": {
                    "name": "Alice",
                    "status": "alive",
                    "mood": "hopeful"
                }
            },
            change_notes=["Alice learns the truth"],
            episode_tone="dramatic"
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            episode_number=1,
            parent_segment_id="seg_1",
            short_description="Climax scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 2")
            ],
            change_notes=["Alice makes her choice"]
        )
        
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        recap = await gen.generate_recap(1)
        
        assert recap.episode_number == 1
        assert recap.story_id == sample_story.id
        assert "seg_1" in recap.segment_ids
        assert "seg_2" in recap.segment_ids
        assert recap.tone == "dramatic"
        assert len(recap.key_themes) > 0
    
    async def test_generate_recap_no_segments_raises(self, sample_story, mock_generator):
        """Generate recap raises when no segments found."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        with pytest.raises(ValueError, match="No segments found"):
            await gen.generate_recap(99)


class TestEpisodeRecapGeneratorArcIntegration:
    """Tests for arc integration."""
    
    @pytest.mark.asyncio
    async def test_generate_new_episode_context_missing_arc_raises(self, sample_story, mock_generator):
        """Generate new episode context raises when arc not found."""
        gen = EpisodeRecapGenerator(sample_story, mock_generator)
        
        with pytest.raises(ValueError, match="Arc .* not found"):
            await gen.generate_new_episode_context("nonexistent_arc")
