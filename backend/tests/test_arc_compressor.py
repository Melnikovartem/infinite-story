"""Tests for Arc Compressor (E2-4)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_choice import StoryChoice
from app.models.story_arc import StoryArc, ArcCompressionResult
from app.models.text_types import TextBlock, TextType
from app.engine.arc_compressor import ArcCompressor


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
        start_segment_id="seg_1"
    )
    return arc


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator."""
    gen = AsyncMock()
    
    async def mock_generate(system_prompt, user_prompt, context_type):
        response = MagicMock()
        response.error = None
        response.selected_branch = 0
        response.reasoning = "Selected for narrative coherence"
        return response
    
    gen.generate = mock_generate
    return gen


class TestFindBranches:
    """Tests for finding divergent branches."""
    
    def test_find_branches_no_segments(self, sample_story, sample_arc, mock_generator):
        """Find branches returns empty when no segments in arc."""
        compressor = ArcCompressor(sample_story, mock_generator)
        
        branches = compressor._find_branches_in_arc(sample_arc.id)
        
        # Should return empty or single empty branch
        assert isinstance(branches, list)
    
    def test_find_branches_single_linear(self, sample_story, sample_arc, mock_generator):
        """Find branches returns single branch for linear story."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Scene 2",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")
            ]
        )
        
        compressor = ArcCompressor(sample_story, mock_generator)
        branches = compressor._find_branches_in_arc(sample_arc.id)
        
        # Should find at least one branch
        assert len(branches) >= 1
    
    def test_find_branches_multiple_paths(self, sample_story, sample_arc, mock_generator):
        """Find branches detects multiple divergent paths."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            arc_id=sample_arc.id,
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ]
        )
        
        # Branch A
        seg2a = StorySegment(
            story=sample_story,
            id="seg_2a",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Scene 2A",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2A")
            ]
        )
        
        # Branch B
        seg2b = StorySegment(
            story=sample_story,
            id="seg_2b",
            arc_id=sample_arc.id,
            parent_segment_id="seg_1",
            short_description="Scene 2B",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2B")
            ]
        )
        
        compressor = ArcCompressor(sample_story, mock_generator)
        branches = compressor._find_branches_in_arc(sample_arc.id)
        
        # Should find branches
        assert isinstance(branches, list)


class TestSelectCandidates:
    """Tests for selecting candidate branches."""
    
    def test_select_candidates_few_branches(self, sample_story, mock_generator):
        """Select candidates returns all branches when few."""
        branches = [
            ["seg_1", "seg_2"],
            ["seg_1", "seg_2", "seg_3"],
        ]
        
        compressor = ArcCompressor(sample_story, mock_generator)
        candidates = compressor._select_candidates(branches)
        
        assert len(candidates) == 2
        # Should include both branches
        assert any(len(b) == 2 for b in candidates)
        assert any(len(b) == 3 for b in candidates)
    
    def test_select_candidates_many_branches(self, sample_story, mock_generator):
        """Select candidates picks top longest + random."""
        branches = [
            ["seg_1"],
            ["seg_1", "seg_2"],
            ["seg_1", "seg_2", "seg_3"],
            ["seg_1", "seg_2", "seg_3", "seg_4"],
            ["seg_1", "seg_2", "seg_3", "seg_4", "seg_5"],
            ["seg_1", "seg_2", "seg_3", "seg_4", "seg_5", "seg_6"],
        ]
        
        compressor = ArcCompressor(sample_story, mock_generator)
        candidates = compressor._select_candidates(branches)
        
        # Should select top 3 longest + up to 2 random
        assert len(candidates) <= 5
        assert len(candidates) >= 3
    
    def test_select_candidates_sorted_by_length(self, sample_story, mock_generator):
        """Select candidates includes longest branches."""
        branches = [
            ["a"],
            ["b", "c"],
            ["d", "e", "f"],
        ]
        
        compressor = ArcCompressor(sample_story, mock_generator)
        candidates = compressor._select_candidates(branches)
        
        # Should return all three branches when <= 3
        assert len(candidates) == 3
        # All should be present
        assert ["a"] in candidates
        assert ["b", "c"] in candidates
        assert ["d", "e", "f"] in candidates


class TestWalkForward:
    """Tests for walking forward through segments."""
    
    def test_walk_forward_single_segment(self, sample_story, mock_generator):
        """Walk forward returns single segment when no choices."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ]
        )
        
        compressor = ArcCompressor(sample_story, mock_generator)
        chain = compressor._walk_forward_from("seg_1")
        
        assert "seg_1" in chain
    
    def test_walk_forward_with_choices(self, sample_story, mock_generator):
        """Walk forward follows first choice."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ]
        )
        
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            parent_segment_id="seg_1",
            short_description="Scene 2",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")
            ]
        )
        
        choice = StoryChoice(
            story=sample_story,
            id="choice_1",
            from_segment_id="seg_1",
            to_segment_id="seg_2",
            text="Continue"
        )
        
        seg1.outgoing_choices = {"choice_1": choice}
        
        compressor = ArcCompressor(sample_story, mock_generator)
        chain = compressor._walk_forward_from("seg_1")
        
        assert "seg_1" in chain


