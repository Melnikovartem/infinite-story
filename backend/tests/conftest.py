import os
import sys
import pytest
import shutil
import json
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus, SegmentStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice, ChoiceStatus
from app.models.text_types import TextBlock, TextType
from app.models.story_base import LOCAL_DATA_DIR
from app.engine.generator import TextGenerator


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with markers and settings"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


# ============================================================================
# FIXTURES: Core Story Components
# ============================================================================

@pytest.fixture
def sample_story():
    """Create a minimal test story."""
    return Story(
        id="test_story",
        title="Test Story",
        description="A test story for testing",
        genre="Test",
        user_id="test_user",
        start_segment_id="segment_001"
    )


@pytest.fixture
def sample_character(sample_story):
    """Create a test character."""
    return StoryCharacter(
        story=sample_story,
        id="char_001",
        name="Test Character",
        description="A test character",
        background="Test background"
    )


@pytest.fixture
def sample_location(sample_story):
    """Create a test location."""
    return StoryLocation(
        story=sample_story,
        id="loc_001",
        name="Test Location",
        description="A test location"
    )


@pytest.fixture
def sample_segment(sample_story):
    """Create a test segment."""
    return StorySegment(
        story=sample_story,
        id="segment_001",
        short_description="The beginning",
        atmosphere="mysterious",
        time_of_day="evening",
        weather="clear",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The story begins..."
            )
        ]
    )


@pytest.fixture
def sample_choice(sample_story):
    """Create a test choice."""
    return StoryChoice(
        story=sample_story,
        id="choice_001",
        from_segment_id="segment_001",
        to_segment_id="segment_002",
        text="Continue forward"
    )


