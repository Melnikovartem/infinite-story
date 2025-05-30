from typing import List, Union, Dict
from .story_block import StoryBlock

class StoryContext(StoryBlock):
    """Context for a story.
    
    This represents the fundamental truths and worldbuilding elements
    that provide context for the story.
    """
    fundamental_truths: List[str]
    worldbuilding: Union[str, Dict]

    def __init__(self, **data):
        """Initialize a StoryContext instance.
        
        Args:
            story: Optional Story instance to add this context to
            **data: Context data fields
        """
        super().__init__(**data)
        self.story.add_context(self)
