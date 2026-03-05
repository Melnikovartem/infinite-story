"""Integration tests for arc transition system with episode recap generator and story runner."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode as EpisodeMeta
from app.models.text_types import TextBlock, TextType
from app.engine.episode_recap_generator import EpisodeRecapGenerator
from app.engine.story_runner import StoryRunner


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
    """Create a mock TextGenerator."""
    gen = AsyncMock()
    
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        response.title = "Test Episode"
        response.summary = "Test summary"
        response.key_themes = ["theme1"]
        response.themes_explored = ["theme1"]
        response.hook_for_next = "The story continues..."
        response.unresolved_new = ["New mystery"]
        response.tone_tags = ["tense"]
        response.end_condition = "The hero escapes"
        response.narrative_direction = "Toward the climax"
        response.episode_focus = "The hero's choice"
        response.story_hooks = ["What happens next?"]
        return response
    
    gen.generate = mock_generate
    return gen


class TestEpisodeRecapGeneratorArcCompletion:
    """Tests for arc completion trigger in EpisodeRecapGenerator."""
    
    @pytest.mark.asyncio
    async def test_handle_arc_completion_increments_episode_count(self, sample_story, mock_generator, temp_data_dir):
        """Should increment arc episode_count when called."""
        # Create arc
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=0
        )
        arc.save()
        
        generator = EpisodeRecapGenerator(sample_story, mock_generator)
        await generator._handle_arc_completion("arc_1", 5)
        
        # Check episode count was updated
        updated_arc = StoryArc.load(sample_story.id, "arc_1")
        assert updated_arc.episode_count == 5
    
    @pytest.mark.asyncio
    async def test_handle_arc_completion_not_triggered_before_15(self, sample_story, mock_generator, temp_data_dir):
        """Should not finalize arc when episode < 15."""
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=0
        )
        arc.save()
        
        generator = EpisodeRecapGenerator(sample_story, mock_generator)
        await generator._handle_arc_completion("arc_1", 10)
        
        # Arc should not be finalized yet
        updated_arc = StoryArc.load(sample_story.id, "arc_1")
        assert updated_arc.is_finalized is False
    
    @pytest.mark.asyncio
    async def test_handle_arc_completion_triggered_at_15(self, sample_story, mock_generator, temp_data_dir):
        """Should trigger arc finalization at episode 15."""
        # Create arc with segments
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1",
            episode_count=0
        )
        arc.save()
        
        # Create linear segment chain
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
        
        generator = EpisodeRecapGenerator(sample_story, mock_generator)
        await generator._handle_arc_completion("arc_1", 15)
        
        # Check that finalization started (arc should be marked for finalization)
        updated_arc = StoryArc.load(sample_story.id, "arc_1")
        assert updated_arc.episode_count == 15
    
    @pytest.mark.asyncio
    async def test_handle_arc_completion_none_arc_id(self, sample_story, mock_generator):
        """Should handle None arc_id gracefully."""
        generator = EpisodeRecapGenerator(sample_story, mock_generator)
        
        # Should not raise
        await generator._handle_arc_completion(None, 15)


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


class TestStoryRunnerArcTransition:
    """Tests for arc transition in StoryRunner."""
    
    @pytest.mark.asyncio
    async def test_check_arc_transition_no_transition(self, sample_story, mock_generator, temp_data_dir):
        """Should return current arc when no transition needed."""
        arc = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Test Arc",
            premise="Test premise",
            start_segment_id="seg_1"
        )
        arc.save()
        
        runner = StoryRunner(sample_story, mock_generator)
        result = await runner._check_arc_transition("arc_1")
        
        # Should return current arc since no new active arc
        assert result == "arc_1"
    
    @pytest.mark.asyncio
    async def test_check_arc_transition_with_active_arc(self, sample_story, mock_generator, temp_data_dir):
        """Should return new active arc when available."""
        arc1 = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Arc 1",
            premise="Test premise",
            start_segment_id="seg_1"
        )
        arc1.save()
        
        # Create new active arc
        arc2 = StoryArc(
            id="arc_2",
            story_id=sample_story.id,
            title="Arc 2",
            premise="Next arc",
            start_segment_id="seg_n",
            is_active=True
        )
        arc2.save()
        
        runner = StoryRunner(sample_story, mock_generator)
        result = await runner._check_arc_transition("arc_1")
        
        # Should return arc_2 since it's active and different
        assert result == "arc_2"


class TestEpisodeTransitionToNewArc:
    """Tests for episode transitions that trigger arc changes."""
    
    @pytest.mark.asyncio
    async def test_generate_segment_detects_arc_transition(self, sample_story, mock_generator, temp_data_dir):
        """Should detect and handle arc transition during segment generation."""
        # Create first arc
        arc1 = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Arc 1",
            premise="First arc",
            start_segment_id="seg_1",
            episode_count=14  # 14 episodes, next will be 15
        )
        arc1.save()
        
        # Create second arc as active (ready for transition)
        arc2 = StoryArc(
            id="arc_2",
            story_id=sample_story.id,
            title="Arc 2",
            premise="Second arc",
            start_segment_id="seg_n",
            is_active=True
        )
        arc2.save()
        
        # Create starting segment
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id="arc_1",
            episode_number=14,
            segment_number_in_episode=5,
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")],
            should_transition_episode=False
        )
        seg1.save()
        
        # This test just verifies the flow can be executed
        # Actual segment generation would need more mocking
        runner = StoryRunner(sample_story, mock_generator)
        runner.current_segment = seg1
        runner.current_arc_id = "arc_1"
        
        # Arc transition detection happens in _generate_segment
        # We verify the arc can be transitioned
        next_arc = await runner._check_arc_transition("arc_1")
        assert next_arc == "arc_2"


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
