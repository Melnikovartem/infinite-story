import pytest
from unittest.mock import AsyncMock, patch
from app.engine.generator import TextGenerator
from app.engine.openai_generator import OpenAIGenerator
from app.models.text_types import TextType
from app.models.text_types import SceneTextGeneratorResponse, TextGeneratorResponse, WorldTextGeneratorResponse, CharacterTextGeneratorResponse, LocationTextGeneratorResponse
from datetime import datetime, UTC

class MockGenerator(TextGenerator):
    """Mock generator for testing that provides predefined responses for different context types."""
    
    def __init__(self, response_type=None):
        super().__init__()
        self.response_type = response_type
        self.last_system_prompt = None
        self.last_user_prompt = None
        
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Return a predefined response based on the context type."""
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        
        if self.response_type == SceneTextGeneratorResponse:
            return '''{
                "short_description": "A mysterious room reveals its secrets",
                "text_blocks": [
                    {
                        "type": "narrator_describing",
                        "content": "The room is dimly lit by flickering torches on the walls. Ancient symbols are carved into the stone floor, forming an intricate pattern that seems to pulse with a faint blue light.",
                        "emotion": "mysterious"
                    },
                    {
                        "type": "character_speech",
                        "content": "These symbols... they look familiar.",
                        "character": "Test Character",
                        "emotion": "curious"
                    },
                    {
                        "type": "sfx",
                        "content": "A low hum begins to emanate from the symbols",
                        "sound_asset": "mystical_hum"
                    }
                ],
                "location_change": null,
                "character_status_change": {"Test Character": "investigating"},
                "choice_1": "Examine the symbols more closely",
                "choice_2": "Search for an exit",
                "atmosphere": "mysterious",
                "time_of_day": "night",
                "weather": "indoor",
                "key_items": ["ancient symbols", "torches", "stone floor"]
            }'''
        elif self.response_type == WorldTextGeneratorResponse:
            return '''{
                "name": "Test World",
                "backstory": "A world created for testing purposes",
                "major_events": ["The Great Test", "The Mocking Period"],
                "cultures": [{"name": "Test Culture", "description": "A culture for testing"}],
                "magic_system": "Test magic system",
                "technology_level": "medieval",
                "political_system": "testocracy",
                "religions": [{"name": "Test Religion", "beliefs": "Testing is divine"}],
                "maps": ["test_map_1", "test_map_2"]
            }'''
        elif self.response_type == CharacterTextGeneratorResponse:
            return '''{
                "displayed_name": "Test Character",
                "name_parts": ["Test", "Character"],
                "short_description": "A character created for testing",
                "background": "Born in a test environment",
                "age": 25,
                "gender": "unknown",
                "personality_traits": ["curious", "methodical"],
                "physical_description": "Average height, test-like appearance",
                "goals": ["Complete all tests", "Find bugs"],
                "fears": ["Failing tests", "Infinite loops"],
                "relationships": {"Test NPC": "friend"},
                "backstory": "Created specifically for testing purposes",
                "motivations": ["Testing", "Debugging"],
                "skills": ["Testing", "Mocking"],
                "inventory": ["Test sword", "Debug potion"]
            }'''
        elif self.response_type == LocationTextGeneratorResponse:
            return '''{
                "displayed_name": "Test Location",
                "name_parts": ["Test", "Location"],
                "short_description": "A location for testing",
                "long_description": "A detailed test location with various test features",
                "history": "Created for testing purposes",
                "local_culture": {"name": "Test Culture", "description": "Test-focused culture"},
                "points_of_interest": ["Test Point 1", "Test Point 2"],
                "connected_locations": ["Test Location 2", "Test Location 3"]
            }'''
        else:
            raise ValueError(f"Unsupported response type: {self.response_type}")

@pytest.fixture
def mock_openai_response():
    return {
        "choices": [{
            "message": {
                "content": '''{
                    "short_description": "A tense confrontation in the tavern",
                    "text_blocks": [
                        {
                            "type": "narrator_describing",
                            "content": "The dim light of the tavern casts long shadows across the wooden tables.",
                            "emotion": "tense"
                        },
                        {
                            "type": "character_speech",
                            "content": "I've been waiting for you.",
                            "character": "John",
                            "emotion": "angry"
                        }
                    ],
                    "location_change": null,
                    "character_status_change": {"John": "hostile"},
                    "choice_1": "Draw your weapon",
                    "choice_2": "Try to talk it out",
                    "atmosphere": "tense",
                    "time_of_day": "evening",
                    "weather": "clear",
                    "key_items": ["dagger", "whiskey bottle"]
                }'''
            }
        }]
    }

@pytest.mark.asyncio
async def test_scene_generation(mock_openai_response):
    """Test generating a scene using the OpenAIGenerator."""
    # Create generator with mock client
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    # Mock the client's post method
    generator.client.post = AsyncMock(return_value=AsyncMock(
        raise_for_status=AsyncMock(),
        json=lambda: mock_openai_response
    ))
    
    # Generate a scene
    response = await generator.generate(
        system_prompt="You are a creative writing expert",
        user_prompt="Create a tense scene in a tavern",
        context_type="scene"
    )
    
    # Verify response type
    assert response.error is None
    assert isinstance(response, SceneTextGeneratorResponse)
    
    # Verify response content
    assert response.short_description == "A tense confrontation in the tavern"
    assert len(response.text_blocks) == 2
    
    # Verify first text block
    assert response.text_blocks[0].type == TextType.NARRATOR_DESCRIBING
    assert response.text_blocks[0].content == "The dim light of the tavern casts long shadows across the wooden tables."
    assert response.text_blocks[0].emotion == "tense"
    
    # Verify second text block
    assert response.text_blocks[1].type == TextType.CHARACTER_SPEECH
    assert response.text_blocks[1].content == "I've been waiting for you."
    assert response.text_blocks[1].character == "John"
    assert response.text_blocks[1].emotion == "angry"
    
    # Verify other fields
    assert response.character_status_change == {"John": "hostile"}
    assert response.choice_1 == "Draw your weapon"
    assert response.choice_2 == "Try to talk it out"
    assert response.atmosphere == "tense"
    assert response.time_of_day == "evening"
    assert response.weather == "clear"
    assert response.key_items == ["dagger", "whiskey bottle"]

@pytest.mark.asyncio
async def test_scene_generation_error_handling():
    """Test error handling during scene generation."""
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    # Mock the client to raise an exception
    generator.client.post = AsyncMock(side_effect=Exception("API Error"))
    
    # Generate a scene
    response = await generator.generate(
        system_prompt="You are a creative writing expert",
        user_prompt="Create a tense scene in a tavern",
        context_type="scene"
    )
    
    # Verify error response
    assert isinstance(response, TextGeneratorResponse)
    assert response.error is not None

@pytest.mark.asyncio
async def test_scene_generation_invalid_json():
    """Test handling of invalid JSON response."""
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    # Mock the client to return invalid JSON
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json = lambda: {
        "choices": [{
            "message": {
                "content": "This is not valid JSON"
            }
        }]
    }
    generator.client.post = AsyncMock(return_value=mock_response)
    
    # Generate a scene
    response = await generator.generate(
        system_prompt="You are a creative writing expert",
        user_prompt="Create a tense scene in a tavern",
        context_type="scene"
    )
    
    # Verify error response
    assert isinstance(response, TextGeneratorResponse)
    assert response.error is not None

@pytest.mark.asyncio
async def test_prompt_handling():
    """Test that prompts are correctly passed between generate and _generate_content."""
    generator = MockGenerator(SceneTextGeneratorResponse)
    
    system_prompt = "You are a creative writing expert"
    user_prompt = "Create a tense scene in a tavern"
    context_type = "scene"
    
    expected_system_prompt = '''You are a creative writing expert

Response Schema:
{
  "short_description": {
    "type": "string",
    "description": "Brief summary of the scene"
  },
  "atmosphere": {
    "type": "Optional[string]",
    "description": "The overall mood and atmosphere of the scene"
  },
  "time_of_day": {
    "type": "Optional[string]",
    "description": "When the scene takes place"
  },
  "weather": {
    "type": "Optional[string]",
    "description": "Weather conditions during the scene"
  },
  "key_items": {
    "type": "List[string]",
    "description": "Important items present or mentioned in the scene"
  },
  "text_blocks": {
    "type": "List[{'type': 'object', 'properties': {'type': {'type': 'string', 'enum': ['narrator_describing', 'narrator_commentary', 'flashback', 'dream_sequence', 'character_speech', 'character_thought', 'poem_or_song', 'letter_or_note', 'sfx', 'visual_cue', 'media_overlay', 'scene_title', 'location_label', 'system_message'], 'description': 'The type of text block'}, 'text': {'type': 'string', 'description': 'The actual text content of the block'}}, 'text_type_descriptions': [{'value': 'narrator_describing', 'description': 'Narrative description of scenes, actions, environments'}, {'value': 'narrator_commentary', 'description': "Narrator's commentary or observations"}, {'value': 'flashback', 'description': 'Past events being recalled'}, {'value': 'dream_sequence', 'description': 'Dream or vision sequences'}, {'value': 'character_speech', 'description': 'Direct dialogue from characters'}, {'value': 'character_thought', 'description': 'Internal thoughts/monologue'}, {'value': 'poem_or_song', 'description': 'Poetic or musical content'}, {'value': 'letter_or_note', 'description': 'Written correspondence'}, {'value': 'sfx', 'description': 'Sound effects'}, {'value': 'visual_cue', 'description': 'Visual descriptions or cues'}, {'value': 'media_overlay', 'description': 'Overlaid media elements'}, {'value': 'scene_title', 'description': 'Title of a scene'}, {'value': 'location_label', 'description': 'Location identifiers'}, {'value': 'system_message', 'description': 'System/meta messages'}]}]",
    "description": "Sequence of text blocks that make up the scene"
  },
  "characters_present": {
    "type": "List[string]",
    "description": "List of character ids present in the scene"
  },
  "locations_present": {
    "type": "List[string]",
    "description": "List of location ids present in the scene"
  },
  "character_status_change": {
    "type": "Dict[string, string]",
    "description": "Changes in character states during the scene"
  },
  "location_status_change": {
    "type": "Dict[string, string]",
    "description": "Changes in location status during the scene"
  },
  "choice_1": {
    "type": "string",
    "description": "First choice presented to the player"
  },
  "choice_2": {
    "type": "string",
    "description": "Second choice presented to the player"
  }
}'''
    
    # Generate content
    await generator.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        context_type=context_type
    )
    
    # Verify prompts were passed correctly
    assert generator.last_system_prompt == expected_system_prompt
    assert generator.last_user_prompt == user_prompt