from pydantic import BaseModel, Field
from .story_base import StoryBase

class StoryCharacter(StoryBase):
    """A character in a story.
    
    This represents a character with their name, description, and background.
    """
    story_id: str = Field(alias="story_id")
    name: str
    description: str
    background: str
