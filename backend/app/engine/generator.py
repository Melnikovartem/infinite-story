from typing import TypeVar, Generic, Type, Optional, Dict, Any
from pydantic import BaseModel, ValidationError
import json
import re
import logging
from ..models.text_types import TextGeneratorResponse, WorldTextGeneratorResponse, CharacterTextGeneratorResponse, LocationTextGeneratorResponse, SceneTextGeneratorResponse

logger = logging.getLogger("infinite_story.engine.generator")

class TextGenerator:
    """Class for generating text content using AI models.
    
    This class handles text generation with different response types based on context.
    It automatically determines the appropriate response type and generates content accordingly.
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are an expert storyteller and creative writing assistant. Your role is to help create engaging, immersive, and coherent narrative content for an interactive storytelling system.

Key responsibilities:
1. Maintain narrative consistency with the established world and characters
2. Create vivid, descriptive scenes that engage the reader
3. Ensure character voices and personalities remain consistent
4. Build upon existing story elements while introducing new possibilities
5. Generate content that fits the specified context type (world, character, location, or scene)
6. Push the story forward with each response, creating a sense of progression and engagement

Remember to:
- Keep responses focused and concise
- Maintain the established tone and style
- Consider the impact on the overall story arc
- Create opportunities for meaningful player choices
- Ensure all generated content is appropriate for a general audience

IMPORTANT: You MUST return a valid JSON object that includes ALL required fields from the schema. Do not omit any required fields."""
    
    def __init__(
        self,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """Initialize the text generator.
        
        Args:
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        """
        self.response_types = {
            "world": WorldTextGeneratorResponse,
            "character": CharacterTextGeneratorResponse,
            "location": LocationTextGeneratorResponse,
            "scene": SceneTextGeneratorResponse
        }
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context_type: str
    ) -> TextGeneratorResponse:
        """Generate content based on prompts and context type.
        
        Args:
            system_prompt: The system prompt that sets the behavior of the AI. If empty, uses default prompt.
            user_prompt: The user prompt that specifies what to generate
            context_type: The type of content to generate ("world", "character", "location", "scene")
            
        Returns:
            A parsed response of the appropriate TextGeneratorResponse type
            
        Raises:
            ValueError: If the context_type is invalid or response cannot be parsed
        """
        if context_type not in self.response_types:
            raise ValueError(f"Invalid context_type: {context_type}. Must be one of {list(self.response_types.keys())}")
            
        response_type = self.response_types[context_type]
        
        try:
            # Get the schema description for the response type
            schema = response_type.get_schema_description()

            # Use default prompt if system_prompt is empty
            effective_system_prompt = system_prompt.strip() if system_prompt.strip() else self.DEFAULT_SYSTEM_PROMPT

            # Combine system prompt with schema
            full_system_prompt = f"""{effective_system_prompt}

Response Schema (ALL fields are REQUIRED unless marked Optional):
{schema}

Return ONLY a valid JSON object with all required fields filled in. Do not include any explanatory text before or after the JSON."""

            logger.debug(f"Generating {context_type} content with system prompt length: {len(full_system_prompt)}")
            logger.debug(f"User prompt: {user_prompt[:200]}..." if len(user_prompt) > 200 else f"User prompt: {user_prompt}")

            # Generate content using the internal method
            raw_response = await self._generate_content(full_system_prompt, user_prompt)

            logger.debug(f"Raw response length: {len(raw_response)}")
            logger.debug(f"Raw response preview: {raw_response[:500]}..." if len(raw_response) > 500 else f"Raw response: {raw_response}")

            # Extract JSON using regex first
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.finditer(json_pattern, raw_response)
            json_str = None

            # Try each potential JSON match
            for match in matches:
                try:
                    json_str = match.group(0)
                    # Validate that it's actually JSON
                    json.loads(json_str)
                    logger.debug(f"Found valid JSON: {json_str[:200]}..." if len(json_str) > 200 else f"Found valid JSON: {json_str}")
                    break
                except json.JSONDecodeError:
                    continue

            if not json_str:
                error_msg = "No valid JSON found in the response"
                logger.error(f"{error_msg}. Raw response: {raw_response}")
                return response_type(
                    raw_response=raw_response,
                    error=error_msg
                )

            logger.debug(f"Parsing JSON into {response_type.__name__}")
            try:
                response = response_type.model_validate_json(json_str)
                response.raw_response = raw_response
                logger.info(f"Successfully generated {context_type} content")
                return response
            except ValidationError as ve:
                # Log the validation error with details about missing fields
                error_msg = f"Validation error: {ve}. JSON received: {json_str}"
                logger.error(error_msg)
                return response_type(
                    raw_response=raw_response,
                    error=f"AI response missing required fields: {ve}"
                )

        except ValidationError as ve:
            # If validation fails, return a response with detailed error
            error_msg = f"Validation error: {ve}"
            logger.error(error_msg)
            return response_type(
                raw_response="",
                error=error_msg
            )
        except Exception as e:
            # If parsing fails, return a response with the error using the correct response type
            error_msg = f"Error during generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return response_type(
                raw_response="",
                error=error_msg
            )
            
    def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Internal method to generate content using the AI model.
        
        This method should be implemented to handle the actual AI model interaction.
        
        Args:
            system_prompt: The system prompt that includes the schema
            user_prompt: The user prompt that specifies what to generate
            
        Returns:
            A JSON string containing the generated content
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("_generate_content method must be implemented")