# ============================================================================
# FIXTURES: Data Management
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Use temporary directory for test data.
    
    This fixture sets up an isolated data directory for tests
    to avoid interfering with production data.
    """
    # Backup original directory
    original_data_dir = LOCAL_DATA_DIR
    
    # Create test data directory
    test_data_dir = tmp_path / ".infinite_story_data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Monkeypatch the LOCAL_DATA_DIR to use temp directory
    # We need to do this at the module level since it's imported
    import app.models.story_base
    monkeypatch.setattr(app.models.story_base, "LOCAL_DATA_DIR", test_data_dir)
    
    yield test_data_dir
    
    # Cleanup is automatic with tmp_path


@pytest.fixture
def clean_data_dir():
    """Clean up test data directory after tests."""
    data_dir = LOCAL_DATA_DIR / "test_story"
    
    # Clean before test
    if data_dir.exists():
        shutil.rmtree(data_dir)
    
    yield
    
    # Clean after test
    if data_dir.exists():
        shutil.rmtree(data_dir)


# ============================================================================
# FIXTURES: Story with Relations
# ============================================================================

@pytest.fixture
def complete_story(sample_story, sample_character, sample_location, sample_segment):
    """Create a complete story with character, location, and segment."""
    sample_story.add_character(sample_character)
    sample_story.add_location(sample_location)
    sample_story.add_segment(sample_segment)
    return sample_story


@pytest.fixture
def story_with_choices(complete_story, sample_choice):
    """Create a story with segments and choices."""
    complete_story.add_choice(sample_choice)
    return complete_story


# ============================================================================
# FACTORY FUNCTIONS: Create Test Objects
# ============================================================================

def factory_story(
    id: str = "test_story",
    title: str = "Test Story",
    description: str = "A test story",
    genre: str = "Test",
    user_id: str = "test_user",
    start_segment_id: str = "segment_001",
    **kwargs
) -> Story:
    """Factory function for creating Story instances.
    
    Args:
        id: Story ID
        title: Story title
        description: Story description
        genre: Story genre
        user_id: User ID
        start_segment_id: ID of starting segment
        **kwargs: Additional keyword arguments
        
    Returns:
        Story instance
    """
    return Story(
        id=id,
        story_id=id,
        title=title,
        description=description,
        genre=genre,
        user_id=user_id,
        start_segment_id=start_segment_id,
        **kwargs
    )


def factory_character(
    story: Story,
    id: str = "char_001",
    name: str = "Test Character",
    description: str = "A test character",
    background: str = "Test background",
    **kwargs
) -> StoryCharacter:
    """Factory function for creating StoryCharacter instances.
    
    Args:
        story: Parent story
        id: Character ID
        name: Character name
        description: Character description
        background: Character background
        **kwargs: Additional keyword arguments
        
    Returns:
        StoryCharacter instance
    """
    return StoryCharacter(
        story=story,
        id=id,
        name=name,
        description=description,
        background=background,
        **kwargs
    )


def factory_location(
    story: Story,
    id: str = "loc_001",
    name: str = "Test Location",
    description: str = "A test location",
    **kwargs
) -> StoryLocation:
    """Factory function for creating StoryLocation instances.
    
    Args:
        story: Parent story
        id: Location ID
        name: Location name
        description: Location description
        **kwargs: Additional keyword arguments
        
    Returns:
        StoryLocation instance
    """
    return StoryLocation(
        story=story,
        id=id,
        name=name,
        description=description,
        **kwargs
    )


def factory_segment(
    story: Story,
    id: str = "segment_001",
    short_description: str = "A scene",
    atmosphere: str = "neutral",
    text_blocks: list = None,
    **kwargs
) -> StorySegment:
    """Factory function for creating StorySegment instances.
    
    Args:
        story: Parent story
        id: Segment ID
        short_description: Short description of segment
        atmosphere: Atmosphere/mood of segment
        text_blocks: List of text blocks (default empty)
        **kwargs: Additional keyword arguments
        
    Returns:
        StorySegment instance
    """
    if text_blocks is None:
        text_blocks = [
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The scene unfolds..."
            )
        ]
    
    return StorySegment(
        story=story,
        id=id,
        short_description=short_description,
        atmosphere=atmosphere,
        text_blocks=text_blocks,
        **kwargs
    )


def factory_choice(
    story: Story,
    id: str = "choice_001",
    from_segment_id: str = "segment_001",
    to_segment_id: str = "segment_002",
    text: str = "Continue",
    **kwargs
) -> StoryChoice:
    """Factory function for creating StoryChoice instances.
    
    Args:
        story: Parent story
        id: Choice ID
        from_segment_id: ID of segment this choice leads from
        to_segment_id: ID of segment this choice leads to
        text: Choice text
        **kwargs: Additional keyword arguments
        
    Returns:
        StoryChoice instance
    """
    return StoryChoice(
        story=story,
        id=id,
        from_segment_id=from_segment_id,
        to_segment_id=to_segment_id,
        text=text,
        **kwargs
    )


# ============================================================================
# FIXTURES: Mock & Helper Objects
# ============================================================================

@pytest.fixture
def character_status():
    """Create a CharacterStatus object."""
    return CharacterStatus(
        character_id="char_001",
        current_status="active"
    )


@pytest.fixture
def location_status():
    """Create a LocationStatus object."""
    return LocationStatus(
        location_id="loc_001",
        current_status="accessible"
    )


# ============================================================================
# FIXTURES: Text & Content
# ============================================================================

@pytest.fixture
def narrator_text_block():
    """Create a narrator text block."""
    return TextBlock(
        type=TextType.NARRATOR_DESCRIBING,
        content="The narrator speaks..."
    )


@pytest.fixture
def dialogue_text_block():
    """Create a dialogue text block."""
    return TextBlock(
        type=TextType.CHARACTER_SPEECH,
        content="This is what I say",
        character="char_001",
        emotion="curious"
    )


@pytest.fixture
def system_text_block():
    """Create a system message text block."""
    return TextBlock(
        type=TextType.SYSTEM_MESSAGE,
        content="Game update: Your inventory is full"
    )


# ============================================================================
# UTILITY FUNCTIONS FOR TESTS
# ============================================================================

def create_test_story_with_segments(count: int = 3) -> tuple[Story, list]:
    """Create a test story with multiple segments.
    
    Args:
        count: Number of segments to create
        
    Returns:
        Tuple of (Story, list of Segments)
    """
    story = factory_story()
    segments = []
    
    for i in range(count):
        seg = factory_segment(
            story,
            id=f"segment_{i:03d}",
            short_description=f"Scene {i}"
        )
        segments.append(seg)
    
    return story, segments


def create_test_story_with_choices(segment_count: int = 3) -> tuple[Story, list, list]:
    """Create a test story with segments and connecting choices.
    
    Args:
        segment_count: Number of segments to create
        
    Returns:
        Tuple of (Story, list of Segments, list of Choices)
    """
    story, segments = create_test_story_with_segments(segment_count)
    choices = []
    
    # Create choices connecting segments
    for i in range(len(segments) - 1):
        choice = factory_choice(
            story,
            id=f"choice_{i:03d}",
            from_segment_id=segments[i].id,
            to_segment_id=segments[i + 1].id,
            text=f"Go to scene {i + 1}"
        )
        choices.append(choice)
    
    return story, segments, choices


# ============================================================================
# MOCK GENERATOR FOR TESTING
# ============================================================================

class MockGenerator:
    """Mock text generator for testing without API calls"""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.responses = []
    
    async def generate_scene(self, prompt: str, **kwargs) -> str:
        """Mock scene generation"""
        self.call_count += 1
        self.last_prompt = prompt
        
        if self.responses:
            return self.responses.pop(0)
        
        # Default response
        return f"Generated scene for prompt (mock response #{self.call_count})"
    
    async def generate_choice(self, context: str, **kwargs) -> List[str]:
        """Mock choice generation"""
        return [
            "Choice 1 generated by mock",
            "Choice 2 generated by mock",
            "Choice 3 generated by mock"
        ]
    
    def add_response(self, response: str):
        """Queue a response"""
        self.responses.append(response)
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.last_prompt = None
        self.responses = []


@pytest.fixture
def mock_generator():
    """Provide a mock text generator"""
    return MockGenerator()


@pytest.fixture
def mock_generator_asyncio(mock_generator):
    """Provide a mock generator as AsyncMock"""
    gen = AsyncMock()
    gen.generate_scene = mock_generator.generate_scene
    gen.generate_choice = mock_generator.generate_choice
    return gen


# ============================================================================
# ADDITIONAL CHAIN FIXTURES FOR E0+E1 INTEGRATION
# ============================================================================

@pytest.fixture
def three_segment_chain(sample_story, sample_character, sample_location):
    """Create 3 connected segments in the same episode for integration testing"""
    segments = []
    
    for i in range(1, 4):
        segment = StorySegment(
            story=sample_story,
            id=f"chain_seg_{i}",
            story_id=sample_story.id,
            short_description=f"Segment {i} in chain",
            text_blocks=[
                TextBlock(
                    type=TextType.NARRATOR_DESCRIBING,
                    content=f"Scene content for segment {i}"
                )
            ],
            characters=[
                CharacterStatus(
                    character_id=sample_character.id,
                    current_status="active"
                )
            ] if i == 1 else [],
            locations=[
                LocationStatus(
                    location_id=sample_location.id,
                    current_status="active"
                )
            ] if i == 1 else [],
            episode_number=1,
            segment_number_in_episode=i,
            parent_segment_id=f"chain_seg_{i-1}" if i > 1 else None,
            change_notes=[f"Change noted in segment {i}"]
        )
        segments.append(segment)
    
    return segments


@pytest.fixture
def multi_episode_chain(sample_story, sample_character, sample_location):
    """Create segments spanning multiple episodes for integration testing"""
    segments = []
    seg_id = 1
    
    # Create 3 episodes with 3 segments each
    for ep in range(1, 4):
        for seg_in_ep in range(1, 4):
            segment = StorySegment(
                story=sample_story,
                id=f"multi_seg_{seg_id}",
                story_id=sample_story.id,
                short_description=f"Episode {ep}, Segment {seg_in_ep}",
                text_blocks=[
                    TextBlock(
                        type=TextType.NARRATOR_DESCRIBING,
                        content=f"Content for E{ep}S{seg_in_ep}"
                    )
                ],
                episode_number=ep,
                segment_number_in_episode=seg_in_ep,
                parent_segment_id=f"multi_seg_{seg_id-1}" if seg_id > 1 else None
            )
            segments.append(segment)
            seg_id += 1
    
    return segments


# ============================================================================
# TEST DATA FILES FIXTURES
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory path"""
    fixtures_path = Path(__file__).parent / "fixtures"
    fixtures_path.mkdir(exist_ok=True)
    return fixtures_path


@pytest.fixture
def sample_story_json(fixtures_dir):
    """Create a sample story JSON file for testing"""
    story_data = {
        "id": "test_story_1",
        "title": "Test Story",
        "description": "A test story",
        "genre": "Fantasy",
        "user_id": "test_user",
        "start_segment_id": "start_1",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat()
    }
    
    file_path = fixtures_dir / "sample_story.json"
    with open(file_path, 'w') as f:
        json.dump(story_data, f)
    
    yield file_path
    
    # Cleanup
    if file_path.exists():
        file_path.unlink()
