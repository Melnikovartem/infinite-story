"""Mock generators for testing without API calls.

These mocks simulate the behavior of text generators and other
external services for isolated unit testing.
"""

from typing import Optional, List, Dict, Any, Union
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import ResponseSchema, OutputFormat


class MockTextGenerator(TextGenerator):
    """Mock text generator that returns predictable test data.
    
    Supports both generate_structured() (returns dicts) and
    _generate_content() (returns raw text strings).
    """
    
    def __init__(self, response_data: Optional[dict] = None):
        """Initialize mock generator.
        
        Args:
            response_data: Dict to return from generate_structured() (uses default if None)
        """
        super().__init__()
        self.call_count = 0
        self.last_system_prompt = None
        self.last_user_prompt = None
        self.response_data = response_data or self._default_response()
    
    def _default_response(self) -> dict:
        """Create a default scene response as a dict."""
        return {
            "short_description": "A test scene unfolds",
            "atmosphere": "mysterious",
            "time_of_day": "evening",
            "weather": "clear",
            "key_items": ["item_1", "item_2"],
            "text_blocks": [
                {
                    "type": "narrator_describing",
                    "content": "The test scene begins..."
                }
            ],
            "characters_present": ["char_1"],
            "locations_present": ["loc_1"],
            "character_status_change": {},
            "location_status_change": {},
            "choice_1": "Continue forward",
            "choice_2": "Turn back",
        }
    
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Return a JSON string of the response data."""
        import json
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        
        data = dict(self.response_data)
        data["short_description"] = f"Scene {self.call_count}: {data.get('short_description', 'test')}"
        return json.dumps(data)
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: ResponseSchema,
        fallback_defaults: Optional[List[dict]] = None,
        output_format: OutputFormat = OutputFormat.JSON,
    ) -> Union[dict, List[dict]]:
        """Generate a response (mock implementation).
        
        Args:
            system_prompt: System prompt (stored for inspection)
            user_prompt: User prompt (stored for inspection)
            schema: Response schema (unused in mock)
            fallback_defaults: Fallback defaults (unused in mock)
            output_format: Output format (unused in mock)
            
        Returns:
            Mock response dict or list of dicts
        """
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        
        # Create a copy with incremented counter
        data = dict(self.response_data)
        data["short_description"] = f"Scene {self.call_count}: {data.get('short_description', 'test')}"
        
        if schema.expect_array:
            return [data]
        return data
    
    def get_call_count(self) -> int:
        """Get number of times generator was called."""
        return self.call_count
    
    def get_last_prompt(self) -> Optional[str]:
        """Get the last user prompt used."""
        return self.last_user_prompt
    
    def reset(self) -> None:
        """Reset call tracking."""
        self.call_count = 0
        self.last_system_prompt = None
        self.last_user_prompt = None


class MockGeneratorWithErrors(MockTextGenerator):
    """Mock generator that can simulate errors."""
    
    def __init__(self, fail_on_call: int = 1):
        """Initialize error-prone mock.
        
        Args:
            fail_on_call: Which call number should fail (1-indexed)
        """
        super().__init__()
        self.fail_on_call = fail_on_call
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: ResponseSchema,
        fallback_defaults: Optional[List[dict]] = None,
        output_format: OutputFormat = OutputFormat.JSON,
    ) -> Union[dict, List[dict]]:
        """Generate, but fail on specified call by returning fallback/empty."""
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        
        if self.call_count == self.fail_on_call:
            # Simulate failure: return fallback defaults or empty
            if fallback_defaults:
                if schema.expect_array:
                    return fallback_defaults
                return fallback_defaults[0]
            if schema.expect_array:
                return []
            return {}
        
        return await super().generate_structured(
            system_prompt, user_prompt, schema, fallback_defaults, output_format
        )
    
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Generate raw content, but raise on specified call."""
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        
        if self.call_count == self.fail_on_call:
            raise Exception("Mock generation error")
        
        return await super()._generate_content(system_prompt, user_prompt)


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
    text_blocks: Optional[List[dict]] = None,
    characters_present: Optional[List[str]] = None,
    locations_present: Optional[List[str]] = None,
    error: Optional[str] = None
) -> dict:
    """Create a customized mock response dict.
    
    Args:
        short_description: Scene description
        atmosphere: Scene atmosphere
        text_blocks: Text block dicts (default single narrator block)
        characters_present: Character IDs present
        locations_present: Location IDs present
        error: Error message if response failed
        
    Returns:
        Mock response dict
    """
    if text_blocks is None:
        text_blocks = [
            {
                "type": "narrator_describing",
                "content": "The scene continues..."
            }
        ]
    
    if characters_present is None:
        characters_present = []
    
    if locations_present is None:
        locations_present = []
    
    result = {
        "short_description": short_description,
        "atmosphere": atmosphere,
        "time_of_day": "unknown",
        "weather": "unknown",
        "key_items": [],
        "text_blocks": text_blocks,
        "characters_present": characters_present,
        "locations_present": locations_present,
        "character_status_change": {},
        "location_status_change": {},
        "choice_1": "Continue",
        "choice_2": "Reconsider",
    }
    
    if error:
        result["error"] = error
    
    return result
