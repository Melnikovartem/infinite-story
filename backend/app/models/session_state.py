"""Session state management for story progress tracking (v2: minimal)."""

from datetime import datetime, UTC
from typing import List, Optional, Any
import json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from app.models.story_base import StoryBase


class SessionState(StoryBase):
    """Represents a player's minimal game session state.
    
    v2 simplification: tracks only the journey path. All other state
    (character states, episode info, protagonist data) lives on segments
    and episode recaps.
    
    This model tracks:
    - Current position in the story graph
    - Visited segments (the path taken)
    - Visited choices (decisions made)
    """
    
    story_id: str = Field(..., description="ID of the story being played")
    user_id: str = Field(..., description="ID of the user playing")
    current_segment_id: str = Field(..., description="ID of the current segment")
    
    # Journey so far (minimal tracking)
    visited_segments: List[str] = Field(
        default_factory=list,
        description="List of segment IDs visited in order"
    )
    visited_choices: List[str] = Field(
        default_factory=list,
        description="List of choice IDs made in order"
    )
    
    def __init__(self, **data: Any):
        """Initialize a SessionState instance."""
        super().__init__(**data)
        # Ensure current segment is tracked
        if self.current_segment_id not in self.visited_segments:
            self.visited_segments.append(self.current_segment_id)
    
    @field_validator('visited_segments')
    @classmethod
    def validate_visited_segments(cls, v: List[str]) -> List[str]:
        """Validate that visited_segments is a list of unique segment IDs."""
        if not isinstance(v, list):
            raise ValueError("visited_segments must be a list")
        
        # Ensure uniqueness while preserving order
        seen = set()
        unique_segments = []
        for segment_id in v:
            if segment_id not in seen:
                unique_segments.append(segment_id)
                seen.add(segment_id)
        
        return unique_segments
    
    def add_visited(self, segment_id: str, choice_id: Optional[str] = None) -> None:
        """Add a visited segment and optional choice.
        
        Args:
            segment_id: ID of the segment visited
            choice_id: Optional ID of the choice that led here
        """
        if segment_id not in self.visited_segments:
            self.visited_segments.append(segment_id)
        if choice_id and choice_id not in self.visited_choices:
            self.visited_choices.append(choice_id)
    
    def move_to(self, segment_id: str) -> None:
        """Move to a new segment, tracking the visit.
        
        Args:
            segment_id: ID of the segment to move to
        """
        self.current_segment_id = segment_id
        self.add_visited(segment_id)
        self.updated_at = datetime.now(UTC)
    
    def to_dict(self) -> dict:
        """Convert session state to dictionary for serialization.
        
        Returns:
            Dictionary representation of the session
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create SessionState from dictionary.
        
        Args:
            data: Dictionary containing session data
            
        Returns:
            SessionState instance
        """
        return cls(**data)
    
    @classmethod
    def save_to_file(cls, story_id: str, session: 'SessionState') -> Path:
        """Save session to disk as JSON file.
        
        Args:
            story_id: ID of the story
            session: SessionState instance to save
            
        Returns:
            Path where the session was saved
        """
        # Create directory structure: .infinite_story_data/{story_id}/
        data_dir = Path(".infinite_story_data") / story_id
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as runner_state.json
        file_path = data_dir / "runner_state.json"
        with open(file_path, "w") as f:
            json.dump(session.to_dict(), f, indent=2, default=str)
        
        return file_path
    
    @classmethod
    def load_from_file(cls, story_id: str) -> Optional['SessionState']:
        """Load session from disk JSON file.
        
        Args:
            story_id: ID of the story
            
        Returns:
            SessionState instance if found, None otherwise
        """
        file_path = Path(".infinite_story_data") / story_id / "runner_state.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None for corrupted sessions
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load session from {file_path}: {e}")
            return None
    
    @classmethod
    def delete_from_file(cls, story_id: str) -> bool:
        """Delete saved session from disk.
        
        Args:
            story_id: ID of the story
            
        Returns:
            True if session was deleted, False if it didn't exist
        """
        file_path = Path(".infinite_story_data") / story_id / "runner_state.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    @classmethod
    def exists(cls, story_id: str) -> bool:
        """Check if a saved session exists for a story.
        
        Args:
            story_id: ID of the story
            
        Returns:
            True if session file exists, False otherwise
        """
        file_path = Path(".infinite_story_data") / story_id / "runner_state.json"
        return file_path.exists()
