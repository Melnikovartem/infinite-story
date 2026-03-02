"""Character state snapshot model for tracking character state across segments and episodes."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Optional


class CharacterStateSnapshot(BaseModel):
    """Strong-typed snapshot of character state for segments/episodes.
    
    This model replaces loose Dict[str, Any] character_states with a structured,
    strongly-typed representation that tracks health, emotional status, relationships,
    inventory, and progress toward character arc goals.
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
        description="character_id -> how relationship changed (e.g., 'char_king': 'betrayed - trust destroyed')"
    )
    
    # Inventory (only important items)
    inventory: Dict[str, str] = Field(
        default_factory=dict,
        description="item_name -> significance/notes (e.g., 'sword': 'bloodstained - evidence of fight')"
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
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "character_id": "char_knight",
                "description": "A once-loyal knight, now wounded and doubting",
                "health_status": "wounded in shoulder",
                "emotional_status": "betrayed, angry, resolute",
                "relationship_notes": {
                    "char_king": "betrayed - trust destroyed forever",
                    "char_princess": "saved her - fragile trust forming"
                },
                "inventory": {
                    "sword": "bloodstained - evidence of the fight",
                    "shield": "cracked - damaged protecting princess",
                    "letter": "king's confession - hidden, dangerous knowledge"
                },
                "character_arc_goal": "learn to trust despite past betrayal",
                "goal_progress": 0.4,
                "goal_notes": "Confronted past betrayal, learning to trust princess"
            }
        }
    )
