from typing import Any, Optional
from pydantic import Field, model_validator
from .story_base import StoryBase
from .story import Story


class StoryBlock(StoryBase):
    """Base class for all story blocks that require a story object.
    
    This class extends StoryBase to provide story object functionality
    and overloads the load method to require a story object.
    """
    story: Story = Field(default=None, exclude=True)

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

    def get_short_overview(self) -> str:
        """Get a short descriptor of this story block.
        
        This should be overridden by subclasses to provide a brief description
        of the block's content and purpose.
        
        Returns:
            A string describing the block
        """
        raise NotImplementedError("Subclasses must implement get_short_overview")

    def get_full_overview(self) -> str:
        """Get detailed information about this story block.
        
        This should be overridden by subclasses to provide comprehensive
        information about the block's content, relationships, and state.
        
        Returns:
            A string containing detailed information about the block
        """
        raise NotImplementedError("Subclasses must implement get_full_overview")

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