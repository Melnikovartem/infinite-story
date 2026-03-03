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
    
    def get_short_context(self) -> str:
        """Get short context for this fraction (used in prompts).
        
        Returns:
            Brief description for use in LLM prompts
        """
        return self.short_description
    
    def get_full_context(self) -> str:
        """Get full context for this fraction.
        
        Returns:
            Comprehensive description with goal and themes
        """
        context = f"""Fraction: {self.title}

{self.full_description}

Main Goal: {self.main_goal}

Themes: {', '.join(self.themes) if self.themes else 'N/A'}

Central Conflict: {self.central_conflict}"""
        
        if self.narrative_direction:
            context += f"\n\nNarrative Direction: {self.narrative_direction}"
        
        return context
    
    def to_context(self, format: str = "full") -> str:
        """Convert to context string for use in LLM prompts.
        
        Args:
            format: "short" for brief, "full" for comprehensive
            
        Returns:
            Formatted context string
        """
        if format == "short":
            return self.get_short_context()
        return self.get_full_context()
    
    def get_short_overview(self) -> str:
        """Get a brief overview of the fraction."""
        return f"{self.title} (Order {self.order})"
    
    def get_full_overview(self) -> str:
        """Get a detailed overview of the fraction."""
        return f"""Fraction: {self.title}

Order: {self.order}

{self.full_description}

Main Goal: {self.main_goal}

Themes: {', '.join(self.themes) if self.themes else 'N/A'}

Central Conflict: {self.central_conflict}

Characters: {len(self.character_ids)}
Locations: {len(self.location_ids)}"""
