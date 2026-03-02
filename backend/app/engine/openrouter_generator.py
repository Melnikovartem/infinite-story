"""OpenRouter API implementation of the TextGenerator.

OpenRouter provides access to multiple LLM providers through a unified API,
including Deepseek, OpenAI, Anthropic, and more.
"""

import json
import logging
from typing import Optional, Dict, Any
import httpx
from .generator import TextGenerator
from ..models.text_types import TextGeneratorResponse
from ..utils.model_selector import ModelSelector

logger = logging.getLogger("infinite_story.engine.openrouter_generator")


class OpenRouterGenerator(TextGenerator):
    """OpenRouter API implementation of the TextGenerator.
    
    This generator uses OpenRouter's unified API to access multiple LLM providers.
    OpenRouter supports models like Deepseek, GPT, Claude, and many others.
    
    Reference: https://openrouter.ai/docs/api/chat-completions
    """
    
    # Available models on OpenRouter
    AVAILABLE_MODELS = {
        "deepseek-v3": "deepseek/deepseek-v3",
        "deepseek-chat": "deepseek/deepseek-chat",
        "gpt-4-turbo": "openai/gpt-4-turbo-preview",
        "gpt-4": "openai/gpt-4",
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        "claude-3-opus": "anthropic/claude-3-opus",
        "claude-3-sonnet": "anthropic/claude-3-sonnet",
        "claude-3-haiku": "anthropic/claude-3-haiku",
        "mixtral-8x22b": "mistralai/mixtral-8x22b-instruct",
        "llama-2-70b": "meta-llama/llama-2-70b-chat",
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v3",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
        auto_fallback: bool = True
    ):
        """Initialize the OpenRouter generator.
        
        Args:
            api_key: OpenRouter API key
            model: Model identifier (can be short name or full model path)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            site_url: Your app's URL (helps with API rate limits)
            site_name: Your app's name (helps identify requests)
            auto_fallback: If True, automatically fallback to cheapest available model if requested model is unavailable
        """
        super().__init__(temperature=temperature, max_tokens=max_tokens)
        self.api_key = api_key
        self.site_url = site_url
        self.site_name = site_name
        self.auto_fallback = auto_fallback
        
        # Map short model names to full paths if needed
        requested_model = self.AVAILABLE_MODELS.get(model, model)
        
        # Use model selector for intelligent fallback
        if auto_fallback:
            selector = ModelSelector(api_key)
            try:
                self.model = selector.validate_and_fallback(requested_model)
                if self.model != requested_model:
                    logger.info(f"Model '{requested_model}' not available, using fallback: {self.model}")
            except ValueError as e:
                logger.error(f"Model validation failed: {e}")
                self.model = requested_model
        else:
            self.model = requested_model
        
        # Initialize HTTP client with OpenRouter headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": site_url or "https://infinite-story.ai",
            "X-Title": site_name or "Infinite Story Engine",
        }
        
        self.client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers=headers,
            timeout=60.0
        )
        
        logger.info(f"OpenRouter generator initialized with model: {self.model}")
    
    async def _generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using the OpenRouter API.
        
        Args:
            system_prompt: The system prompt that includes the schema
            user_prompt: The user prompt that specifies what to generate
            
        Returns:
            A JSON string containing the generated content
            
        Raises:
            Exception: If the API call fails
        """
        try:
            import time
            start_time = time.time()
            
            logger.info(f"[OpenRouter] ▶️  Starting generation with model: {self.model}")
            logger.debug(f"[OpenRouter] System prompt length: {len(system_prompt)} chars")
            logger.debug(f"[OpenRouter] User prompt length: {len(user_prompt)} chars")
            logger.debug(f"[OpenRouter] Temperature: {self.temperature}, Max tokens: {self.max_tokens}")
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            
            api_start = time.time()
            logger.info(f"[OpenRouter] 🌐 Sending API request...")
            
            response = await self.client.post(
                "/chat/completions",
                json=payload
            )
            
            api_duration = time.time() - api_start
            logger.info(f"[OpenRouter] 📡 API response received - Status: {response.status_code}, Duration: {api_duration:.2f}s")
            
            response.raise_for_status()
            
            parse_start = time.time()
            response_data = response.json()
            parse_duration = time.time() - parse_start
            logger.debug(f"[OpenRouter] Response parsed in {parse_duration:.2f}s")
            
            # Extract content from response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                
                logger.info(f"[OpenRouter] ✅ Response received: {len(content)} chars")
                logger.debug(f"[OpenRouter] Response preview: {content[:300]}..." if len(content) > 300 else f"[OpenRouter] Response: {content}")
                
                # Log token usage if available
                if "usage" in response_data:
                    usage = response_data["usage"]
                    logger.info(
                        f"[OpenRouter] 📊 Tokens - Prompt: {usage.get('prompt_tokens', '?')}, "
                        f"Completion: {usage.get('completion_tokens', '?')}, "
                        f"Total: {usage.get('total_tokens', '?')}"
                    )
                
                total_duration = time.time() - start_time
                logger.info(f"[OpenRouter] ✨ Generation completed in {total_duration:.2f}s (API: {api_duration:.2f}s + Parse: {parse_duration:.2f}s)")
                return content
            else:
                raise ValueError("No choices in API response")
        
        except httpx.HTTPStatusError as e:
            error_msg = f"OpenRouter API error ({e.response.status_code})"
            logger.error(f"[OpenRouter] HTTP Error: {e.response.status_code}")
            
            # Parse error message from response if available
            try:
                error_data = e.response.json()
                logger.debug(f"[OpenRouter] Error response body: {json.dumps(error_data, indent=2)}")
                if "error" in error_data:
                    error_msg += f": {error_data['error'].get('message', str(error_data['error']))}"
            except Exception as parse_err:
                logger.debug(f"[OpenRouter] Could not parse error response: {parse_err}")
                error_msg += f": {str(e)}"
            
            logger.error(f"[OpenRouter] {error_msg}")
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"Failed to generate content via OpenRouter: {str(e)}"
            logger.error(f"[OpenRouter] {error_msg}", exc_info=True)
            raise Exception(error_msg)
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context_type: str
    ) -> TextGeneratorResponse:
        """Generate content based on prompts and context type.
        
        Args:
            system_prompt: The system prompt that sets the behavior of the AI
            user_prompt: The user prompt that specifies what to generate
            context_type: The type of content to generate ("world", "character", "location", "scene")
            
        Returns:
            A parsed response of the appropriate TextGeneratorResponse type
        """
        return await super().generate(system_prompt, user_prompt, context_type)
    
    @classmethod
    def get_available_models(cls) -> Dict[str, str]:
        """Get available models with their descriptions.
        
        Returns:
            Dictionary mapping short names to full model paths
        """
        return cls.AVAILABLE_MODELS.copy()
    
    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.debug("OpenRouter client closed")
    
    def __del__(self):
        """Ensure client is closed when object is destroyed."""
        try:
            # Note: This is not ideal for async, but provides a safety net
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
            else:
                loop.run_until_complete(self.close())
        except:
            pass
