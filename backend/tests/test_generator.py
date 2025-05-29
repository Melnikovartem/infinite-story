import pytest
from unittest.mock import AsyncMock, patch
from app.engine.generator import TextGenerator
from app.engine.openai_generator import OpenAIGenerator
from app.models.types import SceneTextGeneratorResponse, TextGeneratorResponse, TextType, TextBlock

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

class MockGenerator(TextGenerator):
    """Mock generator that records prompts for testing."""
    def __init__(self):
        super().__init__()
        self.last_system_prompt = None
        self.last_user_prompt = None
        
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return '{"raw_response": "test response"}'

@pytest.mark.asyncio
async def test_prompt_handling():
    """Test that prompts are correctly passed between generate and _generate_content."""
    generator = MockGenerator()
    
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
  "text_blocks": {
    "type": "array of text blocks",
    "description": "Sequence of text blocks that make up the scene"
  },
  "location_change": {
    "type": "string (optional)",
    "description": "New location if the scene changes location"
  },
  "character_status_change": {
    "type": "object with string key-value pairs",
    "description": "Changes in character states during the scene"
  },
  "choice_1": {
    "type": "string",
    "description": "First choice presented to the player"
  },
  "choice_2": {
    "type": "string",
    "description": "Second choice presented to the player"
  },
  "atmosphere": {
    "type": "string",
    "description": "The overall mood and atmosphere of the scene"
  },
  "time_of_day": {
    "type": "string (optional)",
    "description": "When the scene takes place"
  },
  "weather": {
    "type": "string (optional)",
    "description": "Weather conditions during the scene"
  },
  "key_items": {
    "type": "array of strings",
    "description": "Important items present or mentioned in the scene"
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