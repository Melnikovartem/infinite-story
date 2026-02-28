"""Session state management for story progress tracking."""

from datetime import datetime, UTC
from typing import List, Optional, Any
import json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class SessionState(BaseModel):
    """Represents a player's current game session.
    
    This model tracks the player's progress through a story including:
    - Current location in the story
    - Visited segments
    - Scene counter for progress display
    - Time tracking (start and last update)
    """
    
    story_id: str = Field(..., description="ID of the story being played")
    current_segment_id: str = Field(..., description="ID of the current segment")
    visited_segments: List[str] = Field(
        default_factory=list,
        description="List of segment IDs visited in order"
    )
    scene_counter: int = Field(
        default=1,
        ge=0,
        description="Current scene number (0-indexed or 1-indexed based on visited_segments length)"
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the session started"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the session was last updated"
    )
    
    def __init__(self, **data: Any):
        """Initialize a SessionState instance.
        
        Validates that current_segment_id is in visited_segments or is the first segment.
        """
        super().__init__(**data)
        # Ensure current segment is tracked
        if self.current_segment_id not in self.visited_segments:
            if not self.visited_segments:
                self.visited_segments.append(self.current_segment_id)
            else:
                self.visited_segments.append(self.current_segment_id)
    
    @field_validator('visited_segments')
    @classmethod
    def validate_visited_segments(cls, v: List[str]) -> List[str]:
        """Validate that visited_segments is a non-empty list of unique segment IDs."""
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
    
    def add_segment(self, segment_id: str) -> None:
        """Add a visited segment to the session.
        
        Args:
            segment_id: ID of the segment to add
        """
        if segment_id not in self.visited_segments:
            self.visited_segments.append(segment_id)
        self.current_segment_id = segment_id
        self.scene_counter = len(self.visited_segments)
        self.last_updated = datetime.now(UTC)
    
    def get_elapsed_seconds(self) -> int:
        """Calculate elapsed time in seconds.
        
        Returns:
            Number of seconds since session started
        """
        elapsed = datetime.now(UTC) - self.start_time
        return int(elapsed.total_seconds())
    
    def get_elapsed_formatted(self) -> str:
        """Format elapsed time as human-readable string.
        
        Returns:
            Formatted time string (e.g., "2h 15m 30s")
        """
        seconds = self.get_elapsed_seconds()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    
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
