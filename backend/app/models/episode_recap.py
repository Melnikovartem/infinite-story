"""Episode recap models for summarizing episodes and tracking character states."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from app.models.story_base import StoryBase


class CharacterState(BaseModel):
    """Snapshot of a character's state at a point in time."""
    id: str
    name: str
    status: str  # e.g., "alive", "dead", "missing"
    mood: str  # e.g., "hopeful", "desperate", "angry"
    loyalty: float = Field(0.0, ge=-1.0, le=1.0)  # -1 (enemy) to 1 (ally)
    location: Optional[str] = None
    relationships: Dict[str, str] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class EpisodeRecap(StoryBase):
    """Summary of an entire episode.
    
    Captures the narrative arc of an episode, character state transitions,
    and thematic elements for use in future episode generation.
    """
    story_id: str
    episode_number: int
    arc_id: Optional[str] = None
    
    # Narrative summary
    title: str  # Auto-generated, e.g., "The Betrayal"
    summary: str  # 2-3 paragraph narrative recap
    
    # Character states at start and end
    starting_character_states: Dict[str, CharacterState] = Field(
        default_factory=dict
    )
    ending_character_states: Dict[str, CharacterState] = Field(
        default_factory=dict
    )
    
    # Segments & choices
    segment_ids: List[str] = Field(default_factory=list)
    choice_ids: List[str] = Field(default_factory=list)
    
    # Thematic reflection
    key_themes: List[str] = Field(default_factory=list)
    tone: str = Field(default="")  # e.g., "dark_and_mysterious"
    
    # ========================================================================
    # NEW: Enhanced Theme & Hook Tracking
    # ========================================================================
    themes_explored: List[str] = Field(
        default_factory=list,
        description="Which themes from selected_themes were actually explored in segments"
    )
    theme_depth: Dict[str, str] = Field(
        default_factory=dict,
        description="theme_name -> how deeply was it explored"
    )
    hook_for_next: str = Field(
        default="",
        description="Hook that bridges to the next episode"
    )
    unresolved_new: List[str] = Field(
        default_factory=list,
        description="New mysteries/questions raised this episode"
    )
    
    # ========================================================================
    # NEW: World Object State Snapshots (Character & Location Evolution)
    # ========================================================================
    # Updated descriptions of characters at episode end (for next episode context)
    episode_character_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> updated description at episode end"
    )
    # Updated descriptions of locations at episode end (for next episode context)
    episode_location_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="location_id -> updated description at episode end"
    )
    
    # ========================================================================
    # NEW: Episode Completion Tracking
    # ========================================================================
    episode_complete: bool = Field(
        default=True,
        description="Marked True when recap is generated"
    )
    segment_count: int = Field(
        default=0,
        ge=0,
        description="How many segments in this episode"
    )
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generator_model: str = Field(default="gpt-4o-mini")
    
    def get_short_overview(self) -> str:
        """Brief summary for UI."""
        return f"Episode {self.episode_number}: {self.title}"
    
    def get_full_overview(self) -> str:
        """Detailed view for AI prompts."""
        return f"""
Episode {self.episode_number}: {self.title}

Tone: {self.tone}
Key Themes: {', '.join(self.key_themes)}

Summary:
{self.summary}

Characters:
{self._format_characters()}
"""
    
    def _format_characters(self) -> str:
        """Format character states for display."""
        lines = []
        for char_id, state in self.ending_character_states.items():
            lines.append(
                f"  {state.name}: {state.status}, {state.mood} "
                f"(loyalty: {state.loyalty:+.1f})"
            )
        return "\n".join(lines) if lines else "  (No character states recorded)"
