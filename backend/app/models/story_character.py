from pydantic import BaseModel
from .story_base import StoryBase

class Character(StoryBase):
    """A character in a story.
    
    This represents a character with their name, description, and background.
    """
    story_id: str
    name: str
    description: str
    background: str
