from enum import Enum
from typing import Optional
from pydantic import BaseModel

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
    type: TextType
    content: str
    character: Optional[str] = None
    emotion: Optional[str] = None
    visual_asset: Optional[str] = None
    sound_asset: Optional[str] = None 