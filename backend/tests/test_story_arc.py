"""Tests for StoryArc and ArcCompressionResult models (E0-3)."""

import pytest
from datetime import datetime, UTC
from app.models.story_arc import StoryArc, ArcCompressionResult


class TestArcCompressionResult:
    """Tests for ArcCompressionResult model."""
    
    def test_compression_result_creation(self):
        """Create a compression result."""
        result = ArcCompressionResult(
            arc_id="arc_001",
            mainline_branch_segments=["seg_1", "seg_2", "seg_3"],
            archived_segments=["seg_1_alt", "seg_2_alt"],
            selection_rationale="Branch followed by most users and most coherent narrative"
        )
        
        assert result.arc_id == "arc_001"
        assert len(result.mainline_branch_segments) == 3
        assert len(result.archived_segments) == 2
        assert "most users" in result.selection_rationale
    
    def test_compression_result_defaults(self):
        """Compression result with defaults."""
        result = ArcCompressionResult(
            arc_id="arc_002",
            mainline_branch_segments=["seg_1"],
            archived_segments=[],
            selection_rationale="Only one branch exists"
        )
        
        assert result.compression_model == "gpt-4o-mini"
        assert isinstance(result.compressed_at, datetime)
        assert len(result.archived_segments) == 0


class TestStoryArc:
    """Tests for StoryArc model."""
    
    def test_story_arc_creation(self):
        """Create a story arc with basic fields."""
        arc = StoryArc(
            id="arc_001",
            story_id="story_1",
            title="The Rise of the Northern Kingdom",
            description="A tale of ambition and power in the frozen north",
            premise="Power corrupts the innocent",
            narrative_direction="Towards inevitable downfall",
            start_segment_id="seg_1"
        )
        
        assert arc.id == "arc_001"
        assert arc.story_id == "story_1"
        assert arc.title == "The Rise of the Northern Kingdom"
        assert arc.premise == "Power corrupts the innocent"
        assert arc.start_segment_id == "seg_1"
    
    def test_story_arc_defaults(self):
        """Story arc with default values."""
        arc = StoryArc(
            id="arc_002",
            story_id="story_1",
            title="The Fall",
            description="Consequences unfold",
            premise="All empires crumble",
            narrative_direction="Towards redemption or ruin",
            start_segment_id="seg_10"
        )
        
        assert arc.episode_ids == []
        assert arc.episode_count == 0
        assert arc.current_segment_id is None
        assert arc.is_compressed is False
        assert arc.compression_result is None
    
    def test_story_arc_with_episodes(self):
        """Story arc with episode tracking."""
        arc = StoryArc(
            id="arc_003",
            story_id="story_1",
            title="The Reckoning",
            description="The final arc",
            premise="Consequences arrive",
            narrative_direction="Towards resolution",
            start_segment_id="seg_20",
            episode_ids=["ep_1", "ep_2", "ep_3"],
            episode_count=3
        )
        
        assert len(arc.episode_ids) == 3
        assert arc.episode_count == 3
    
    def test_story_arc_with_current_segment(self):
        """Story arc with current segment tracking."""
        arc = StoryArc(
            id="arc_004",
            story_id="story_1",
            title="In Progress",
            description="Currently being played",
            premise="A tale unfolds",
            narrative_direction="Unknown",
            start_segment_id="seg_1",
            current_segment_id="seg_5"
        )
        
        assert arc.current_segment_id == "seg_5"
    
    def test_story_arc_uncompressed(self):
        """Uncompressed arc has no compression result."""
        arc = StoryArc(
            id="arc_005",
            story_id="story_1",
            title="Active Arc",
            description="Still generating",
            premise="Story continues",
            narrative_direction="Forward",
            start_segment_id="seg_1"
        )
        
        assert arc.is_compressed is False
        assert arc.compression_result is None


