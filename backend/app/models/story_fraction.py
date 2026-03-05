"""Story Fraction model for managing story factions/divisions."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.story_base import StoryBase


class StoryFraction(StoryBase):
    """A group of people/faction with their own motives and goals.
    
    A fraction is a major narrative division (like an act) centered around
    a particular group, faction, or set of motivations. Characters are 
    assigned to fractions, and locations are associated with them.
    """
    
    title: str = Field(..., description="Title of the fraction (e.g., 'The Awakening')")
    order: int = Field(..., description="Order number (1st, 2nd, 3rd fraction, etc)")
    
    short_description: str = Field(
        "",
        description="Brief description (1-2 sentences, used in prompts)"
    )
    
    full_description: str = Field(
        "",
        description="Detailed description (3-5 sentences with rich details)"
    )
    
    main_goal: str = Field(
        "",
        description="What should happen in this fraction? Main goal/outcome"
    )
    
    themes: List[str] = Field(
        default_factory=list,
        description="Key themes for this fraction (e.g., ['betrayal', 'redemption'])"
    )
    
    tone: str = Field(
        "neutral",
        description="Emotional tone (epic, intimate, dark, hopeful, etc)"
    )
    
    central_conflict: str = Field(
        "",
        description="Main conflict driving this fraction"
    )
    
    # Narrative guidance
    narrative_direction: str = Field(
        "",
        description="Guideline for where this fraction is heading"
    )
    
    character_ids: List[str] = Field(
        default_factory=list,
        description="Character IDs assigned to this fraction"
    )
    
    location_ids: List[str] = Field(
        default_factory=list,
        description="Location IDs associated with this fraction"
    )
    
    def to_context_short(self) -> str:
        """Short context: title and brief description."""
        return f"{self.title} (Order {self.order}): {self.short_description}"
    
    def to_context_full(self) -> str:
        """Full context: complete fraction information."""
        context = f"""Fraction: {self.title}

Order: {self.order}

{self.full_description}

Main Goal: {self.main_goal}

Themes: {', '.join(self.themes) if self.themes else 'N/A'}

Central Conflict: {self.central_conflict}

Characters: {len(self.character_ids)}
Locations: {len(self.location_ids)}"""
        
        if self.narrative_direction:
            context += f"\n\nNarrative Direction: {self.narrative_direction}"
        
        return context
