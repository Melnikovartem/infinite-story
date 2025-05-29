from pydantic import BaseModel
from .story_base import StoryBase

class StoryCharacter(StoryBase):
    """A character in a story.
    
    This represents a character with their name, description, and background.
    """
    name: str
    description: str
    background: str
