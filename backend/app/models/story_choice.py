from typing import Optional
from pydantic import BaseModel, Field
from .story_block import StoryBlock
    
class ChoiceFlags(BaseModel):
    """Flags for content warnings and restrictions."""
    nsfw: bool = False
    violent: bool = False

class StoryChoice(StoryBlock):
    """A choice in a story.
    
    This represents a choice that the player can make, with text and references
    to the segments it connects.
    """
    from_segment_id: Optional[str] = None
    to_segment_id: Optional[str] = None
    text: str
    tone: Optional[str] = Field(
        None,
        description="The tone of this choice: aggressive, cautious, diplomatic, exploratory, etc."
    )
    consequence_hint: Optional[str] = Field(
        None,
        description="A brief hint about what this choice might lead to"
    )
    clicks_logged: int = 0
    clicks_anonymous: int = 0
    flags: ChoiceFlags = Field(default_factory=ChoiceFlags)
    locked: bool = Field(
        False,
        description="Whether this choice is locked during generation to prevent race conditions"
    )

    def __init__(self, **data):
        """Initialize a StoryChoice instance.
        
        Args:
            story: Optional Story instance to add this choice to
            **data: Choice data fields
        """
        super().__init__(**data)
        self.story.add_choice(self)
    
    def to_context_short(self) -> str:
        """Short context: choice text."""
        return self.text
    
    def to_context_full(self) -> str:
        """Full context: choice text with metadata."""
        parts = [f"Choice: {self.text}"]
        if self.tone:
            parts.append(f"Tone: {self.tone}")
        if self.consequence_hint:
            parts.append(f"May lead to: {self.consequence_hint}")
        if self.from_segment_id:
            parts.append(f"From: {self.from_segment_id}")
        if self.to_segment_id:
            parts.append(f"To: {self.to_segment_id}")
        if self.flags.nsfw or self.flags.violent:
            flags = []
            if self.flags.nsfw:
                flags.append("NSFW")
            if self.flags.violent:
                flags.append("Violent")
            parts.append(f"Flags: {', '.join(flags)}")
        return " | ".join(parts)
    
    def lock(self) -> None:
        """Lock this choice to prevent concurrent generation."""
        self.locked = True
        self.save()
    
    def unlock(self) -> None:
        """Unlock this choice after generation attempt."""
        self.locked = False
        self.save()
