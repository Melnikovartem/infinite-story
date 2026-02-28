"""Model selection and fallback system for OpenRouter API.

This module provides utilities to:
1. Fetch available models from OpenRouter
2. Select models based on pricing (cheapest first)
3. Validate if a requested model is available
4. Provide automatic fallback to a cheaper model if requested model fails
"""

import httpx
import logging
from typing import Optional, Dict, List, Tuple
from functools import lru_cache

logger = logging.getLogger("infinite_story.utils.model_selector")


class ModelSelector:
    """Manages model selection and fallback for OpenRouter API."""
    
    # Fallback order: prefer cheapest reliable models
    FALLBACK_MODELS = [
        "deepseek/deepseek-v3.2",  # Very cheap, good quality
        "deepseek/deepseek-chat-v3.1",  # Cheapest deepseek
        "anthropic/claude-3-haiku",  # Reliable, still cheap
        "openai/gpt-3.5-turbo",  # Well-known, decent price
    ]
    
    def __init__(self, api_key: str):
        """Initialize the model selector with OpenRouter API key.
        
        Args:
            api_key: OpenRouter API key
        """
        self.api_key = api_key
        self._models_cache: Optional[Dict] = None
    
    def _fetch_models(self) -> Dict[str, Dict]:
        """Fetch available models from OpenRouter API.
        
        Returns:
            Dictionary mapping model IDs to model info
        """
        try:
            response = httpx.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch models: {response.status_code}")
                return {}
            
            data = response.json()
            models = data.get("data", [])
            
            # Create a dictionary mapping model IDs to model info
            model_dict = {}
            for model in models:
                model_dict[model["id"]] = {
                    "id": model["id"],
                    "name": model.get("name", ""),
                    "pricing": model.get("pricing", {}),
                    "context_length": model.get("context_length", 0),
                }
            
            logger.info(f"Fetched {len(model_dict)} available models from OpenRouter")
            return model_dict
        
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return {}
    
    def get_available_models(self) -> Dict[str, Dict]:
        """Get cached list of available models.
        
        Returns:
            Dictionary mapping model IDs to model info
        """
        if self._models_cache is None:
            self._models_cache = self._fetch_models()
        return self._models_cache
    
    def is_model_available(self, model_id: str) -> bool:
        """Check if a specific model is available on OpenRouter.
        
        Args:
            model_id: Model ID to check
            
        Returns:
            True if model is available, False otherwise
        """
        models = self.get_available_models()
        return model_id in models
    
    def get_model_price(self, model_id: str) -> Tuple[float, float]:
        """Get the pricing for a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Tuple of (prompt_price, completion_price), or (float('inf'), float('inf')) if not found
        """
        models = self.get_available_models()
        if model_id not in models:
            return float('inf'), float('inf')
        
        pricing = models[model_id].get("pricing", {})
        prompt = float(pricing.get("prompt", float('inf')))
        completion = float(pricing.get("completion", float('inf')))
        
        return prompt, completion
    
    def get_cheapest_model(self, candidates: Optional[List[str]] = None) -> Optional[str]:
        """Find the cheapest available model from a list of candidates.
        
        Args:
            candidates: List of model IDs to choose from. If None, uses FALLBACK_MODELS.
            
        Returns:
            The cheapest available model ID, or None if none are available
        """
        to_check = candidates or self.FALLBACK_MODELS
        models = self.get_available_models()
        
        if not models:
            logger.warning("No models available from OpenRouter")
            return None
        
        # Filter to available models and sort by total cost
        available_with_price = []
        for model_id in to_check:
            if model_id in models:
                prompt_price, completion_price = self.get_model_price(model_id)
                # Use average cost as estimate (more tokens tend to be in completion)
                avg_cost = (prompt_price + completion_price) / 2
                available_with_price.append((model_id, avg_cost))
        
        if not available_with_price:
            logger.warning(f"None of the candidate models are available: {to_check}")
            return None
        
        # Sort by price and return cheapest
        available_with_price.sort(key=lambda x: x[1])
        cheapest = available_with_price[0][0]
        prompt_price, completion_price = self.get_model_price(cheapest)
        
        logger.info(f"Selected cheapest model: {cheapest} (prompt: ${prompt_price}, completion: ${completion_price})")
        return cheapest
    
    def validate_and_fallback(self, requested_model: str) -> str:
        """Validate a requested model and fallback to cheapest if not available.
        
        Args:
            requested_model: The model the user requested
            
        Returns:
            Either the requested model (if available) or a fallback model
            
        Raises:
            ValueError: If no models are available at all
        """
        models = self.get_available_models()
        
        if not models:
            raise ValueError(
                "No models available from OpenRouter. Check your API key and internet connection."
            )
        
        # Check if requested model is available
        if self.is_model_available(requested_model):
            logger.info(f"Using requested model: {requested_model}")
            return requested_model
        
        logger.warning(f"Requested model '{requested_model}' not available, falling back to cheapest")
        
        # Try our fallback order first
        fallback = self.get_cheapest_model()
        if fallback:
            logger.info(f"Fallback model selected: {fallback}")
            return fallback
        
        # Last resort: just pick any available model
        if models:
            last_resort = list(models.keys())[0]
            logger.warning(f"Using last resort model: {last_resort}")
            return last_resort
        
        raise ValueError("No models available from OpenRouter")


def get_model_selector(api_key: str) -> ModelSelector:
    """Factory function to get a ModelSelector instance.
    
    Args:
        api_key: OpenRouter API key
        
    Returns:
        ModelSelector instance
    """
    return ModelSelector(api_key)
