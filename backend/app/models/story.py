from typing import Optional, List, Dict, TYPE_CHECKING
import logging
from pydantic import PrivateAttr
from .story_base import StoryBase

logger = logging.getLogger("infinite_story.models.story")


if TYPE_CHECKING:
    from .story_character import StoryCharacter
    from .story_location import StoryLocation
    from .story_segment import StorySegment
    from .story_choice import StoryChoice
    from .story_context import StoryContext
    from .story_segment import SegmentStatus
    from .story_fraction import StoryFraction

class Story(StoryBase):
    """A story in the system.
    
    This represents a complete story with metadata and references to its segments.
    """
    title: str
    description: str
    genre: Optional[str] = None
    user_id: Optional[str] = None
    start_segment_id: Optional[str] = None  # Reference to the first segment of the story
    
    # Private component caches
    _characters: Dict[str, 'StoryCharacter'] = PrivateAttr(default_factory=dict)
    _locations: Dict[str, 'StoryLocation'] = PrivateAttr(default_factory=dict)
    _segments: Dict[str, 'StorySegment'] = PrivateAttr(default_factory=dict)
    _choices: Dict[str, 'StoryChoice'] = PrivateAttr(default_factory=dict)
    _context: Optional['StoryContext'] = PrivateAttr(default=None)
    _fractions: Dict[str, 'StoryFraction'] = PrivateAttr(default_factory=dict)
    
    def __init__(self, **data):
        """Initialize a Story instance.
        
        For Story instances, the story_id is always the same as the id.
        """
        if 'id' in data and 'story_id' not in data:
            data['story_id'] = data['id']
        super().__init__(**data)
    
    def add_context(self, context: 'StoryContext') -> None:
        """Add context to the story.

        Args:
            context: The context to add
        """
        if context.story_id != self.id:
            raise ValueError(f"Context belongs to story {context.story_id}, not {self.id}")
        logger.debug(f"Adding context '{context.id}' to story '{self.id}'")
        self._context = context
        context.story = self
    
    def add_character(self, character: 'StoryCharacter') -> None:
        """Add a character to the story.

        Args:
            character: The character to add
        """
        if character.story_id != self.id:
            raise ValueError(f"Character {character.id} belongs to story {character.story_id}, not {self.id}")
        logger.debug(f"Adding character '{character.id}' ({character.name}) to story '{self.id}'")
        self._characters[character.id] = character
        character.story = self
        
    def add_location(self, location: 'StoryLocation') -> None:
        """Add a location to the story.

        Args:
            location: The location to add
        """
        if location.story_id != self.id:
            raise ValueError(f"Location {location.id} belongs to story {location.story_id}, not {self.id}")
        logger.debug(f"Adding location '{location.id}' ({location.name}) to story '{self.id}'")
        self._locations[location.id] = location
        location.story = self
        
    def add_segment(self, segment: 'StorySegment') -> None:
        """Add a segment to the story.

        Args:
            segment: The segment to add
        """
        if segment.story_id != self.id:
            raise ValueError(f"Segment {segment.id} belongs to story {segment.story_id}, not {self.id}")
        logger.debug(f"Adding segment '{segment.id}' to story '{self.id}'")
        self._segments[segment.id] = segment
        segment.story = self
        
    def add_choice(self, choice: 'StoryChoice') -> None:
        """Add a choice to the story.

        Args:
            choice: The choice to add
        """
        if choice.story_id != self.id:
            raise ValueError(f"Choice {choice.id} belongs to story {choice.story_id}, not {self.id}")
        logger.debug(f"Adding choice '{choice.id}' (from: {choice.from_segment_id}, to: {choice.to_segment_id}) to story '{self.id}'")
        self._choices[choice.id] = choice
        choice.story = self
        
    def get_character(self, character_id: str) -> Optional['StoryCharacter']:
        """Get a character by ID.
        
        Args:
            character_id: The ID of the character to get
            
        Returns:
            The character, or None if not found
        """
        return self._characters.get(character_id)
        
    def get_location(self, location_id: str) -> Optional['StoryLocation']:
        """Get a location by ID.
        
        Args:
            location_id: The ID of the location to get
            
        Returns:
            The location, or None if not found
        """
        return self._locations.get(location_id)
        
    def get_segment(self, segment_id: str, include_archived: bool = False) -> Optional['StorySegment']:
        """Get a segment by ID, respecting archive status.
        
        Args:
            segment_id: The ID of the segment to get
            include_archived: If False (default), archived segments return None
            
        Returns:
            The segment, or None if not found or archived (unless include_archived=True)
        """
        seg = self._segments.get(segment_id)
        
        if seg and not include_archived:
            # Import locally to avoid circular dependency
            from .story_segment import SegmentStatus
            if seg.status == SegmentStatus.ARCHIVED:
                return None
        
        return seg
        
    def get_choice(self, choice_id: str) -> Optional['StoryChoice']:
        """Get a choice by ID.
        
        Args:
            choice_id: The ID of the choice to get
            
        Returns:
            The choice, or None if not found
        """
        return self._choices.get(choice_id)
    
    def add_fraction(self, fraction: 'StoryFraction') -> None:
        """Add a fraction to the story.

        Args:
            fraction: The fraction to add
        """
        if fraction.story_id != self.id:
            raise ValueError(f"Fraction {fraction.id} belongs to story {fraction.story_id}, not {self.id}")
        logger.debug(f"Adding fraction '{fraction.id}' ({fraction.title}) to story '{self.id}'")
        self._fractions[fraction.id] = fraction
        fraction.story = self
    
    def get_fraction(self, fraction_id: str) -> Optional['StoryFraction']:
        """Get a fraction by ID.
        
        Args:
            fraction_id: The ID of the fraction to get
            
        Returns:
            The fraction, or None if not found
        """
        return self._fractions.get(fraction_id)
    
    def get_all_fractions(self) -> List['StoryFraction']:
        """Get all fractions in the story.
        
        Returns:
            A list of all fractions, sorted by order
        """
        fractions = list(self._fractions.values())
        return sorted(fractions, key=lambda f: f.order)
    
    def get_available_choices(self, segment_id: str) -> List['StoryChoice']:
        """Get available choices from a segment, excluding archived destinations.
        
        This method returns only choices that lead to non-archived segments.
        
        Args:
            segment_id: The ID of the segment to get choices from
            
        Returns:
            A list of available choices from the segment
        """
        seg = self.get_segment(segment_id)
        if not seg:
            return []
        
        choices = []
        for choice_id in seg.outgoing_choices if hasattr(seg, 'outgoing_choices') else {}:
            choice = self._choices.get(choice_id)
            if not choice:
                continue
            
            # Check if destination is archived
            if choice.to_segment_id:
                dest = self.get_segment(choice.to_segment_id, include_archived=False)
                if dest is None:
                    # Destination is either missing or archived - skip this choice
                    continue
            
            choices.append(choice)
        
        return choices
        
    def get_all_characters(self) -> List['StoryCharacter']:
        """Get all characters in the story.
        
        Returns:
            A list of all characters
        """
        return list(self._characters.values())
        
    def get_all_locations(self) -> List['StoryLocation']:
        """Get all locations in the story.
        
        Returns:
            A list of all locations
        """
        return list(self._locations.values())
        
    def get_all_segments(self) -> List['StorySegment']:
        """Get all segments in the story.
        
        Returns:
            A list of all segments
        """
        return list(self._segments.values())
        
    def get_all_choices(self) -> List['StoryChoice']:
        """Get all choices in the story.
        
        Returns:
            A list of all choices
        """
        return list(self._choices.values())

    def get_story_id(self) -> str:
        """Get the story ID for this object.
        
        For the Story class, the story ID is the same as the object's ID.
        """
        return self.id
