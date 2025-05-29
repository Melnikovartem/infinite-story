from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from .story_base import StoryBase

if TYPE_CHECKING:
    from .story import Story

class StoryLocation(StoryBase):
    """A location in a story.
    
    This represents a location with its name and description.
    """
    story_id: str = Field(alias="story_id")
    name: str
    description: str

    def __init__(self, story: Optional['Story'] = None, **data):
        """Initialize a StoryLocation instance.
        
        Args:
            story: Optional Story instance to add this location to
            **data: Location data fields
        """
        super().__init__(**data)
        if story is not None:
            story.add_location(self)
