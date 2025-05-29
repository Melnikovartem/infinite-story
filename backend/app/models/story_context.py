from typing import List, Dict, Union
from pydantic import BaseModel
from .story_base import StoryBase

class StoryContext(StoryBase):
    """Context for a story.
    
    This represents the fundamental truths and worldbuilding elements
    that provide context for the story.
    """
    story_id: str
    fundamental_truths: List[str]
    worldbuilding: Union[str, Dict]
