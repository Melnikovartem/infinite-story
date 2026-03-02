"""Tests for archive state handling in Story (E2-5)."""

import pytest
from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_choice import StoryChoice
from app.models.text_types import TextBlock, TextType


@pytest.fixture
def sample_story():
    """Create a test story."""
    return Story(
        id="test_story",
        title="Test Story",
        description="A test story"
    )


class TestGetSegmentWithArchive:
    """Tests for get_segment with archive status handling."""
    
    def test_get_segment_returns_active(self, sample_story):
        """Get segment returns active segment."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Active scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            status=SegmentStatus.GENERATED
        )
        
        result = sample_story.get_segment("seg_1")
        assert result is not None
        assert result.id == "seg_1"
    
    def test_get_segment_excludes_archived_by_default(self, sample_story):
        """Get segment returns None for archived segment by default."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Archived scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            status=SegmentStatus.ARCHIVED
        )
        
        result = sample_story.get_segment("seg_1")
        assert result is None
    
    def test_get_segment_includes_archived_when_requested(self, sample_story):
        """Get segment returns archived segment when include_archived=True."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Archived scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            status=SegmentStatus.ARCHIVED
        )
        
        result = sample_story.get_segment("seg_1", include_archived=True)
        assert result is not None
        assert result.id == "seg_1"
        assert result.status == SegmentStatus.ARCHIVED
    
    def test_get_segment_nonexistent_returns_none(self, sample_story):
        """Get segment returns None for nonexistent segment."""
        result = sample_story.get_segment("nonexistent")
        assert result is None
    
    def test_get_segment_nonexistent_archived_flag_ignored(self, sample_story):
        """Get segment returns None for nonexistent even with include_archived."""
        result = sample_story.get_segment("nonexistent", include_archived=True)
        assert result is None


class TestGetAvailableChoices:
    """Tests for get_available_choices with archive filtering."""
    
    def test_get_available_choices_empty(self, sample_story):
        """Get available choices returns empty list for nonexistent segment."""
        choices = sample_story.get_available_choices("nonexistent")
        assert choices == []
    
    def test_get_available_choices_active_destination(self, sample_story):
        """Get available choices returns choice to active destination."""
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
            short_description="Scene 2",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")
            ],
            status=SegmentStatus.GENERATED
        )
        
        choice = StoryChoice(
            story=sample_story,
            id="choice_1",
            from_segment_id="seg_1",
            to_segment_id="seg_2",
            text="Continue to scene 2"
        )
        
        # Manually set outgoing choices (normally done by game loop)
        seg1.outgoing_choices = {"choice_1": choice}
        
        choices = sample_story.get_available_choices("seg_1")
        assert len(choices) == 1
        assert choices[0].id == "choice_1"
    
    def test_get_available_choices_excludes_archived_destination(self, sample_story):
        """Get available choices excludes choice to archived destination."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ]
        )
        
        seg2_archived = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Archived scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")
            ],
            status=SegmentStatus.ARCHIVED
        )
        
        choice = StoryChoice(
            story=sample_story,
            id="choice_1",
            from_segment_id="seg_1",
            to_segment_id="seg_2",
            text="Continue to archived scene"
        )
        
        # Manually set outgoing choices
        seg1.outgoing_choices = {"choice_1": choice}
        
        choices = sample_story.get_available_choices("seg_1")
        assert len(choices) == 0
    
    def test_get_available_choices_mixed_destinations(self, sample_story):
        """Get available choices returns only choices to active segments."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ]
        )
        
        seg2_active = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2 (active)",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 2")
            ],
            status=SegmentStatus.GENERATED
        )
        
        seg3_archived = StorySegment(
            story=sample_story,
            id="seg_3",
            short_description="Scene 3 (archived)",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 3")
            ],
            status=SegmentStatus.ARCHIVED
        )
        
        choice1 = StoryChoice(
            story=sample_story,
            id="choice_1",
            from_segment_id="seg_1",
            to_segment_id="seg_2",
            text="Continue to active scene"
        )
        
        choice2 = StoryChoice(
            story=sample_story,
            id="choice_2",
            from_segment_id="seg_1",
            to_segment_id="seg_3",
            text="Continue to archived scene"
        )
        
        # Manually set outgoing choices
        seg1.outgoing_choices = {
            "choice_1": choice1,
            "choice_2": choice2
        }
        
        choices = sample_story.get_available_choices("seg_1")
        assert len(choices) == 1
        assert choices[0].id == "choice_1"
    
    def test_get_available_choices_with_missing_destination(self, sample_story):
        """Get available choices excludes choice to missing destination."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content 1")
            ]
        )
        
        choice = StoryChoice(
            story=sample_story,
            id="choice_1",
            from_segment_id="seg_1",
            to_segment_id="nonexistent_seg",
            text="Continue to missing scene"
        )
        
        # Manually set outgoing choices
        seg1.outgoing_choices = {"choice_1": choice}
        
        choices = sample_story.get_available_choices("seg_1")
        assert len(choices) == 0


class TestArchiveWorkflow:
    """Integration tests for archive workflow."""
    
    def test_archive_segment_then_query(self, sample_story):
        """Archive segment then verify it's excluded from queries."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene",
            text_blocks=[
                TextBlock(type=TextType.NARRATOR_DESCRIBING, content="Content")
            ],
            status=SegmentStatus.GENERATED
        )
        
        # Verify segment is accessible
        assert sample_story.get_segment("seg_1") is not None
        
        # Archive the segment
        seg.status = SegmentStatus.ARCHIVED
        sample_story.add_segment(seg)
        
        # Verify segment is now excluded
        assert sample_story.get_segment("seg_1") is None
        
        # Verify segment is still accessible with flag
        assert sample_story.get_segment("seg_1", include_archived=True) is not None
    
    def test_archive_removes_choices_to_archived(self, sample_story):
        """Archiving segments removes choices pointing to them."""
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
        
        # Initially, choice is available
        assert len(sample_story.get_available_choices("seg_1")) == 1
        
        # Archive the destination
        seg2.status = SegmentStatus.ARCHIVED
        sample_story.add_segment(seg2)
        
        # Now choice should be unavailable
        assert len(sample_story.get_available_choices("seg_1")) == 0
