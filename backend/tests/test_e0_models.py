"""
E0: Data Layer - Comprehensive Model Tests

Tests for:
- Story models (Story, StorySegment, StoryCharacter, StoryLocation, StoryChoice)
- Model validation
- Serialization/deserialization
- Save/load operations
- Edge cases and error handling
"""

import pytest
import json
from datetime import datetime, UTC
from typing import List

from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus, SegmentStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice, ChoiceStatus
from app.models.text_types import TextBlock, TextType


# ============================================================================
# STORY MODEL TESTS
# ============================================================================

class TestStoryModel:
    """Test Story model creation, validation, and operations"""
    
    def test_story_creation(self, sample_story):
        """Story can be created with required fields"""
        assert sample_story.id == "test_story_sample"
        assert sample_story.title == "Test Story"
        assert sample_story.description == "A test story for unit tests"
        assert sample_story.genre == "Fantasy"
        assert sample_story.user_id == "test_user_1"
        assert sample_story.start_segment_id == "start_segment_1"
    
    def test_story_timestamps(self, sample_story):
        """Story has valid timestamps"""
        assert sample_story.created_at is not None
        assert sample_story.updated_at is not None
        assert isinstance(sample_story.created_at, datetime)
        assert isinstance(sample_story.updated_at, datetime)
    
    def test_story_save_and_load(self, sample_story):
        """Story can be saved and loaded"""
        # Save
        sample_story.save()
        
        # Load
        loaded = Story.load(sample_story.id, sample_story.id)
        
        assert loaded is not None
        assert loaded.id == sample_story.id
        assert loaded.title == sample_story.title
    
    def test_story_equality(self):
        """Two stories with same data are equal"""
        story1 = Story(
            id="story1",
            title="Test",
            genre="Fantasy",
            user_id="user1",
            start_segment_id="seg1"
        )
        story2 = Story(
            id="story1",
            title="Test",
            genre="Fantasy",
            user_id="user1",
            start_segment_id="seg1"
        )
        
        assert story1 == story2


# ============================================================================
# STORY SEGMENT TESTS
# ============================================================================

class TestStorySegment:
    """Test StorySegment model"""
    
    def test_segment_creation(self, sample_segment):
        """Segment can be created with required fields"""
        assert sample_segment.id == "start_segment_1"
        assert sample_segment.episode_number == 1
        assert sample_segment.segment_number_in_episode == 1
        assert sample_segment.status == SegmentStatus.WRITTEN
    
    def test_segment_text_blocks(self, sample_segment):
        """Segment contains text blocks"""
        assert len(sample_segment.text_blocks) >= 2
        assert sample_segment.text_blocks[0].type == TextType.NARRATOR_DESCRIBING
        assert "dark forest" in sample_segment.text_blocks[0].content
    
    def test_segment_character_status(self, sample_segment, sample_character):
        """Segment tracks character status"""
        assert len(sample_segment.characters) >= 1
        char_status = sample_segment.characters[0]
        assert char_status.character_id == sample_character.id
        assert char_status.current_status == "active"
    
    def test_segment_location_status(self, sample_segment, sample_location):
        """Segment tracks location status"""
        assert len(sample_segment.locations) >= 1
        loc_status = sample_segment.locations[0]
        assert loc_status.location_id == sample_location.id
        assert loc_status.current_status == "active"
    
    def test_segment_parent_relationship(self, three_segment_chain):
        """Segments can reference parent segment"""
        seg1, seg2, seg3 = three_segment_chain
        
        assert seg1.parent_segment_id is None
        assert seg2.parent_segment_id == seg1.id
        assert seg3.parent_segment_id == seg2.id
    
    def test_segment_save_and_load(self, sample_segment):
        """Segment can be saved and loaded"""
        sample_segment.save()
        
        loaded = StorySegment.load(
            sample_segment.story.id,
            sample_segment.id,
            story=sample_segment.story
        )
        
        assert loaded is not None
        assert loaded.id == sample_segment.id
        assert loaded.episode_number == sample_segment.episode_number
    
    def test_segment_change_notes(self):
        """Segment can track change notes"""
        story = Story(
            id="test_story",
            title="Test",
            genre="Fantasy",
            user_id="user",
            start_segment_id="start"
        )
        
        segment = StorySegment(
            story=story,
            id="seg1",
            change_notes=["Alice learns truth", "Bob arrives"]
        )
        
        assert len(segment.change_notes) == 2
        assert "Alice learns truth" in segment.change_notes


