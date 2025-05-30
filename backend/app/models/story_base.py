import json
import os
from datetime import datetime, UTC
from typing import Dict, Any, Optional, TypeVar, Generic, Type, Union, TYPE_CHECKING
from pydantic import BaseModel, Field, model_validator, PrivateAttr
from pathlib import Path

T = TypeVar('T', bound='StoryBase')

LOCAL_DATA_DIR = Path(".infinite_story_data")

class StoryBase(BaseModel):
    """Base class for all story components.
    
    This class provides common functionality for all story components,
    including saving, loading, and listing.
    """
    id: str
    story_id: str  # Required field for all story components
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __init__(self, **data: Any):
        """Initialize a StoryBase instance.
        
        Args:
            **data: Component data fields
        """
        if 'story' in data and data['story'] is not None:
            data['story_id'] = data['story'].id
        super().__init__(**data)
    
    def get_story_id(self) -> str:
        """Get the story ID for this object.
        
        This should be overridden by classes that don't have a direct story_id field.
        """
        # Check if the class has a story_id field in its model fields
        if 'story_id' in self.__class__.model_fields:
            return getattr(self, 'story_id')
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_story_id method")
    
    @classmethod
    def ensure_directory_exists(cls, path: Path) -> None:
        """Ensure that a directory exists, creating it if necessary.
        
        Args:
            path: The directory path to ensure exists
        """
        path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_base_dir(cls) -> Path:
        """Get the base data directory.
        
        Returns:
            Path object pointing to the base data directory
        """
        base_dir = Path('data')
        cls.ensure_directory_exists(base_dir)
        return base_dir
    
    @classmethod
    def get_story_dir(cls, story_id: str) -> Path:
        """Get the directory for a specific story.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            Path object pointing to the story directory
        """
        story_dir = cls.get_base_dir() / story_id
        cls.ensure_directory_exists(story_dir)
        return story_dir
    
    @classmethod
    def get_storage_dir(cls, story_id: str) -> Path:
        """Get the storage directory for this type of story object.
        
        Args:
            story_id: The ID of the story this object belongs to
            
        Returns:
            Path object pointing to the storage directory
        """
        # Get the class name without 'Story' prefix and convert to snake_case
        class_name = cls.__name__.replace('Story', '').lower()
        storage_dir = cls.get_story_dir(story_id) / class_name
        cls.ensure_directory_exists(storage_dir)
        return storage_dir
    
    @classmethod
    def get_file_path(cls, story_id: str, object_id: str) -> Path:
        """Get the file path for a specific object.
        
        Args:
            story_id: The ID of the story this object belongs to
            object_id: The ID of the object
            
        Returns:
            Path object pointing to the JSON file
        """
        return cls.get_storage_dir(story_id) / f"{object_id}.json"
    
    def save(self) -> None:
        """Save the component to disk."""
        # Get the data directory for this story
        data_dir = LOCAL_DATA_DIR / self.story_id
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the component type directory
        component_type = self.__class__.__name__.lower()
        component_dir = data_dir / component_type
        component_dir.mkdir(exist_ok=True)
        
        # Save the component
        file_path = component_dir / f"{self.id}.json"
        with open(file_path, "w") as f:
            json.dump(self.model_dump(), f, default=str)
            
    @classmethod
    def load(cls, story_id: str, component_id: str, **other_data: Any) -> Optional['StoryBase']:
        """Load a component from disk.
        
        Args:
            story_id: The ID of the story
            component_id: The ID of the component to load
            
        Returns:
            The loaded component, or None if it doesn't exist
        """
        # Get the component type directory
        component_type = cls.__name__.lower()
        file_path = LOCAL_DATA_DIR / story_id / component_type / f"{component_id}.json"
        
        if not file_path.exists():
            return None
            
        # Load the component
        with open(file_path, "r") as f:
            data = json.load(f)
            
        # Create the component
        component = cls(**data, **other_data)
        component.story_id = story_id
        return component
        
    @classmethod
    def list_all(cls, story_id: str) -> list[str]:
        """List all components of this type for a story.
        
        Args:
            story_id: The ID of the story
            
        Returns:
            A list of component IDs
        """
        # Get the component type directory
        component_type = cls.__name__.lower()
        component_dir = LOCAL_DATA_DIR / story_id / component_type
        
        if not component_dir.exists():
            return []
            
        # List all components
        return [f.stem for f in component_dir.glob("*.json")]
    
    @classmethod
    def list_stories(cls) -> list[str]:
        """List all stories in the data directory.
        
        Returns:
            A list of story IDs
        """
        if not LOCAL_DATA_DIR.exists():
            return []
            
        return [f.name for f in LOCAL_DATA_DIR.iterdir() if f.is_dir()]
        
    def delete(self) -> None:
        """Delete the component from disk."""
        # Get the component type directory
        component_type = self.__class__.__name__.lower()
        file_path = LOCAL_DATA_DIR / self.story_id / component_type / f"{self.id}.json"
        
        if file_path.exists():
            file_path.unlink()