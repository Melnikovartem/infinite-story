"""Model information and management utilities.

Provides information about available AI models and their characteristics.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Information about an AI model."""
    short_name: str
    full_path: str
    provider: str
    description: str
    recommended: bool = False
    max_tokens: int = 2000
    context_window: int = 4000


# Available models organized by provider
AVAILABLE_MODELS: Dict[str, List[ModelInfo]] = {
    "openrouter": [
        ModelInfo(
            short_name="deepseek-v3",
            full_path="deepseek/deepseek-v3",
            provider="Deepseek",
            description="Latest Deepseek model - excellent for creative writing and story generation",
            recommended=True,
            max_tokens=4000,
            context_window=32000
        ),
        ModelInfo(
            short_name="deepseek-chat",
            full_path="deepseek/deepseek-chat",
            provider="Deepseek",
            description="Deepseek Chat model - good balance of speed and quality",
            max_tokens=4000,
            context_window=8000
        ),
        ModelInfo(
            short_name="gpt-4-turbo",
            full_path="openai/gpt-4-turbo-preview",
            provider="OpenAI",
            description="OpenAI's latest GPT-4 variant - very capable but slower",
            max_tokens=4096,
            context_window=128000
        ),
        ModelInfo(
            short_name="gpt-4",
            full_path="openai/gpt-4",
            provider="OpenAI",
            description="OpenAI's GPT-4 - powerful but may be slower",
            max_tokens=2048,
            context_window=8000
        ),
        ModelInfo(
            short_name="gpt-3.5-turbo",
            full_path="openai/gpt-3.5-turbo",
            provider="OpenAI",
            description="OpenAI's fast GPT-3.5 - good for quick generation",
            max_tokens=2048,
            context_window=4000
        ),
        ModelInfo(
            short_name="claude-3-opus",
            full_path="anthropic/claude-3-opus",
            provider="Anthropic",
            description="Claude 3 Opus - most capable Claude model",
            max_tokens=4096,
            context_window=200000
        ),
        ModelInfo(
            short_name="claude-3-sonnet",
            full_path="anthropic/claude-3-sonnet",
            provider="Anthropic",
            description="Claude 3 Sonnet - balanced Claude model",
            max_tokens=4096,
            context_window=200000
        ),
        ModelInfo(
            short_name="claude-3-haiku",
            full_path="anthropic/claude-3-haiku",
            provider="Anthropic",
            description="Claude 3 Haiku - fast Claude model",
            max_tokens=1024,
            context_window=200000
        ),
        ModelInfo(
            short_name="mixtral-8x22b",
            full_path="mistralai/mixtral-8x22b-instruct",
            provider="Mistral",
            description="Mistral's powerful mixture-of-experts model",
            max_tokens=4096,
            context_window=65000
        ),
        ModelInfo(
            short_name="llama-2-70b",
            full_path="meta-llama/llama-2-70b-chat",
            provider="Meta",
            description="Meta's Llama 2 70B - open-source model",
            max_tokens=2048,
            context_window=4000
        ),
    ],
    "openai": [
        ModelInfo(
            short_name="gpt-4o-mini",
            full_path="gpt-4o-mini",
            provider="OpenAI",
            description="OpenAI's latest mini model - fast and capable",
            recommended=True,
            max_tokens=2048,
            context_window=8000
        ),
        ModelInfo(
            short_name="gpt-4-turbo",
            full_path="gpt-4-turbo-preview",
            provider="OpenAI",
            description="OpenAI's GPT-4 Turbo variant",
            max_tokens=4096,
            context_window=128000
        ),
        ModelInfo(
            short_name="gpt-4",
            full_path="gpt-4",
            provider="OpenAI",
            description="OpenAI's original GPT-4",
            max_tokens=2048,
            context_window=8000
        ),
        ModelInfo(
            short_name="gpt-3.5-turbo",
            full_path="gpt-3.5-turbo",
            provider="OpenAI",
            description="OpenAI's fast GPT-3.5",
            max_tokens=2048,
            context_window=4000
        ),
    ]
}


def get_models_by_provider(provider: str) -> List[ModelInfo]:
    """Get all available models for a specific provider.
    
    Args:
        provider: The provider name ('openrouter' or 'openai')
        
    Returns:
        List of ModelInfo objects for that provider
    """
    return AVAILABLE_MODELS.get(provider, [])


def get_recommended_models() -> Dict[str, ModelInfo]:
    """Get recommended models for each provider.
    
    Returns:
        Dictionary mapping provider to recommended ModelInfo
    """
    recommended = {}
    for provider, models in AVAILABLE_MODELS.items():
        for model in models:
            if model.recommended:
                recommended[provider] = model
                break
    return recommended


def get_model_info(model_name: str, provider: str) -> ModelInfo:
    """Get information about a specific model.
    
    Args:
        model_name: Short name of the model
        provider: Provider name
        
    Returns:
        ModelInfo object for the model
        
    Raises:
        ValueError: If model not found
    """
    models = get_models_by_provider(provider)
    for model in models:
        if model.short_name == model_name:
            return model
    raise ValueError(f"Model '{model_name}' not found for provider '{provider}'")


def format_model_list(provider: str) -> str:
    """Format available models for display.
    
    Args:
        provider: Provider name
        
    Returns:
        Formatted string listing available models
    """
    models = get_models_by_provider(provider)
    if not models:
        return f"No models available for provider '{provider}'"
    
    lines = [f"\n=== Available models for {provider} ===\n"]
    for model in models:
        recommended_marker = " ⭐ RECOMMENDED" if model.recommended else ""
        lines.append(
            f"• {model.short_name}{recommended_marker}\n"
            f"  Provider: {model.provider}\n"
            f"  Description: {model.description}\n"
            f"  Max tokens: {model.max_tokens} | Context: {model.context_window}\n"
        )
    
    return "\n".join(lines)


def get_model_recommendations(use_case: str) -> List[Tuple[str, str]]:
    """Get model recommendations for a specific use case.
    
    Args:
        use_case: Type of use case ('story', 'speed', 'quality', 'budget')
        
    Returns:
        List of (model_short_name, reason) tuples
    """
    recommendations = []
    
    if use_case == "story":
        # Best for story generation
        recommendations = [
            ("deepseek-v3", "Excellent for creative writing and narrative generation"),
            ("gpt-4-turbo", "Very capable for complex storytelling"),
            ("claude-3-opus", "Strong narrative consistency"),
        ]
    elif use_case == "speed":
        # Fastest models
        recommendations = [
            ("gpt-3.5-turbo", "Fastest generation with acceptable quality"),
            ("deepseek-chat", "Fast Deepseek variant"),
            ("claude-3-haiku", "Fast Claude model"),
        ]
    elif use_case == "quality":
        # Best quality
        recommendations = [
            ("gpt-4-turbo", "Highest quality responses"),
            ("claude-3-opus", "Most capable Claude"),
            ("deepseek-v3", "Latest cutting-edge model"),
        ]
    elif use_case == "budget":
        # Most cost-effective
        recommendations = [
            ("deepseek-v3", "Very cost-effective with high quality"),
            ("gpt-3.5-turbo", "Budget-friendly OpenAI option"),
            ("claude-3-haiku", "Cheap Claude option"),
        ]
    
    return recommendations
