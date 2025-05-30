from pydantic import BaseModel, Field
from .story_block import StoryBlock
    
class ChoiceFlags(BaseModel):
    """Flags for content warnings and restrictions."""
    nsfw: bool = False
    violent: bool = False

class StoryChoice(StoryBlock):
    """A choice in a story.
    
    This represents a choice that the player can make, with text and references
    to the segments it connects.
    """
    from_segment_id: str
    to_segment_id: str
    text: str
    clicks_logged: int = 0
    clicks_anonymous: int = 0
    flags: ChoiceFlags = Field(default_factory=ChoiceFlags)

    def __init__(self, **data):
        """Initialize a StoryChoice instance.
        
        Args:
            story: Optional Story instance to add this choice to
            **data: Choice data fields
        """
        super().__init__(**data)
        self.story.add_choice(self)
