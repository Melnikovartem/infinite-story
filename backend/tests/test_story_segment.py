import pytest
from datetime import datetime, UTC
from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice
from app.models.story_context import StoryContext
from app.models.text_types import TextType, TextBlock

@pytest.fixture
def story():
    """Create a test story with basic metadata."""
    return Story(
        id="test_story_1",
        title="Test Story",
        description="A test story for unit testing",
        genre="Fantasy",
        user_id="test_user_1"
    )

@pytest.fixture
def story_context(story):
    """Create a test story context."""
    return StoryContext(
        id="test_context_1",
        story_id=story.id,
        fundamental_truths=[
            "Magic exists in this world",
            "The kingdom is at war"
        ],
        worldbuilding={
            "setting": "Medieval fantasy kingdom",
            "magic_system": "Elemental magic",
            "political_system": "Monarchy"
        }
    )

@pytest.fixture
def character(story):
    """Create a test character."""
    return StoryCharacter(
        story=story,
        id="test_character_1",
        story_id=story.id,
        name="Test Character",
        description="A brave warrior",
        background="Born in a small village, trained in combat"
    )

@pytest.fixture
def location(story):
    """Create a test location."""
    return StoryLocation(
        story=story,
        id="test_location_1",
        story_id=story.id,
        name="Test Castle",
        description="An ancient castle on a hill"
    )

@pytest.fixture
def story_segment(story, character, location):
    """Create a test story segment with text blocks and character/location statuses."""
    return StorySegment(
        story=story,
        id="test_segment_1",
        story_id=story.id,
        short_description="The beginning of an adventure",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The sun rises over the ancient castle.",
                emotion="peaceful"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="I must find the magical artifact.",
                character="test_character_1",
                emotion="determined"
            )
        ],
        characters=[
            CharacterStatus(
                character_id=character.id,
                current_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id=location.id,
                current_status="active"
            )
        ]
    )

@pytest.fixture
def story_choice(story, story_segment):
    """Create a test story choice."""
    return StoryChoice(
        story=story,
        id="test_choice_1",
        story_id=story.id,
        from_segment_id=story_segment.id,
        to_segment_id="test_segment_2",
        text="Enter the castle"
    )

def test_story_segment_creation(story_segment, character, location):
    """Test that a story segment is created correctly with all its components."""
    assert story_segment.id == "test_segment_1"
    assert story_segment.short_description == "The beginning of an adventure"
    assert len(story_segment.text_blocks) == 2
    assert len(story_segment.characters) == 1
    assert len(story_segment.locations) == 1
    
    # Test text blocks
    assert story_segment.text_blocks[0].type == TextType.NARRATOR_DESCRIBING
    assert story_segment.text_blocks[1].type == TextType.CHARACTER_SPEECH
    assert story_segment.text_blocks[1].character == character.id
    
    # Test character and location statuses
    assert story_segment.characters[0].character_id == character.id
    assert story_segment.locations[0].location_id == location.id

def test_story_segment_choice_connections(story_segment, story_choice):
    """Test that story segment correctly manages incoming and outgoing choices."""
    # Add the choice to the segment
    story_segment.add_outgoing_choice(story_choice)
    
    assert len(story_segment.outgoing_choices) == 1
    assert story_segment.outgoing_choices[story_choice.id] == story_choice
    
    # Test incoming choice
    story_segment.add_incoming_choice(story_choice)
    assert len(story_segment.incoming_choices) == 1
    assert story_segment.incoming_choices[story_choice.id] == story_choice

def test_story_segment_save_and_load(story_segment, story):
    """Test that a story segment can be saved and loaded correctly."""
    # Save the segment
    story_segment.save()
    
    # Load the segment
    loaded_segment = StorySegment.load(story_segment.story_id, story_segment.id, story=story)
    
    assert loaded_segment is not None
    assert loaded_segment.id == story_segment.id
    assert loaded_segment.short_description == story_segment.short_description
    assert len(loaded_segment.text_blocks) == len(story_segment.text_blocks)
    assert len(loaded_segment.characters) == len(story_segment.characters)
    assert len(loaded_segment.locations) == len(story_segment.locations) 