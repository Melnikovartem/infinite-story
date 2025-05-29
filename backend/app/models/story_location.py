from datetime import datetime
from pydantic import BaseModel, Field

class Location(BaseModel):
    id: str
    story_id: str
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
