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
    type: TextType = Field(description="The type of text block (narrative, dialogue, etc.)")
    content: str = Field(description="The actual text content of the block")
    emotion: Optional[str] = Field(None, description="The emotion of the text block")
    character: Optional[str] = Field(None, description="The character speaking the text block")

    @classmethod
    def get_schema_description(cls) -> str:
        """Get the schema description for the text block."""
        # Build list of all text types from enum
        text_types = []
        text_type_descriptions = {
            TextType.NARRATOR_DESCRIBING: "Narrative description of scenes, actions, environments",
            TextType.NARRATOR_COMMENTARY: "Narrator's commentary or observations", 
            TextType.FLASHBACK: "Past events being recalled",
            TextType.DREAM_SEQUENCE: "Dream or vision sequences",
            TextType.CHARACTER_SPEECH: "Direct dialogue from characters",
            TextType.CHARACTER_THOUGHT: "Internal thoughts/monologue",
            TextType.POEM_OR_SONG: "Poetic or musical content", 
            TextType.LETTER_OR_NOTE: "Written correspondence",
            TextType.SFX: "Sound effects",
            TextType.VISUAL_CUE: "Visual descriptions or cues",
            TextType.MEDIA_OVERLAY: "Overlaid media elements",
            TextType.SCENE_TITLE: "Title of a scene",
            TextType.LOCATION_LABEL: "Location identifiers",
            TextType.SYSTEM_MESSAGE: "System/meta messages"
        }

        for text_type in TextType:
            text_types.append({
                "value": text_type.value,
                "description": text_type_descriptions[text_type]
            })

        # Build schema with text types and descriptions
        schema = {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [t["value"] for t in text_types],
                    "description": "The type of text block"
                },
                "content": {
                    "type": "string",
                    "description": "The actual text content of the block"
                },
                "emotion": {
                    "type": "string",
                    "description": "Optional: The emotion of the text block"
                },
                "character": {
                    "type": "string",
                    "description": "Optional: The character speaking (for dialogue blocks)"
                }
            },
            "text_type_descriptions": text_types
        }
        
        return str(schema)


class TextGeneratorResponse(BaseModel):
    """Abstract base class for generator responses."""
    raw_response: Optional[str] = Field(None, description="The raw response from the generator")
    error: Optional[str] = Field(None, description="Any error that occurred during generation")

    @classmethod
    def get_schema_description(cls) -> str:
        """Generate a human-readable schema description for text generation."""
        schema = ["{"]
        for field_name, field in cls.model_fields.items():
            if field_name in ["raw_response", "parsed_data", "error"]:
                continue
                
            description = field.description or ""
            
            # Get custom type description based on field annotation
            if field.annotation == Optional[str]:
                type_desc = "Optional[string]"
            elif field.annotation == str:
                type_desc = "string"
            elif field.annotation == int:
                type_desc = "integer"
            elif field.annotation == List[str]:
                type_desc = "List[string]"
            elif field.annotation == List[Dict[str, str]]:
                type_desc = "List[Dict[string, string]]"
            elif field.annotation == Dict[str, str]:
                type_desc = "Dict[string, string]"
            elif field.annotation == Dict[str, Any]:
                type_desc = "Dict[string, Any]"
            elif field.annotation == List[TextBlock]:
                text_block_schema = TextBlock.get_schema_description()
                type_desc = f"List[{text_block_schema}]"
            else:
                type_desc = "Any"
                
            schema.append(f'  "{field_name}": {{')
            schema.append(f'    "type": "{type_desc}",')
            schema.append(f'    "description": "{description}"')
            schema.append('  },')
        if len(schema) > 1:
            schema[-1] = schema[-1].rstrip(',')  # Remove trailing comma from last item
        schema.append("}")
        return "\n".join(schema)

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