"""StoryEpisode model - the single source of truth for episode-level data.

Replaces both EpisodeMeta and EpisodeRecap with a single StoryBlock that owns
all episode metadata, state snapshots, and recap information.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, UTC

from .story_block import StoryBlock


class CharacterState(BaseModel):
    """Snapshot of a character's state at a point in time."""
    id: str
    name: str
    status: str = "alive"  # e.g., "alive", "dead", "missing"
    mood: str = "neutral"  # e.g., "hopeful", "desperate", "angry"
    loyalty: float = Field(0.0, ge=-1.0, le=1.0)  # -1 (enemy) to 1 (ally)
    location: Optional[str] = None
    relationships: Dict[str, str] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class CharacterStateSnapshot(BaseModel):
    """Strong-typed snapshot of character state for segments/episodes.
    
    Tracks health, emotional status, relationships, inventory, 
    and progress toward character arc goals.
    """
    
    character_id: str = Field(
        ...,
        description="Unique identifier for the character"
    )
    
    # Core identity
    description: str = Field(
        default="",
        description="Character description (updated per episode)"
    )
    
    # Status fields
    health_status: str = Field(
        default="healthy",
        description="Character health (healthy, wounded, dying, dead, etc.)"
    )
    emotional_status: str = Field(
        default="neutral",
        description="Character emotional state (hopeful, angry, betrayed, resolved, etc.)"
    )
    
    # Relationships
    relationship_notes: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> how relationship changed"
    )
    
    # Inventory (only important items)
    inventory: Dict[str, str] = Field(
        default_factory=dict,
        description="item_name -> significance/notes"
    )
    
    # Character arc progress
    character_arc_goal: str = Field(
        default="",
        description="From arc definition (e.g., 'learn to trust despite past betrayal')"
    )
    goal_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress toward goal (0.0-1.0)"
    )
    goal_notes: str = Field(
        default="",
        description="What happened toward goal this episode"
    )
    
    # Legacy fields (optional, for backward compatibility)
    mood: str = Field(
        default="",
        description="[DEPRECATED] Legacy mood field"
    )
    loyalty: float = Field(
        default=0.0,
        description="[DEPRECATED] Legacy loyalty field (-1.0 to 1.0)"
    )
    location: Optional[str] = Field(
        default=None,
        description="[DEPRECATED] Legacy location field"
    )


