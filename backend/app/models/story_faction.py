"""Story Faction model - a persistent political group/faction in the story world.

Factions are tied to arcs and can evolve via running changes from episodes/segments.
They represent political groups, organizations, religious orders, etc.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from .story_block import StoryBlock


class StoryFaction(StoryBlock):
    """A political faction or organization in the story world.
    
    Factions are persistent world-state objects tied to arcs. They can
    evolve over time through running changes from episodes and segments
    (e.g., a faction loses its leader, gains new territory, shifts alignment).
    
    Storage: .infinite_story_data/<story_id>/storyfaction/<faction_id>.json
    """
    
    name: str = Field(..., description="Display name of the faction")
    description: str = Field(
        "",
        description="Short description (1-2 sentences, used in scene prompts)"
    )
    
    # Core identity
    goals: List[str] = Field(
        default_factory=list,
        description="Current faction goals (2-3 short-term goals driving their actions)"
    )
    leader: str = Field(
        "Unknown",
        description="Name and title of the faction's leader"
    )
    resources: str = Field(
        "Unknown",
        description="What they control/possess (gold, magic, military, influence, etc)"
    )
    alignment: str = Field(
        "Neutral",
        description="Moral stance or alignment (e.g., Good, Evil, Neutral, Lawful, Chaotic)"
    )
    
    # Arc relationship
    arc_id: Optional[str] = Field(
        None,
        description="Which story arc this faction is currently active in"
    )
    
    # Evolution tracking - these get updated by running changes
    original_description: Optional[str] = Field(
        None,
        description="The original description at creation (for comparison)"
    )
    status: str = Field(
        "active",
        description="Current faction status: active, weakened, destroyed, disbanded, merged, hidden"
    )
    territory: str = Field(
        "",
        description="Territory or area of influence"
    )
    member_character_ids: List[str] = Field(
        default_factory=list,
        description="Character IDs that belong to this faction"
    )
    rival_faction_ids: List[str] = Field(
        default_factory=list,
        description="IDs of rival/enemy factions"
    )
    allied_faction_ids: List[str] = Field(
        default_factory=list,
        description="IDs of allied factions"
    )
    
    # Running state changes (accumulated from episodes)
    change_history: List[str] = Field(
        default_factory=list,
        description="History of significant changes (e.g., 'Leader overthrown in Episode 3')"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # Preserve original description on first creation
        if self.original_description is None and self.description:
            self.original_description = self.description
        self.story.add_faction(self)
    
    def to_context_short(self) -> str:
        """Short context for LLM prompts."""
        parts = [f"{self.name}: {self.description}"]
        if self.status != "active":
            parts.append(f"[{self.status}]")
        return " ".join(parts)
    
    def to_context_full(self) -> str:
        """Full context for LLM prompts."""
        goals_str = "\n".join(f"  - {g}" for g in self.goals) if self.goals else "  (unknown)"
        
        context = f"""Faction: {self.name}
Status: {self.status}
Description: {self.description}
Leader: {self.leader}
Alignment: {self.alignment}
Resources: {self.resources}
Goals:
{goals_str}"""
        
        if self.territory:
            context += f"\nTerritory: {self.territory}"
        
        if self.change_history:
            recent = self.change_history[-3:]  # Last 3 changes
            context += "\nRecent changes:\n" + "\n".join(f"  - {c}" for c in recent)
        
        return context
    
    def apply_change(self, change_description: str) -> None:
        """Record a change to this faction from running story events.
        
        Args:
            change_description: Human-readable description of what changed
        """
        self.change_history.append(change_description)
