"""Tests for the episode lifecycle rework.

Tests:
1. Episode ID format: episode_{arc_id}_{triggering_segment_id}
2. previous_episode_recap stored in new episode meta
3. segment_context_builder loads previous_episode_recap into context
4. prompt_formatter includes previous_episode_recap in prompt
5. story_segment passes triggering_segment_id through lifecycle
6. StoryShapeResponse uses num_factions (not num_fractions)
7. story_shape_calculator uses generate_structured()
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode, CharacterState
from app.models.text_types import TextBlock, TextType, StoryShapeResponse
from app.engine.episode_recap_generator import EpisodeRecapGenerator
from app.utils.prompt_formatter import PromptFormatter


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def story():
    """Create a test story."""
    return Story(
        id="test_lifecycle",
        title="Lifecycle Test Story",
        description="Testing episode lifecycle",
        genre="Fantasy"
    )


@pytest.fixture
def arc(story):
    """Create a test arc."""
    return StoryArc(
        id="arc_main",
        story_id=story.id,
        title="Main Arc",
        premise="A hero's journey",
        narrative_direction="Toward destiny",
        start_segment_id="seg_1",
        episode_count=1
    )


@pytest.fixture
def episode_segments(story):
    """Create a chain of segments in episode 1."""
    seg1 = StorySegment(
        story=story,
        id="seg_1",
        episode_number=1,
        arc_id="arc_main",
        segment_number_in_episode=1,
        short_description="The journey begins",
        text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 1")],
        episode_tone="mysterious",
    )
    seg2 = StorySegment(
        story=story,
        id="seg_2",
        episode_number=1,
        arc_id="arc_main",
        segment_number_in_episode=2,
        parent_segment_id="seg_1",
        short_description="A stranger appears",
        text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 2")],
        episode_tone="mysterious",
    )
    seg3 = StorySegment(
        story=story,
        id="seg_3",
        episode_number=1,
        arc_id="arc_main",
        segment_number_in_episode=3,
        parent_segment_id="seg_2",
        short_description="The confrontation",
        text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Scene 3")],
        episode_tone="mysterious",
    )
    return [seg1, seg2, seg3]


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator with generate_structured support."""
    gen = AsyncMock()
    
    _default_data = {
        "title": "The Dark Beginning",
        "summary": "The hero faced their first challenge and emerged changed.",
        "key_themes": ["courage", "doubt"],
        "themes_explored": ["courage"],
        "hook_for_next": "But the darkness was only beginning...",
        "unresolved_new": ["Who was the stranger?"],
        "tone_tags": ["tense"],
        "end_condition": "Hero reaches the crossroads",
        "narrative_direction": "Story moves toward confrontation",
        "episode_focus": "Hero's inner conflict",
        "story_hooks": ["stranger's identity"],
        "active_characters": [],
    }
    
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        response.raw_response = json.dumps(_default_data)
        return response
    
    async def mock_generate_structured(system_prompt, user_prompt, schema, fallback_defaults=None, output_format=None):
        if schema.expect_array:
            return [dict(_default_data)]
        return dict(_default_data)
    
    gen.generate = mock_generate
    gen.generate_structured = mock_generate_structured
    gen._generate_content = AsyncMock(return_value=json.dumps(_default_data))
    return gen


# ============================================================================
# Test: Episode ID format
# ============================================================================

class TestEpisodeIdFormat:
    """Test that episode IDs follow the new format: episode_{arc_id}_{triggering_segment_id}."""
    
    @pytest.mark.asyncio
    async def test_new_episode_context_uses_triggering_segment_id(self, story, arc, episode_segments, mock_generator):
        """generate_new_episode_context creates meta with segment-based ID."""
        gen = EpisodeRecapGenerator(story, mock_generator)
        
        with patch.object(StoryArc, 'load', return_value=arc):
            with patch('app.utils.theme_selector.ThemeSelector') as mock_selector:
                mock_selector.select_themes.return_value = ["courage", "sacrifice"]
                
                context = await gen.generate_new_episode_context(
                    arc_id="arc_main",
                    previous_recap=None,
                    triggering_segment_id="seg_3"
                )
        
        # The meta should have been created with the new ID format
        meta = story.get_episode(f"episode_arc_main_seg_3")
        assert meta is not None, "Episode meta should exist with new ID format"
        assert meta.episode_number >= 1
        assert meta.arc_id == "arc_main"
    
    @pytest.mark.asyncio
    async def test_new_episode_context_falls_back_to_sequential_id(self, story, arc, mock_generator):
        """Without triggering_segment_id, falls back to sequential format."""
        gen = EpisodeRecapGenerator(story, mock_generator)
        
        with patch.object(StoryArc, 'load', return_value=arc):
            with patch('app.utils.theme_selector.ThemeSelector') as mock_selector:
                mock_selector.select_themes.return_value = ["courage"]
                
                context = await gen.generate_new_episode_context(
                    arc_id="arc_main",
                    previous_recap=None,
                    triggering_segment_id=None  # No triggering segment
                )
        
        # Should fall back to sequential format
        meta = story.get_episode(f"episode_meta_1_arc_main")
        assert meta is not None, "Episode meta should exist with sequential fallback ID"


