from typing import TYPE_CHECKING, Any, Optional
from pydantic import Field, model_validator
from .story_base import StoryBase
from .story import Story


class StoryBlock(StoryBase):
    """Base class for all story blocks that require a story object.
    
    This class extends StoryBase to provide story object functionality
    and overloads the load method to require a story object.
    """
    story: 'Story' = Field(default=None, exclude=True)

    def __init__(self, **data: Any):
        """Initialize a StoryBlock instance.
        
        Args:
            **data: Component data fields, must include 'story'
        """
        if 'story' not in data:
            raise ValueError("Story object is required for StoryBlock")
        if 'story_id' not in data:
            data['story_id'] = data['story'].id
        super().__init__(**data)

    @model_validator(mode='after')
    def validate_story_id(self) -> 'StoryBlock':
        """Validate that the story_id matches the story.id."""
        if self.story_id != self.story.id:
            raise ValueError(f"story_id {self.story_id} does not match story.id {self.story.id}")
        return self

    def to_context_short(self) -> str:
        """Short context for LLM prompts.
        
        Returns short_description + recap if available. Should be overridden
        by subclasses to provide a brief context string.
        
        Returns:
            A short context string
        """
        raise NotImplementedError("Subclasses must implement to_context_short")

    def to_context_full(self) -> str:
        """Full context for LLM prompts.
        
        Returns description + all relevant fields. Should be overridden
        by subclasses to provide comprehensive context.
        
        Returns:
            A full context string
        """
        raise NotImplementedError("Subclasses must implement to_context_full")

    @classmethod
    def load(cls, story_id: str, component_id: str, story: 'Story', **other_data: Any) -> Optional['StoryBlock']:
        """Load a component from disk.
        
        Args:
            story_id: The ID of the story
            component_id: The ID of the component to load
            story: The story object this block belongs to
            **other_data: Additional data to pass to the constructor
            
        Returns:
            The loaded component, or None if it doesn't exist
        """
        return super().load(story_id, component_id, story=story, **other_data)