from typing import List, Union, Dict, Optional, TYPE_CHECKING
from pydantic import BaseModel
from .story_base import StoryBase

if TYPE_CHECKING:
    from .story import Story

class StoryContext(StoryBase):
    """Context for a story.
    
    This represents the fundamental truths and worldbuilding elements
    that provide context for the story.
    """
    fundamental_truths: List[str]
    worldbuilding: Union[str, Dict]

    def __init__(self, story: Optional['Story'] = None, **data):
        """Initialize a StoryContext instance.
        
        Args:
            story: Optional Story instance to add this context to
            **data: Context data fields
        """
        super().__init__(**data)
        if story is not None:
            story.add_context(self)
