"""Story Arc model for managing narrative arcs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.story_base import StoryBase
from datetime import datetime, UTC


class ArcCompressionResult(BaseModel):
    """Result of arc compression after 15 episodes."""
    arc_id: str
    compressed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    mainline_branch_segments: List[str] = Field(
        default_factory=list,
        description="Canonical path segments after compression"
    )
    archived_segments: List[str] = Field(
        default_factory=list,
        description="Segments replaced by compression"
    )
    
    selection_rationale: str = Field(
        "",
        description="Why this branch was chosen"
    )
    compression_model: str = Field(
        "gpt-4o-mini",
        description="Which model performed the compression"
    )


class StoryArc(StoryBase):
    """A collection of connected episodes forming a narrative arc."""
    
    title: str = Field(..., description="Title of the arc")
    description: str = Field(
        "",
        description="Detailed description of the arc"
    )
    
    episode_ids: List[str] = Field(
        default_factory=list,
        description="List of episode IDs in this arc"
    )
    episode_count: int = Field(
        0,
        ge=0,
        description="Number of episodes in this arc"
    )
    
    start_segment_id: str = Field(
        ...,
        description="First segment of this arc"
    )
    current_segment_id: Optional[str] = Field(
        None,
        description="Latest segment in this arc"
    )
    
    # Thematic guidance
    premise: str = Field(
        "",
        description="Core idea of the arc (e.g., 'Power corrupts the innocent')"
    )
    narrative_direction: str = Field(
        "",
        description="Guideline for where arc is heading"
    )
    
    # Compression status
    is_compressed: bool = Field(
        False,
        description="Whether this arc has been compressed"
    )
    compression_result: Optional[ArcCompressionResult] = Field(
        None,
        description="Result of arc compression if compressed"
    )
    
    def get_short_overview(self) -> str:
        """Get a brief overview of the arc."""
        return f"{self.title} ({self.episode_count} episodes)"
    
    def get_full_overview(self) -> str:
        """Get a detailed overview of the arc."""
        return f"""
Arc: {self.title}

Premise: {self.premise}
Direction: {self.narrative_direction}

Episodes: {self.episode_count}
Compressed: {self.is_compressed}

Description:
{self.description}
"""
