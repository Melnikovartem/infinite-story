"""Episode metadata model for storing episode-level information."""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.story_base import StoryBase
from app.models.character_state import CharacterStateSnapshot


class EpisodeMeta(StoryBase):
    """Metadata for an episode (15-20 segments).
    
    This model tracks episode-level information separate from segments, including:
    - Theme selection and focus
    - Episode context (tone, end condition, narrative direction)
    - Segment tracking
    - Character snapshots
    
    Storage: One JSON file per episode per arc
    Naming: episode_meta_{episode_number}_{arc_id}.json
    """
    
    # Identity
    episode_number: int = Field(
        ...,
        description="Episode number within the arc",
        ge=1
    )
    arc_id: str = Field(
        ...,
        description="Arc ID this episode belongs to"
    )
    
    # From E2-2 generation
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
    theme_rationale: str = Field(
        default="",
        description="Why these specific themes were selected"
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
    
    # Episode naming (updated after recap)
    episode_name: str = Field(
        default="",
        description="Auto-generated episode name after recap (e.g., 'The Betrayal Unfolds')"
    )
    
    # Segment tracking
    start_segment_id: str = Field(
        default="",
        description="ID of first segment in this episode"
    )
    end_segment_id: Optional[str] = Field(
        default=None,
        description="ID of last segment in this episode (set when complete)"
    )
    segment_count: int = Field(
        default=0,
        ge=0,
        description="Total number of segments in this episode"
    )
    
    # ========================================================================
    # CHARACTER METADATA (ALL characters in episode)
    # ========================================================================
    # This stores ALL character metadata for the entire episode, not just per-segment.
    # EpisodeMeta is the single source of truth for episode-wide character state.
    character_state_snapshot: Dict[str, CharacterStateSnapshot] = Field(
        default_factory=dict,
        description="Character ID -> CharacterStateSnapshot (ALL characters, episode-wide state)"
    )
    active_characters: List[str] = Field(
        default_factory=list,
        description="Character IDs most likely active in this episode (selected by LLM during generation)"
    )
    
    # ========================================================================
    # LOCATION METADATA (ALL locations in episode)
    # ========================================================================
    # Stores location state snapshots at episode level (parallel to characters)
    location_state_snapshot: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Location ID -> {name, description, current_state} (ALL locations, episode-wide state)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "episode_meta_1_arc_1",
                "story_id": "story_1",
                "episode_number": 1,
                "arc_id": "arc_1",
                "episode_tone": "tense",
                "episode_end_condition": "The king must make a choice",
                "narrative_direction": "Building toward betrayal",
                "selected_themes": ["betrayal", "trust"],
                "theme_rationale": "Arc's core themes, not yet explored",
                "episode_focus": "The knight's moral dilemma",
                "story_hooks": ["Is the king loyal?", "What is the conspiracy?"],
                "episode_name": "Episode 1: Suspicions Arise",
                "start_segment_id": "seg_1",
                "end_segment_id": "seg_15",
                "segment_count": 15,
                "character_state_snapshot": {}
            }
        }
    )
