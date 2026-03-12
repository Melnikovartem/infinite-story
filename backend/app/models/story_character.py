from typing import Any, Optional, List, Dict
from enum import Enum
from pydantic import Field, field_validator
from .story_block import StoryBlock
from .visuals import SpriteSheet, SpriteEmotion


class AvatarShape(str, Enum):
    """Available avatar shapes for characters."""
    SQUARE = "square"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    STAR = "star"
    PENTAGON = "pentagon"


class CharacterRole(str, Enum):
    """Character roles in the story."""
    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    ALLY = "ally"
    MINOR = "minor"


class CharacterState:
    """Represents a character's state at a specific segment."""
    
    def __init__(self, segment_id: str, emotion: Optional[str] = None, 
                 status: str = "present", notes: str = ""):
        self.segment_id = segment_id
        self.emotion = emotion
        self.status = status  # present, absent, mentioned
        self.notes = notes
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segment_id": self.segment_id,
            "emotion": self.emotion,
            "status": self.status,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CharacterState":
        """Create from dictionary."""
        return cls(
            segment_id=data["segment_id"],
            emotion=data.get("emotion"),
            status=data.get("status", "present"),
            notes=data.get("notes", "")
        )


class StoryCharacter(StoryBlock):
    """A character in a story.
    
    This represents a character with their name, description, background, and avatar.
    Characters can be assigned to factions or be independent.
    """
    name: str
    description: str  # Short description (physical appearance + impression)
    background: str
    full_description: str = ""  # Detailed description (3-5 sentences)
    avatar_shape: AvatarShape = Field(default=AvatarShape.CIRCLE)
    avatar_color: str = Field(default="#FF6B6B")
    running_status: List[dict[str, Any]] = Field(default_factory=list)
    
    # Current episode state
    current_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current state during episode: {mood, status, location, loyalty, relationships, goals}"
    )
    
    # Faction and location association
    faction_id: Optional[str] = Field(default=None, description="ID of the faction this character belongs to")
    associated_locations: List[str] = Field(default_factory=list)  # Location IDs where character appears
    
    # Character characteristics
    role: CharacterRole = Field(default=CharacterRole.MINOR)  # protagonist, antagonist, ally, minor
    personality: List[str] = Field(default_factory=list)  # Key personality traits (3-4 items)
    goals: str = ""  # What does this character want?
    relationships: Dict[str, str] = Field(default_factory=dict)  # character_id -> relationship description
    
    # Recap (updated as story progresses)
    recap: Optional[str] = Field(None, description="Current recap of this character (updated during story)")
    
    # ── Visual system ────────────────────────────────────────────────────
    # Visual description used as the base prompt for sprite generation.
    # More detailed than `description` -- focused on visual/physical traits.
    visual_description: str = Field(
        default="",
        description="Detailed visual/physical description for image generation (hair, eyes, clothing, build, distinguishing features)"
    )
    # Whether sprites have been generated for this character
    has_sprites: bool = Field(default=False, description="Whether sprite images exist for this character")
    # Whether this character should get priority sprite generation (protagonist, antagonist, major allies)
    sprites_priority: bool = Field(default=False, description="Whether to generate full sprite set during story creation")

    def __init__(self, **data: Any):
        """Initialize a StoryCharacter instance.
        
        Args:
            **data: Character data fields
        """
        # Map importance_tier → role if callers pass the legacy kwarg.
        # Generators use importance_tier="major"/"minor" but the model
        # only has `role: CharacterRole`.
        tier = data.pop("importance_tier", None)
        if tier and "role" not in data:
            _tier_map = {
                "major": CharacterRole.PROTAGONIST,
                "protagonist": CharacterRole.PROTAGONIST,
                "antagonist": CharacterRole.ANTAGONIST,
                "ally": CharacterRole.ALLY,
                "minor": CharacterRole.MINOR,
            }
            data["role"] = _tier_map.get(str(tier).lower(), CharacterRole.MINOR)
        super().__init__(**data)
        self.story.add_character(self)
    
    @field_validator('avatar_color')
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate that avatar_color is a valid hex color."""
        if not isinstance(v, str):
            raise ValueError("avatar_color must be a string")
        
        # Remove # if present
        color = v.lstrip('#')
        
        # Check length (3 or 6 characters)
        if len(color) not in (3, 6):
            raise ValueError(f"Invalid hex color: {v}. Must be #XXX or #XXXXXX")
        
        # Check if all characters are valid hex
        try:
            int(color, 16)
        except ValueError:
            raise ValueError(f"Invalid hex color: {v}. Must contain only hex characters")
        
        # Return with # prefix
        return f"#{color}" if not v.startswith('#') else v

    def add_state(self, segment_id: str, emotion: Optional[str] = None,
                  status: str = "present", notes: str = "") -> None:
        """Add or update character state at a segment.
        
        Args:
            segment_id: The segment ID where this state applies
            emotion: The character's emotional state
            status: Whether character is present, absent, or mentioned
            notes: Additional notes about the character at this segment
        """
        state_dict = {
            "segment_id": segment_id,
            "emotion": emotion,
            "status": status,
            "notes": notes
        }
        
        # Check if we already have a state for this segment
        for existing_state in self.running_status:
            if existing_state["segment_id"] == segment_id:
                # Update existing state
                existing_state.update(state_dict)
                return
        
        # Add new state if not found
        self.running_status.append(state_dict)
    
    def get_state_at_segment(self, segment_id: str) -> Optional[dict[str, Any]]:
        """Get character's state at a specific segment.
        
        Args:
            segment_id: The segment ID to look up
            
        Returns:
            The character state dict at that segment, or None if not found
        """
        for state in self.running_status:
            if state["segment_id"] == segment_id:
                return state
        return None
    
    def get_state_arc(self) -> List[dict[str, Any]]:
        """Get the character's emotional arc through the story.
        
        Returns:
            List of states in order they appear
        """
        return self.running_status.copy()
    
    def get_sprite_sheet(self) -> Optional[SpriteSheet]:
        """Load the sprite sheet manifest for this character."""
        return SpriteSheet.load(self.story_id, self.id)
    
    def get_sprite_path(self, emotion: str = "neutral") -> Optional[str]:
        """Get the relative path to a sprite image for a given emotion.
        
        Falls back through: exact match -> mapped emotion -> neutral -> any available.
        Returns None if no sprites exist.
        """
        sheet = self.get_sprite_sheet()
        if not sheet:
            return None
        entry = sheet.get_best_sprite(emotion)
        if not entry or not entry.filename:
            return None
        return sheet.get_relative_path(SpriteEmotion(entry.emotion))
    
    def to_context_short(self) -> str:
        """Short context: description + recap if available."""
        parts = [f"{self.name}: {self.description}"]
        if self.recap:
            parts.append(self.recap)
        return " | ".join(parts)

    def to_context_full(self) -> str:
        """Full context: complete character information."""
        # Get all segments where this character appears
        character_segments = []
        for segment in self.story.get_all_segments():
            for char_status in segment.characters:
                if char_status.character_id == self.id:
                    character_segments.append(f"- {segment.short_description} ({char_status.current_status})")

        # Format the full character information
        info = f"""Character: {self.name}
Description: {self.description}
Background: {self.background}
Avatar: {self.avatar_shape.value} {self.avatar_color}

Appearances:
{chr(10).join(character_segments) if character_segments else "No appearances yet"}"""

        return info
