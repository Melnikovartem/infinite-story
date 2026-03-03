from .story_block import StoryBlock
from typing import Dict, Any
from pydantic import Field

class StoryLocation(StoryBlock):
    """A location in a story.
    
    This represents a location with its name and descriptions.
    
    The description field evolves over episodes as episodes are flushed.
    current_state tracks the latest state during an episode.
    """
    name: str
    description: str  # Short description (1-2 sentences), evolves at episode-end
    full_description: str = ""  # Full detailed description, evolves at episode-end
    
    # ========================================================================
    # NEW: Current Episode State
    # ========================================================================
    # Tracks location state during current episode, reset at episode start
    current_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current state during episode: {stability, accessibility, corruption, ownership, inhabitants, etc.}"
    )

    def __init__(self, **data):
        """Initialize a StoryLocation instance.
        
        Args:
            story: Optional Story instance to add this location to
            **data: Location data fields
        """
        super().__init__(**data)
        self.story.add_location(self)

    def get_short_overview(self) -> str:
        """Get a short descriptor of this location.
        
        Returns:
            A string describing the location's key features
        """
        return f"{self.name}: {self.description}"

    def get_full_overview(self) -> str:
        """Get detailed information about this location.
        
        Returns:
            A string containing comprehensive location information
        """
        # Get all segments where this location appears
        location_segments = []
        for segment in self.story.get_all_segments():
            for loc_status in segment.locations:
                if loc_status.location_id == self.id:
                    location_segments.append(f"- {segment.short_description} ({loc_status.current_status})")

        # Format the full location information
        info = f"""Location: {self.name}
Description: {self.description}

Appearances:
{chr(10).join(location_segments) if location_segments else "No appearances yet"}"""

        return info
