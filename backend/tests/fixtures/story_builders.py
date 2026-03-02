"""Helper functions for building complete test stories.

These utilities create fully-formed story structures with characters,
locations, segments, and choices for integration testing.
"""

from typing import Optional, List, Dict, Any
from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_choice import StoryChoice


def create_test_story_with_segments(
    story_id: str = "test_story",
    segment_count: int = 3
) -> tuple[Story, List[StorySegment]]:
    """Create a test story with multiple segments.
    
    Creates a story with N segments, useful for testing navigation
    and segment relationships.
    
    Args:
        story_id: ID for the story
        segment_count: Number of segments to create
        
    Returns:
        Tuple of (Story, list of Segments)
        
    Example:
        story, segments = create_test_story_with_segments("my_story", 5)
        assert len(segments) == 5
        assert story.id == "my_story"
    """
    story = Story(
        id=story_id,
        title=f"Test Story: {story_id}",
        description="A test story for testing",
        genre="Test",
        start_segment_id="segment_001"
    )
    
    segments = []
    for i in range(segment_count):
        seg_id = f"segment_{i+1:03d}"
        segment = StorySegment(
            story=story,
            id=seg_id,
            short_description=f"Scene {i+1}",
            atmosphere="neutral",
            text_blocks=[]
        )
        segments.append(segment)
    
    return story, segments


def create_test_story_with_choices(
    story_id: str = "test_story",
    segment_count: int = 3
) -> tuple[Story, List[StorySegment], List[StoryChoice]]:
    """Create a test story with segments connected by choices.
    
    Creates a linear story where segments are connected by choices,
    forming a chain: segment_1 -> choice -> segment_2 -> choice -> segment_3, etc.
    
    Args:
        story_id: ID for the story
        segment_count: Number of segments to create
        
    Returns:
        Tuple of (Story, list of Segments, list of Choices)
        
    Example:
        story, segs, choices = create_test_story_with_choices("my_story", 4)
        assert len(segs) == 4
        assert len(choices) == 3  # One less than segments
    """
    story, segments = create_test_story_with_segments(story_id, segment_count)
    choices = []
    
    # Create choices connecting segments linearly
    for i in range(len(segments) - 1):
        choice = StoryChoice(
            story=story,
            id=f"choice_{i+1:03d}",
            from_segment_id=segments[i].id,
            to_segment_id=segments[i+1].id,
            text=f"Proceed to {segments[i+1].short_description}"
        )
        choices.append(choice)
        
        # Setup bidirectional references
        segments[i].add_outgoing_choice(choice)
        segments[i+1].add_incoming_choice(choice)
    
    return story, segments, choices


def create_test_story_with_characters(
    story_id: str = "test_story",
    character_count: int = 3,
    segment_count: int = 1
) -> tuple[Story, List[StoryCharacter], List[StorySegment]]:
    """Create a test story with characters and segments.
    
    Creates a story with multiple characters and segments, useful for
    testing character presence in scenes.
    
    Args:
        story_id: ID for the story
        character_count: Number of characters to create
        segment_count: Number of segments to create
        
    Returns:
        Tuple of (Story, list of Characters, list of Segments)
        
    Example:
        story, chars, segs = create_test_story_with_characters(
            "my_story", 
            character_count=3,
            segment_count=2
        )
        assert len(chars) == 3
        assert len(segs) == 2
    """
    story = Story(
        id=story_id,
        title=f"Test Story: {story_id}",
        description="A test story with characters",
        genre="Test",
        start_segment_id="segment_001"
    )
    
    # Create characters
    characters = []
    for i in range(character_count):
        char = StoryCharacter(
            story=story,
            id=f"char_{i+1:03d}",
            name=f"Character {i+1}",
            description=f"Test character {i+1}",
            background=f"Background for character {i+1}"
        )
        characters.append(char)
    
    # Create segments with some characters present
    segments = []
    for i in range(segment_count):
        seg = StorySegment(
            story=story,
            id=f"segment_{i+1:03d}",
            short_description=f"Scene {i+1}",
            atmosphere="neutral",
            text_blocks=[],
            characters_present=[c.id for c in characters[:min(2, character_count)]]
        )
        segments.append(seg)
    
    return story, characters, segments


