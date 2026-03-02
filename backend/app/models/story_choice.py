from typing import Optional
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
    from_segment_id: Optional[str] = None
    to_segment_id: Optional[str] = None
    text: str
    clicks_logged: int = 0
    clicks_anonymous: int = 0
    flags: ChoiceFlags = Field(default_factory=ChoiceFlags)
    locked: bool = Field(
        False,
        description="Whether this choice is locked during generation to prevent race conditions"
    )

    def __init__(self, **data):
        """Initialize a StoryChoice instance.
        
        Args:
            story: Optional Story instance to add this choice to
            **data: Choice data fields
        """
        super().__init__(**data)
        self.story.add_choice(self)
    
    def lock(self) -> None:
        """Lock this choice to prevent concurrent generation."""
        self.locked = True
        self.save()
    
    def unlock(self) -> None:
        """Unlock this choice after generation attempt."""
        self.locked = False
        self.save()
