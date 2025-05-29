from typing import Optional
from pydantic import Field
from .story_base import StoryBase

class Story(StoryBase):
    """A story in the system.
    
    This represents a complete story with metadata and references to its segments.
    """
    title: str
    description: str
    genre: Optional[str] = None
    user_id: Optional[str] = None
    start_segment_id: Optional[str] = None  # Reference to the first segment of the story
    
    @property
    def story_id(self) -> str:
        """Get the story ID.
        
        For the Story class, the story_id is the same as the object's id.
        """
        return self.id
