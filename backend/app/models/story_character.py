from typing import Any, Optional, List
from enum import Enum
from pydantic import Field, field_validator
from .story_block import StoryBlock


class AvatarShape(str, Enum):
    """Available avatar shapes for characters."""
    SQUARE = "square"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    STAR = "star"
    PENTAGON = "pentagon"


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
    """
    name: str
    description: str
    background: str
    avatar_shape: AvatarShape = Field(default=AvatarShape.CIRCLE)
    avatar_color: str = Field(default="#FF6B6B")
    running_status: List[dict[str, Any]] = Field(default_factory=list)

    def __init__(self, **data: Any):
        """Initialize a StoryCharacter instance.
        
        Args:
            **data: Character data fields
        """
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
    
    def get_short_overview(self) -> str:
        """Get a short descriptor of this character.
        
        Returns:
            A string describing the character's role and key traits
        """
        return f"{self.name}: {self.description} (Avatar: {self.avatar_shape.value} {self.avatar_color})"

    def get_full_overview(self) -> str:
        """Get detailed information about this character.
        
        Returns:
            A string containing comprehensive character information
        """
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
