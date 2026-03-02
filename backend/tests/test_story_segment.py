import pytest
from datetime import datetime, UTC
from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus, SegmentStatus
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


# E0-1 Tests: Enhanced StorySegment with episode/arc context
class TestSegmentStatusEnum:
    """Tests for SegmentStatus enum."""
    
    def test_segment_status_values(self):
        """Test that SegmentStatus enum has correct values."""
        assert SegmentStatus.UNEXPLORED.value == "unexplored"
        assert SegmentStatus.GENERATING.value == "generating"
        assert SegmentStatus.GENERATED.value == "generated"
        assert SegmentStatus.ARCHIVED.value == "archived"
    
    def test_segment_status_from_string(self):
        """Test creating SegmentStatus from string values."""
        status = SegmentStatus("generated")
        assert status == SegmentStatus.GENERATED


class TestSegmentEnhancedFields:
    """Tests for E0-1 enhanced segment fields."""
    
    def test_segment_creation_with_defaults(self, story):
        """Segment created with E0-1 defaults."""
        segment = StorySegment(
            story=story,
            id="seg_1",
            short_description="A test segment",
            story_id=story.id
        )
        
        assert segment.episode_number == 1
        assert segment.status == SegmentStatus.UNEXPLORED
        assert segment.character_states == {}
        assert segment.change_notes == []
        assert segment.protagonist_alive is True
        assert segment.triggers_episode_transition is False
        assert segment.pacing_weight == 0.0
        assert segment.end_condition_proximity == 0.0
    
    def test_segment_episode_context(self, story):
        """Test segment with episode context."""
        segment = StorySegment(
            story=story,
            id="seg_2",
            short_description="Episode start",
            story_id=story.id,
            arc_id="arc_001",
            episode_number=2,
            episode_tone="dark_and_mysterious",
            episode_end_condition="protagonist discovers the truth",
            segment_number_in_episode=3
        )
        
        assert segment.arc_id == "arc_001"
        assert segment.episode_number == 2
        assert segment.episode_tone == "dark_and_mysterious"
        assert segment.episode_end_condition == "protagonist discovers the truth"
        assert segment.segment_number_in_episode == 3
    
    def test_segment_character_state_tracking(self, story):
        """Test segment with character state snapshot."""
        char_states = {
            "char_1": {"mood": "hopeful", "location": "castle", "alive": True},
            "char_2": {"mood": "angry", "location": "forest", "alive": True}
        }
        
        segment = StorySegment(
            story=story,
            id="seg_3",
            short_description="State snapshot",
            story_id=story.id,
            character_states=char_states,
            change_notes=["Character 1 learned a secret", "Character 2 fled"]
        )
        
        assert segment.character_states == char_states
        assert len(segment.change_notes) == 2
        assert "secret" in segment.change_notes[0]
    
    def test_segment_pacing_weight_validation(self, story):
        """Test pacing weight is constrained to 0.0-1.0."""
        # Valid values
        for weight in [0.0, 0.5, 1.0]:
            segment = StorySegment(
                story=story,
                id=f"seg_pace_{int(weight*10)}",
                short_description="Pacing test",
                story_id=story.id,
                pacing_weight=weight
            )
            assert segment.pacing_weight == weight
    
    def test_segment_parent_tracking(self, story):
        """Test parent segment and choice tracking."""
        segment = StorySegment(
            story=story,
            id="seg_child",
            short_description="Child segment",
            story_id=story.id,
            parent_segment_id="seg_parent",
            parent_choice_id="choice_001"
        )
        
        assert segment.parent_segment_id == "seg_parent"
        assert segment.parent_choice_id == "choice_001"


class TestSegmentImmutability:
    """Tests for immutability lock after generation."""
    
    def test_segment_is_locked_property(self, story):
        """Test is_locked property."""
        segment = StorySegment(
            story=story,
            id="seg_lock_1",
            short_description="Lock test",
            story_id=story.id
        )
        
        assert segment.is_locked is False
        assert segment.status == SegmentStatus.UNEXPLORED
        
        # Mark as generated
        segment.status = SegmentStatus.GENERATED
        assert segment.is_locked is True
    
    def test_segment_validate_locked_raises_error(self, story):
        """Cannot modify generated segment."""
        segment = StorySegment(
            story=story,
            id="seg_lock_2",
            short_description="Lock validation test",
            story_id=story.id
        )
        
        # Should not raise when unexplored
        segment.validate_locked()  # No error
        
        # Mark as generated and test
        segment.status = SegmentStatus.GENERATED
        with pytest.raises(ValueError, match="locked after generation"):
            segment.validate_locked()


class TestSegmentSerialization:
    """Tests for save/load with new fields."""
    
    def test_segment_serialization_with_episode_fields(self, story):
        """Save and load segment with episode context."""
        original = StorySegment(
            story=story,
            id="seg_serial_1",
            short_description="Serialization test",
            story_id=story.id,
            episode_number=2,
            arc_id="arc_001",
            pacing_weight=0.5,
            character_states={"char_1": {"mood": "sad"}},
            protagonist_id="char_1"
        )
        
        original.save()
        loaded = StorySegment.load(story.id, "seg_serial_1", story=story)
        
        assert loaded is not None
        assert loaded.episode_number == 2
        assert loaded.arc_id == "arc_001"
        assert loaded.pacing_weight == 0.5
        assert loaded.character_states == {"char_1": {"mood": "sad"}}
        assert loaded.protagonist_id == "char_1"
    
    def test_segment_serialization_with_status(self, story):
        """Save and load segment with status enum."""
        segment = StorySegment(
            story=story,
            id="seg_serial_2",
            short_description="Status serialization",
            story_id=story.id,
            status=SegmentStatus.GENERATED
        )
        
        segment.save()
        loaded = StorySegment.load(story.id, "seg_serial_2", story=story)
        
        assert loaded is not None
        assert loaded.status == SegmentStatus.GENERATED
        assert loaded.is_locked is True 