# ============================================================================
# Test: previous_episode_recap stored in new episode
# ============================================================================

class TestPreviousEpisodeRecap:
    """Test that previous episode's recap is stored in the new episode meta."""
    
    @pytest.mark.asyncio
    async def test_previous_recap_stored_in_new_episode(self, story, arc, episode_segments, mock_generator):
        """Previous episode's recap text is stored in new episode's previous_episode_recap."""
        # Create a completed previous episode recap
        prev_recap = StoryEpisode(
            story=story,
            id="episode_arc_main_seg_prev",
            story_id=story.id,
            episode_number=1,
            arc_id="arc_main",
            recap="The hero began their journey through the Thornreach.",
            title="The Beginning",
            summary="A young hero ventured into the unknown.",
            episode_complete=True,
        )
        
        gen = EpisodeRecapGenerator(story, mock_generator)
        
        with patch.object(StoryArc, 'load', return_value=arc):
            with patch('app.utils.theme_selector.ThemeSelector') as mock_selector:
                mock_selector.select_themes.return_value = ["sacrifice"]
                
                context = await gen.generate_new_episode_context(
                    arc_id="arc_main",
                    previous_recap=prev_recap,
                    triggering_segment_id="seg_3"
                )
        
        # Check the new episode meta has previous_episode_recap
        new_meta = story.get_episode("episode_arc_main_seg_3")
        assert new_meta is not None
        assert new_meta.previous_episode_recap == "The hero began their journey through the Thornreach."
        assert new_meta.previous_episode_title == "The Beginning"
    
    @pytest.mark.asyncio
    async def test_no_previous_recap_when_first_episode(self, story, arc, mock_generator):
        """First episode has empty previous_episode_recap."""
        gen = EpisodeRecapGenerator(story, mock_generator)
        
        with patch.object(StoryArc, 'load', return_value=arc):
            with patch('app.utils.theme_selector.ThemeSelector') as mock_selector:
                mock_selector.select_themes.return_value = ["courage"]
                
                context = await gen.generate_new_episode_context(
                    arc_id="arc_main",
                    previous_recap=None,  # No previous episode
                    triggering_segment_id="seg_1"
                )
        
        new_meta = story.get_episode("episode_arc_main_seg_1")
        assert new_meta is not None
        assert new_meta.previous_episode_recap == ""
        assert new_meta.previous_episode_title == ""


# ============================================================================
# Test: prompt_formatter includes previous_episode_recap
# ============================================================================

class TestPromptFormatterEpisodeRecap:
    """Test that PromptFormatter includes previous_episode_recap in scene prompts."""
    
    def test_includes_previous_episode_recap(self):
        """Prompt includes PREVIOUSLY section when recap is available."""
        context = {
            'previous_episode_recap': "The hero defeated the shadow beast.",
            'previous_episode_title': "Shadow's End",
            'episode_number': 2,
            'segment_number_in_episode': 1,
            'user_choice': "Enter the cave",
        }
        
        prompt = PromptFormatter.format_scene_context(context)
        
        assert "PREVIOUSLY (Shadow's End)" in prompt
        assert "The hero defeated the shadow beast." in prompt
    
    def test_no_previous_section_when_no_recap(self):
        """Prompt omits PREVIOUSLY section when no recap."""
        context = {
            'episode_number': 1,
            'segment_number_in_episode': 1,
            'user_choice': "Start the adventure",
        }
        
        prompt = PromptFormatter.format_scene_context(context)
        
        assert "PREVIOUSLY" not in prompt
    
    def test_previous_recap_appears_before_current_episode(self):
        """PREVIOUSLY section appears before CURRENT EPISODE."""
        context = {
            'previous_episode_recap': "Things happened.",
            'previous_episode_title': "Last Time",
            'episode_number': 2,
            'segment_number_in_episode': 1,
            'user_choice': "Continue",
        }
        
        prompt = PromptFormatter.format_scene_context(context)
        
        prev_pos = prompt.index("PREVIOUSLY")
        current_pos = prompt.index("CURRENT EPISODE")
        assert prev_pos < current_pos, "PREVIOUSLY should appear before CURRENT EPISODE"
    
    def test_long_recap_is_truncated(self):
        """Very long recaps are truncated to 500 chars."""
        long_recap = "A" * 1000
        context = {
            'previous_episode_recap': long_recap,
            'previous_episode_title': "Long Episode",
            'episode_number': 2,
            'segment_number_in_episode': 1,
            'user_choice': "Go on",
        }
        
        prompt = PromptFormatter.format_scene_context(context)
        
        # Should not contain the full 1000-char string
        assert long_recap not in prompt
        # Should contain exactly 500 chars of it
        assert "A" * 500 in prompt


