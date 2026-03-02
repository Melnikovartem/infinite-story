import os
import sys
import pytest
import shutil
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus, SegmentStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice, ChoiceStatus
from app.models.text_types import TextBlock, TextType, SceneTextGeneratorResponse
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


# ============================================================================
# BASE FIXTURES - Story & Data Setup
# ============================================================================

@pytest.fixture
def sample_story():
    """Create a test story with basic setup"""
    test_story_id = "test_story_sample"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story",
        description="A test story for unit tests",
        genre="Fantasy",
        user_id="test_user_1",
        start_segment_id="start_segment_1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    yield story
    
    # Cleanup after test
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)


@pytest.fixture
def sample_character(sample_story):
    """Create a test character"""
    character = StoryCharacter(
        story=sample_story,
        id="char_alice",
        story_id=sample_story.id,
        name="Alice",
        description="The protagonist",
        background="A curious adventurer seeking truth"
    )
    return character


@pytest.fixture
def sample_location(sample_story):
    """Create a test location"""
    location = StoryLocation(
        story=sample_story,
        id="loc_forest",
        story_id=sample_story.id,
        name="Dark Forest",
        description="A mysterious ancient forest"
    )
    return location


@pytest.fixture
def sample_segment(sample_story, sample_character, sample_location):
    """Create a test segment"""
    segment = StorySegment(
        story=sample_story,
        id="start_segment_1",
        story_id=sample_story.id,
        short_description="The story begins in a mysterious location",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="You find yourself in a dark forest..."
            ),
            TextBlock(
                type=TextType.CHARACTER_DIALOGUE,
                content="Alice says: 'What brings you here?'"
            )
        ],
        characters=[
            CharacterStatus(
                character_id=sample_character.id,
                current_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id=sample_location.id,
                current_status="active"
            )
        ],
        episode_number=1,
        segment_number_in_episode=1,
        status=SegmentStatus.WRITTEN
    )
    return segment


# ============================================================================
# FACTORY FIXTURES - Segment Chain Creation
# ============================================================================

@pytest.fixture
def three_segment_chain(sample_story, sample_character, sample_location):
    """Create 3 connected segments in the same episode"""
    segments = []
    
    for i in range(1, 4):
        segment = StorySegment(
            story=sample_story,
            id=f"seg_{i}",
            story_id=sample_story.id,
            short_description=f"Segment {i} description",
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
            ],
            locations=[
                LocationStatus(
                    location_id=sample_location.id,
                    current_status="active"
                )
            ],
            episode_number=1,
            segment_number_in_episode=i,
            parent_segment_id=f"seg_{i-1}" if i > 1 else None,
            change_notes=[f"Change noted in segment {i}"],
            status=SegmentStatus.WRITTEN
        )
        segments.append(segment)
    
    return segments


@pytest.fixture
def multi_episode_chain(sample_story, sample_character, sample_location):
    """Create segments spanning multiple episodes"""
    segments = []
    seg_id = 1
    
    # Episode 1: 3 segments
    for ep in range(1, 4):
        for seg_in_ep in range(1, 4):
            segment = StorySegment(
                story=sample_story,
                id=f"seg_{seg_id}",
                story_id=sample_story.id,
                short_description=f"Episode {ep}, Segment {seg_in_ep}",
                text_blocks=[
                    TextBlock(
                        type=TextType.NARRATOR_DESCRIBING,
                        content=f"Content for E{ep}S{seg_in_ep}"
                    )
                ],
                characters=[
                    CharacterStatus(
                        character_id=sample_character.id,
                        current_status="active"
                    )
                ],
                locations=[
                    LocationStatus(
                        location_id=sample_location.id,
                        current_status="active"
                    )
                ],
                episode_number=ep,
                segment_number_in_episode=seg_in_ep,
                parent_segment_id=f"seg_{seg_id-1}" if seg_id > 1 else None,
                status=SegmentStatus.WRITTEN
            )
            segments.append(segment)
            seg_id += 1
    
    return segments


# ============================================================================
# CHOICE FIXTURES
# ============================================================================

@pytest.fixture
def sample_choice(sample_segment):
    """Create a test choice"""
    choice = StoryChoice(
        story=sample_segment.story,
        id="choice_1",
        story_id=sample_segment.story.id,
        from_segment_id=sample_segment.id,
        choice_text="Explore the forest further",
        status=ChoiceStatus.AVAILABLE
    )
    return choice


@pytest.fixture
def choice_with_target(sample_segment, three_segment_chain):
    """Create a choice that points to an existing segment"""
    choice = StoryChoice(
        story=sample_segment.story,
        id="choice_2",
        story_id=sample_segment.story.id,
        from_segment_id=sample_segment.id,
        to_segment_id=three_segment_chain[1].id,
        choice_text="Return to where you came from",
        status=ChoiceStatus.AVAILABLE
    )
    return choice


# ============================================================================
# MOCK FIXTURES - AI Generator
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
    """Create a sample story JSON file"""
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


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def clear_test_data():
    """Clear all test data before and after test"""
    test_data_dir = LOCAL_DATA_DIR
    
    # Cleanup before
    if test_data_dir.exists():
        for item in test_data_dir.iterdir():
            if item.name.startswith("test_"):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    
    yield
    
    # Cleanup after
    if test_data_dir.exists():
        for item in test_data_dir.iterdir():
            if item.name.startswith("test_"):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()


# ============================================================================
# FACTORIES - Functions for creating test objects
# ============================================================================

def factory_segment(
    story: Story,
    id: str = "seg_factory",
    episode_number: int = 1,
    segment_number: int = 1,
    parent_id: Optional[str] = None,
    status: SegmentStatus = SegmentStatus.WRITTEN,
    **kwargs
) -> StorySegment:
    """Factory for creating test segments with defaults"""
    defaults = {
        "story": story,
        "id": id,
        "story_id": story.id,
        "episode_number": episode_number,
        "segment_number_in_episode": segment_number,
        "parent_segment_id": parent_id,
        "status": status,
        "short_description": f"Test segment {id}",
        "text_blocks": [
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="Test content"
            )
        ],
    }
    defaults.update(kwargs)
    return StorySegment(**defaults)


def factory_choice(
    story: Story,
    from_segment_id: str,
    id: str = "choice_factory",
    to_segment_id: Optional[str] = None,
    choice_text: str = "Test choice",
    **kwargs
) -> StoryChoice:
    """Factory for creating test choices with defaults"""
    defaults = {
        "story": story,
        "id": id,
        "story_id": story.id,
        "from_segment_id": from_segment_id,
        "to_segment_id": to_segment_id,
        "choice_text": choice_text,
        "status": ChoiceStatus.AVAILABLE,
    }
    defaults.update(kwargs)
    return StoryChoice(**defaults)


def factory_character(
    story: Story,
    id: str = "char_factory",
    name: str = "Test Character",
    **kwargs
) -> StoryCharacter:
    """Factory for creating test characters with defaults"""
    defaults = {
        "story": story,
        "id": id,
        "story_id": story.id,
        "name": name,
        "description": f"Description of {name}",
    }
    defaults.update(kwargs)
    return StoryCharacter(**defaults)


def factory_location(
    story: Story,
    id: str = "loc_factory",
    name: str = "Test Location",
    **kwargs
) -> StoryLocation:
    """Factory for creating test locations with defaults"""
    defaults = {
        "story": story,
        "id": id,
        "story_id": story.id,
        "name": name,
        "description": f"Description of {name}",
    }
    defaults.update(kwargs)
    return StoryLocation(**defaults)
