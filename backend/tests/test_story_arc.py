"""Unit tests for StoryArc model."""

import pytest
import shutil
from datetime import datetime, UTC
from pathlib import Path

from app.models.story import Story
from app.models.story_arc import StoryArc, ArcCompressionResult
from app.models.story_base import LOCAL_DATA_DIR


@pytest.fixture
def test_data():
    """Fixture to set up and tear down test data for StoryArc tests."""
    test_story_id = "test_arc_story"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story for Arcs",
        description="A test story for arc testing",
        genre="Test",
        user_id="test_user_1",
        start_segment_id="seg_1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    yield {
        "story": story,
        "story_id": test_story_id,
        "test_data_dir": test_data_dir
    }
    
    # Clean up after test
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)


def test_story_arc_creation(test_data):
    """Test creating a StoryArc with basic fields."""
    story = test_data["story"]
    story_id = test_data["story_id"]
    
    arc = StoryArc(
        story=story,
        id="arc_1",
        title="The Rise of the Northern Kingdom",
        description="An epic tale of ambition and power",
        start_segment_id="seg_1",
        premise="Power corrupts the innocent",
        narrative_direction="Building towards a major betrayal",
        episode_count=5
    )
    
    assert arc.id == "arc_1"
    assert arc.story_id == story_id
    assert arc.title == "The Rise of the Northern Kingdom"
    assert arc.description == "An epic tale of ambition and power"
    assert arc.start_segment_id == "seg_1"
    assert arc.premise == "Power corrupts the innocent"
    assert arc.narrative_direction == "Building towards a major betrayal"
    assert arc.episode_count == 5
    assert arc.is_compressed is False
    assert arc.compression_result is None
    assert arc.episode_ids == []
    assert arc.current_segment_id is None


def test_story_arc_serialization(test_data):
    """Test saving and loading a StoryArc."""
    story = test_data["story"]
    story_id = test_data["story_id"]
    
    arc = StoryArc(
        story=story,
        id="arc_2",
        title="The Fall of Kings",
        description="A tragic narrative",
        start_segment_id="seg_1",
        premise="Pride precedes destruction",
        narrative_direction="Moving towards downfall",
        episode_count=8,
        current_segment_id="seg_15",
        episode_ids=["ep_1", "ep_2", "ep_3"]
    )
    
    # Save the arc
    arc.save()
    
    # Load it back
    loaded = StoryArc.load(story_id, "arc_2")
    
    assert loaded is not None
    assert loaded.id == arc.id
    assert loaded.title == arc.title
    assert loaded.description == arc.description
    assert loaded.start_segment_id == arc.start_segment_id
    assert loaded.premise == arc.premise
    assert loaded.narrative_direction == arc.narrative_direction
    assert loaded.episode_count == arc.episode_count
    assert loaded.current_segment_id == arc.current_segment_id
    assert loaded.episode_ids == ["ep_1", "ep_2", "ep_3"]


def test_arc_compression_result(test_data):
    """Test ArcCompressionResult creation and integration with StoryArc."""
    story = test_data["story"]
    
    compression = ArcCompressionResult(
        arc_id="arc_1",
        mainline_branch_segments=["seg_1", "seg_2", "seg_3"],
        archived_segments=["seg_alt_1", "seg_alt_2"],
        selection_rationale="This path maximized character development",
        compression_model="gpt-4o"
    )
    
    assert compression.arc_id == "arc_1"
    assert compression.mainline_branch_segments == ["seg_1", "seg_2", "seg_3"]
    assert compression.archived_segments == ["seg_alt_1", "seg_alt_2"]
    assert compression.selection_rationale == "This path maximized character development"
    assert compression.compression_model == "gpt-4o"
    assert compression.compressed_at is not None
    
    # Create an arc with compression
    arc = StoryArc(
        story=story,
        id="arc_compressed",
        title="Compressed Arc",
        start_segment_id="seg_1",
        is_compressed=True,
        compression_result=compression
    )
    
    assert arc.is_compressed is True
    assert arc.compression_result == compression


def test_story_arc_overviews(test_data):
    """Test the overview methods of StoryArc."""
    story = test_data["story"]
    
    arc = StoryArc(
        story=story,
        id="arc_3",
        title="The Magical Revolution",
        description="Magic awakens in the world",
        start_segment_id="seg_1",
        premise="Knowledge is power",
        narrative_direction="Magic spreads across the land",
        episode_count=12
    )
    
    # Test short overview
    short = arc.get_short_overview()
    assert "The Magical Revolution" in short
    assert "12 episodes" in short
    
    # Test full overview
    full = arc.get_full_overview()
    assert "Arc: The Magical Revolution" in full
    assert "Premise: Knowledge is power" in full
    assert "Direction: Magic spreads across the land" in full
    assert "Episodes: 12" in full
    assert "Compressed: False" in full
    assert "Description:" in full


def test_story_arc_list_all(test_data):
    """Test listing all arcs for a story."""
    story = test_data["story"]
    story_id = test_data["story_id"]
    
    # Create multiple arcs
    arcs = []
    for i in range(3):
        arc = StoryArc(
            story=story,
            id=f"arc_{i}",
            title=f"Arc {i}",
            start_segment_id=f"seg_{i}",
        )
        arc.save()
        arcs.append(arc)
    
    # List all arcs
    arc_ids = StoryArc.list_all(story_id)
    
    assert len(arc_ids) == 3
    assert "arc_0" in arc_ids
    assert "arc_1" in arc_ids
    assert "arc_2" in arc_ids


def test_story_arc_with_episode_ids(test_data):
    """Test StoryArc with episode tracking."""
    story = test_data["story"]
    
    episodes = ["ep_1", "ep_2", "ep_3", "ep_4", "ep_5"]
    
    arc = StoryArc(
        story=story,
        id="arc_episodes",
        title="The Five-Episode Arc",
        start_segment_id="seg_1",
        current_segment_id="seg_25",
        episode_ids=episodes,
        episode_count=len(episodes)
    )
    
    assert len(arc.episode_ids) == 5
    assert arc.episode_count == 5
    assert arc.episode_ids == episodes


def test_story_arc_defaults(test_data):
    """Test StoryArc default values."""
    story = test_data["story"]
    
    arc = StoryArc(
        story=story,
        id="arc_defaults",
        title="Minimal Arc",
        start_segment_id="seg_1"
    )
    
    assert arc.description == ""
    assert arc.premise == ""
    assert arc.narrative_direction == ""
    assert arc.episode_ids == []
    assert arc.episode_count == 0
    assert arc.is_compressed is False
    assert arc.compression_result is None
    assert arc.current_segment_id is None