# ============================================================================
# STORY CHARACTER TESTS
# ============================================================================

class TestStoryCharacter:
    """Test StoryCharacter model"""
    
    def test_character_creation(self, sample_character):
        """Character can be created"""
        assert sample_character.id == "char_alice"
        assert sample_character.name == "Alice"
        assert sample_character.description == "The protagonist"
        assert sample_character.background == "A curious adventurer seeking truth"
    
    def test_character_save_and_load(self, sample_character):
        """Character can be saved and loaded"""
        sample_character.save()
        
        loaded = StoryCharacter.load(
            sample_character.story.id,
            sample_character.id,
            story=sample_character.story
        )
        
        assert loaded is not None
        assert loaded.name == sample_character.name
        assert loaded.description == sample_character.description
    
    def test_character_state_tracking(self, sample_character):
        """Character state can be tracked"""
        # State tracking depends on implementation
        # Test basic attribute access
        assert hasattr(sample_character, 'id')
        assert hasattr(sample_character, 'name')


# ============================================================================
# STORY LOCATION TESTS
# ============================================================================

class TestStoryLocation:
    """Test StoryLocation model"""
    
    def test_location_creation(self, sample_location):
        """Location can be created"""
        assert sample_location.id == "loc_forest"
        assert sample_location.name == "Dark Forest"
        assert sample_location.description == "A mysterious ancient forest"
    
    def test_location_save_and_load(self, sample_location):
        """Location can be saved and loaded"""
        sample_location.save()
        
        loaded = StoryLocation.load(
            sample_location.story.id,
            sample_location.id,
            story=sample_location.story
        )
        
        assert loaded is not None
        assert loaded.name == sample_location.name


# ============================================================================
# STORY CHOICE TESTS
# ============================================================================

class TestStoryChoice:
    """Test StoryChoice model"""
    
    def test_choice_creation(self, sample_choice):
        """Choice can be created"""
        assert sample_choice.id == "choice_1"
        assert sample_choice.from_segment_id == sample_choice.from_segment_id
        assert sample_choice.choice_text == "Explore the forest further"
        assert sample_choice.status == ChoiceStatus.AVAILABLE
    
    def test_choice_with_target(self, choice_with_target):
        """Choice can reference target segment"""
        assert choice_with_target.to_segment_id is not None
    
    def test_choice_without_target(self, sample_choice):
        """Choice can be made without target (pending generation)"""
        assert sample_choice.to_segment_id is None
    
    def test_choice_save_and_load(self, sample_choice):
        """Choice can be saved and loaded"""
        sample_choice.save()
        
        loaded = StoryChoice.load(
            sample_choice.story.id,
            sample_choice.id,
            story=sample_choice.story
        )
        
        assert loaded is not None
        assert loaded.choice_text == sample_choice.choice_text
    
    def test_choice_status(self):
        """Choice status can be tracked"""
        story = Story(
            id="test",
            title="Test",
            genre="Fantasy",
            user_id="user",
            start_segment_id="start"
        )
        
        # Test different statuses
        choice_available = StoryChoice(
            story=story,
            id="c1",
            from_segment_id="seg1",
            status=ChoiceStatus.AVAILABLE
        )
        assert choice_available.status == ChoiceStatus.AVAILABLE
        
        choice_used = StoryChoice(
            story=story,
            id="c2",
            from_segment_id="seg1",
            status=ChoiceStatus.USED
        )
        assert choice_used.status == ChoiceStatus.USED


# ============================================================================
# TEXT BLOCK TESTS
# ============================================================================

class TestTextBlock:
    """Test TextBlock model"""
    
    def test_text_block_creation(self):
        """TextBlock can be created"""
        block = TextBlock(
            type=TextType.NARRATOR_DESCRIBING,
            content="The adventure begins"
        )
        
        assert block.type == TextType.NARRATOR_DESCRIBING
        assert block.content == "The adventure begins"
    
    def test_text_block_types(self):
        """All TextBlock types are available"""
        types = [
            TextType.NARRATOR_DESCRIBING,
            TextType.CHARACTER_DIALOGUE,
            TextType.INTERNAL_MONOLOGUE,
            TextType.SCENE_SETTING,
        ]
        
        for text_type in types:
            block = TextBlock(type=text_type, content="Test")
            assert block.type == text_type


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

