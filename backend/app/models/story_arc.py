"""Story arc models for representing narrative arcs and compression results."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from app.models.story_base import StoryBase


class ArcCompressionResult(BaseModel):
    """Result of arc compression after 15 episodes.
    
    When an arc reaches completion (typically after 15 episodes),
    the system compresses branching paths by selecting the mainline
    branch and archiving alternatives.
    """
    arc_id: str
    compressed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    mainline_branch_segments: List[str]  # Canonical path
    archived_segments: List[str]  # Replaced segments
    
    selection_rationale: str  # Why this branch was chosen
    compression_model: str = "gpt-4o-mini"


class StoryArc(StoryBase):
    """A collection of connected episodes forming a narrative arc.
    
    An arc represents a larger narrative structure consisting of multiple
    episodes with a unified premise and direction. Arcs are compressed
    after reaching episode limits to manage story growth.
    """
    story_id: str
    
    title: str  # e.g., "The Rise of the Northern Kingdom"
    description: str
    
    episode_ids: List[str] = Field(default_factory=list)
    episode_count: int = 0
    
    start_segment_id: str  # First segment of this arc
    current_segment_id: Optional[str] = None  # Latest segment
    
    # Thematic guidance
    premise: str  # Core idea (e.g., "Power corrupts the innocent")
    narrative_direction: str  # Guideline for where arc is heading
    
    # Compression status
    is_compressed: bool = False
    compression_result: Optional[ArcCompressionResult] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    def get_short_overview(self) -> str:
        """Get a short overview of the arc."""
        return f"{self.title} ({self.episode_count} episodes)"
    
    def get_full_overview(self) -> str:
        """Get a detailed overview for AI prompts."""
        return f"""
Arc: {self.title}

Premise: {self.premise}
Direction: {self.narrative_direction}

Episodes: {self.episode_count}
Compressed: {self.is_compressed}

Description:
{self.description}
"""
    
    def mark_compressed(self, compression_result: ArcCompressionResult) -> None:
        """Mark this arc as compressed with the result."""
        self.is_compressed = True
        self.compression_result = compression_result
    
    def add_episode(self, episode_id: str) -> None:
        """Add an episode to this arc."""
        if episode_id not in self.episode_ids:
            self.episode_ids.append(episode_id)
            self.episode_count = len(self.episode_ids)
