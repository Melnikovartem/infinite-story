from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from .story_base import StoryBase

if TYPE_CHECKING:
    from .story import Story

class StoryCharacter(StoryBase):
    """A character in a story.
    
    This represents a character with their name, description, and background.
    """
    story_id: str = Field(alias="story_id")
    name: str
    description: str
    background: str

    def __init__(self, story: Optional['Story'] = None, **data):
        """Initialize a StoryCharacter instance.
        
        Args:
            story: Optional Story instance to add this character to
            **data: Character data fields
        """
        super().__init__(**data)
        if story is not None:
            story.add_character(self)
