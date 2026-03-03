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
    
    # ========================================================================
    # A. THEMES SYSTEM (NEW)
    # ========================================================================
    themes: List[str] = Field(
        default_factory=list,
        description="List of themes in this arc (e.g., ['betrayal', 'redemption', 'power'])"
    )
    theme_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Weights for theme selection (set from defaults, can be customized)"
    )
    
    # ========================================================================
    # B. CHARACTER DEVELOPMENT (NEW)
    # ========================================================================
    character_arc_goals: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> goal (e.g., 'char_1': 'learn to trust')"
    )
    key_characters: List[str] = Field(
        default_factory=list,
        description="Character IDs important to this arc"
    )
    
    # ========================================================================
    # C. NARRATIVE STRUCTURE (NEW)
    # ========================================================================
    unresolved_mysteries: List[str] = Field(
        default_factory=list,
        description="Questions/mysteries to resolve in this arc"
    )
    plot_hooks: List[str] = Field(
        default_factory=list,
        description="Key plot points/hooks to explore"
    )
    central_conflict: str = Field(
        default="",
        description="Main conflict driving this arc"
    )
    
    # ========================================================================
    # D. GENERATION GUIDANCE (NEW)
    # ========================================================================
    arc_tone: str = Field(
        default="neutral",
        description="Overall arc tone (different from episode tone)"
    )
    arc_mood: str = Field(
        default="",
        description="Dominant emotional mood"
    )
    generation_guidelines: str = Field(
        default="",
        description="Special AI generation instructions for this arc"
    )
    
    # ========================================================================
    # E. WORLD OBJECTS - ACTIVE TRACKING (NEW)
    # ========================================================================
    # These are selected/active objects for THIS arc to keep context focused
    active_locations: List[str] = Field(
        default_factory=list,
        description="Location IDs that are active/important in this arc"
    )
    active_characters: List[str] = Field(
        default_factory=list,
        description="Character IDs that might appear in this arc"
    )
    active_factions: List[str] = Field(
        default_factory=list,
        description="Faction/group IDs relevant to this arc"
    )
    
    # ========================================================================
    # F. EPISODE RUNNING STATE - CHARACTER & LOCATION EVOLUTION
    # ========================================================================
    # Episode-level character descriptions (updated at episode end)
    episode_character_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> description for this arc (updated each episode)"
    )
    # Episode-level location descriptions (updated at episode end)
    episode_location_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="location_id -> description for this arc (updated each episode)"
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
