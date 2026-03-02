"""Tests for SegmentContextBuilder - E1-1 implementation."""

import pytest
from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.text_types import TextBlock, TextType
from app.engine.segment_context_builder import SegmentContextBuilder


class TestWalkEpisodeChain:
    """Test the _walk_episode_chain method."""
    
    def test_walk_episode_chain_single_segment(self, sample_story):
        """Test walking a single segment (episode start)."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            episode_number=1
        )
        
        builder = SegmentContextBuilder(sample_story)
        chain = builder._walk_episode_chain("seg_1")
        
        assert chain == ["seg_1"]
    
    def test_walk_episode_chain_three_segments(self, sample_story):
        """Test walking backward through three connected segments."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            episode_number=1
        )
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2",
            episode_number=1,
            parent_segment_id="seg_1"
        )
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            short_description="Scene 3",
            episode_number=1,
            parent_segment_id="seg_2"
        )
        
        builder = SegmentContextBuilder(sample_story)
        chain = builder._walk_episode_chain("seg_3")
        
        assert chain == ["seg_1", "seg_2", "seg_3"]
    
    def test_walk_episode_chain_stops_at_episode_boundary(self, sample_story):
        """Test that walking stops when episode changes."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            episode_number=1
        )
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2",
            episode_number=1,
            parent_segment_id="seg_1"
        )
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            short_description="Scene 3",
            episode_number=2,
            parent_segment_id="seg_2"
        )
        
        builder = SegmentContextBuilder(sample_story)
        chain = builder._walk_episode_chain("seg_3")
        
        # Should only include seg_3 since episode changes at seg_2->seg_3
        assert chain == ["seg_3"]
    
    def test_walk_episode_chain_missing_parent(self, sample_story):
        """Test that walking handles missing parent gracefully."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            episode_number=1
        )
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2",
            episode_number=1,
            parent_segment_id="nonexistent"  # Points to missing segment
        )
        
        builder = SegmentContextBuilder(sample_story)
        chain = builder._walk_episode_chain("seg_2")
        
        # Should include seg_2 but stop when parent is missing
        assert chain == ["seg_2"]
    
    def test_walk_episode_chain_missing_segment(self, sample_story):
        """Test that walking nonexistent segment returns empty list."""
        builder = SegmentContextBuilder(sample_story)
        chain = builder._walk_episode_chain("nonexistent")
        
        assert chain == []


class TestAccumulateChanges:
    """Test the _accumulate_changes method."""
    
    def test_accumulate_no_changes(self, sample_story):
        """Test accumulating when no changes exist."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            change_notes=[]
        )
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2",
            change_notes=[]
        )
        
        builder = SegmentContextBuilder(sample_story)
        changes = builder._accumulate_changes(["seg_1", "seg_2"])
        
        assert changes == []
    
    def test_accumulate_single_change(self, sample_story):
        """Test accumulating a single change note."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            change_notes=["Alice found the key"]
        )
        
        builder = SegmentContextBuilder(sample_story)
        changes = builder._accumulate_changes(["seg_1"])
        
        assert changes == ["Alice found the key"]
    
    def test_accumulate_multiple_changes_across_segments(self, sample_story):
        """Test accumulating changes from multiple segments."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            change_notes=["Alice is sad"]
        )
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2",
            change_notes=["Alice finds hope", "Bob arrives"]
        )
        
        builder = SegmentContextBuilder(sample_story)
        changes = builder._accumulate_changes(["seg_1", "seg_2"])
        
        assert changes == ["Alice is sad", "Alice finds hope", "Bob arrives"]
    
    def test_accumulate_missing_segments_ignored(self, sample_story):
        """Test that missing segments are handled gracefully."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            change_notes=["Change 1"]
        )
        
        builder = SegmentContextBuilder(sample_story)
        changes = builder._accumulate_changes(["seg_1", "nonexistent", "also_nonexistent"])
        
        assert changes == ["Change 1"]


