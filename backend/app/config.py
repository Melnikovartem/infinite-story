"""Configuration management for the story engine."""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class GeneratorConfig(BaseModel):
    """Configuration for AI text generation."""
    api_key: str = Field(description="API key for the LLM provider")
    base_url: str = Field(default="https://api.openai.com", description="Base URL for the API")
    model: str = Field(default="gpt-4o-mini", description="Model name to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens to generate")


class Config(BaseModel):
    """Main application configuration."""
    generator: GeneratorConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config instance with values from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        generator_config = GeneratorConfig(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        )

        return cls(generator=generator_config)

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from .env file if it exists, then from environment.

        Returns:
            Config instance
        """
        # Try to load from .env file in the backend directory
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)

        return cls.from_env()
