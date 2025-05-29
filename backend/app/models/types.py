from enum import Enum
from typing import Optional, List, Dict, Any
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
    type: TextType
    content: str
    character: Optional[str] = None
    emotion: Optional[str] = None
    visual_asset: Optional[str] = None
    sound_asset: Optional[str] = None

class TextGeneratorResponse(BaseModel):
    """Base class for generator responses."""
    raw_response: str
    parsed_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

class WorldTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating world/setting details."""
    name: str
    backstory: str
    major_events: List[str] = Field(default_factory=list)
    cultures: List[Dict[str, str]] = Field(default_factory=list)
    magic_system: Optional[Dict[str, Any]] = None
    technology_level: str
    political_system: str
    religions: List[Dict[str, str]] = Field(default_factory=list)
    maps: List[str] = Field(default_factory=list)

class LocationTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating location details."""
    displayed_name: str
    name_parts: List[str] = Field(default_factory=list)
    short_description: str
    long_description: str
    history: str
    local_culture: Optional[Dict[str, str]] = None
    points_of_interest: List[str] = Field(default_factory=list)
    connected_locations: List[str] = Field(default_factory=list)

class CharacterTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating character details."""
    displayed_name: str
    name_parts: List[str] = Field(default_factory=list)
    short_description: str
    background: str
    age: Optional[int] = None
    gender: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    physical_description: str
    goals: List[str] = Field(default_factory=list)
    fears: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)
    backstory: str
    motivations: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    inventory: List[str] = Field(default_factory=list)

class SceneTextGeneratorResponse(TextGeneratorResponse):
    """Response from the scene generation model."""
    short_description: str
    text_blocks: List[TextBlock] = Field(default_factory=list)
    location_change: Optional[str] = None
    character_status_change: Dict[str, str] = Field(default_factory=dict)
    choice_1: str
    choice_2: str
    atmosphere: str
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    key_items: List[str] = Field(default_factory=list)