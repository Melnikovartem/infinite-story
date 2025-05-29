from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Story(BaseModel):
    id: str
    title: str
    description: str
    genre: Optional[str] = None
    user_id: Optional[str] = None
    start_segment_id: Optional[str] = None  # Reference to the first segment of the story
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