def create_branching_story(
    story_id: str = "test_story",
    branch_depth: int = 2,
    choices_per_segment: int = 2
) -> tuple[Story, Dict[str, StorySegment], Dict[str, StoryChoice]]:
    """Create a test story with branching paths.
    
    Creates a story tree with multiple branches, useful for testing
    pathfinding and choice logic.
    
    Args:
        story_id: ID for the story
        branch_depth: How deep the branches should go
        choices_per_segment: How many choices each segment should have
        
    Returns:
        Tuple of (Story, dict of Segments, dict of Choices)
        
    Example:
        story, segs, choices = create_branching_story("my_story", depth=2, choices=2)
        # Creates a tree with 1 + 2 + 4 = 7 segments (exponential growth)
    """
    story = Story(
        id=story_id,
        title=f"Branching Story: {story_id}",
        description="A branching story for testing",
        genre="Test",
        start_segment_id="segment_001"
    )
    
    segments = {}
    choices = {}
    
    # Create root segment
    root = StorySegment(
        story=story,
        id="segment_001",
        short_description="The beginning",
        atmosphere="neutral",
        text_blocks=[]
    )
    segments["segment_001"] = root
    
    # Create branches
    segment_counter = 2
    
    def create_branch(parent_id: str, depth: int) -> None:
        """Recursively create branches."""
        nonlocal segment_counter
        
        if depth == 0:
            return
        
        parent = segments[parent_id]
        
        for choice_idx in range(choices_per_segment):
            seg_id = f"segment_{segment_counter:03d}"
            segment_counter += 1
            
            # Create segment
            segment = StorySegment(
                story=story,
                id=seg_id,
                short_description=f"Branch {depth} - Choice {choice_idx + 1}",
                atmosphere="neutral",
                text_blocks=[]
            )
            segments[seg_id] = segment
            
            # Create choice connecting parent to this segment
            choice_id = f"choice_{len(choices)+1:03d}"
            choice = StoryChoice(
                story=story,
                id=choice_id,
                from_segment_id=parent_id,
                to_segment_id=seg_id,
                text=f"Branch {choice_idx + 1}"
            )
            choices[choice_id] = choice
            
            # Setup bidirectional references
            parent.add_outgoing_choice(choice)
            segment.add_incoming_choice(choice)
            
            # Recurse deeper
            create_branch(seg_id, depth - 1)
    
    # Build the tree
    create_branch("segment_001", branch_depth)
    
    return story, segments, choices


def create_story_with_multiple_characters(
    story_id: str = "test_story",
    character_data: Optional[List[Dict[str, str]]] = None
) -> tuple[Story, List[StoryCharacter]]:
    """Create a story with custom character data.
    
    Allows specification of exact character properties for testing
    specific character-related logic.
    
    Args:
        story_id: ID for the story
        character_data: List of dicts with 'name', 'description', 'background'
        
    Returns:
        Tuple of (Story, list of Characters)
        
    Example:
        chars_data = [
            {"name": "Alice", "description": "The protagonist", "background": "..."},
            {"name": "Bob", "description": "The mentor", "background": "..."},
        ]
        story, chars = create_story_with_multiple_characters("my_story", chars_data)
    """
    story = Story(
        id=story_id,
        title=f"Story with Characters: {story_id}",
        description="A story with specific characters",
        genre="Test",
        start_segment_id="segment_001"
    )
    
    if character_data is None:
        character_data = [
            {"name": "Hero", "description": "The main character", "background": "..."},
            {"name": "Companion", "description": "A helpful friend", "background": "..."},
        ]
    
    characters = []
    for i, char_info in enumerate(character_data):
        char = StoryCharacter(
            story=story,
            id=f"char_{i+1:03d}",
            name=char_info.get("name", f"Character {i+1}"),
            description=char_info.get("description", "A character"),
            background=char_info.get("background", "Unknown")
        )
        characters.append(char)
    
    return story, characters
