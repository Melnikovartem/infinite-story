"""Session state management for story progress tracking."""

from datetime import datetime, UTC
from typing import List, Optional, Any
import json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from app.models.story_base import StoryBase


class SessionState(StoryBase):
    """Represents a player's current game session - minimal state tracking.
    
    This model tracks the player's progress through a story including:
    - Current location in the story
    - Visited segments and choices
    
    v2 Note: Simplified to only track the journey path. Character state tracking
    is now handled by EpisodeRecap. Episode context is in StorySegment.
    """
    
    user_id: str = Field(..., description="ID of the user playing the story")
    current_segment_id: str = Field(..., description="ID of the current segment")
    
    visited_segments: List[str] = Field(
        default_factory=list,
        description="List of segment IDs visited in order"
    )
    visited_choices: List[str] = Field(
        default_factory=list,
        description="List of choice IDs made in order"
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
    
    @field_validator('visited_choices')
    @classmethod
    def validate_visited_choices(cls, v: List[str]) -> List[str]:
        """Validate that visited_choices is a list of unique choice IDs."""
        if not isinstance(v, list):
            raise ValueError("visited_choices must be a list")
        
        # Ensure uniqueness while preserving order
        seen = set()
        unique_choices = []
        for choice_id in v:
            if choice_id not in seen:
                unique_choices.append(choice_id)
                seen.add(choice_id)
        
        return unique_choices
    
    def add_visited(self, segment_id: str, choice_id: Optional[str] = None) -> None:
        """Add a visited segment and optionally a choice to the session.
        
        Args:
            segment_id: ID of the segment to add
            choice_id: Optional ID of the choice that led to this segment
        """
        if segment_id not in self.visited_segments:
            self.visited_segments.append(segment_id)
        if choice_id and choice_id not in self.visited_choices:
            self.visited_choices.append(choice_id)
        self.updated_at = datetime.now(UTC)
    
    def move_to(self, segment_id: str, choice_id: Optional[str] = None) -> None:
        """Move to a new segment and mark it as visited.
        
        Args:
            segment_id: ID of the segment to move to
            choice_id: Optional ID of the choice that led to this segment
        """
        self.current_segment_id = segment_id
        self.add_visited(segment_id, choice_id)
    
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
