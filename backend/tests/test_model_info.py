"""Tests for model information and recommendations."""

import pytest
from app.utils.model_info import (
    ModelInfo,
    get_models_by_provider,
    get_recommended_models,
    get_model_info,
    format_model_list,
    get_model_recommendations,
    AVAILABLE_MODELS
)


class TestModelInfo:
    """Tests for ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test creating ModelInfo instance."""
        model = ModelInfo(
            short_name="test-model",
            full_path="provider/test-model",
            provider="TestProvider",
            description="A test model",
            recommended=True,
            max_tokens=2000,
            context_window=4000
        )
        
        assert model.short_name == "test-model"
        assert model.full_path == "provider/test-model"
        assert model.provider == "TestProvider"
        assert model.recommended is True
        assert model.max_tokens == 2000
    
    def test_model_info_defaults(self):
        """Test ModelInfo default values."""
        model = ModelInfo(
            short_name="model",
            full_path="provider/model",
            provider="Provider",
            description="Description"
        )
        
        assert model.recommended is False
        assert model.max_tokens == 2000
        assert model.context_window == 4000


class TestModelProvider:
    """Tests for model provider functionality."""
    
    def test_get_openrouter_models(self):
        """Test retrieving OpenRouter models."""
        models = get_models_by_provider("openrouter")
        
        assert isinstance(models, list)
        assert len(models) > 0
        
        # Check that models have required attributes
        for model in models:
            assert hasattr(model, 'short_name')
            assert hasattr(model, 'provider')
            assert hasattr(model, 'description')
    
    def test_get_openai_models(self):
        """Test retrieving OpenAI models."""
        models = get_models_by_provider("openai")
        
        assert isinstance(models, list)
        assert len(models) > 0
    
    def test_get_invalid_provider(self):
        """Test retrieving models for invalid provider."""
        models = get_models_by_provider("invalid")
        assert models == []
    
    def test_deepseek_v3_in_openrouter(self):
        """Test that deepseek-v3 is in OpenRouter models."""
        models = get_models_by_provider("openrouter")
        model_names = [m.short_name for m in models]
        
        assert "deepseek-v3" in model_names
    
    def test_deepseek_v3_recommended(self):
        """Test that deepseek-v3 is marked as recommended."""
        models = get_models_by_provider("openrouter")
        deepseek = next((m for m in models if m.short_name == "deepseek-v3"), None)
        
        assert deepseek is not None
        assert deepseek.recommended is True


class TestRecommendations:
    """Tests for model recommendations."""
    
    def test_get_recommended_models(self):
        """Test getting recommended models."""
        recommended = get_recommended_models()
        
        assert isinstance(recommended, dict)
        assert "openrouter" in recommended
        assert "openai" in recommended
    
    def test_openrouter_recommended(self):
        """Test that OpenRouter has a recommended model."""
        recommended = get_recommended_models()
        
        assert "openrouter" in recommended
        openrouter_model = recommended["openrouter"]
        assert openrouter_model.recommended is True
        assert openrouter_model.provider == "Deepseek"
    
    def test_openai_recommended(self):
        """Test that OpenAI has a recommended model."""
        recommended = get_recommended_models()
        
        assert "openai" in recommended
        openai_model = recommended["openai"]
        assert openai_model.recommended is True
    
    def test_story_recommendations(self):
        """Test getting recommendations for story use case."""
        recs = get_model_recommendations("story")
        
        assert isinstance(recs, list)
        assert len(recs) > 0
        
        # Each recommendation is a tuple of (model_name, reason)
        for model_name, reason in recs:
            assert isinstance(model_name, str)
            assert isinstance(reason, str)
    
    def test_speed_recommendations(self):
        """Test getting recommendations for speed use case."""
        recs = get_model_recommendations("speed")
        
        assert len(recs) > 0
        model_names = [name for name, _ in recs]
        
        # Speed recommendations should include fast models
        assert any("turbo" in name or "haiku" in name for name in model_names)
    
    def test_quality_recommendations(self):
        """Test getting recommendations for quality use case."""
        recs = get_model_recommendations("quality")
        
        assert len(recs) > 0
        model_names = [name for name, _ in recs]
        
        # Quality should include capable models
        assert any("gpt-4" in name or "opus" in name or "v3" in name for name in model_names)
    
    def test_budget_recommendations(self):
        """Test getting recommendations for budget use case."""
        recs = get_model_recommendations("budget")
        
        assert len(recs) > 0
        model_names = [name for name, _ in recs]
        
        # Budget should include cost-effective models
        assert "deepseek-v3" in model_names or "gpt-3.5-turbo" in model_names
    
    def test_invalid_use_case(self):
        """Test handling of invalid use case."""
        recs = get_model_recommendations("invalid")
        assert recs == []


