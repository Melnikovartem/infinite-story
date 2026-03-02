"""Arc recap model for storing summaries of completed story arcs."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, UTC

from app.models.story_base import StoryBase


class ArcRecap(StoryBase):
    """Summary of a completed story arc.
    
    Created when an arc is completed and compressed. Provides quick reference for
    arc history without needing to load all episodes.
    
    Storage: One JSON file per arc
    Naming: arc_recap_{arc_id}.json
    """
    
    # Identity
    arc_id: str = Field(
        ...,
        description="ID of the arc this recap summarizes"
    )
    arc_number: int = Field(
        ...,
        description="Sequential number of this arc (1st, 2nd, 3rd, etc.)",
        ge=1
    )
    
    # Arc definition
    premise: str = Field(
        default="",
        description="The core narrative premise of the arc"
    )
    central_conflict: str = Field(
        default="",
        description="The main conflict/challenge of the arc"
    )
    
    # Narrative summary
    title: str = Field(
        default="",
        description="Auto-generated arc title (e.g., 'The Betrayal', 'Rise of the Rebel')"
    )
    summary: str = Field(
        default="",
        description="3-5 paragraph narrative summary of the entire arc"
    )
    
    # Episodes & segments
    episode_count: int = Field(
        default=0,
        ge=0,
        description="Number of episodes in this arc"
    )
    segment_count: int = Field(
        default=0,
        ge=0,
        description="Total number of segments across all episodes"
    )
    episode_recaps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Summaries of each episode (episode_number, title, summary)"
    )
    
    # Character arcs
    character_arc_goals: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> their arc goal (e.g., 'learn to trust')"
    )
    character_resolutions: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> how their arc was resolved"
    )
    
    # Thematic & narrative tracking
    themes: List[str] = Field(
        default_factory=list,
        description="Major themes explored across the arc"
    )
    themes_explored_depth: Dict[str, str] = Field(
        default_factory=dict,
        description="theme -> how was it explored and resolved"
    )
    
    # Mysteries & plot points
    central_mysteries: List[str] = Field(
        default_factory=list,
        description="Main questions/mysteries that drove the arc"
    )
    mysteries_resolved: Dict[str, str] = Field(
        default_factory=dict,
        description="mystery -> how it was resolved"
    )
    unresolved_mysteries: List[str] = Field(
        default_factory=list,
        description="Mysteries that remain unresolved for next arc"
    )
    
    # Character relationships
    relationship_changes: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="char1_id -> {char2_id -> relationship change description}"
    )
    
    # Arc outcome
    outcome: str = Field(
        default="",
        description="Overall outcome of the arc (victory, defeat, transformation, etc.)"
    )
    tone: str = Field(
        default="",
        description="Overall tone/mood of the arc (e.g., 'dark_and_epic', 'hopeful_struggle')"
    )
    
    # Setup for next arc
    hook_for_next_arc: str = Field(
        default="",
        description="Hook or setup that leads into the next arc"
    )
    new_status_quo: str = Field(
        default="",
        description="The new status quo established by end of arc"
    )
    
    # Compression info (when arc was compressed)
    compressed: bool = Field(
        default=False,
        description="Whether this arc has been compressed (frozen canonical path)"
    )
    compression_date: Optional[datetime] = Field(
        default=None,
        description="When this arc was compressed"
    )
    canonical_path_summary: str = Field(
        default="",
        description="Summary of the canonical path chosen during compression"
    )
    
    # Generation metadata
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    generator_model: str = Field(default="gpt-4o-mini")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "arc_recap_arc_1",
                "story_id": "story_1",
                "arc_id": "arc_1",
                "arc_number": 1,
                "premise": "A knight must uncover a conspiracy within the royal court",
                "central_conflict": "Trust vs. Duty to the crown",
                "title": "The Betrayal at Court",
                "summary": "The first arc follows Sir Aldric as he discovers cracks in the foundation of his oath to the king...",
                "episode_count": 15,
                "segment_count": 287,
                "character_arc_goals": {
                    "char_knight": "learn to trust despite past betrayal",
                    "char_king": "choose redemption over power"
                },
                "character_resolutions": {
                    "char_knight": "Finally trusted Princess Aurora, found new purpose",
                    "char_king": "Abdicated throne, sought penance"
                },
                "themes": ["betrayal", "trust", "duty", "redemption"],
                "central_mysteries": [
                    "Who sent the poisoned wine?",
                    "What is the king's true agenda?"
                ],
                "mysteries_resolved": {
                    "Who sent the poisoned wine?": "The advisor, trying to frame the princess",
                    "What is the king's true agenda?": "Unknowingly serving a shadowy council"
                },
                "unresolved_mysteries": [
                    "Who commands the shadowy council?",
                    "What is their ultimate goal?"
                ],
                "outcome": "King's advisor captured, new council formed, peace restored",
                "tone": "dark_and_dramatic",
                "hook_for_next_arc": "Rumors of the council's true leader in distant lands",
                "new_status_quo": "Kingdom rebuilding with honest leadership",
                "compressed": True,
                "compression_date": "2025-03-02T00:00:00+00:00",
                "canonical_path_summary": "Knight sided with princess, king learned truth, advisor exiled",
                "generated_at": "2025-03-02T00:00:00+00:00"
            }
        }
    )
