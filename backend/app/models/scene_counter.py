"""Scene counter and progress tracking models."""

from datetime import datetime, UTC
from typing import Optional, Any
from pydantic import BaseModel, Field


class SceneCounter(BaseModel):
    """Tracks player progress through story scenes.
    
    Provides metrics about the player's position and time spent in the story.
    """
    
    scene_number: int = Field(
        ge=1,
        description="Current scene number (1-indexed)"
    )
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the session started"
    )
    elapsed_seconds: int = Field(
        default=0,
        ge=0,
        description="Elapsed time in seconds since session start"
    )
    total_visited: int = Field(
        default=1,
        ge=1,
        description="Total number of unique scenes visited"
    )
    
    def update_elapsed(self) -> int:
        """Recalculate elapsed time from start_time to now.
        
        Returns:
            Updated elapsed_seconds value
        """
        now = datetime.now(UTC)
        elapsed = now - self.start_time
        self.elapsed_seconds = int(elapsed.total_seconds())
        return self.elapsed_seconds
    
    def get_elapsed_formatted(self) -> str:
        """Format elapsed time as human-readable string.
        
        Returns:
            Formatted time string (e.g., "2h 15m 30s")
        """
        self.update_elapsed()
        seconds = self.elapsed_seconds
        
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
    
    def get_reading_pace(self) -> float:
        """Calculate reading pace (minutes per scene).
        
        Returns:
            Minutes per scene
        """
        self.update_elapsed()
        if self.total_visited == 0:
            return 0.0
        
        total_minutes = self.elapsed_seconds / 60
        return total_minutes / self.total_visited
    
    def estimate_remaining_time(self, estimated_total_scenes: Optional[int] = None) -> Optional[int]:
        """Estimate remaining time if total scenes is known.
        
        Args:
            estimated_total_scenes: Expected total number of scenes (if known)
            
        Returns:
            Estimated remaining seconds, or None if cannot estimate
        """
        if estimated_total_scenes is None or estimated_total_scenes <= self.total_visited:
            return None
        
        pace = self.get_reading_pace()
        remaining_scenes = estimated_total_scenes - self.total_visited
        return int(remaining_scenes * pace * 60)  # Convert to seconds
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SceneCounter':
        """Create from dictionary.
        
        Args:
            data: Dictionary containing scene counter data
            
        Returns:
            SceneCounter instance
        """
        return cls(**data)