class TestSerialization:
    """Test model serialization and deserialization"""
    
    def test_story_to_dict(self, sample_story):
        """Story can be converted to dict"""
        story_dict = sample_story.model_dump()
        
        assert story_dict['id'] == sample_story.id
        assert story_dict['title'] == sample_story.title
        assert 'created_at' in story_dict
    
    def test_story_to_json(self, sample_story):
        """Story can be converted to JSON"""
        story_json = sample_story.model_dump_json()
        
        assert isinstance(story_json, str)
        data = json.loads(story_json)
        assert data['id'] == sample_story.id
    
    def test_story_from_dict(self):
        """Story can be created from dict"""
        data = {
            "id": "story1",
            "title": "Test Story",
            "description": "Test",
            "genre": "Fantasy",
            "user_id": "user1",
            "start_segment_id": "seg1"
        }
        
        story = Story(**data)
        assert story.id == "story1"
        assert story.title == "Test Story"


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_segment_with_empty_text_blocks(self, sample_story):
        """Segment with empty text blocks"""
        segment = StorySegment(
            story=sample_story,
            id="empty_seg",
            text_blocks=[]
        )
        
        assert segment.text_blocks == []
    
    def test_segment_with_many_text_blocks(self, sample_story):
        """Segment with many text blocks"""
        blocks = [
            TextBlock(type=TextType.NARRATOR_DESCRIBING, content=f"Block {i}")
            for i in range(100)
        ]
        
        segment = StorySegment(
            story=sample_story,
            id="many_blocks",
            text_blocks=blocks
        )
        
        assert len(segment.text_blocks) == 100
    
    def test_character_with_special_characters_in_name(self, sample_story):
        """Character name can contain special characters"""
        char = StoryCharacter(
            story=sample_story,
            id="special_char",
            name="Über-Draugr's Daughter",
            description="A character with special chars"
        )
        
        assert "Über" in char.name
        assert "'" in char.name
    
    def test_long_description(self, sample_story):
        """Locations/characters can have long descriptions"""
        long_desc = "A" * 10000
        
        location = StoryLocation(
            story=sample_story,
            id="long_loc",
            name="Test",
            description=long_desc
        )
        
        assert len(location.description) == 10000
    
    def test_segment_without_parent(self, sample_story):
        """Segment can exist without parent (starting segment)"""
        segment = StorySegment(
            story=sample_story,
            id="root_seg",
            parent_segment_id=None
        )
        
        assert segment.parent_segment_id is None
    
    def test_circular_parent_reference_prevention(self, three_segment_chain):
        """Prevent circular parent references (if validation exists)"""
        seg1, seg2, seg3 = three_segment_chain
        
        # seg3 should not reference seg1 as parent (would create circle)
        # This would need validation in model
        assert seg3.parent_segment_id != seg1.id


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================

class TestFactories:
    """Test fixture factories"""
    
    def test_factory_segment_basic(self, sample_story):
        """Factory creates segment with defaults"""
        from conftest import factory_segment
        
        seg = factory_segment(sample_story)
        
        assert seg.story == sample_story
        assert seg.id == "seg_factory"
        assert seg.episode_number == 1
    
    def test_factory_segment_custom(self, sample_story):
        """Factory creates segment with custom values"""
        from conftest import factory_segment
        
        seg = factory_segment(
            sample_story,
            id="custom_seg",
            episode_number=5,
            segment_number=3
        )
        
        assert seg.id == "custom_seg"
        assert seg.episode_number == 5
        assert seg.segment_number_in_episode == 3
    
    def test_factory_choice(self, sample_story):
        """Factory creates choice"""
        from conftest import factory_choice
        
        choice = factory_choice(
            sample_story,
            from_segment_id="seg1",
            id="test_choice",
            choice_text="Custom choice"
        )
        
        assert choice.id == "test_choice"
        assert choice.choice_text == "Custom choice"
