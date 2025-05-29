from typing import Dict, List, Optional, Set
from ..models.story import Story
from ..models.story_segment import StorySegment
from ..models.story_character import StoryCharacter
from ..models.story_location import StoryLocation
from ..models.story_choice import StoryChoice

class StoryRunner:
    """Manages the runtime state of a story and handles the game loop."""
    
    def __init__(self, story: Story):
        self.story = story
        self.current_segment: Optional[StorySegment] = None
        self.active_characters: Dict[str, StoryCharacter] = {}  # character_id -> character
        self.active_locations: Dict[str, StoryLocation] = {}    # location_id -> location
        self.visited_segments: Set[str] = set()  # Set of segment IDs we've visited
        
    def start(self) -> None:
        """Start the story from the beginning."""
        if not self.story.start_segment_id:
            raise ValueError("Story has no start segment")
            
        # Load the start segment
        self.current_segment = self._load_segment(self.story.start_segment_id)
        # Add start segment to visited segments
        self.visited_segments.add(self.story.start_segment_id)
        self._update_active_entities()
        
    def _load_segment(self, segment_id: str) -> StorySegment:
        """Load a story segment by ID."""
        # TODO: Implement actual segment loading from storage
        # For now, return a mock segment
        return StorySegment(
            id=segment_id,
            story_id=self.story.story_id,
            from_choice_id=None,  # Start segment has no previous choice
            text_blocks=[],
            characters=[],
            locations=[]
        )
        
    def _update_active_entities(self) -> None:
        """Update the active characters and locations based on current segment."""
        if not self.current_segment:
            return
            
        # Update active characters
        for char_data in self.current_segment.characters:
            if char_data.character_id not in self.active_characters:
                # TODO: Load character from storage
                self.active_characters[char_data.character_id] = StoryCharacter(
                    id=char_data.character_id,
                    story_id=self.story.story_id,
                    name=f"Character {char_data.character_id}",
                    description=""
                )
                
        # Update active locations
        for loc_data in self.current_segment.locations:
            if loc_data.location_id not in self.active_locations:
                # TODO: Load location from storage
                self.active_locations[loc_data.location_id] = StoryLocation(
                    id=loc_data.location_id,
                    story_id=self.story.story_id,
                    name=f"Location {loc_data.location_id}",
                    description=""
                )
                
    def get_available_choices(self) -> List[StoryChoice]:
        """Get the choices available in the current segment."""
        if not self.current_segment:
            return []
            
        # TODO: Load choices from storage
        return []
        
    def make_choice(self, choice_id: str) -> None:
        """Make a choice and progress the story."""
        if not self.current_segment:
            raise ValueError("No current segment")
            
        # TODO: Load choice from storage
        choice = StoryChoice(
            id=choice_id,
            story_id=self.story.story_id,
            from_segment_id=self.current_segment.id,
            to_segment_id="",  # TODO: Get from storage
            text=""
        )
        
        # Move to the next segment
        self.current_segment = self._load_segment(choice.to_segment_id)
        self.visited_segments.add(choice.to_segment_id)
        self._update_active_entities()
        
    def get_current_state(self) -> dict:
        """Get the current state of the story."""
        return {
            "current_segment": self.current_segment,
            "active_characters": list(self.active_characters.values()),
            "active_locations": list(self.active_locations.values()),
            "visited_segments": list(self.visited_segments)
        }
