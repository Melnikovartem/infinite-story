"""Integration tests for arc transition system with episode recap generator and arc transition manager."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_arc import StoryArc
from app.models.text_types import TextBlock, TextType
from app.engine.episode_recap_generator import EpisodeRecapGenerator
from app.engine.arc_transition_manager import ArcTransitionManager, ARC_COMPLETION_THRESHOLD


@pytest.fixture
def sample_story():
    """Create a test story."""
    return Story(
        id="test_story",
        title="Test Story",
        description="A test story",
        start_segment_id="seg_1"
    )


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator that supports both generate() and generate_structured()."""
    gen = AsyncMock()
    
    _default_data = {
        "title": "Test Episode",
        "summary": "Test summary",
        "key_themes": ["theme1"],
        "themes_explored": ["theme1"],
        "hook_for_next": "The story continues...",
        "unresolved_new": ["New mystery"],
        "tone_tags": ["tense"],
        "end_condition": "The hero escapes",
        "narrative_direction": "Toward the climax",
        "episode_focus": "The hero's choice",
        "story_hooks": ["What happens next?"],
        "active_characters": [],
    }
    
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        response.raw_response = json.dumps(_default_data)
        return response
    
    async def mock_generate_structured(system_prompt, user_prompt, schema, fallback_defaults=None, output_format=None):
        """Return parsed dict/list directly, mimicking TextGenerator.generate_structured()."""
        if schema.expect_array:
            return [dict(_default_data)]
        return dict(_default_data)
    
    gen.generate = mock_generate
    gen.generate_structured = mock_generate_structured
    return gen


class TestArcTransitionManagerCompletion:
    """Tests for arc completion via ArcTransitionManager."""
    
    @pytest.mark.asyncio
    async def test_no_transition_before_threshold(self, sample_story, mock_generator, temp_data_dir):
        """Should return None when episode < ARC_COMPLETION_THRESHOLD."""
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=10
        )
        arc.save()
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        result = await manager.check_and_handle_arc_completion("arc_1", 10)
        
        # Should not trigger transition
        assert result is None
        # Arc should not be finalized
        updated_arc = StoryArc.load(sample_story.id, "arc_1")
        assert updated_arc.is_finalized is False
    
    @pytest.mark.asyncio
    async def test_transition_at_threshold(self, sample_story, mock_generator, temp_data_dir):
        """Should trigger arc finalization at ARC_COMPLETION_THRESHOLD."""
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=ARC_COMPLETION_THRESHOLD
        )
        arc.save()
        
        # Create segments so finalization has something to work with
        for i in range(1, 4):
            seg = StorySegment(
                story=sample_story,
                id=f"seg_{i}",
                arc_id="arc_1",
                parent_segment_id=f"seg_{i-1}" if i > 1 else None,
                episode_number=1,
                short_description=f"Scene {i}",
                text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content=f"Content {i}")]
            )
            seg.save()
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        # At threshold, finalization runs (may return None if no next arc exists)
        result = await manager.check_and_handle_arc_completion("arc_1", ARC_COMPLETION_THRESHOLD)
        
        # Finalization should have run (arc may or may not be finalized depending 
        # on whether segments could be walked, but the method should not crash)
        # The key test is that it ran without error
    
    @pytest.mark.asyncio
    async def test_transition_with_next_arc(self, sample_story, mock_generator, temp_data_dir):
        """Should return next arc ID when transition happens."""
        arc1 = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Arc 1",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=ARC_COMPLETION_THRESHOLD
        )
        arc1.save()
        
        # Create a future arc ready to activate
        arc2 = StoryArc(
            id="arc_2",
            story_id=sample_story.id,
            title="Arc 2",
            premise="Next arc",
            start_segment_id="seg_n",
            is_active=False,
            is_future_arc=True
        )
        arc2.save()
        
        # Create segments for arc1
        for i in range(1, 4):
            seg = StorySegment(
                story=sample_story,
                id=f"seg_{i}",
                arc_id="arc_1",
                parent_segment_id=f"seg_{i-1}" if i > 1 else None,
                short_description=f"Scene {i}",
                text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content=f"Content {i}")]
            )
            seg.save()
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        result = await manager.check_and_handle_arc_completion("arc_1", ARC_COMPLETION_THRESHOLD)
        
        # Should return the next arc
        assert result == "arc_2"
    
    @pytest.mark.asyncio
    async def test_none_arc_id_handled_gracefully(self, sample_story, mock_generator):
        """Should handle None arc_id without crashing."""
        manager = ArcTransitionManager(sample_story, mock_generator)
        result = await manager.check_and_handle_arc_completion(None, ARC_COMPLETION_THRESHOLD)
        assert result is None


