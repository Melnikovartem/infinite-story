from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from ..models.text_types import TextBlock

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
                type_desc = "string (optional)"
            elif field.annotation == str:
                type_desc = "string"
            elif field.annotation == int:
                type_desc = "integer"
            elif field.annotation == List[str]:
                type_desc = "array of strings"
            elif field.annotation == List[Dict[str, str]]:
                type_desc = "array of objects with string key-value pairs"
            elif field.annotation == Dict[str, str]:
                type_desc = "object with string key-value pairs"
            elif field.annotation == Dict[str, Any]:
                type_desc = "object with mixed value types"
            elif field.annotation == List[TextBlock]:
                type_desc = "array of text blocks"
            else:
                type_desc = "mixed"
                
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
    name: str = Field(description="The name of the world/setting")
    backstory: str = Field(description="The historical background and creation story of the world")
    major_events: List[str] = Field(default_factory=list, description="List of significant historical events that shaped the world")
    cultures: List[Dict[str, str]] = Field(default_factory=list, description="List of cultures with their key characteristics")
    magic_system: Optional[str] = Field(None, description="Description of the world's magic system if applicable")
    technology_level: str = Field(description="The technological advancement level of the world")
    political_system: str = Field(description="The governing system and power structures")
    religions: List[Dict[str, str]] = Field(default_factory=list, description="List of religions and their key beliefs")
    maps: List[str] = Field(default_factory=list, description="List of map references or descriptions")

class LocationTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating location details."""
    displayed_name: str = Field(description="The name as it should be displayed to users")
    name_parts: List[str] = Field(default_factory=list, description="Components that make up the location name")
    short_description: str = Field(description="Brief overview of the location")
    long_description: str = Field(description="Detailed description of the location's appearance and atmosphere")
    history: str = Field(description="Historical background of the location")
    local_culture: Optional[Dict[str, str]] = Field(None, description="Cultural aspects specific to this location")
    points_of_interest: List[str] = Field(default_factory=list, description="Notable features or landmarks")
    connected_locations: List[str] = Field(default_factory=list, description="Other locations that are directly connected to this one")

class CharacterTextGeneratorResponse(TextGeneratorResponse):
    """Response for generating character details."""
    displayed_name: str = Field(description="The name as it should be displayed to users")
    name_parts: List[str] = Field(default_factory=list, description="Components that make up the character's name")
    short_description: str = Field(description="Brief overview of the character")
    background: str = Field(description="Character's background story")
    age: Optional[int] = Field(None, description="Character's age if known")
    gender: Optional[str] = Field(None, description="Character's gender if specified")
    personality_traits: List[str] = Field(default_factory=list, description="Key personality characteristics")
    physical_description: str = Field(description="Detailed description of physical appearance")
    goals: List[str] = Field(default_factory=list, description="Character's objectives and desires")
    fears: List[str] = Field(default_factory=list, description="Character's fears and phobias")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Relationships with other characters")
    backstory: str = Field(description="Detailed life history and experiences")
    motivations: List[str] = Field(default_factory=list, description="What drives the character's actions")
    skills: List[str] = Field(default_factory=list, description="Character's abilities and talents")
    inventory: List[str] = Field(default_factory=list, description="Items the character possesses")

class SceneTextGeneratorResponse(TextGeneratorResponse):
    """Response from the scene generation model."""
    short_description: str = Field(description="Brief summary of the scene")
    text_blocks: List[TextBlock] = Field(default_factory=list, description="Sequence of text blocks that make up the scene")
    location_change: Optional[str] = Field(None, description="New location if the scene changes location")
    character_status_change: Dict[str, str] = Field(default_factory=dict, description="Changes in character states during the scene")
    choice_1: str = Field(description="First choice presented to the player")
    choice_2: str = Field(description="Second choice presented to the player")
    atmosphere: str = Field(description="The overall mood and atmosphere of the scene")
    time_of_day: Optional[str] = Field(None, description="When the scene takes place")
    weather: Optional[str] = Field(None, description="Weather conditions during the scene")
    key_items: List[str] = Field(default_factory=list, description="Important items present or mentioned in the scene")

class ChoiceGenerationResponse(TextGeneratorResponse):
    """Response for generating story choices."""
    choice_text: str = Field(description="The text of the choice presented to the player")
    next_segment_hint: str = Field(description="A hint about what might happen if this choice is made")
    flags: Dict[str, bool] = Field(default_factory=dict, description="Content warning flags for the choice")
    impact: Dict[str, str] = Field(default_factory=dict, description="Expected impact of this choice on characters and story") 