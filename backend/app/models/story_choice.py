from pydantic import BaseModel, Field
from .story_base import StoryBase

class ChoiceFlags(BaseModel):
    """Flags for content warnings and restrictions."""
    nsfw: bool = False
    violent: bool = False

class Choice(StoryBase):
    """A choice in a story.
    
    This represents a choice that leads from one story segment to another.
    """
    story_id: str
    from_segment_id: str
    to_segment_id: str
    text: str
    clicks_logged: int = 0
    clicks_anonymous: int = 0
    flags: ChoiceFlags = Field(default_factory=ChoiceFlags)
