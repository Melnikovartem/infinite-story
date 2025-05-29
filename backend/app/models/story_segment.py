from typing import List, Optional
from pydantic import BaseModel
from .story_base import StoryBase
from .types import TextBlock

class CharacterStatus(BaseModel):
    """Status of a character in a story segment."""
    character_id: str
    ai_status: str

class LocationStatus(BaseModel):
    """Status of a location in a story segment."""
    location_id: str
    ai_status: str

class StorySegment(StoryBase):
    """A segment of a story.
    
    This represents a single segment of a story, containing text blocks,
    character statuses, and location statuses.
    """
    story_id: str
    from_choice_id: Optional[str]
    text_blocks: List[TextBlock]
    characters: List[CharacterStatus]
    locations: List[LocationStatus]
