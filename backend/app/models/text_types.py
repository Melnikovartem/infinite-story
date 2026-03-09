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


class StorylineType(str, Enum):
    """Storyline types that affect generation style and display rollout."""
    ACTION = "action"               # Fast-paced combat, chases, physical danger
    MYSTERY = "mystery"             # Investigation, clues, deduction, secrets
    ROMANCE = "romance"             # Relationships, emotional bonds, intimacy
    POLITICAL = "political"         # Intrigue, alliances, betrayal, power plays
    HORROR = "horror"               # Dread, fear, the unknown, survival
    COMEDY = "comedy"               # Humor, wit, absurdity, lighthearted moments
    DRAMA = "drama"                 # Character conflict, moral dilemmas, emotional weight
    EXPLORATION = "exploration"     # Discovery, travel, world-building, wonder


# Default storyline display configs: {type: (color, delay_ms, prefix_icon)}
STORYLINE_DISPLAY_CONFIG = {
    StorylineType.ACTION:      {"color": "bold red",      "delay": 0.02, "icon": "⚔️",  "rollout": "burst"},
    StorylineType.MYSTERY:     {"color": "dim cyan",      "delay": 0.08, "icon": "🔍", "rollout": "fade"},
    StorylineType.ROMANCE:     {"color": "magenta",       "delay": 0.06, "icon": "💕", "rollout": "gentle"},
    StorylineType.POLITICAL:   {"color": "yellow",        "delay": 0.05, "icon": "👑", "rollout": "measured"},
    StorylineType.HORROR:      {"color": "red dim",       "delay": 0.10, "icon": "💀", "rollout": "crawl"},
    StorylineType.COMEDY:      {"color": "bright_green",  "delay": 0.03, "icon": "😄", "rollout": "bounce"},
    StorylineType.DRAMA:       {"color": "white",         "delay": 0.06, "icon": "🎭", "rollout": "steady"},
    StorylineType.EXPLORATION: {"color": "green",         "delay": 0.05, "icon": "🗺️",  "rollout": "sweep"},
}


class TextBlock(BaseModel):
    """A block of text in a story segment."""
    type: TextType = Field(description="The type of text block (narrative, dialogue, etc.)")
    content: str = Field(description="The actual text content of the block")
    emotion: Optional[str] = Field(None, description="The emotion of the text block")
    character: Optional[str] = Field(None, description="The character speaking the text block")
    storyline: Optional[str] = Field(None, description="Storyline type: action, mystery, romance, political, horror, comedy, drama, exploration")


class TextGeneratorResponse(BaseModel):
    """Abstract base class for generator responses."""
    raw_response: Optional[str] = Field(None, description="The raw response from the generator")
    error: Optional[str] = Field(None, description="Any error that occurred during generation")

class WorldTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating world/setting details."""
    name: Optional[str] = Field(None, description="The name of the world/setting")
    backstory: Optional[str] = Field(None, description="The historical background and creation story of the world")
    major_events: List[str] = Field(default_factory=list, description="List of significant historical events that shaped the world")
    cultures: List[Dict[str, str]] = Field(default_factory=list, description="List of cultures with their key characteristics")
    magic_system: Optional[str] = Field(None, description="Description of the world's magic system if applicable")
    technology_level: Optional[str] = Field(None, description="The technological advancement level of the world")
    political_system: Optional[str] = Field(None, description="The governing system and power structures")
    religions: List[Dict[str, str]] = Field(default_factory=list, description="List of religions and their key beliefs")
    maps: List[str] = Field(default_factory=list, description="List of map references or descriptions")

class LocationTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating location details."""
    displayed_name: Optional[str] = Field(None, description="The name as it should be displayed to users")
    name_parts: List[str] = Field(default_factory=list, description="Components that make up the location name")
    short_description: Optional[str] = Field(None, description="Brief overview of the location")
    long_description: Optional[str] = Field(None, description="Detailed description of the location's appearance and atmosphere")
    history: Optional[str] = Field(None, description="Historical background of the location")
    local_culture: Optional[Dict[str, str]] = Field(None, description="Cultural aspects specific to this location")
    points_of_interest: List[str] = Field(default_factory=list, description="Notable features or landmarks")
    connected_locations: List[str] = Field(default_factory=list, description="Other locations that are directly connected to this one")

class CharacterTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating character details."""
    displayed_name: Optional[str] = Field(None, description="The name as it should be displayed to users")
    name_parts: List[str] = Field(default_factory=list, description="Components that make up the character's name")
    short_description: Optional[str] = Field(None, description="Brief overview of the character")
    background: Optional[str] = Field(None, description="Character's background story")
    age: Optional[str] = Field(None, description="Character's age if known (e.g., '35', 'mid-30s', 'ancient')")
    gender: Optional[str] = Field(None, description="Character's gender if specified")
    personality_traits: List[str] = Field(default_factory=list, description="Key personality characteristics")
    physical_description: Optional[str] = Field(None, description="Detailed description of physical appearance")
    goals: List[str] = Field(default_factory=list, description="Character's objectives and desires")
    fears: List[str] = Field(default_factory=list, description="Character's fears and phobias")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Relationships with other characters")
    backstory: Optional[str] = Field(None, description="Detailed life history and experiences")
    motivations: List[str] = Field(default_factory=list, description="What drives the character's actions")
    skills: List[str] = Field(default_factory=list, description="Character's abilities and talents")
    inventory: List[str] = Field(default_factory=list, description="Items the character possesses")

class SceneTextGeneratorResponse(TextGeneratorResponse):
    """Response from the scene generation model."""
    # Core Scene Information
    short_description: Optional[str] = Field(None, description="Brief summary of the scene")
    atmosphere: Optional[str] = Field(None, description="The overall mood and atmosphere of the scene")
    time_of_day: Optional[str] = Field(None, description="When the scene takes place")
    weather: Optional[str] = Field(None, description="Weather conditions during the scene")
    key_items: List[str] = Field(default_factory=list, description="Important items present or mentioned in the scene")

    text_blocks: List[TextBlock] = Field(default_factory=list, description="Sequence of text blocks that make up the scene")

    characters_present: List[str] = Field(default_factory=list, description="List of character ids present in the scene")
    locations_present: List[str] = Field(default_factory=list, description="List of location ids present in the scene")

    # Updates
    character_status_change: Dict[str, str] = Field(default_factory=dict, description="Changes in character states during the scene")
    location_status_change: Dict[str, str] = Field(default_factory=dict, description="Changes in location status during the scene")
    
    # Character Evolution (E2-3 Enhanced)
    change_notes: List[str] = Field(
        default_factory=list,
        description="Running log of character/location changes for episode tracking (e.g., 'Knight received conflicting order', 'Trust in king wavered')"
    )
    
    # Choices
    choice_1: Optional[str] = Field(None, description="First choice presented to the player")
    choice_2: Optional[str] = Field(None, description="Second choice presented to the player")

class ChoiceGenerationResponse(TextGeneratorResponse):
    """Response for generating story choices."""
    choice_text: Optional[str] = Field(None, description="The text of the choice presented to the player")
    next_segment_hint: Optional[str] = Field(None, description="A hint about what might happen if this choice is made")
    flags: Dict[str, bool] = Field(default_factory=dict, description="Content warning flags for the choice")
    impact: Dict[str, str] = Field(default_factory=dict, description="Expected impact of this choice on characters and story")


class StoryShapeResponse(TextGeneratorResponse):
    """Response for calculating story shape/structure."""
    scale: str = Field(..., description="Story scale: epic, large, medium, or small")
    num_factions: int = Field(..., description="Number of factions needed")
    num_locations: int = Field(..., description="Number of locations needed")
    characters_per_faction: Dict[str, int] = Field(
        ..., 
        description="Min and max number of characters per faction (e.g., {'min': 2, 'max': 4})"
    )
    num_independent_characters: int = Field(..., description="Number of independent characters (not tied to factions)")
    reasoning: Optional[str] = Field(None, description="Explanation for why this shape was chosen") 