"""Character recap model for storing short summaries of characters."""

from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, UTC

from app.models.story_base import StoryBase


class CharacterRecap(StoryBase):
    """Short recap/summary of a character at a point in time.
    
    Created/updated throughout the story to track character evolution.
    Provides quick character reference without loading full StoryCharacter.
    
    Storage: One JSON file per character
    Naming: character_recap_{character_id}.json (updated continuously)
    """
    
    # Identity
    character_id: str = Field(
        ...,
        description="ID of the character this recap describes"
    )
    character_name: str = Field(
        ...,
        description="Character's name"
    )
    
    # Current state (short form)
    short_description: str = Field(
        default="",
        description="1-2 sentence current character summary"
    )
    current_status: str = Field(
        default="alive",
        description="alive, dead, missing, or other relevant status"
    )
    current_emotion: str = Field(
        default="neutral",
        description="Current dominant emotional state"
    )
    
    # Key relationships (abbreviated)
    key_relationships: Dict[str, str] = Field(
        default_factory=dict,
        description="character_id -> one word relationship type (ally, enemy, neutral, uncertain)"
    )
    
    # Character arc tracking
    arc_id: str = Field(
        default="",
        description="Current arc ID"
    )
    character_arc_goal: str = Field(
        default="",
        description="From arc definition - what this character should achieve"
    )
    goal_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress toward their arc goal"
    )
    
    # Last known info
    last_seen_segment_id: str = Field(
        default="",
        description="ID of last segment where character appeared"
    )
    last_seen_episode: int = Field(
        default=0,
        description="Last episode where character appeared"
    )
    
    # New character event
    is_new_character: bool = Field(
        default=False,
        description="Was this character introduced recently as new character theme event?"
    )
    introduced_theme: Optional[str] = Field(
        default=None,
        description="If new character, which theme event introduced them?"
    )
    
    # Update tracking
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this recap was last updated"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "character_recap_char_knight",
                "story_id": "story_1",
                "character_id": "char_knight",
                "character_name": "Sir Roland",
                "short_description": "Once a loyal knight, now doubting the king's motives after discovering inconsistencies in orders",
                "current_status": "alive",
                "current_emotion": "suspicious",
                "key_relationships": {
                    "char_king": "suspicious",
                    "char_princess": "protective",
                    "char_advisor": "uncertain"
                },
                "arc_id": "arc_1",
                "character_arc_goal": "learn to trust despite past betrayal",
                "goal_progress": 0.25,
                "last_seen_segment_id": "seg_5",
                "last_seen_episode": 1,
                "is_new_character": False,
                "introduced_theme": None,
                "updated_at": "2025-03-02T00:00:00+00:00"
            }
        }
    )
