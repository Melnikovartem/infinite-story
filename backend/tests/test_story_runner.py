import pytest
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice
from app.models.text_types import TextBlock, TextType
from app.engine.story_runner import StoryRunner

@pytest.fixture
def test_story():
    """Create a complete test story with all necessary components."""
    # Create the main story
    story = Story(
        id="test_story_1",
        title="Test Story",
        description="A test story for unit testing",
        genre="Test",
        user_id="test_user_1",
        start_segment_id="start_segment_1",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create a character
    character = StoryCharacter(
        story=story,
        id="char_1",
        name="Test Character",
        description="A test character",
        background="Test background"
    )
    
    # Create a location
    location = StoryLocation(
        story=story,
        id="loc_1",
        name="Test Location",
        description="A test location"
    )
    
    # Create the start segment
    start_segment = StorySegment(
        story=story,
        id="start_segment_1",
        from_choice_id=None,  # Start segment has no previous choice
        short_description="The beginning of the story",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The story begins..."
            )
        ],
        characters=[
            CharacterStatus(
                character_id=character.id,
                ai_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id=location.id,
                ai_status="active"
            )
        ]
    )
    
    # Create a choice
    choice = StoryChoice(
        story=story,
        id="choice_1",
        from_segment_id=start_segment.id,
        to_segment_id="next_segment_1",
        text="Continue the story"
    )
    
    # Create the next segment
    next_segment = StorySegment(
        story=story,
        id="next_segment_1",
        from_choice_id=choice.id,
        short_description="The continuation of the story",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The story continues..."
            )
        ],
        characters=[
            CharacterStatus(
                character_id=character.id,
                ai_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id=location.id,
                ai_status="active"
            )
        ]
    )
    
    return story

def test_story_runner_initialization(test_story):
    """Test that StoryRunner initializes correctly with a valid story."""
    # Create a story runner
    runner = StoryRunner(test_story)
    
    # Verify the story is set correctly
    assert runner.story.id == test_story.id
    assert runner.story.title == test_story.title
    
    # Verify initial state
    assert runner.current_segment is None
    assert runner.active_characters == {}
    assert runner.active_locations == {}
    assert runner.visited_segments == set()

def test_story_runner_start(test_story):
    """Test that StoryRunner starts correctly from the start segment."""
    runner = StoryRunner(test_story)
    
    # Start the story
    runner.start()
    
    # Verify that current segment is set
    assert runner.current_segment is not None
    assert runner.current_segment.id == test_story.start_segment_id
    
    # Verify that start segment is marked as visited
    assert test_story.start_segment_id in runner.visited_segments
    
    # Verify that the story object is properly set
    assert runner.current_segment.story == test_story

def test_story_runner_start_without_start_segment():
    """Test that StoryRunner raises an error when starting a story without a start segment."""
    # Create a story without a start segment
    story_without_start = Story(
        id="test_story_2",
        title="Test Story Without Start",
        description="A test story without a start segment",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    runner = StoryRunner(story_without_start)
    
    # Verify that starting the story raises a ValueError
    with pytest.raises(ValueError):
        runner.start() 