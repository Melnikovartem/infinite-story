from pydantic import BaseModel, Field
from .story_base import StoryBase

class StoryLocation(StoryBase):
    """A location in a story.
    
    This represents a location with its name and description.
    """
    story_id: str = Field(alias="story_id")
    name: str
    description: str