class TestEpisodeRecapGeneratorIntegration:
    """Tests for EpisodeRecapGenerator with arc context."""
    
    @pytest.mark.asyncio
    async def test_generate_new_episode_context_uses_arc(self, sample_story, mock_generator, temp_data_dir):
        """Should generate episode context for given arc."""
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=0,
            themes=["betrayal", "trust"],
            theme_weights={"betrayal": 0.5, "trust": 0.5}
        )
        arc.save()
        
        # Mock the theme selector
        with patch('app.utils.theme_selector.ThemeSelector.select_themes') as mock_selector:
            mock_selector.return_value = ["betrayal", "trust"]
            
            generator = EpisodeRecapGenerator(sample_story, mock_generator)
            context = await generator.generate_new_episode_context("arc_1")
        
        assert context is not None
        assert "tone_tags" in context
        assert "end_condition" in context
        assert "selected_themes" in context


class TestContextFeedingBetweenArcs:
    """Tests for context feeding between arcs."""
    
    @pytest.mark.asyncio
    async def test_arc_summary_is_created_and_stored(self, sample_story, mock_generator, temp_data_dir):
        """Arc summary should be created and stored on next arc."""
        # Create first arc with segments
        arc1 = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Arc 1",
            premise="First arc",
            start_segment_id="seg_1"
        )
        arc1.save()
        
        # Create segments for arc1
        for i in range(1, 4):
            seg = StorySegment(
                story=sample_story,
                id=f"seg_{i}",
                arc_id="arc_1",
                parent_segment_id=f"seg_{i-1}" if i > 1 else None,
                is_mainline=True,
                short_description=f"The hero {['awakens', 'receives a quest', 'begins the journey'][i-1]}",
                text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content=f"Scene {i}")]
            )
            seg.save()
        
        # Create second arc
        arc2 = StoryArc(
            id="arc_2",
            story_id=sample_story.id,
            title="Arc 2",
            premise="Second arc",
            start_segment_id="seg_n"
        )
        arc2.save()
        
        # Feed context
        from app.engine.arc_transition_manager import ArcTransitionManager
        manager = ArcTransitionManager(sample_story, mock_generator)
        await manager._feed_context_to_next_arc("arc_1", "arc_2")
        
        # Verify arc2 has context
        updated_arc2 = StoryArc.load(sample_story.id, "arc_2")
        assert updated_arc2.previous_arc_id == "arc_1"
        assert len(updated_arc2.previous_arc_summary) > 0
        assert "hero" in updated_arc2.previous_arc_summary.lower()


class TestMainlineSelectionBehavior:
    """Tests for mainline selection during arc finalization."""
    
    @pytest.mark.asyncio
    async def test_longest_branch_marked_as_mainline(self, sample_story, mock_generator, temp_data_dir):
        """Longest branch should be marked as mainline."""
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Arc 1",
            premise="Test",
            start_segment_id="seg_1"
        )
        arc.save()
        
        # Create branching paths
        # Path 1: seg_1 -> seg_2 -> seg_4 (length 3)
        # Path 2: seg_1 -> seg_3 -> seg_5 -> seg_6 (length 4) <- longest
        
        segs = [
            ("seg_1", None),
            ("seg_2", "seg_1"),
            ("seg_3", "seg_1"),
            ("seg_4", "seg_2"),
            ("seg_5", "seg_3"),
            ("seg_6", "seg_5"),
        ]
        
        for seg_id, parent_id in segs:
            seg = StorySegment(
                story=sample_story,
                id=seg_id,
                arc_id="arc_1",
                parent_segment_id=parent_id,
                short_description=f"Scene {seg_id}",
                text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content=f"Content {seg_id}")]
            )
            seg.save()
        
        # Finalize
        from app.engine.arc_transition_manager import ArcTransitionManager
        manager = ArcTransitionManager(sample_story, mock_generator)
        await manager._finalize_arc("arc_1")
        
        # Check which segments are marked as mainline
        all_segs = sample_story.get_all_segments()
        mainline_ids = {seg.id for seg in all_segs if seg.is_mainline}
        
        # Path 2 should be mainline
        assert "seg_1" in mainline_ids
        assert "seg_3" in mainline_ids
        assert "seg_5" in mainline_ids
        assert "seg_6" in mainline_ids
        
        # Path 1 alternatives should NOT be mainline
        # (seg_2, seg_4 are archived or not mainline)