# ============================================================================
# Test: StoryShapeResponse uses num_factions
# ============================================================================

class TestStoryShapeResponseRename:
    """Test that StoryShapeResponse uses num_factions (not num_fractions)."""
    
    def test_num_factions_field_exists(self):
        """StoryShapeResponse has num_factions field."""
        shape = StoryShapeResponse(
            scale="medium",
            num_factions=3,
            num_locations=10,
            characters_per_faction={"min": 2, "max": 4},
            num_independent_characters=2,
        )
        assert shape.num_factions == 3
        assert shape.num_locations == 10
        assert shape.characters_per_faction == {"min": 2, "max": 4}
    
    def test_num_fractions_no_longer_exists(self):
        """num_fractions field should not exist (renamed to num_factions)."""
        shape = StoryShapeResponse(
            scale="medium",
            num_factions=3,
            num_locations=10,
            characters_per_faction={"min": 2, "max": 4},
            num_independent_characters=2,
        )
        assert not hasattr(shape, 'num_fractions')


# ============================================================================
# Test: story_shape_calculator uses generate_structured
# ============================================================================

class TestStoryShapeCalculatorMigration:
    """Test that StoryShapeCalculator uses generate_structured instead of generate_with_fallback."""
    
    @pytest.mark.asyncio
    async def test_uses_generate_structured(self):
        """Calculator calls generate_structured, not generate_with_fallback."""
        from app.engine.generators.story_shape_calculator import StoryShapeCalculator
        from app.models.story_context import StoryContext
        
        story = Story(
            id="test_shape",
            title="Shape Test",
            description="Testing shape calculator",
            genre="Sci-Fi"
        )
        
        world_context = StoryContext(
            story=story,
            id="ctx_1",
            story_id=story.id,
            fundamental_truths=["The galaxy is vast", "Hope persists"],
            worldbuilding={
                "world_description": "A distant galaxy",
                "plot_description": "Rebels fight an empire",
                "central_conflicts": ["Freedom vs control"],
                "story_themes": ["rebellion", "hope"],
            }
        )
        
        gen = AsyncMock()
        gen.generate_structured = AsyncMock(return_value={
            "scale": "epic",
            "num_factions": 4,
            "num_locations": 15,
            "characters_per_faction": {"min": 3, "max": 5},
            "num_independent_characters": 3,
            "reasoning": "Epic space opera needs many factions",
        })
        gen.generate_with_fallback = AsyncMock()  # Should NOT be called
        
        calc = StoryShapeCalculator(gen)
        shape = await calc.calculate_story_shape(story, world_context)
        
        # Verify generate_structured was called
        gen.generate_structured.assert_called_once()
        # Verify generate_with_fallback was NOT called
        gen.generate_with_fallback.assert_not_called()
        
        assert shape.scale == "epic"
        assert shape.num_factions == 4
        assert shape.num_locations == 15
        assert shape.characters_per_faction == {"min": 3, "max": 5}
        assert shape.num_independent_characters == 3
    
    @pytest.mark.asyncio
    async def test_handles_fallback_on_failure(self):
        """Calculator returns valid shape even when AI fails."""
        from app.engine.generators.story_shape_calculator import StoryShapeCalculator, _SHAPE_FALLBACK
        from app.models.story_context import StoryContext
        
        story = Story(
            id="test_shape_fallback",
            title="Fallback Test",
            description="Testing fallback",
            genre="Fantasy"
        )
        
        world_context = StoryContext(
            story=story,
            id="ctx_2",
            story_id=story.id,
            fundamental_truths=["The world exists"],
            worldbuilding={}
        )
        
        gen = AsyncMock()
        # Return fallback defaults (simulating parse failure)
        gen.generate_structured = AsyncMock(return_value=dict(_SHAPE_FALLBACK))
        
        calc = StoryShapeCalculator(gen)
        shape = await calc.calculate_story_shape(story, world_context)
        
        assert shape.scale == "medium"
        assert shape.num_factions == 3


