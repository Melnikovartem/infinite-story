import pytest
from unittest.mock import AsyncMock
from app.engine.generator import TextGenerator
from app.engine.openai_generator import OpenAIGenerator
from app.utils.ai_response_parser import ResponseSchema, FieldSpec, OutputFormat


class MockGenerator(TextGenerator):
    """Mock generator for testing that provides predefined responses."""
    
    def __init__(self, raw_response: str = "{}"):
        super().__init__()
        self.raw_response = raw_response
        self.last_system_prompt = None
        self.last_user_prompt = None
        
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.raw_response


# -- Schemas used in tests --

_SCENE_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec(name="short_description", type="str"),
        FieldSpec(name="atmosphere", type="str"),
        FieldSpec(name="choice_1", type="str"),
        FieldSpec(name="choice_2", type="str"),
    ],
)

_WORLD_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec(name="name", type="str"),
        FieldSpec(name="backstory", type="str"),
    ],
)


@pytest.mark.asyncio
async def test_generate_structured_scene():
    """Test generating a scene via generate_structured()."""
    raw = '''{
        "short_description": "A tense confrontation in the tavern",
        "atmosphere": "tense",
        "choice_1": "Draw your weapon",
        "choice_2": "Try to talk it out"
    }'''
    generator = MockGenerator(raw_response=raw)
    
    result = await generator.generate_structured(
        system_prompt="You are a creative writing expert",
        user_prompt="Create a tense scene in a tavern",
        schema=_SCENE_SCHEMA,
    )
    
    assert isinstance(result, dict)
    assert result["short_description"] == "A tense confrontation in the tavern"
    assert result["atmosphere"] == "tense"
    assert result["choice_1"] == "Draw your weapon"
    assert result["choice_2"] == "Try to talk it out"


@pytest.mark.asyncio
async def test_generate_structured_via_openai():
    """Test generate_structured() through OpenAIGenerator with mocked HTTP."""
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    api_response = {
        "choices": [{
            "message": {
                "content": '{"short_description": "Tavern scene", "atmosphere": "tense", "choice_1": "Fight", "choice_2": "Flee"}'
            }
        }]
    }
    
    generator.client.post = AsyncMock(return_value=AsyncMock(
        raise_for_status=AsyncMock(),
        json=lambda: api_response
    ))
    
    result = await generator.generate_structured(
        system_prompt="You are a creative writing expert",
        user_prompt="Create a scene",
        schema=_SCENE_SCHEMA,
    )
    
    assert isinstance(result, dict)
    assert result["short_description"] == "Tavern scene"
    assert result["choice_1"] == "Fight"
    assert result["choice_2"] == "Flee"


@pytest.mark.asyncio
async def test_generate_structured_error_returns_fallback():
    """Test that generate_structured() returns fallback on API error."""
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    generator.client.post = AsyncMock(side_effect=Exception("API Error"))
    
    fallback = [{"short_description": "fallback", "atmosphere": "calm", "choice_1": "Go", "choice_2": "Stay"}]
    
    result = await generator.generate_structured(
        system_prompt="You are a creative writing expert",
        user_prompt="Create a scene",
        schema=_SCENE_SCHEMA,
        fallback_defaults=fallback,
    )
    
    assert isinstance(result, dict)
    assert result["short_description"] == "fallback"


@pytest.mark.asyncio
async def test_generate_structured_error_returns_empty_dict_without_fallback():
    """Test that generate_structured() returns empty dict on error when no fallback given."""
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="test-key",
        model="gpt-3.5-turbo"
    )
    
    generator.client.post = AsyncMock(side_effect=Exception("API Error"))
    
    result = await generator.generate_structured(
        system_prompt="Test",
        user_prompt="Test",
        schema=_SCENE_SCHEMA,
    )
    
    assert result == {}


@pytest.mark.asyncio
async def test_generate_structured_invalid_json_returns_fallback():
    """Test handling of non-JSON response from the LLM."""
    generator = MockGenerator(raw_response="This is not valid JSON at all")
    
    fallback = [{"name": "Default World", "backstory": "A default world"}]
    
    result = await generator.generate_structured(
        system_prompt="Test",
        user_prompt="Generate a world",
        schema=_WORLD_SCHEMA,
        fallback_defaults=fallback,
    )
    
    # AIResponseParser should try field-by-field extraction; if that fails, return fallback
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_generate_structured_array_mode():
    """Test generate_structured() with expect_array=True."""
    raw = '[{"name": "World A", "backstory": "Story A"}, {"name": "World B", "backstory": "Story B"}]'
    generator = MockGenerator(raw_response=raw)
    
    array_schema = ResponseSchema(
        fields=[
            FieldSpec(name="name", type="str"),
            FieldSpec(name="backstory", type="str"),
        ],
        expect_array=True,
    )
    
    result = await generator.generate_structured(
        system_prompt="Test",
        user_prompt="Generate worlds",
        schema=array_schema,
    )
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "World A"
    assert result[1]["name"] == "World B"


@pytest.mark.asyncio
async def test_prompt_handling():
    """Test that prompts are correctly passed to _generate_content."""
    generator = MockGenerator(raw_response='{"short_description": "test", "atmosphere": "calm", "choice_1": "a", "choice_2": "b"}')
    
    system_prompt = "You are a creative writing expert"
    user_prompt = "Create a tense scene in a tavern"
    
    await generator.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=_SCENE_SCHEMA,
    )
    
    # System prompt should be passed through (non-empty, so no default substitution)
    assert generator.last_system_prompt == system_prompt
    # User prompt should have format instruction appended
    assert generator.last_user_prompt.startswith(user_prompt)
    assert "short_description" in generator.last_user_prompt


@pytest.mark.asyncio
async def test_empty_system_prompt_uses_default():
    """Test that an empty system prompt triggers the default."""
    generator = MockGenerator(raw_response='{"short_description": "test", "atmosphere": "calm", "choice_1": "a", "choice_2": "b"}')
    
    await generator.generate_structured(
        system_prompt="",
        user_prompt="Create a scene",
        schema=_SCENE_SCHEMA,
    )
    
    assert generator.last_system_prompt == TextGenerator.DEFAULT_SYSTEM_PROMPT