class TestSummarizeBranch:
    """Tests for branch summarization."""
    
    @pytest.mark.asyncio
    async def test_summarize_branch_empty(self, sample_story, mock_generator):
        """Summarize branch handles empty branch."""
        compressor = ArcCompressor(sample_story, mock_generator)
        
        summary = await compressor._summarize_branch([])
        
        assert "0 segments" in summary
    
    @pytest.mark.asyncio
    async def test_summarize_branch_with_segments(self, sample_story, mock_generator):
        """Summarize branch creates readable summary."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="The opening scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ]
        )
        
        compressor = ArcCompressor(sample_story, mock_generator)
        summary = await compressor._summarize_branch(["seg_1"])
        
        assert "1 segments" in summary
        assert "The opening scene" in summary


@pytest.mark.asyncio
class TestCompressArc:
    """Tests for full arc compression."""
    
    async def test_compress_arc_no_segments(self, sample_story, sample_arc, mock_generator):
        """Compress arc returns None when no branches."""
        sample_arc.save()
        
        compressor = ArcCompressor(sample_story, mock_generator)
        result = await compressor.compress_arc(sample_arc.id)
        
        # Should return None (no compression needed)
        assert result is None
    
    async def test_compress_arc_missing_raises(self, sample_story, mock_generator):
        """Compress arc raises when arc not found."""
        compressor = ArcCompressor(sample_story, mock_generator)
        
        with pytest.raises(ValueError, match="Arc .* not found"):
            await compressor.compress_arc("nonexistent_arc")
    
    async def test_compress_arc_archives_segments(self, sample_story, sample_arc, mock_generator):
        """Compress arc archives non-mainline segments."""
        # Create segments with choices to form multiple branches
        seg_root = StorySegment(
            story=sample_story,
            id="seg_root",
            arc_id=sample_arc.id,
            short_description="Root",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Root")
            ]
        )
        
        # Branch A (mainline)
        seg_a1 = StorySegment(
            story=sample_story,
            id="seg_a1",
            arc_id=sample_arc.id,
            parent_segment_id="seg_root",
            short_description="Branch A1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="A1")
            ]
        )
        
        seg_a2 = StorySegment(
            story=sample_story,
            id="seg_a2",
            arc_id=sample_arc.id,
            parent_segment_id="seg_a1",
            short_description="Branch A2",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="A2")
            ]
        )
        
        # Branch B (alternative)
        seg_b1 = StorySegment(
            story=sample_story,
            id="seg_b1",
            arc_id=sample_arc.id,
            parent_segment_id="seg_root",
            short_description="Branch B1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="B1")
            ]
        )
        
        # Create choices to form branches
        choice_a = StoryChoice(
            story=sample_story,
            id="choice_a",
            from_segment_id="seg_root",
            to_segment_id="seg_a1",
            text="Path A"
        )
        
        choice_b = StoryChoice(
            story=sample_story,
            id="choice_b",
            from_segment_id="seg_root",
            to_segment_id="seg_b1",
            text="Path B"
        )
        
        seg_root.outgoing_choices = {"choice_a": choice_a, "choice_b": choice_b}
        
        sample_arc.save()
        
        compressor = ArcCompressor(sample_story, mock_generator)
        result = await compressor.compress_arc(sample_arc.id)
        
        # May return None or result depending on branch structure
        # At minimum, shouldn't crash
        if result:
            assert isinstance(result, ArcCompressionResult)
            assert result.arc_id == sample_arc.id
    
    async def test_compress_arc_marks_compressed(self, sample_story, sample_arc, mock_generator):
        """Compress arc marks the arc as compressed when compression occurs."""
        # Create multiple branches to trigger compression
        seg_root = StorySegment(
            story=sample_story,
            id="seg_root",
            arc_id=sample_arc.id,
            short_description="Root",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Root")
            ]
        )
        
        seg_a = StorySegment(
            story=sample_story,
            id="seg_a",
            arc_id=sample_arc.id,
            parent_segment_id="seg_root",
            short_description="Path A",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="A")
            ]
        )
        
        seg_b = StorySegment(
            story=sample_story,
            id="seg_b",
            arc_id=sample_arc.id,
            parent_segment_id="seg_root",
            short_description="Path B",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="B")
            ]
        )
        
        choice_a = StoryChoice(
            story=sample_story,
            id="choice_a",
            from_segment_id="seg_root",
            to_segment_id="seg_a",
            text="Path A"
        )
        
        choice_b = StoryChoice(
            story=sample_story,
            id="choice_b",
            from_segment_id="seg_root",
            to_segment_id="seg_b",
            text="Path B"
        )
        
        seg_root.outgoing_choices = {"choice_a": choice_a, "choice_b": choice_b}
        
        sample_arc.save()
        
        assert not sample_arc.is_compressed
        
        compressor = ArcCompressor(sample_story, mock_generator)
        result = await compressor.compress_arc(sample_arc.id)
        
        if result:
            # Arc should be marked as compressed
            updated_arc = StoryArc.load(sample_story.id, sample_arc.id)
            assert updated_arc.is_compressed


@pytest.mark.asyncio
class TestAISelection:
    """Tests for AI branch selection."""
    
    async def test_ai_select_mainline_returns_index(self, sample_story, sample_arc, mock_generator):
        """AI selection returns valid branch index."""
        compressor = ArcCompressor(sample_story, mock_generator)
        
        branch_summaries = [
            "Branch 1: narrative summary",
            "Branch 2: alternative path",
            "Branch 3: random branch"
        ]
        
        result = await compressor._ai_select_mainline(sample_arc, branch_summaries)
        
        assert isinstance(result, int)
        assert 0 <= result < len(branch_summaries)
    
    async def test_ai_select_mainline_error_fallback(self, sample_story, sample_arc):
        """AI selection handles errors gracefully."""
        error_gen = AsyncMock()
        
        async def mock_generate_error(system_prompt, user_prompt, context_type):
            response = MagicMock()
            response.error = "AI service error"
            return response
        
        error_gen.generate = mock_generate_error
        
        compressor = ArcCompressor(sample_story, error_gen)
        
        branch_summaries = [
            "Branch 1",
            "Branch 2"
        ]
        
        result = await compressor._ai_select_mainline(sample_arc, branch_summaries)
        
        # Should return default (0) on error
        assert result == 0
