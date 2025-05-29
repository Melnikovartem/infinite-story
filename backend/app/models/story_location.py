from pydantic import BaseModel
from .story_base import StoryBase

class StoryLocation(StoryBase):
    """A location in a story.
    
    This represents a location with its name and description.
    """
    name: str
    description: str