class TestShouldTransitionEpisode:
    """Test the _should_transition_episode method."""
    
    def test_transition_on_high_proximity(self, sample_story):
        """Test transition when end_condition_proximity >= 0.8."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            end_condition_proximity=0.85
        )
        
        builder = SegmentContextBuilder(sample_story)
        result = builder._should_transition_episode(seg, [])
        
        assert result is True
    
    def test_no_transition_on_low_proximity(self, sample_story):
        """Test no transition when proximity is low."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            end_condition_proximity=0.5,
            segment_number_in_episode=10
        )
        
        builder = SegmentContextBuilder(sample_story)
        result = builder._should_transition_episode(seg, [])
        
        assert result is False
    
    def test_transition_on_segment_count(self, sample_story):
        """Test transition when segment_number_in_episode >= 18."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            segment_number_in_episode=18,
            end_condition_proximity=0.0
        )
        
        builder = SegmentContextBuilder(sample_story)
        result = builder._should_transition_episode(seg, [])
        
        assert result is True
    
    def test_transition_on_end_keyword(self, sample_story):
        """Test transition when changes contain end keywords."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            end_condition_proximity=0.0,
            segment_number_in_episode=10
        )
        changes = ["The climax arrives", "All secrets revealed"]
        
        builder = SegmentContextBuilder(sample_story)
        result = builder._should_transition_episode(seg, changes)
        
        assert result is True
    
    def test_no_transition_without_triggers(self, sample_story):
        """Test no transition when none of the triggers are met."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            end_condition_proximity=0.3,
            segment_number_in_episode=5
        )
        changes = ["Alice learns a fact", "Bob speaks"]
        
        builder = SegmentContextBuilder(sample_story)
        result = builder._should_transition_episode(seg, changes)
        
        assert result is False


class TestCalculatePacingWeight:
    """Test the _calculate_pacing_weight method."""
    
    def test_pacing_weight_at_transition(self, sample_story):
        """Test pacing weight when transitioning to next episode."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            segment_number_in_episode=5
        )
        
        builder = SegmentContextBuilder(sample_story)
        weight = builder._calculate_pacing_weight(seg, will_transition=True)
        
        assert weight == 0.9
    
    def test_pacing_weight_nonlinear_progression(self, sample_story):
        """Test that pacing weight increases nonlinearly."""
        builder = SegmentContextBuilder(sample_story)
        
        seg_5 = StorySegment(
            story=sample_story,
            id="seg_5",
            short_description="Scene 5",
            segment_number_in_episode=5
        )
        weight_5 = builder._calculate_pacing_weight(seg_5, False)
        
        seg_15 = StorySegment(
            story=sample_story,
            id="seg_15",
            short_description="Scene 15",
            segment_number_in_episode=15
        )
        weight_15 = builder._calculate_pacing_weight(seg_15, False)
        
        # Nonlinear: weight increases faster later
        assert weight_5 < weight_15
        assert weight_5 > 0.0
        assert weight_15 < 1.0
    
    def test_pacing_weight_at_start(self, sample_story):
        """Test pacing weight at start of episode."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            segment_number_in_episode=1
        )
        
        builder = SegmentContextBuilder(sample_story)
        weight = builder._calculate_pacing_weight(seg, False)
        
        # Should be very small
        assert weight > 0.0
        assert weight < 0.01
    
    def test_pacing_weight_capped_at_0_99(self, sample_story):
        """Test that pacing weight is capped at 0.99."""
        seg = StorySegment(
            story=sample_story,
            id="seg_20",
            short_description="Scene 20",
            segment_number_in_episode=20
        )
        
        builder = SegmentContextBuilder(sample_story)
        weight = builder._calculate_pacing_weight(seg, False)
        
        # Should be capped at 0.99
        assert weight <= 0.99


class TestBuildContext:
    """Test the build_context method - integration of all components."""
    
    def test_build_context_basic(self, sample_story):
        """Test building context for a basic segment."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            episode_number=2,
            episode_tone="dark_and_mysterious",
            episode_end_condition="reach the castle",
            protagonist_id="alice",
            segment_number_in_episode=5,
            character_states={"alice": {"mood": "determined"}},
            change_notes=["Alice prepares for the journey"]
        )
        
        builder = SegmentContextBuilder(sample_story)
        context = builder.build_context("seg_1", "Go forward boldly")
        
        assert context['episode_number'] == 2
        assert context['episode_tone'] == "dark_and_mysterious"
        assert context['episode_end_condition'] == "reach the castle"
        assert context['protagonist_id'] == "alice"
        assert context['user_choice'] == "Go forward boldly"
        assert context['pacing_weight'] > 0.0
        assert context['pacing_weight'] < 1.0
        assert 'character_states' in context
        assert 'accumulated_changes' in context
        assert 'previous_segments' in context
    
    def test_build_context_with_parent_chain(self, sample_story):
        """Test building context with a parent segment chain."""
        seg1 = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            episode_number=1,
            change_notes=["Started the journey"]
        )
        seg2 = StorySegment(
            story=sample_story,
            id="seg_2",
            short_description="Scene 2",
            episode_number=1,
            parent_segment_id="seg_1",
            change_notes=["Met a stranger"]
        )
        seg3 = StorySegment(
            story=sample_story,
            id="seg_3",
            short_description="Scene 3",
            episode_number=1,
            parent_segment_id="seg_2",
            change_notes=["Learned a secret"]
        )
        
        builder = SegmentContextBuilder(sample_story)
        context = builder.build_context("seg_3", "Ask more questions")
        
        # Should accumulate all changes
        assert "Started the journey" in context['accumulated_changes']
        assert "Met a stranger" in context['accumulated_changes']
        assert "Learned a secret" in context['accumulated_changes']
    
    def test_build_context_missing_segment_raises_error(self, sample_story):
        """Test that building context with missing segment raises error."""
        builder = SegmentContextBuilder(sample_story)
        
        with pytest.raises(ValueError, match="Segment nonexistent not found"):
            builder.build_context("nonexistent", "Some choice")
    
    def test_build_context_transition_detection(self, sample_story):
        """Test that context correctly detects episode transitions."""
        seg = StorySegment(
            story=sample_story,
            id="seg_1",
            short_description="Scene 1",
            segment_number_in_episode=18,
            end_condition_proximity=0.0
        )
        
        builder = SegmentContextBuilder(sample_story)
        context = builder.build_context("seg_1", "Make a choice")
        
        assert context['should_transition_episode'] is True
        assert context['pacing_weight'] == 0.9  # From will_transition
    
    def test_build_context_accumulates_last_five_segments(self, sample_story):
        """Test that context includes up to last 5 previous segments."""
        segments = []
        for i in range(1, 8):
            parent_id = f"seg_{i-1}" if i > 1 else None
            seg = StorySegment(
                story=sample_story,
                id=f"seg_{i}",
                short_description=f"Scene {i}",
                episode_number=1,
                parent_segment_id=parent_id
            )
            segments.append(seg)
        
        builder = SegmentContextBuilder(sample_story)
        context = builder.build_context("seg_7", "Do something")
        
        # Should have up to 5 previous segment overviews
        # Since _walk_episode_chain returns all segments in episode
        # we take the last 5, so segments 3-7
        assert len(context['previous_segments']) <= 5
