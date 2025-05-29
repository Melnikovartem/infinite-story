import json
from typing import Optional, Dict, Any
import httpx
from .generator import Generator
from ..models.story_segment import StorySegment, TextBlock, CharacterStatus, LocationStatus
from ..models.types import TextType

class OpenAIGenerator(Generator[StorySegment]):
    """OpenAI-style API implementation of the Generator interface.
    
    This generator uses an OpenAI-compatible API to generate story segments.
    It handles the API communication and response parsing to create validated StorySegment objects.
    """
    
    def __init__(
        self,
        api_base: str,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Initialize the OpenAI generator.
        
        Args:
            api_base: Base URL for the API
            api_key: API key for authentication
            model: Model name to use for generation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(
            base_url=api_base,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> StorySegment:
        """Generate a story segment using the OpenAI API.
        
        Args:
            system_prompt: The system-level prompt that defines the behavior and constraints
            user_prompt: The user-level prompt that specifies what to generate
            context: Optional additional context for the generation
            
        Returns:
            A validated StorySegment instance
            
        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If the API response cannot be parsed into a StorySegment
        """
        # Prepare the system message with context
        full_system_message = system_prompt
        if context:
            full_system_message += f"\nContext: {json.dumps(context)}"
        
        # Prepare the messages for the API
        messages = [
            {"role": "system", "content": full_system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        # Make the API request
        response = await self.client.post(
            "/v1/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        try:
            # Parse the JSON response into a StorySegment
            data = json.loads(content)
            return StorySegment(
                id=data["id"],
                story_id=data["story_id"],
                from_choice_id=data.get("from_choice_id"),
                text_blocks=[
                    TextBlock(
                        type=TextType(block["type"]),
                        content=block["content"],
                        character=block.get("character"),
                        emotion=block.get("emotion"),
                        visual_asset=block.get("visual_asset"),
                        sound_asset=block.get("sound_asset")
                    )
                    for block in data["text_blocks"]
                ],
                characters=[
                    CharacterStatus(
                        character_id=char["character_id"],
                        ai_status=char["ai_status"]
                    )
                    for char in data["characters"]
                ],
                locations=[
                    LocationStatus(
                        location_id=loc["location_id"],
                        ai_status=loc["ai_status"]
                    )
                    for loc in data["locations"]
                ]
            )
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to parse API response into StorySegment: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

async def main():
    generator = OpenAIGenerator(
        api_base="https://api.openai.com",
        api_key="your-api-key",
        model="gpt-3.5-turbo"
    )
    
    try:
        segment = await generator.generate(
            system_prompt="You are a story generator that creates narrative segments in JSON format.",
            user_prompt="Generate a story segment about a mysterious forest",
            context={"story_id": "123", "current_location": "forest"}
        )
        print(segment)
    finally:
        await generator.close() 