class TestStoryArcMethods:
    """Tests for StoryArc helper methods."""
    
    def test_get_short_overview(self):
        """Test short overview method."""
        arc = StoryArc(
            id="arc_006",
            story_id="story_1",
            title="The Beginning",
            description="First arc",
            premise="It begins",
            narrative_direction="Forward",
            start_segment_id="seg_1",
            episode_count=3
        )
        
        overview = arc.get_short_overview()
        assert "The Beginning" in overview
        assert "3 episodes" in overview
    
    def test_get_full_overview(self):
        """Test full overview method."""
        arc = StoryArc(
            id="arc_007",
            story_id="story_1",
            title="The Middle",
            description="The heart of the story",
            premise="Conflict escalates",
            narrative_direction="Towards climax",
            start_segment_id="seg_10",
            episode_count=5,
            is_compressed=True
        )
        
        overview = arc.get_full_overview()
        assert "The Middle" in overview
        assert "Conflict escalates" in overview
        assert "Towards climax" in overview
        assert "5" in overview
        assert "True" in overview
    
    def test_mark_compressed(self):
        """Test marking arc as compressed."""
        arc = StoryArc(
            id="arc_008",
            story_id="story_1",
            title="Completed",
            description="Ready for compression",
            premise="Arc complete",
            narrative_direction="Finalized",
            start_segment_id="seg_1"
        )
        
        assert arc.is_compressed is False
        assert arc.compression_result is None
        
        compression = ArcCompressionResult(
            arc_id=arc.id,
            mainline_branch_segments=["seg_1", "seg_2", "seg_3"],
            archived_segments=["seg_1_alt"],
            selection_rationale="Most coherent path"
        )
        
        arc.mark_compressed(compression)
        
        assert arc.is_compressed is True
        assert arc.compression_result is not None
        assert arc.compression_result.arc_id == "arc_008"
    
    def test_add_episode(self):
        """Test adding episodes to arc."""
        arc = StoryArc(
            id="arc_009",
            story_id="story_1",
            title="Growing Arc",
            description="Episodes will be added",
            premise="Growth",
            narrative_direction="Expansion",
            start_segment_id="seg_1"
        )
        
        assert arc.episode_count == 0
        
        arc.add_episode("ep_1")
        assert arc.episode_count == 1
        assert "ep_1" in arc.episode_ids
        
        arc.add_episode("ep_2")
        assert arc.episode_count == 2
        
        # Adding duplicate should not increase count
        arc.add_episode("ep_1")
        assert arc.episode_count == 2


class TestStoryArcSerialization:
    """Tests for StoryArc save/load."""
    
    def test_story_arc_save_and_load(self):
        """Save and load a story arc."""
        arc = StoryArc(
            id="arc_010",
            story_id="test_story",
            title="Serialization Test",
            description="Testing save/load",
            premise="Test premise",
            narrative_direction="Test direction",
            start_segment_id="seg_1",
            episode_ids=["ep_1", "ep_2"],
            episode_count=2
        )
        
        # Save
        arc.save()
        
        # Load
        loaded = StoryArc.load("test_story", "arc_010")
        
        assert loaded is not None
        assert loaded.title == "Serialization Test"
        assert loaded.premise == "Test premise"
        assert len(loaded.episode_ids) == 2
        assert loaded.episode_count == 2
    
    def test_story_arc_save_with_compression(self):
        """Save and load compressed arc."""
        compression = ArcCompressionResult(
            arc_id="arc_011",
            mainline_branch_segments=["seg_1", "seg_2", "seg_3"],
            archived_segments=["seg_1_alt"],
            selection_rationale="Best narrative flow"
        )
        
        arc = StoryArc(
            id="arc_011",
            story_id="test_story",
            title="Compressed Arc",
            description="Already compressed",
            premise="Complete",
            narrative_direction="Finalized",
            start_segment_id="seg_1",
            is_compressed=True,
            compression_result=compression
        )
        
        arc.save()
        loaded = StoryArc.load("test_story", "arc_011")
        
        assert loaded is not None
        assert loaded.is_compressed is True
        assert loaded.compression_result is not None
        assert len(loaded.compression_result.mainline_branch_segments) == 3
        assert len(loaded.compression_result.archived_segments) == 1
