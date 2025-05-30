from typing import Any, ForwardRef
from .story_block import StoryBlock


StoryRef = ForwardRef('Story')

class StoryCharacter(StoryBlock):
    """A character in a story.
    
    This represents a character with their name, description, and background.
    """
    name: str
    description: str
    background: str

    def __init__(self, **data: Any):
        """Initialize a StoryCharacter instance.
        
        Args:
            **data: Character data fields
        """
        super().__init__(**data)
        self.story.add_character(self)

# Update forward references
StoryCharacter.model_rebuild()
