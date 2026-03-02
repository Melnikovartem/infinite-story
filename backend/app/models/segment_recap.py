"""Segment recap model for storing short summaries of individual segments."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, UTC

from app.models.story_base import StoryBase


class SegmentRecap(StoryBase):
    """Short recap/summary of a single segment.
    
    Created after each segment is generated. Provides quick summaries for
    context building without needing to load full segment data.
    
    Storage: One JSON file per segment
    Naming: segment_recap_{segment_id}.json
    """
    
    # Identity
    segment_id: str = Field(
        ...,
        description="ID of the segment this recap summarizes"
    )
    episode_number: int = Field(
        ...,
        description="Episode number this segment belongs to",
        ge=1
    )
    arc_id: str = Field(
        ...,
        description="Arc ID this segment belongs to"
    )
    segment_number_in_episode: int = Field(
        ...,
        description="Position of segment within episode",
        ge=1
    )
    
    # Content summary
    short_description: str = Field(
        default="",
        description="Brief 1-2 sentence scene description"
    )
    key_events: List[str] = Field(
        default_factory=list,
        description="Key plot events that happened (3-4 items max)"
    )
    
    # Character tracking
    characters_present: List[str] = Field(
        default_factory=list,
        description="Character IDs present in this segment"
    )
    character_changes: List[str] = Field(
        default_factory=list,
        description="How characters changed/evolved (extracted from change_notes)"
    )
    
    # Running log of changes (for character updates)
    change_notes: List[str] = Field(
        default_factory=list,
        description="Running log of all character/location changes in this segment"
    )
    
    # Theme & narrative tracking
    themes_present: List[str] = Field(
        default_factory=list,
        description="Which episode themes were explored in this segment"
    )
    
    # Generation metadata
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "segment_recap_seg_1",
                "story_id": "story_1",
                "segment_id": "seg_1",
                "episode_number": 1,
                "arc_id": "arc_1",
                "segment_number_in_episode": 1,
                "short_description": "The knight discovers an inconsistency in the king's orders",
                "key_events": [
                    "Knight receives conflicting command from king",
                    "Questions advisor about order validity",
                    "Advisor deflects suspiciously"
                ],
                "characters_present": ["char_knight", "char_king", "char_advisor"],
                "character_changes": [
                    "Knight's trust in king begins to waver",
                    "Advisor's loyalty questioned"
                ],
                "change_notes": [
                    "Knight received conflicting order from king",
                    "Knight questioned advisor's motives",
                    "Advisor avoided direct answer"
                ],
                "themes_present": ["betrayal", "trust"],
                "generated_at": "2025-03-02T00:00:00+00:00"
            }
        }
    )
