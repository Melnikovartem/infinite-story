"""Story Arc model for managing narrative arcs."""

import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Clean raw JSON fragments from corrupted titles."""
        if not v:
            return v
        # Strip leading JSON noise like ': "', '": "', etc.
        cleaned = re.sub(r'^[\s":,{}\[\]]+', '', v).strip()
        # If still contains JSON structural chars, extract the first quoted string
        if any(c in cleaned for c in ['{', '":', '\\n']):
            match = re.search(r'["\']?([A-Z][^"\'\\{},]+)', cleaned)
            if match:
                cleaned = match.group(1).strip()
        # Truncate if unreasonably long
        if len(cleaned) > 150:
            cleaned = cleaned[:150].rsplit(' ', 1)[0]
        return cleaned or v
    
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
    min_episodes: int = Field(
        8,
        ge=1,
        description="Minimum episodes before arc can complete (even if goal is reached)"
    )
    max_episodes: int = Field(
        25,
        ge=1,
        description="Maximum episodes for arc (arc must complete by this point)"
    )
    conflict_resolution_progress: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="How resolved is the central conflict (0.0=unresolved, 1.0=resolved)"
    )
    mysteries_resolved: List[str] = Field(
        default_factory=list,
        description="Which mysteries from unresolved_mysteries have been resolved"
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
    active_characters: List[str] = Field(
        default_factory=list,
        description="Character IDs most likely active in this arc (selected by LLM during generation)"
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
    # NOTE: active_characters is already defined above in section B (Character Development)
    # It stores character IDs selected by LLM during generation
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
    
    # ========================================================================
    # G. ARC FINALIZATION & TRANSITION (E2-5 NEW)
    # ========================================================================
    is_finalized: bool = Field(
        False,
        description="Whether this arc has been finalized after 15 episodes"
    )
    mainline_segment_count: int = Field(
        0,
        ge=0,
        description="Number of segments in the canonical mainline path"
    )
    
    # Future arc support
    is_future_arc: bool = Field(
        False,
        description="Whether this arc is a pre-generated future arc (not yet active)"
    )
    is_active: bool = Field(
        False,
        description="Whether this arc is currently the active arc for segment generation"
    )
    
    # Context from previous arc
    previous_arc_id: Optional[str] = Field(
        None,
        description="ID of the arc that preceded this one"
    )
    previous_arc_summary: str = Field(
        "",
        description="Summary of the previous arc's mainline narrative for continuity"
    )
    
    # ========================================================================
    # H. ARC RECAP (populated when arc completes)
    # ========================================================================
    recap: Optional[str] = Field(
        None,
        description="Short 1-2 sentence recap of the arc"
    )
    recap_title: str = Field(
        default="",
        description="Auto-generated arc title for recap (e.g., 'The Betrayal at Court')"
    )
    recap_summary: str = Field(
        default="",
        description="3-5 paragraph narrative summary of the entire arc"
    )
    character_arc_resolutions: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> how their arc was resolved"
    )
    mysteries_resolved: Dict[str, str] = Field(
        default_factory=dict,
        description="mystery -> how it was resolved"
    )
    unresolved_for_next: List[str] = Field(
        default_factory=list,
        description="Mysteries that remain unresolved for next arc"
    )
    outcome: str = Field(
        default="",
        description="Overall outcome of the arc (victory, defeat, transformation, etc.)"
    )
    hook_for_next_arc: str = Field(
        default="",
        description="Hook or setup that leads into the next arc"
    )
    new_status_quo: str = Field(
        default="",
        description="The new status quo established by end of arc"
    )
    
    def to_context_short(self) -> str:
        """Short context: title + recap if available."""
        base = f"{self.title} ({self.episode_count} episodes)"
        if self.recap:
            base += f" | {self.recap}"
        return base
    
    def to_context_full(self) -> str:
        """Full context: complete arc information."""
        return f"""
Arc: {self.title}

Premise: {self.premise}
Direction: {self.narrative_direction}

Episodes: {self.episode_count}
Compressed: {self.is_compressed}

Description:
{self.description}
"""
