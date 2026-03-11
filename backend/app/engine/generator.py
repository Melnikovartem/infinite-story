from typing import Optional, List, Union
import logging
from ..utils.ai_response_parser import AIResponseParser, ResponseSchema, OutputFormat

logger = logging.getLogger("infinite_story.engine.generator")


class TextGenerator:
    """Class for generating text content using AI models.
    
    Uses generate_structured() for all structured data generation and
    _generate_content() for raw text generation. Subclasses must implement
    _generate_content() to handle the actual LLM API call.
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
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.last_raw_response: Optional[str] = None  # Last raw AI response (for debugging)
        
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: ResponseSchema,
        fallback_defaults: Optional[List[dict]] = None,
        output_format: OutputFormat = OutputFormat.JSON,
    ) -> Union[dict, List[dict]]:
        """Generate AI content and parse it into structured data via AIResponseParser.

        This is the preferred method for all generators that need structured data
        back from the LLM. It handles prompt instruction injection, raw text
        extraction, and robust multi-strategy parsing in one call.

        Args:
            system_prompt: System prompt for the AI. If empty, uses default.
            user_prompt: User prompt describing what to generate. The schema's
                         format instruction is appended automatically.
            schema: ResponseSchema defining expected fields, types, and whether
                    to expect an array or single object.
            fallback_defaults: Default dicts returned if parsing completely fails.
            output_format: Which format instruction to inject into the prompt
                          (JSON, XML, or XML_JSON hybrid).

        Returns:
            If schema.expect_array is False: a single dict (first parsed item).
            If schema.expect_array is True: a list of dicts.
            On total failure: fallback_defaults (or empty dict / empty list).
        """
        if fallback_defaults is None:
            fallback_defaults = []

        # Build the format instruction from the schema
        format_instruction = AIResponseParser.get_prompt_instruction(schema, output_format)

        # Append format instruction to user prompt
        full_user_prompt = f"{user_prompt}\n\n{format_instruction}"

        # Use default prompt if system_prompt is empty
        effective_system_prompt = system_prompt.strip() if system_prompt.strip() else self.DEFAULT_SYSTEM_PROMPT

        try:
            # Call the raw AI generation (subclasses implement this)
            raw_response = await self._generate_content(effective_system_prompt, full_user_prompt)
            self.last_raw_response = raw_response

            logger.debug(f"[generate_structured] Raw response length: {len(raw_response)}")

            # Parse with AIResponseParser (multi-strategy, robust)
            parsed = AIResponseParser.parse(
                raw_response,
                schema,
                fallback_defaults=fallback_defaults,
                preferred_format=output_format,
            )

            # Detect if parsing fell back to defaults
            is_fallback = (parsed == fallback_defaults)
            if is_fallback and raw_response and raw_response.strip():
                logger.warning(
                    f"[generate_structured] Parsing fell back to defaults. "
                    f"Raw response ({len(raw_response)} chars):\n"
                    f"{raw_response[:2000]}"
                )

            if schema.expect_array:
                return parsed  # List[dict]
            else:
                # Single object mode: return first item or fallback
                if parsed:
                    return parsed[0]
                return fallback_defaults[0] if fallback_defaults else {}

        except Exception as e:
            logger.error(f"[generate_structured] Generation failed: {e}", exc_info=True)
            self.last_raw_response = None
            if schema.expect_array:
                return fallback_defaults
            return fallback_defaults[0] if fallback_defaults else {}

    def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Internal method to generate content using the AI model.
        
        This method should be implemented to handle the actual AI model interaction.
        
        Args:
            system_prompt: The system prompt that includes the schema
            user_prompt: The user prompt that specifies what to generate
            
        Returns:
            The raw text response from the AI model
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("_generate_content method must be implemented")
