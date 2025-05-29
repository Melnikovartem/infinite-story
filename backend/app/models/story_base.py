import json
import os
from datetime import datetime, UTC
from typing import Dict, Any, Optional, TypeVar, Generic, Type
from pydantic import BaseModel, Field
from pathlib import Path

T = TypeVar('T', bound='StoryBase')

class StoryBase(BaseModel):
    """Base class for all story-related models with save functionality.
    
    This class provides common functionality for saving and loading story objects
    to/from JSON files in a structured directory.
    
    Storage structure:
    /data/<story_id>/<object_type>/<object_id>.json
    """
    
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    @property
    def story_id(self) -> str:
        """Get the story ID for this object.
        
        This should be overridden by classes that don't have a direct story_id field.
        """
        if hasattr(self, 'story_id'):
            return self.story_id
        raise NotImplementedError(f"{self.__class__.__name__} must implement story_id property")
    
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
        """Save the object to a JSON file.
        
        The file will be saved in a directory structure based on the story ID and object type:
        /data/<story_id>/<object_type>/<object_id>.json
        
        Raises:
            IOError: If the file cannot be written
        """
        # Update the updated_at timestamp
        self.updated_at = datetime.now(UTC)
        
        # Ensure all necessary directories exist
        storage_dir = self.get_storage_dir(self.story_id)
        
        # Get the file path
        file_path = self.get_file_path(self.story_id, self.id)
        
        # Convert to dict and save as JSON
        data = self.model_dump()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    @classmethod
    def load(cls: Type[T], story_id: str, object_id: str) -> Optional[T]:
        """Load an object from a JSON file.
        
        Args:
            story_id: The ID of the story this object belongs to
            object_id: The ID of the object to load
            
        Returns:
            The loaded object, or None if the file doesn't exist
            
        Raises:
            ValueError: If the file exists but contains invalid data
        """
        file_path = cls.get_file_path(story_id, object_id)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.model_validate(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading {cls.__name__} from {file_path}: {e}")
    
    @classmethod
    def list_all(cls, story_id: str) -> list[str]:
        """List all object IDs of this type for a specific story.
        
        Args:
            story_id: The ID of the story to list objects for
            
        Returns:
            List of object IDs
        """
        storage_dir = cls.get_storage_dir(story_id)
        if not storage_dir.exists():
            return []
        
        return [
            f.stem for f in storage_dir.glob("*.json")
        ]
    
    def delete(self) -> None:
        """Delete the object's JSON file.
        
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = self.get_file_path(self.story_id, self.id)
        if file_path.exists():
            file_path.unlink() 