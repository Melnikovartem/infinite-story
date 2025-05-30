import pytest
import os
import shutil
from datetime import datetime, UTC
from pathlib import Path

from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice
from app.models.text_types import TextBlock, TextType, SceneTextGeneratorResponse
from app.engine.generator import TextGenerator
from tests.test_generator import MockGenerator

@pytest.fixture
def test_data():
    """Fixture to set up and tear down test data."""
    test_story_id = "test_story_1"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Clean up any existing test data
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
        
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story",
        description="A test story for model testing",
        genre="Test",
        user_id="test_user_1",
        start_segment_id="start_segment_1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    # Create test character
    character = StoryCharacter(
        story=story,
        id="char_1",
        story_id=story.id,
        name="Test Character",
        description="A test character",
        background="Test background"
    )
    
    # Create test location
    location = StoryLocation(
        story=story,
        id="loc_1",
        story_id=story.id,
        name="Test Location",
        description="A test location"
    )
    
    # Create test segment
    segment = StorySegment(
        story=story,
        id="start_segment_1",
        story_id=story.id,
        from_choice_id=None,
        short_description="The story begins in a mysterious location",
        text_blocks=[
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The story begins..."
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
    
    # Create test choice
    choice = StoryChoice(
        story=story,
        id="choice_1",
        story_id=story.id,
        from_segment_id=segment.id,
        to_segment_id="next_segment_1",
        text="Continue the story"
    )
    
    generator = MockGenerator(SceneTextGeneratorResponse)
    
    yield {
        "story": story,
        "character": character,
        "location": location,
        "segment": segment,
        "choice": choice,
        "generator": generator,
        "test_story_id": test_story_id,
        "test_data_dir": test_data_dir
    }
    
    # Clean up after tests
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)

@pytest.mark.asyncio
async def test_story_save_load(test_data):
    """Test saving and loading a story."""
    story = test_data["story"]
    test_story_id = test_data["test_story_id"]
    
    # Save the story
    story.save()
    
    # Load the story
    loaded_story = Story.load(test_story_id, story.id)
    
    # Verify the loaded story matches the original
    assert loaded_story is not None
    assert loaded_story.id == story.id
    assert loaded_story.title == story.title
    assert loaded_story.description == story.description

@pytest.mark.asyncio
async def test_character_save_load(test_data):
    """Test saving and loading a character."""
    character = test_data["character"]
    test_story_id = test_data["test_story_id"]
    story = test_data["story"]
    
    # Save the character
    character.save()
    
    # Load the character
    loaded_character = StoryCharacter.load(test_story_id, character.id, story=story)
    
    # Verify the loaded character matches the original
    assert loaded_character is not None
    assert loaded_character.id == character.id
    assert loaded_character.name == character.name
    assert loaded_character.description == character.description

@pytest.mark.asyncio
async def test_segment_save_load(test_data):
    """Test saving and loading a segment."""
    segment = test_data["segment"]
    test_story_id = test_data["test_story_id"]
    story = test_data["story"]
    
    # Save the segment
    segment.save()
    
    # Load the segment
    loaded_segment = StorySegment.load(test_story_id, segment.id, story=story)
    
    # Verify the loaded segment matches the original
    assert loaded_segment is not None
    assert loaded_segment.id == segment.id
    assert loaded_segment.short_description == segment.short_description
    assert len(loaded_segment.text_blocks) == len(segment.text_blocks)
    assert loaded_segment.text_blocks[0].content == segment.text_blocks[0].content
    assert len(loaded_segment.characters) == len(segment.characters)
    assert len(loaded_segment.locations) == len(segment.locations)

@pytest.mark.asyncio
async def test_choice_save_load(test_data):
    """Test saving and loading a choice."""
    choice = test_data["choice"]
    test_story_id = test_data["test_story_id"]
    story = test_data["story"]
    
    # Save the choice
    choice.save()
    
    # Load the choice
    loaded_choice = StoryChoice.load(test_story_id, choice.id, story=story)
    
    # Verify the loaded choice matches the original
    assert loaded_choice is not None
    assert loaded_choice.id == choice.id
    assert loaded_choice.text == choice.text
    assert loaded_choice.from_segment_id == choice.from_segment_id
    assert loaded_choice.to_segment_id == choice.to_segment_id

@pytest.mark.asyncio
async def test_list_all(test_data):
    """Test listing all objects of a type."""
    story = test_data["story"]
    character = test_data["character"]
    segment = test_data["segment"]
    choice = test_data["choice"]
    test_story_id = test_data["test_story_id"]
    
    # Save all objects
    story.save()
    character.save()
    segment.save()
    choice.save()
    
    # List all stories
    story_ids = Story.list_all(test_story_id)
    assert story.id in story_ids
    
    # List all characters
    character_ids = StoryCharacter.list_all(test_story_id)
    assert character.id in character_ids
    
    # List all segments
    segment_ids = StorySegment.list_all(test_story_id)
    assert segment.id in segment_ids
    
    # List all choices
    choice_ids = StoryChoice.list_all(test_story_id)
    assert choice.id in choice_ids

@pytest.mark.asyncio
async def test_delete(test_data):
    """Test deleting objects."""
    story = test_data["story"]
    character = test_data["character"]
    test_story_id = test_data["test_story_id"]
    
    # Save all objects
    story.save()
    character.save()
    
    # Delete the character
    character.delete()
    
    # Verify the character is deleted
    loaded_character = StoryCharacter.load(test_story_id, character.id, story=story)
    assert loaded_character is None
    
    # Verify the story still exists
    loaded_story = Story.load(test_story_id, story.id)
    assert loaded_story is not None

@pytest.mark.asyncio
async def test_generate_next_scene(test_data):
    """Test generating a new scene from a choice."""
    segment = test_data["segment"]
    generator = test_data["generator"]
    test_story_id = test_data["test_story_id"]
    story = test_data["story"]
    
    # Generate a new scene and choice
    new_scene, new_choice = await segment.generate_next_scene(
        "Explore the mysterious room",
        generator
    )
    
    # Verify the new scene has the expected structure
    assert new_scene is not None
    assert new_scene.story_id == test_story_id
    assert new_scene.story == story  # Verify story object is set
    assert len(new_scene.text_blocks) == 3  # Mock generator returns 3 text blocks
    assert new_scene.text_blocks[0].type == TextType.NARRATOR_DESCRIBING
    assert new_scene.text_blocks[1].type == TextType.CHARACTER_SPEECH
    assert new_scene.text_blocks[2].type == TextType.SFX
    assert len(new_scene.characters) == len(segment.characters)
    assert len(new_scene.locations) == len(segment.locations)
    
    # Verify the choice pointers
    assert new_scene.from_choice_id == new_choice.id
    assert new_choice.id in new_scene.incoming_choices
    assert new_choice.id in segment.outgoing_choices
    
    # Verify the choice connects the segments correctly
    assert new_choice.from_segment_id == segment.id
    assert new_choice.to_segment_id == new_scene.id