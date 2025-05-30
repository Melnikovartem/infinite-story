from .story_block import StoryBlock

class StoryLocation(StoryBlock):
    """A location in a story.
    
    This represents a location with its name and description.
    """
    name: str
    description: str

    def __init__(self, **data):
        """Initialize a StoryLocation instance.
        
        Args:
            story: Optional Story instance to add this location to
            **data: Location data fields
        """
        super().__init__(**data)
        self.story.add_location(self)
