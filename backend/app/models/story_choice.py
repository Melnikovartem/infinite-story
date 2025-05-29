from datetime import datetime
from pydantic import BaseModel, Field

class ChoiceFlags(BaseModel):
    nsfw: bool = False
    violent: bool = False

class Choice(BaseModel):
    id: str
    story_id: str
    from_segment_id: str
    to_segment_id: str
    text: str
    clicks_logged: int = 0
    clicks_anonymous: int = 0
    flags: ChoiceFlags = Field(default_factory=ChoiceFlags)
    created_at: datetime = Field(default_factory=datetime.utcnow)
