"""Tests for Arc Transition Manager (E2-5)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_arc import StoryArc, ArcCompressionResult
from app.models.text_types import TextBlock, TextType
from app.engine.arc_transition_manager import ArcTransitionManager


@pytest.fixture
def sample_story():
    """Create a test story."""
    return Story(
        id="test_story",
        title="Test Story",
        description="A test story"
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
        start_segment_id="seg_1",
        episode_count=0
    )
    return arc


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator."""
    gen = AsyncMock()
    
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        return response
    
    gen.generate = mock_generate
    return gen


class TestMainlineDetermination:
    """Tests for mainline determination algorithm."""
    
    def test_determine_mainline_single_segment(self, sample_story, sample_arc, mock_generator):
        """Single segment should be marked as mainline."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        mainline = manager._determine_mainline([seg1])
        
        assert len(mainline) == 1
        assert mainline[0].id == "seg_1"
    
    def test_determine_mainline_linear_path(self, sample_story, sample_arc, mock_generator):
        """Linear path should all be mainline."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Scene 2",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")]
        )
        
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            arc_id=sample_arc.id,
            parent_segment_id="seg_2",
            short_description="Scene 3",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 3")]
        )
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        mainline = manager._determine_mainline([seg1, seg2, seg3])
        
        assert len(mainline) == 3
        assert [s.id for s in mainline] == ["seg_1", "seg_2", "seg_3"]
    
    def test_determine_mainline_longest_path(self, sample_story, sample_arc, mock_generator):
        """Longest path should be selected as mainline."""
        # Path 1: seg_1 -> seg_2 -> seg_4 (length 3)
        # Path 2: seg_1 -> seg_3 -> seg_5 -> seg_6 (length 4) <- longest
        
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Start",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Start")]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Path 1-1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="P1-1")]
        )
        
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Path 2-1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="P2-1")]
        )
        
        seg4 = StorySegment(
            story=sample_story,
            id="seg_4",
            arc_id=sample_arc.id,
            parent_segment_id="seg_2",
            short_description="Path 1-2",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="P1-2")]
        )
        
        seg5 = StorySegment(
            story=sample_story,
            id="seg_5",
            arc_id=sample_arc.id,
            parent_segment_id="seg_3",
            short_description="Path 2-2",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="P2-2")]
        )
        
        seg6 = StorySegment(
            story=sample_story,
            id="seg_6",
            arc_id=sample_arc.id,
            parent_segment_id="seg_5",
            short_description="Path 2-3",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="P2-3")]
        )
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        mainline = manager._determine_mainline([seg1, seg2, seg3, seg4, seg5, seg6])
        
        # Should select path 2 (seg_1 -> seg_3 -> seg_5 -> seg_6)
        assert len(mainline) == 4
        assert [s.id for s in mainline] == ["seg_1", "seg_3", "seg_5", "seg_6"]


class TestWalkBackwardToRoot:
    """Tests for backward walking algorithm."""
    
    def test_walk_backward_single_segment(self, sample_story, sample_arc, mock_generator):
        """Walking from root should return only that segment."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        segment_map = {"seg_1": seg1}
        manager = ArcTransitionManager(sample_story, mock_generator)
        path = manager._walk_backward_to_root(seg1, segment_map)
        
        assert len(path) == 1
        assert path[0].id == "seg_1"
    
    def test_walk_backward_full_chain(self, sample_story, sample_arc, mock_generator):
        """Should walk back to root, building full path."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Scene 2",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")]
        )
        
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            arc_id=sample_arc.id,
            parent_segment_id="seg_2",
            short_description="Scene 3",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 3")]
        )
        
        segment_map = {"seg_1": seg1, "seg_2": seg2, "seg_3": seg3}
        manager = ArcTransitionManager(sample_story, mock_generator)
        path = manager._walk_backward_to_root(seg3, segment_map)
        
        assert len(path) == 3
        assert [s.id for s in path] == ["seg_1", "seg_2", "seg_3"]


class TestArcFinalization:
    """Tests for arc finalization."""
    
    @pytest.mark.asyncio
    async def test_finalize_arc_marks_mainline(self, sample_story, sample_arc, mock_generator, temp_data_dir):
        """Finalization should mark mainline segments."""
        # Create segments
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Scene 2",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")]
        )
        
        seg2.save()
        seg1.save()
        sample_arc.save()
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        await manager._finalize_arc(sample_arc.id)
        
        # Reload and check
        arc = StoryArc.load(sample_story.id, sample_arc.id)
        assert arc.is_finalized is True
        assert arc.mainline_segment_count > 0


