import unittest
import os
import shutil
from datetime import datetime, UTC
from pathlib import Path

from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice
from app.models.types import TextBlock, TextType, SceneGenerationResponse, ChoiceGenerationResponse
from app.engine.generator import Generator

class MockGenerator(Generator):
    """Mock generator for testing that provides predefined responses."""
    
    def __init__(self, response_type):
        super().__init__(response_type)
        self.response_type = response_type
        
    def generate(self, prompt: str):
        if self.response_type == SceneGenerationResponse:
            return SceneGenerationResponse(
                raw_response="{}",
                parsed_data={},
                error=None,
                scene_text="The mysterious room reveals its secrets as you explore further.",
                scene_summary="Exploring the mysterious room reveals new clues.",
                character_states={},
                location_states={},
                suggested_choices=[]
            )
        elif self.response_type == ChoiceGenerationResponse:
            return ChoiceGenerationResponse(
                raw_response="{}",
                parsed_data={},
                error=None,
                choice_text="Continue exploring the room",
                choice_context="The room seems to hold more secrets worth investigating.",
                expected_outcomes=[]
            )
        return super().generate(prompt)

class TestStoryModels(unittest.TestCase):
    def setUp(self):
        """Set up test data and clean up any existing test data."""
        self.test_story_id = "test_story_1"
        self.test_data_dir = Path("data") / self.test_story_id
        
        # Clean up any existing test data
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
            
        # Create test story
        self.story = Story(
            id=self.test_story_id,
            title="Test Story",
            description="A test story for model testing",
            genre="Test",
            user_id="test_user_1",
            start_segment_id="start_segment_1",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        # Create test character
        self.character = StoryCharacter(
            id="char_1",
            story_id=self.test_story_id,
            name="Test Character",
            description="A test character",
            background="Test background"
        )
        
        # Create test location
        self.location = StoryLocation(
            id="loc_1",
            story_id=self.test_story_id,
            name="Test Location",
            description="A test location"
        )
        
        # Create test segment
        self.segment = StorySegment(
            id="start_segment_1",
            story_id=self.test_story_id,
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
                    character_id=self.character.id,
                    ai_status="active"
                )
            ],
            locations=[
                LocationStatus(
                    location_id=self.location.id,
                    ai_status="active"
                )
            ]
        )
        
        # Create test choice
        self.choice = StoryChoice(
            id="choice_1",
            story_id=self.test_story_id,
            from_segment_id=self.segment.id,
            to_segment_id="next_segment_1",
            text="Continue the story"
        )
        
        # Create generators
        self.scene_generator = MockGenerator(SceneGenerationResponse)
        self.choice_generator = MockGenerator(ChoiceGenerationResponse)
        
    def tearDown(self):
        """Clean up test data after each test."""
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
            
    def test_story_save_load(self):
        """Test saving and loading a story."""
        # Save the story
        self.story.save()
        
        # Load the story
        loaded_story = Story.load(self.test_story_id, self.story.id)
        
        # Verify the loaded story matches the original
        self.assertIsNotNone(loaded_story)
        self.assertEqual(loaded_story.id, self.story.id)
        self.assertEqual(loaded_story.title, self.story.title)
        self.assertEqual(loaded_story.description, self.story.description)
        
    def test_character_save_load(self):
        """Test saving and loading a character."""
        # Save the character
        self.character.save()
        
        # Load the character
        loaded_character = StoryCharacter.load(self.test_story_id, self.character.id)
        
        # Verify the loaded character matches the original
        self.assertIsNotNone(loaded_character)
        self.assertEqual(loaded_character.id, self.character.id)
        self.assertEqual(loaded_character.name, self.character.name)
        self.assertEqual(loaded_character.description, self.character.description)
        
    def test_segment_save_load(self):
        """Test saving and loading a segment."""
        # Save the segment
        self.segment.save()
        
        # Load the segment
        loaded_segment = StorySegment.load(self.test_story_id, self.segment.id)
        
        # Verify the loaded segment matches the original
        self.assertIsNotNone(loaded_segment)
        self.assertEqual(loaded_segment.id, self.segment.id)
        self.assertEqual(loaded_segment.short_description, self.segment.short_description)
        self.assertEqual(len(loaded_segment.text_blocks), len(self.segment.text_blocks))
        self.assertEqual(loaded_segment.text_blocks[0].content, self.segment.text_blocks[0].content)
        self.assertEqual(len(loaded_segment.characters), len(self.segment.characters))
        self.assertEqual(len(loaded_segment.locations), len(self.segment.locations))
        
    def test_choice_save_load(self):
        """Test saving and loading a choice."""
        # Save the choice
        self.choice.save()
        
        # Load the choice
        loaded_choice = StoryChoice.load(self.test_story_id, self.choice.id)
        
        # Verify the loaded choice matches the original
        self.assertIsNotNone(loaded_choice)
        self.assertEqual(loaded_choice.id, self.choice.id)
        self.assertEqual(loaded_choice.text, self.choice.text)
        self.assertEqual(loaded_choice.from_segment_id, self.choice.from_segment_id)
        self.assertEqual(loaded_choice.to_segment_id, self.choice.to_segment_id)
        
    def test_list_all(self):
        """Test listing all objects of a type."""
        # Save all objects
        self.story.save()
        self.character.save()
        self.segment.save()
        self.choice.save()
        
        # List all stories
        story_ids = Story.list_all(self.test_story_id)
        self.assertIn(self.story.id, story_ids)
        
        # List all characters
        character_ids = StoryCharacter.list_all(self.test_story_id)
        self.assertIn(self.character.id, character_ids)
        
        # List all segments
        segment_ids = StorySegment.list_all(self.test_story_id)
        self.assertIn(self.segment.id, segment_ids)
        
        # List all choices
        choice_ids = StoryChoice.list_all(self.test_story_id)
        self.assertIn(self.choice.id, choice_ids)
        
    def test_delete(self):
        """Test deleting objects."""
        # Save all objects
        self.story.save()
        self.character.save()
        
        # Delete the character
        self.character.delete()
        
        # Verify the character is deleted
        loaded_character = StoryCharacter.load(self.test_story_id, self.character.id)
        self.assertIsNone(loaded_character)
        
        # Verify the story still exists
        loaded_story = Story.load(self.test_story_id, self.story.id)
        self.assertIsNotNone(loaded_story)
        
    def test_generate_next_scene(self):
        """Test generating a new scene from a choice."""
        # Generate a new scene and choice
        new_scene, new_choice = self.segment.generate_next_scene(
            "Explore the mysterious room",
            self.scene_generator,
            self.choice_generator
        )
        
        # Verify the new scene has the expected structure
        self.assertIsNotNone(new_scene)
        self.assertEqual(new_scene.story_id, self.test_story_id)
        self.assertEqual(len(new_scene.text_blocks), 1)
        self.assertEqual(len(new_scene.characters), len(self.segment.characters))
        self.assertEqual(len(new_scene.locations), len(self.segment.locations))
        
        # Verify the choice pointers
        self.assertEqual(new_scene.from_choice_id, new_choice.id)
        self.assertIn(new_choice.id, new_scene.incoming_choices)
        self.assertIn(new_choice.id, self.segment.outgoing_choices)
        
        # Verify the choice connects the segments correctly
        self.assertEqual(new_choice.from_segment_id, self.segment.id)
        self.assertEqual(new_choice.to_segment_id, new_scene.id)

if __name__ == '__main__':
    unittest.main() 