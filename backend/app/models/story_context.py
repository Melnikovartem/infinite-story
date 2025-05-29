from datetime import datetime
from typing import List, Dict, Union
from pydantic import BaseModel, Field

class StoryContext(BaseModel):
    id: str
    story_id: str
    fundamental_truths: List[str]
    worldbuilding: Union[str, Dict]
    created_at: datetime = Field(default_factory=datetime.utcnow)
