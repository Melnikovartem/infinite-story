from pydantic import BaseModel
from .story_base import StoryBase

class Location(StoryBase):
    """A location in a story.
    
    This represents a location with its name and description.
    """
    story_id: str
    name: str
    description: str
