from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class TextType(str, Enum):
    # Narrative Structure
    NARRATOR_DESCRIBING = "narrator_describing"
    NARRATOR_COMMENTARY = "narrator_commentary"
    FLASHBACK = "flashback"
    DREAM_SEQUENCE = "dream_sequence"
    
    # Dialogue & Internal
    CHARACTER_SPEECH = "character_speech"
    CHARACTER_THOUGHT = "character_thought"
    POEM_OR_SONG = "poem_or_song"
    LETTER_OR_NOTE = "letter_or_note"
    
    # Audio/Visual Cues
    SFX = "sfx"
    VISUAL_CUE = "visual_cue"
    MEDIA_OVERLAY = "media_overlay"
    
    # UI & Meta Text
    SCENE_TITLE = "scene_title"
    LOCATION_LABEL = "location_label"
    SYSTEM_MESSAGE = "system_message"

class TextBlock(BaseModel):
    """A block of text in a story segment."""
    type: TextType = Field(description="The type of text block (narrative, dialogue, etc.)")
    content: str = Field(description="The actual text content of the block")
    character: Optional[str] = Field(None, description="The character associated with this text block (for dialogue/thoughts)")
    emotion: Optional[str] = Field(None, description="The emotional state to be conveyed")
    visual_asset: Optional[str] = Field(None, description="Reference to a visual asset to be displayed")
    sound_asset: Optional[str] = Field(None, description="Reference to a sound effect or music to be played") 