from typing import Any
from .story_block import StoryBlock

class StoryCharacter(StoryBlock):
    """A character in a story.
    
    This represents a character with their name, description, and background.
    """
    name: str
    description: str
    background: str

    def __init__(self, **data: Any):
        """Initialize a StoryCharacter instance.
        
        Args:
            **data: Character data fields
        """
        super().__init__(**data)
        self.story.add_character(self)

    def get_short_overview(self) -> str:
        """Get a short descriptor of this character.
        
        Returns:
            A string describing the character's role and key traits
        """
        return f"{self.name}: {self.description}"

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

Appearances:
{chr(10).join(character_segments) if character_segments else "No appearances yet"}"""

        return info