class StoryEpisode(StoryBlock):
    """An episode in a story arc (15-20 segments).
    
    This is the single source of truth for episode-level data, combining
    what was previously split across EpisodeMeta and EpisodeRecap.
    
    Lifecycle:
    1. Created when a new episode starts (with metadata fields)
    2. Updated during episode (state snapshots, segment tracking)
    3. Completed when episode ends (recap fields populated)
    
    Storage: .infinite_story_data/<story_id>/storyepisode/<id>.json
    """
    
    # ========================================================================
    # IDENTITY
    # ========================================================================
    episode_number: int = Field(
        ...,
        description="Episode number within the arc",
        ge=1
    )
    arc_id: str = Field(
        ...,
        description="Arc ID this episode belongs to"
    )
    
    # ========================================================================
    # EPISODE METADATA (set at episode start)
    # ========================================================================
    episode_tone: str = Field(
        default="",
        description="Overall episode tone (e.g., 'tense', 'mysterious')"
    )
    episode_end_condition: str = Field(
        default="",
        description="What should happen at the episode's climax"
    )
    narrative_direction: str = Field(
        default="",
        description="How this episode progresses the arc narrative"
    )
    
    # Theme selection
    selected_themes: List[str] = Field(
        default_factory=list,
        description="2-3 themes selected for this episode via ThemeSelector"
    )
    
    # Generation focus
    episode_focus: str = Field(
        default="",
        description="Which character's arc or plot should be the focus"
    )
    story_hooks: List[str] = Field(
        default_factory=list,
        description="Plot hooks from arc's unresolved_mysteries to explore"
    )
    
    # ========================================================================
    # SEGMENT TRACKING
    # ========================================================================
    start_segment_id: str = Field(
        default="",
        description="ID of first segment in this episode"
    )
    end_segment_id: Optional[str] = Field(
        default=None,
        description="ID of last segment in this episode (set when complete)"
    )
    segment_ids: List[str] = Field(
        default_factory=list,
        description="All segment IDs in this episode"
    )
    choice_ids: List[str] = Field(
        default_factory=list,
        description="All choice IDs made in this episode"
    )
    segment_count: int = Field(
        default=0,
        ge=0,
        description="Total number of segments in this episode"
    )
    
    # ========================================================================
    # CHARACTER & LOCATION STATE SNAPSHOTS (updated during episode)
    # ========================================================================
    character_state_snapshot: Dict[str, CharacterStateSnapshot] = Field(
        default_factory=dict,
        description="Character ID -> CharacterStateSnapshot (episode-wide state)"
    )
    active_characters: List[str] = Field(
        default_factory=list,
        description="Character IDs active in this episode"
    )
    location_state_snapshot: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Location ID -> {name, description, current_state}"
    )
    
    # Accumulated changes from previous episode
    previous_episode_changes: List[str] = Field(
        default_factory=list,
        description="All change_notes from previous episode"
    )
    
    # Faction state tracking
    faction_state_snapshot: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Faction ID -> {name, description, goals, leader, alignment, power_level, members}"
    )
    
    # ========================================================================
    # RECAP (populated when episode completes)
    # ========================================================================
    recap: Optional[str] = Field(
        default=None,
        description="Short 1-2 sentence recap of the episode"
    )
    title: str = Field(
        default="",
        description="Auto-generated episode title (e.g., 'The Betrayal')"
    )
    summary: str = Field(
        default="",
        description="2-3 paragraph narrative recap"
    )
    episode_complete: bool = Field(
        default=False,
        description="Whether this episode has been completed and recapped"
    )
    
    # Character states at start and end (for recap)
    starting_character_states: Dict[str, CharacterState] = Field(
        default_factory=dict
    )
    ending_character_states: Dict[str, CharacterState] = Field(
        default_factory=dict
    )
    
    # Theme tracking (populated during/after episode)
    key_themes: List[str] = Field(
        default_factory=list,
        description="Major themes explored in this episode"
    )
    themes_explored: List[str] = Field(
        default_factory=list,
        description="Which themes from selected_themes were actually explored"
    )
    tone: str = Field(
        default="",
        description="Overall tone/mood of the episode (e.g., 'dark_and_mysterious')"
    )
    
    # Hooks and mysteries
    hook_for_next: str = Field(
        default="",
        description="Hook that bridges to the next episode"
    )
    unresolved_new: List[str] = Field(
        default_factory=list,
        description="New mysteries/questions raised this episode"
    )
    
    # Previous episode recap (stored for LLM context — recap of the episode before this one)
    previous_episode_recap: str = Field(
        default="",
        description="Short recap of the previous episode, used for LLM context continuity"
    )
    previous_episode_title: str = Field(
        default="",
        description="Title of the previous episode"
    )
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generator_model: str = Field(default="gpt-4o-mini")
    
    def __init__(self, **data):
        """Initialize a StoryEpisode instance."""
        super().__init__(**data)
        self.story.add_episode(self)
    
    def to_context_short(self) -> str:
        """Short context for LLM prompts."""
        base = f"Episode {self.episode_number}: {self.title}" if self.title else f"Episode {self.episode_number}"
        if self.recap:
            base += f" - {self.recap}"
        return base
    
    def to_context_full(self) -> str:
        """Full context for LLM prompts."""
        parts = []
        
        # Include previous episode recap for continuity
        if self.previous_episode_recap:
            parts.append(f"Previously ({self.previous_episode_title or 'Last Episode'}): {self.previous_episode_recap}")
            parts.append("")
        
        parts.append(f"Episode {self.episode_number}: {self.title}")
        
        if self.recap:
            parts.append(f"Recap: {self.recap}")
        
        if self.tone:
            parts.append(f"Tone: {self.tone}")
        if self.key_themes:
            parts.append(f"Key Themes: {', '.join(self.key_themes)}")
        
        if self.summary:
            parts.append(f"\nSummary:\n{self.summary}")
        
        chars = self._format_characters()
        if chars:
            parts.append(f"\nCharacters:\n{chars}")
        
        return "\n".join(parts)
    
    def _format_characters(self) -> str:
        """Format character states for display."""
        lines = []
        for char_id, state in self.ending_character_states.items():
            lines.append(
                f"  {state.name}: {state.status}, {state.mood} "
                f"(loyalty: {state.loyalty:+.1f})"
            )
        return "\n".join(lines) if lines else ""
