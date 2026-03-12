"""Abstract image generator interface and DALL-E 3 implementation.

Follows the same pattern as TextGenerator: abstract base with concrete
implementations that handle API calls.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger("infinite_story.engine.image_generator")


class ImageGenerator(ABC):
    """Abstract base class for image generation.
    
    All image generators must implement generate_image() which takes
    a text prompt and returns the path to the saved image file.
    """

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        save_path: Path,
        size: str = "1024x1024",
        quality: str = "standard",
    ) -> Path:
        """Generate an image from a text prompt and save to disk.
        
        Args:
            prompt: The text prompt describing the desired image.
            save_path: Full path where the image should be saved.
            size: Image dimensions (e.g. "1024x1024", "1792x1024").
            quality: Quality level ("standard" or "hd").
            
        Returns:
            The path to the saved image file.
            
        Raises:
            ImageGenerationError: If generation or saving fails.
        """
        ...


class ImageGenerationError(Exception):
    """Raised when image generation fails."""
    pass


class DallE3Generator(ImageGenerator):
    """DALL-E 3 image generator using the OpenAI API.
    
    Uses httpx directly (same pattern as OpenAIGenerator for text)
    to call the OpenAI images/generations endpoint.
    """

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com",
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.client = httpx.AsyncClient(
            base_url=api_base,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def generate_image(
        self,
        prompt: str,
        save_path: Path,
        size: str = "1024x1024",
        quality: str = "standard",
    ) -> Path:
        """Generate an image with DALL-E 3 and save to disk.
        
        Args:
            prompt: The image description prompt.
            save_path: Where to save the resulting PNG.
            size: "1024x1024", "1792x1024", or "1024x1792".
            quality: "standard" (~$0.04) or "hd" (~$0.08).
            
        Returns:
            Path to the saved image.
        """
        logger.info(f"[DALL-E 3] Generating image: {prompt[:80]}...")
        logger.debug(f"[DALL-E 3] Size: {size}, Quality: {quality}")
        logger.debug(f"[DALL-E 3] Save path: {save_path}")

        try:
            response = await self.client.post(
                "/v1/images/generations",
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": size,
                    "quality": quality,
                    "response_format": "url",
                },
            )
            response.raise_for_status()
            data = response.json()

            image_url = data["data"][0]["url"]
            revised_prompt = data["data"][0].get("revised_prompt", "")
            
            if revised_prompt:
                logger.debug(f"[DALL-E 3] Revised prompt: {revised_prompt[:120]}...")

            # Download the image
            logger.debug(f"[DALL-E 3] Downloading image from URL...")
            async with httpx.AsyncClient(timeout=60.0) as download_client:
                img_response = await download_client.get(image_url)
                img_response.raise_for_status()

            # Ensure directory exists and save
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(img_response.content)

            logger.info(f"[DALL-E 3] Image saved: {save_path} ({len(img_response.content)} bytes)")
            return save_path

        except httpx.HTTPStatusError as e:
            error_body = e.response.text if e.response else "No response"
            logger.error(f"[DALL-E 3] API error {e.response.status_code}: {error_body[:200]}")
            raise ImageGenerationError(
                f"DALL-E 3 API returned {e.response.status_code}: {error_body[:200]}"
            ) from e
        except Exception as e:
            logger.error(f"[DALL-E 3] Generation failed: {e}", exc_info=True)
            raise ImageGenerationError(f"Image generation failed: {e}") from e

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def create_image_generator() -> Optional[ImageGenerator]:
    """Factory function to create an image generator from environment config.
    
    Reads OPENAI_API_KEY from environment. Returns None if no key is available.
    """
    import os
    
    # Try to load .env
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-api-key-here":
        logger.warning("[ImageGenerator] No OPENAI_API_KEY found -- image generation disabled")
        return None
    
    api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
    
    logger.info("[ImageGenerator] DALL-E 3 generator initialized")
    return DallE3Generator(api_key=api_key, api_base=api_base)
