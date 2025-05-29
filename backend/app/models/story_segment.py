from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .types import TextBlock

class CharacterStatus(BaseModel):
    character_id: str
    ai_status: str

class LocationStatus(BaseModel):
    location_id: str
    ai_status: str

class StorySegment(BaseModel):
    id: str
    story_id: str
    from_choice_id: Optional[str]
    text_blocks: List[TextBlock]
    characters: List[CharacterStatus]
    locations: List[LocationStatus]
    created_at: datetime = Field(default_factory=datetime.utcnow)