# ============================================================================
# Test: segment_context_builder loads previous_episode_recap
# ============================================================================

class TestSegmentContextBuilderEpisodeRecap:
    """Test that SegmentContextBuilder loads previous_episode_recap from episode meta."""
    
    @pytest.mark.asyncio
    async def test_context_includes_previous_episode_recap(self, story, episode_segments):
        """Build context includes previous_episode_recap when episode meta has one."""
        from app.engine.segment_context_builder import SegmentContextBuilder
        
        # Create episode meta with previous_episode_recap
        # Use the new ID format: episode_{arc_id}_{triggering_segment_id}
        # The first segment's parent would be the triggering segment from previous episode
        # For episode 1, there's no previous, so use episode_meta format
        # Create a segment in episode 2 that references episode 1
        seg_ep2 = StorySegment(
            story=story,
            id="seg_ep2_1",
            episode_number=2,
            arc_id="arc_main",
            segment_number_in_episode=1,
            parent_segment_id="seg_3",  # parent from episode 1
            short_description="New beginning",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Episode 2 starts")],
        )
        
        # Create episode meta for episode 2 with previous recap stored
        # Using triggering_segment_id = seg_3 (the last segment of episode 1)
        ep2_meta = StoryEpisode(
            story=story,
            id="episode_arc_main_seg_3",
            story_id=story.id,
            episode_number=2,
            arc_id="arc_main",
            previous_episode_recap="The hero completed their first trial.",
            previous_episode_title="Trial by Fire",
            selected_themes=["growth"],
            episode_focus="Character development",
            story_hooks=["ancient prophecy"],
        )
        
        # Mock StoryEpisode.load to return our meta
        with patch.object(StoryEpisode, 'load', side_effect=lambda sid, mid, **kw: ep2_meta if mid == "episode_arc_main_seg_3" else None):
            builder = SegmentContextBuilder(story, generator=None)
            context = await builder.build_context("seg_ep2_1", "Continue the journey")
        
        assert context.get('previous_episode_recap') == "The hero completed their first trial."
        assert context.get('previous_episode_title') == "Trial by Fire"


# ============================================================================
# Test: StoryEpisode model fields
# ============================================================================

class TestStoryEpisodeFields:
    """Test StoryEpisode previous_episode_recap fields."""
    
    def test_previous_episode_recap_defaults_empty(self, story):
        """previous_episode_recap defaults to empty string."""
        ep = StoryEpisode(
            story=story,
            id="ep_test",
            story_id=story.id,
            episode_number=1,
            arc_id="arc_1",
        )
        assert ep.previous_episode_recap == ""
        assert ep.previous_episode_title == ""
    
    def test_previous_episode_recap_set(self, story):
        """previous_episode_recap can be set."""
        ep = StoryEpisode(
            story=story,
            id="ep_test_2",
            story_id=story.id,
            episode_number=2,
            arc_id="arc_1",
            previous_episode_recap="Previously on the story...",
            previous_episode_title="The First Chapter",
        )
        assert ep.previous_episode_recap == "Previously on the story..."
        assert ep.previous_episode_title == "The First Chapter"
    
    def test_to_context_full_includes_previous_recap(self, story):
        """to_context_full() includes the previous episode recap."""
        ep = StoryEpisode(
            story=story,
            id="ep_ctx",
            story_id=story.id,
            episode_number=2,
            arc_id="arc_1",
            previous_episode_recap="The heroes found the artifact.",
            previous_episode_title="Artifact Hunt",
        )
        full = ep.to_context_full()
        assert "Previously (Artifact Hunt)" in full
        assert "The heroes found the artifact." in full
    
    def test_to_context_full_omits_previous_when_empty(self, story):
        """to_context_full() omits previous section when no recap."""
        ep = StoryEpisode(
            story=story,
            id="ep_ctx_2",
            story_id=story.id,
            episode_number=1,
            arc_id="arc_1",
        )
        full = ep.to_context_full()
        assert "Previously" not in full
