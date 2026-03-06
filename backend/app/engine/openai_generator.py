import logging
import httpx
from .generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.openai_generator")

class OpenAIGenerator(TextGenerator):
    """OpenAI-style API implementation of the TextGenerator.
    
    This generator uses an OpenAI-compatible API to generate content.
    It handles the API communication and response parsing to create validated responses.
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
        super().__init__(temperature=temperature, max_tokens=max_tokens)
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=api_base,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
    
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using the OpenAI API.
        
        Args:
            system_prompt: The system prompt that includes the schema
            user_prompt: The user prompt that specifies what to generate
            
        Returns:
            A JSON string containing the generated content
            
        Raises:
            Exception: If the API call fails
        """
        try:
            logger.debug(f"[OpenAI] Preparing API request to {self.api_base}/v1/chat/completions")
            logger.debug(f"[OpenAI] Model: {self.model}, Temperature: {self.temperature}, Max tokens: {self.max_tokens}")
            logger.debug(f"[OpenAI] System prompt length: {len(system_prompt)} chars")
            logger.debug(f"[OpenAI] User prompt length: {len(user_prompt)} chars")
            
            logger.debug("[OpenAI] Sending API request...")
            response = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "response_format": {"type": "json_object"}
                }
            )
            logger.debug(f"[OpenAI] API response status: {response.status_code}")
            
            response.raise_for_status()  # This is not async
            
            response_json = response.json()
            content = response_json["choices"][0]["message"]["content"]
            
            logger.debug(f"[OpenAI] Response content length: {len(content)} chars")
            logger.debug(f"[OpenAI] Response preview: {content[:300]}..." if len(content) > 300 else f"[OpenAI] Response: {content}")
            
            return content

        except Exception as e:
            logger.error(f"[OpenAI] API call failed: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate content: {str(e)}")
    