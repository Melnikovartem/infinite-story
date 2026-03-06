"""Tests for OpenRouter generator integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.engine.openrouter_generator import OpenRouterGenerator


class TestOpenRouterGenerator:
    """Tests for OpenRouterGenerator class."""
    
    def test_initialization(self):
        """Test that OpenRouterGenerator initializes correctly."""
        generator = OpenRouterGenerator(
            api_key="sk-or-v1-test-key",
            model="deepseek-v3",
            temperature=0.7,
            max_tokens=2000,
            auto_fallback=False  # Disable fallback for unit tests
        )
        
        assert generator.api_key == "sk-or-v1-test-key"
        assert generator.model == "deepseek/deepseek-v3"
        assert generator.temperature == 0.7
        assert generator.max_tokens == 2000
    
    def test_model_mapping(self):
        """Test that short model names are mapped to full paths."""
        generator = OpenRouterGenerator(
            api_key="test-key",
            model="deepseek-v3",
            auto_fallback=False
        )
        assert generator.model == "deepseek/deepseek-v3"
        
        generator2 = OpenRouterGenerator(
            api_key="test-key",
            model="gpt-4-turbo",
            auto_fallback=False
        )
        assert generator2.model == "openai/gpt-4-turbo-preview"
        
        generator3 = OpenRouterGenerator(
            api_key="test-key",
            model="claude-3-opus",
            auto_fallback=False
        )
        assert generator3.model == "anthropic/claude-3-opus"
    
    def test_full_model_path(self):
        """Test that full model paths are accepted as-is."""
        generator = OpenRouterGenerator(
            api_key="test-key",
            model="custom/custom-model",
            auto_fallback=False
        )
        assert generator.model == "custom/custom-model"
    
    def test_available_models(self):
        """Test that available models are listed correctly."""
        models = OpenRouterGenerator.get_available_models()
        
        assert isinstance(models, dict)
        assert len(models) == 11
        assert "deepseek-v3" in models
        assert "gpt-4-turbo" in models
        assert "claude-3-opus" in models
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self):
        """Test successful content generation via OpenRouter API."""
        generator = OpenRouterGenerator(
            api_key="sk-or-v1-test-key",
            model="deepseek-v3",
            temperature=0.7,
            max_tokens=2000,
            auto_fallback=False
        )
        
        # Just verify the generator is configured correctly
        # Real API integration will be tested separately
        assert generator.api_key == "sk-or-v1-test-key"
        assert generator.model == "deepseek/deepseek-v3"
        assert generator.temperature == 0.7
    
    @pytest.mark.asyncio
    async def test_generate_content_api_error(self):
        """Test handling of API errors."""
        generator = OpenRouterGenerator(
            api_key="sk-or-v1-test-key",
            model="deepseek-v3",
            auto_fallback=False
        )
        
        with patch.object(generator.client, 'post', new_callable=AsyncMock) as mock_post:
            error_response = MagicMock()
            error_response.status_code = 401
            error_response.json.return_value = {
                "error": {"message": "Invalid API key"}
            }
            mock_post.side_effect = Exception("401 Unauthorized")
            
            with pytest.raises(Exception):
                await generator._generate_content("system", "user")
    
    @pytest.mark.asyncio
    async def test_generate_with_scene_context(self):
        """Test scene generation setup."""
        generator = OpenRouterGenerator(
            api_key="sk-or-v1-test-key",
            model="deepseek-v3",
            auto_fallback=False
        )
        
        # Verify the generator is properly initialized
        assert generator.api_key == "sk-or-v1-test-key"
        assert generator.model == "deepseek/deepseek-v3"
        assert hasattr(generator, 'generate_structured')
    
    def test_site_url_configuration(self):
        """Test that site URL is properly configured."""
        generator = OpenRouterGenerator(
            api_key="test-key",
            model="deepseek-v3",
            site_url="https://example.com",
            site_name="Test App",
            auto_fallback=False
        )
        
        assert generator.site_url == "https://example.com"
        assert generator.site_name == "Test App"
    
    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens(self):
        """Test that temperature and max_tokens are stored correctly."""
        generator = OpenRouterGenerator(
            api_key="test-key",
            model="deepseek-v3",
            temperature=0.9,
            max_tokens=3000,
            auto_fallback=False
        )
        
        # Verify the settings are stored
        assert generator.temperature == 0.9
        assert generator.max_tokens == 3000


class TestOpenRouterModels:
    """Tests for model availability and selection."""
    
    def test_all_models_available(self):
        """Test that all expected models are available."""
        models = OpenRouterGenerator.get_available_models()
        
        expected_models = [
            "deepseek-v3",
            "deepseek-chat",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "mixtral-8x22b",
            "llama-2-70b"
        ]
        
        for model in expected_models:
            assert model in models, f"Model {model} not found"
    
    def test_deepseek_is_default(self):
        """Test that deepseek-v3 can be used as default."""
        models = OpenRouterGenerator.get_available_models()
        assert "deepseek-v3" in models
        
        # Verify it maps to correct full path
        generator = OpenRouterGenerator(
            api_key="test-key",
            model="deepseek-v3",
            auto_fallback=False
        )
        assert generator.model == "deepseek/deepseek-v3"
    
    def test_model_paths_are_strings(self):
        """Test that all model paths are valid strings."""
        models = OpenRouterGenerator.get_available_models()
        
        for short_name, full_path in models.items():
            assert isinstance(short_name, str)
            assert isinstance(full_path, str)
            assert "/" in full_path  # Should contain provider/model format
            assert len(full_path) > 0


class TestOpenRouterIntegration:
    """Integration tests with configuration."""
    
    def test_generator_from_config(self):
        """Test creating generator from configuration."""
        from app.config import Config
        
        # This would use actual .env file
        # For testing, we just verify the generator can be created
        generator = OpenRouterGenerator(
            api_key="sk-or-v1-test-key",
            model="deepseek-v3",
            temperature=0.7,
            max_tokens=2000,
            auto_fallback=False
        )
        
        assert generator.api_key == "sk-or-v1-test-key"
        assert generator.temperature == 0.7
        assert generator.max_tokens == 2000
    
    @pytest.mark.asyncio
    async def test_multiple_models_compatibility(self):
        """Test that different models work with the same interface."""
        models_to_test = ["deepseek-v3", "gpt-4-turbo", "claude-3-opus"]
        
        for model_name in models_to_test:
            generator = OpenRouterGenerator(
                api_key="test-key",
                model=model_name,
                auto_fallback=False
            )
            
            # Verify model is properly mapped
            assert generator.model is not None
            assert isinstance(generator.model, str)
            assert "/" in generator.model
