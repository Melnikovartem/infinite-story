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
        self.current_segment = self.story.get_segment(self.story.start_segment_id)
        
        # Mark the start segment as visited
        self.visited_segments.add(self.story.start_segment_id)
        self._update_active_entities()
        
    def _update_active_entities(self) -> None:
        """Update the active characters and locations based on current segment."""
        if not self.current_segment:
            return
            
        # Update active characters
        for char_data in self.current_segment.characters:
            if char_data.character_id not in self.active_characters:
                character = StoryCharacter.load(self.story.id, char_data.character_id, self.story)
                if character:
                    self.active_characters[char_data.character_id] = character
                
        # Update active locations
        for loc_data in self.current_segment.locations:
            if loc_data.location_id not in self.active_locations:
                location = StoryLocation.load(self.story.id, loc_data.location_id, self.story)
                if location:
                    self.active_locations[loc_data.location_id] = location

        
                
    def get_available_choices(self) -> List[StoryChoice]:
        """Get the choices available in the current segment."""
        if not self.current_segment:
            return []
            
        # Return the outgoing choices directly from the segment
        return list(self.current_segment.outgoing_choices.values())
        
    def make_choice(self, choice_id: str) -> None:
        """Make a choice and progress the story."""
        if not self.current_segment:
            raise ValueError("No current segment")
            
        # Load the choice
        choice = StoryChoice.load(self.story.id, choice_id)
        if not choice:
            raise ValueError(f"Choice {choice_id} not found")
            
        if choice.from_segment_id != self.current_segment.id:
            raise ValueError(f"Choice {choice_id} is not available in the current segment")
            
        # Load the next segment
        next_segment = StorySegment.load(self.story.id, choice.to_segment_id)
        if not next_segment:
            raise ValueError(f"Next segment {choice.to_segment_id} not found")
            
        # Move to the next segment
        self.current_segment = next_segment
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
