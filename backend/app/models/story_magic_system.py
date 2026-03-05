"""Story Magic System model - a persistent magic/tech system in the story world.

Magic systems are tied to arcs and can evolve via running changes from episodes/segments.
They represent the rules, limitations, and costs of supernatural/technological power.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from .story_block import StoryBlock


class StoryMagicSystem(StoryBlock):
    """A magic or technology system in the story world.
    
    Magic systems are persistent world-state objects tied to arcs. They can
    evolve over time (e.g., new abilities discovered, old ones lost, costs
    increasing as the world changes).
    
    Design philosophy: LIMITATIONS and COSTS matter more than capabilities.
    This creates meaningful choices: "use magic but pay the price" vs "find another way".
    
    Storage: .infinite_story_data/<story_id>/storymagicsystem/<system_id>.json
    """
    
    name: str = Field(..., description="Name of the magic/tech system")
    description: str = Field(
        "",
        description="Short description (1-2 sentences, used in scene prompts)"
    )
    
    # Core system definition
    rules: List[str] = Field(
        default_factory=list,
        description="What it can do - capabilities/powers available (2-3 items)"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="What it CANNOT do - hard limits (3-4 items, MORE IMPORTANT than rules)"
    )
    costs: List[str] = Field(
        default_factory=list,
        description="Consequences of using it - the price of power (3-4 items)"
    )
    
    # Arc relationship
    arc_id: Optional[str] = Field(
        None,
        description="Which story arc this magic system is currently relevant to"
    )
    
    # Extended world context
    technology_level: str = Field(
        "",
        description="Technology level of the world (e.g., 'Late medieval with magical augmentation')"
    )
    origin: str = Field(
        "",
        description="Where this magic/tech comes from (e.g., 'Ancient ruins', 'Divine gift', 'Natural force')"
    )
    practitioners: str = Field(
        "",
        description="Who can use this system and how common they are"
    )
    
    # Evolution tracking
    original_description: Optional[str] = Field(
        None,
        description="The original description at creation (for comparison)"
    )
    status: str = Field(
        "active",
        description="Current system status: active, weakening, evolving, corrupted, forbidden"
    )
    discovered_abilities: List[str] = Field(
        default_factory=list,
        description="New abilities discovered during the story"
    )
    lost_abilities: List[str] = Field(
        default_factory=list,
        description="Abilities lost or sealed during the story"
    )
    change_history: List[str] = Field(
        default_factory=list,
        description="History of significant changes (e.g., 'Shadow magic weakened after the Seal broke')"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # Preserve original description on first creation
        if self.original_description is None and self.description:
            self.original_description = self.description
        self.story.add_magic_system(self)
    
    def to_context_short(self) -> str:
        """Short context for LLM prompts."""
        parts = [f"{self.name}: {self.description}"]
        if self.status != "active":
            parts.append(f"[{self.status}]")
        return " ".join(parts)
    
    def to_context_full(self) -> str:
        """Full context for LLM prompts."""
        rules_str = "\n".join(f"  - {r}" for r in self.rules) if self.rules else "  (unknown)"
        limits_str = "\n".join(f"  - {l}" for l in self.limitations) if self.limitations else "  (unknown)"
        costs_str = "\n".join(f"  - {c}" for c in self.costs) if self.costs else "  (unknown)"
        
        context = f"""Magic System: {self.name}
Status: {self.status}
Description: {self.description}

Capabilities:
{rules_str}

LIMITATIONS (hard rules):
{limits_str}

Costs & Consequences:
{costs_str}"""
        
        if self.technology_level:
            context += f"\nTechnology Level: {self.technology_level}"
        
        if self.discovered_abilities:
            context += "\nNewly Discovered:\n" + "\n".join(f"  + {a}" for a in self.discovered_abilities)
        
        if self.lost_abilities:
            context += "\nLost/Sealed:\n" + "\n".join(f"  - {a}" for a in self.lost_abilities)
        
        if self.change_history:
            recent = self.change_history[-3:]
            context += "\nRecent changes:\n" + "\n".join(f"  - {c}" for c in recent)
        
        return context
    
    def apply_change(self, change_description: str) -> None:
        """Record a change to this magic system from running story events."""
        self.change_history.append(change_description)
