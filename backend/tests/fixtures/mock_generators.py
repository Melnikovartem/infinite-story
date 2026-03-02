"""Mock generators for testing without API calls.

These mocks simulate the behavior of text generators and other
external services for isolated unit testing.
"""

from typing import Optional, List, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from app.models.text_types import TextBlock, TextType, SceneTextGeneratorResponse


class MockTextGenerator:
    """Mock text generator that returns predictable test data."""
    
    def __init__(self, response_template: Optional[SceneTextGeneratorResponse] = None):
        """Initialize mock generator.
        
        Args:
            response_template: Template response to return (uses default if None)
        """
        self.call_count = 0
        self.last_prompt = None
        self.response_template = response_template or self._default_response()
    
    def _default_response(self) -> SceneTextGeneratorResponse:
        """Create a default response."""
        return SceneTextGeneratorResponse(
            short_description="A test scene unfolds",
            atmosphere="mysterious",
            time_of_day="evening",
            weather="clear",
            key_items=["item_1", "item_2"],
            text_blocks=[
                TextBlock(
                    type=TextType.NARRATOR_DESCRIBING,
                    content="The test scene begins..."
                )
            ],
            characters_present=["char_1"],
            locations_present=["loc_1"],
            character_status_change={},
            location_status_change={},
            choice_1="Continue forward",
            choice_2="Turn back",
            error=None
        )
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context_type: str = "scene"
    ) -> SceneTextGeneratorResponse:
        """Generate a response (mock implementation).
        
        Args:
            system_prompt: System prompt (unused in mock)
            user_prompt: User prompt (stored for inspection)
            context_type: Type of context (unused in mock)
            
        Returns:
            Mock response
        """
        self.call_count += 1
        self.last_prompt = user_prompt
        
        # Create a copy of the template with incremented counter
        response = SceneTextGeneratorResponse(**self.response_template.model_dump())
        response.short_description = f"Scene {self.call_count}: {response.short_description}"
        
        return response
    
    def get_call_count(self) -> int:
        """Get number of times generator was called."""
        return self.call_count
    
    def get_last_prompt(self) -> Optional[str]:
        """Get the last prompt used."""
        return self.last_prompt
    
    def reset(self) -> None:
        """Reset call tracking."""
        self.call_count = 0
        self.last_prompt = None


class MockGeneratorWithErrors(MockTextGenerator):
    """Mock generator that can simulate errors."""
    
    def __init__(self, fail_on_call: int = 1):
        """Initialize error-prone mock.
        
        Args:
            fail_on_call: Which call number should fail (1-indexed)
        """
        super().__init__()
        self.fail_on_call = fail_on_call
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context_type: str = "scene"
    ) -> SceneTextGeneratorResponse:
        """Generate, but fail on specified call.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            context_type: Type of context
            
        Returns:
            Response or error response
        """
        self.call_count += 1
        self.last_prompt = user_prompt
        
        if self.call_count == self.fail_on_call:
            return SceneTextGeneratorResponse(
                short_description="",
                atmosphere="",
                time_of_day="",
                weather="",
                key_items=[],
                text_blocks=[],
                characters_present=[],
                locations_present=[],
                character_status_change={},
                location_status_change={},
                choice_1="",
                choice_2="",
                error="Mock generation error"
            )
        
        return await super().generate(system_prompt, user_prompt, context_type)


class MockCharacterGenerator:
    """Mock character generator for testing character creation."""
    
    def __init__(self):
        """Initialize mock."""
        self.generated_characters = {}
    
    def generate_character(self, character_id: str, prompt: str) -> Dict[str, Any]:
        """Generate a character.
        
        Args:
            character_id: ID for character
            prompt: Generation prompt
            
        Returns:
            Character data
        """
        character = {
            "id": character_id,
            "name": f"Generated Character {character_id}",
            "description": "A mock-generated character",
            "background": "Mock background",
            "traits": ["intelligent", "curious"]
        }
        self.generated_characters[character_id] = character
        return character
    
    def get_generated_count(self) -> int:
        """Get number of characters generated."""
        return len(self.generated_characters)


def create_mock_response(
    short_description: str = "A test scene",
    atmosphere: str = "mysterious",
    text_blocks: Optional[List[TextBlock]] = None,
    characters_present: Optional[List[str]] = None,
    locations_present: Optional[List[str]] = None,
    error: Optional[str] = None
) -> SceneTextGeneratorResponse:
    """Create a customized mock response.
    
    Args:
        short_description: Scene description
        atmosphere: Scene atmosphere
        text_blocks: Text blocks (default single narrator block)
        characters_present: Character IDs present
        locations_present: Location IDs present
        error: Error message if response failed
        
    Returns:
        Mock response object
    """
    if text_blocks is None:
        text_blocks = [
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The scene continues..."
            )
        ]
    
    if characters_present is None:
        characters_present = []
    
    if locations_present is None:
        locations_present = []
    
    return SceneTextGeneratorResponse(
        short_description=short_description,
        atmosphere=atmosphere,
        time_of_day="unknown",
        weather="unknown",
        key_items=[],
        text_blocks=text_blocks,
        characters_present=characters_present,
        locations_present=locations_present,
        character_status_change={},
        location_status_change={},
        choice_1="Continue",
        choice_2="Reconsider",
        error=error
    )