class TestGetModelInfo:
    """Tests for getting specific model information."""
    
    def test_get_deepseek_v3_info(self):
        """Test getting deepseek-v3 information."""
        model = get_model_info("deepseek-v3", "openrouter")
        
        assert model.short_name == "deepseek-v3"
        assert model.provider == "Deepseek"
        assert "story" in model.description.lower() or "creative" in model.description.lower()
    
    def test_get_gpt4_turbo_info(self):
        """Test getting GPT-4 Turbo information."""
        model = get_model_info("gpt-4-turbo", "openrouter")
        
        assert model.short_name == "gpt-4-turbo"
        assert model.provider == "OpenAI"
    
    def test_model_not_found(self):
        """Test error when model not found."""
        with pytest.raises(ValueError):
            get_model_info("nonexistent", "openrouter")
    
    def test_provider_mismatch(self):
        """Test error when model not in provider."""
        with pytest.raises(ValueError):
            # deepseek-v3 only in openrouter, not in openai
            get_model_info("deepseek-v3", "openai")
    
    def test_model_info_accuracy(self):
        """Test that model info contains accurate data."""
        model = get_model_info("deepseek-v3", "openrouter")
        
        assert isinstance(model.max_tokens, int)
        assert isinstance(model.context_window, int)
        assert model.max_tokens > 0
        assert model.context_window > 0
        assert model.context_window >= model.max_tokens


class TestFormatting:
    """Tests for model list formatting."""
    
    def test_format_model_list_openrouter(self):
        """Test formatting OpenRouter model list."""
        formatted = format_model_list("openrouter")
        
        assert isinstance(formatted, str)
        assert "deepseek-v3" in formatted
        assert "RECOMMENDED" in formatted or "⭐" in formatted
    
    def test_format_model_list_openai(self):
        """Test formatting OpenAI model list."""
        formatted = format_model_list("openai")
        
        assert isinstance(formatted, str)
        assert "gpt" in formatted.lower()
    
    def test_format_model_list_invalid_provider(self):
        """Test formatting for invalid provider."""
        formatted = format_model_list("invalid")
        
        assert "No models available" in formatted
    
    def test_format_contains_model_details(self):
        """Test that formatted output includes model details."""
        formatted = format_model_list("openrouter")
        
        # Should include provider, description, and specs
        assert "Provider:" in formatted
        assert "Description:" in formatted or "description" in formatted.lower()
        assert "Max tokens:" in formatted or "max tokens" in formatted.lower()


class TestAvailableModels:
    """Tests for available models data."""
    
    def test_available_models_structure(self):
        """Test structure of AVAILABLE_MODELS."""
        assert isinstance(AVAILABLE_MODELS, dict)
        assert "openrouter" in AVAILABLE_MODELS
        assert "openai" in AVAILABLE_MODELS
    
    def test_models_have_required_fields(self):
        """Test that all models have required fields."""
        for provider, models in AVAILABLE_MODELS.items():
            for model in models:
                assert isinstance(model, ModelInfo)
                assert model.short_name
                assert model.full_path
                assert model.provider
                assert model.description
    
    def test_minimum_models_available(self):
        """Test that minimum number of models are available."""
        total_models = sum(len(models) for models in AVAILABLE_MODELS.values())
        assert total_models >= 10, "Should have at least 10 models"
    
    def test_recommended_models_exist(self):
        """Test that at least one model per provider is recommended."""
        for provider, models in AVAILABLE_MODELS.items():
            recommended = [m for m in models if m.recommended]
            assert len(recommended) > 0, f"Provider {provider} should have recommended models"


class TestModelCompatibility:
    """Tests for model compatibility and consistency."""
    
    def test_all_deepseek_models_available(self):
        """Test that all Deepseek models are available."""
        models = get_models_by_provider("openrouter")
        deepseek_models = [m for m in models if m.provider == "Deepseek"]
        
        assert len(deepseek_models) >= 2  # At least v3 and chat
    
    def test_all_claude_models_available(self):
        """Test that all Claude models are available."""
        models = get_models_by_provider("openrouter")
        claude_models = [m for m in models if m.provider == "Anthropic"]
        
        assert len(claude_models) >= 3  # opus, sonnet, haiku
    
    def test_model_costs_are_reasonable(self):
        """Test that model descriptions don't promise unrealistic costs."""
        models = get_models_by_provider("openrouter")
        
        for model in models:
            # Just verify description exists and is reasonable
            assert len(model.description) > 10
            assert len(model.description) < 500
    
    def test_context_windows_are_reasonable(self):
        """Test that context windows are reasonable values."""
        models = get_models_by_provider("openrouter")
        
        for model in models:
            # Context windows should be reasonable
            assert model.context_window >= 4000  # At least 4K
            assert model.context_window <= 200000  # Max 200K (Claude)
            assert model.max_tokens <= model.context_window