class TestContextFeeding:
    """Tests for context feeding to next arc."""
    
    @pytest.mark.asyncio
    async def test_build_arc_summary(self, sample_story, sample_arc, mock_generator):
        """Should build summary from mainline segments."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="The hero awakens",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="A quest is offered",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")],
            is_mainline=True
        )
        
        seg2.save()
        seg1.save()
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        summary = await manager._build_arc_summary(sample_arc.id)
        
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestArcTransitionCheckAndHandle:
    """Tests for main entry point."""
    
    @pytest.mark.asyncio
    async def test_check_and_handle_not_complete(self, sample_story, sample_arc, mock_generator):
        """Should return None if arc not at threshold."""
        manager = ArcTransitionManager(sample_story, mock_generator)
        result = await manager.check_and_handle_arc_completion(sample_arc.id, 10)
        
        # Should return None since episode 10 != threshold (15)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_check_and_handle_arc_not_found(self, sample_story, mock_generator):
        """Should handle missing arc gracefully."""
        manager = ArcTransitionManager(sample_story, mock_generator)
        result = await manager.check_and_handle_arc_completion("nonexistent_arc", 15)
        
        # Should return None
        assert result is None


class TestGetOrCreateNextArc:
    """Tests for next arc selection/generation."""
    
    @pytest.mark.asyncio
    async def test_get_or_create_with_future_arc(self, sample_story, sample_arc, mock_generator, temp_data_dir):
        """Should use existing future arc if available."""
        # Create a future arc
        future_arc = StoryArc(
            id="arc_2",
            story_id=sample_story.id,
            title="The Second Arc",
            premise="Continuing the journey",
            start_segment_id="seg_n",
            is_future_arc=True
        )
        future_arc.save()
        
        manager = ArcTransitionManager(sample_story, mock_generator)
        next_arc_id = await manager._get_or_create_next_arc(sample_arc.id)
        
        assert next_arc_id == "arc_2"
        
        # Verify future arc was activated
        activated_arc = StoryArc.load(sample_story.id, "arc_2")
        assert activated_arc.is_future_arc is False
        assert activated_arc.is_active is True


class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_finalize_arc_missing_arc(self, sample_story, mock_generator):
        """Should handle missing arc without crashing."""
        manager = ArcTransitionManager(sample_story, mock_generator)
        
        # Should not raise
        await manager._finalize_arc("nonexistent_arc")
    
    def test_determine_mainline_empty_list(self, sample_story, mock_generator):
        """Should handle empty segment list."""
        manager = ArcTransitionManager(sample_story, mock_generator)
        mainline = manager._determine_mainline([])
        
        assert mainline == []
    
    def test_walk_backward_missing_parent(self, sample_story, sample_arc, mock_generator):
        """Should handle missing parent in segment map."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            parent_segment_id="missing_parent",
            short_description="Scene 1",
            text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")]
        )
        
        segment_map = {"seg_1": seg1}  # missing_parent not in map
        manager = ArcTransitionManager(sample_story, mock_generator)
        path = manager._walk_backward_to_root(seg1, segment_map)
        
        # Should return just seg_1 since parent is missing
        assert len(path) == 1
        assert path[0].id == "seg_1"


class TestIntegrationArcTransition:
    """Integration tests for full arc transition flow."""
    
    @pytest.mark.asyncio
    async def test_full_arc_completion_cycle(self, sample_story, mock_generator, temp_data_dir):
        """Test full cycle: create arc, segments, finalize, transition."""
        # Create first arc
        arc1 = StoryArc(
            id="arc_1",
            story_id=sample_story.id,
            title="Arc 1",
            premise="First arc",
            start_segment_id="seg_1",
            episode_count=0,
            unresolved_mysteries=["What is the secret?", "Who is the villain?"]
        )
        arc1.save()
        
        # Create linear segment chain (5 segments)
        prev_id = None
        for i in range(1, 6):
            seg = StorySegment(
                story=sample_story,
                id=f"seg_{i}",
                arc_id="arc_1",
                parent_segment_id=prev_id,
                short_description=f"Scene {i}",
                text_blocks=[TextBlock(type=TextType.NARRATOR_DESCRIBING, content=f"Content {i}")]
            )
            seg.save()
            prev_id = f"seg_{i}"
        
        # Create future arc
        arc2 = StoryArc(
            id="arc_2",
            story_id=sample_story.id,
            title="Arc 2",
            premise="Second arc",
            start_segment_id="seg_n",
            is_future_arc=True
        )
        arc2.save()
        
        # Finalize arc1
        manager = ArcTransitionManager(sample_story, mock_generator)
        await manager._finalize_arc("arc_1")
        
        # Verify finalization
        arc1_final = StoryArc.load(sample_story.id, "arc_1")
        assert arc1_final.is_finalized is True
        assert arc1_final.mainline_segment_count > 0
        
        # Feed context to arc2
        await manager._feed_context_to_next_arc("arc_1", "arc_2")
        
        # Verify context was fed
        arc2_fed = StoryArc.load(sample_story.id, "arc_2")
        assert arc2_fed.previous_arc_id == "arc_1"
        assert len(arc2_fed.previous_arc_summary) > 0
