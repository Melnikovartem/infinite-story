from .story_block import StoryBlock

class StoryLocation(StoryBlock):
    """A location in a story.
    
    This represents a location with its name and descriptions.
    """
    name: str
    description: str  # Short description (1-2 sentences)
    full_description: str = ""  # Full detailed description
    current_state: str = ""  # Current state/changes in this episode

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
