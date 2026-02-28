"""Configuration management for the story engine."""
import os
import logging
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


class GeneratorConfig(BaseModel):
    """Configuration for AI text generation."""
    provider: Literal["openai", "openrouter"] = Field(
        default="openrouter",
        description="AI provider to use (openai or openrouter)"
    )
    api_key: str = Field(description="API key for the LLM provider")
    base_url: str = Field(default="https://api.openai.com", description="Base URL for OpenAI API")
    model: str = Field(default="deepseek-v3", description="Model name to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens to generate")
    site_url: Optional[str] = Field(default=None, description="Your app's URL (for OpenRouter)")
    site_name: Optional[str] = Field(default=None, description="Your app's name (for OpenRouter)")


class Config(BaseModel):
    """Main application configuration."""
    generator: GeneratorConfig

    @staticmethod
    def setup_logging():
        """Setup logging based on environment variables."""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Get logger for our app
        logger = logging.getLogger("infinite_story")
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        return logger

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config instance with values from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        provider = os.getenv("AI_PROVIDER", "openrouter").lower()
        
        if provider not in ["openai", "openrouter"]:
            raise ValueError(
                f"Invalid AI_PROVIDER '{provider}'. Must be 'openai' or 'openrouter'."
            )
        
        # Get API key based on provider
        if provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY environment variable is required when using OpenRouter. "
                    "Please set it in your .env file or environment. "
                    "Get one at https://openrouter.ai"
                )
            # Use deepseek-v3.2 as default - cheapest and works great
            model = os.getenv("AI_MODEL", "deepseek-v3")
        else:  # openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is required when using OpenAI. "
                    "Please set it in your .env file or environment."
                )
            model = os.getenv("AI_MODEL", "gpt-4o-mini")

        generator_config = GeneratorConfig(
            provider=provider,
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
            model=model,
            temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "2000")),
            site_url=os.getenv("OPENROUTER_SITE_URL"),
            site_name=os.getenv("OPENROUTER_SITE_NAME", "Infinite Story Engine"),
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

        # Setup logging first
        cls.setup_logging()

        return cls.from_env()


class Settings(BaseSettings):
    """FastAPI application settings using pydantic-settings."""
    
    app_name: str = "Infinite Story Engine"
    debug: bool = True
    api_base_url: str = "http://localhost:8000"
    data_dir: str = ".infinite_story_data"
    log_level: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env file
    )
