# OpenRouter Integration Guide

This guide explains how to use the Infinite Story Engine with OpenRouter, which provides access to multiple AI models including the recommended Deepseek v3.

## Overview

The story engine now supports two AI providers:
- **OpenRouter** (recommended) - Access to 10+ models including Deepseek v3, GPT-4, Claude, and more
- **OpenAI** (legacy) - Direct OpenAI API access

### Why OpenRouter?

✅ **Access to multiple models** - Switch between providers without code changes
✅ **Better pricing** - Often cheaper than direct API calls
✅ **Deepseek v3** - Excellent for creative writing and story generation
✅ **Unified API** - Same endpoint for all providers
✅ **Easy switching** - Change models with a single config change

## Setup Instructions

### 1. Get Your OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Go to your account settings and copy your API key
4. The key will look like: `sk-or-v1-...`

### 2. Configure Your `.env` File

Update `backend/.env`:

```bash
# Provider selection
AI_PROVIDER=openrouter

# Your OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Model selection (see available models below)
AI_MODEL=deepseek-v3

# Optional: Help OpenRouter identify your app
OPENROUTER_SITE_URL=https://your-app-url.com
OPENROUTER_SITE_NAME=Your App Name

# Generation settings
AI_TEMPERATURE=0.7        # 0.0-2.0 (higher = more creative)
AI_MAX_TOKENS=2000        # Maximum response length
```

### 3. Verify Configuration

```bash
cd backend
source venv/bin/activate
python -c "from app.config import Config; c = Config.load(); print(f'Provider: {c.generator.provider}'); print(f'Model: {c.generator.model}')"
```

Expected output:
```
Provider: openrouter
Model: deepseek-v3
```

## Available Models

### Recommended for Story Generation

```
deepseek-v3 ⭐ (DEFAULT)
├─ Provider: Deepseek
├─ Type: Latest cutting-edge model
├─ Best for: Creative writing, narrative generation
├─ Max tokens: 4000
├─ Context window: 32,000 tokens
└─ Performance: Excellent quality, reasonable speed
```

### Alternative Models

**Deepseek Models:**
- `deepseek-chat` - Balanced speed/quality variant

**OpenAI Models (via OpenRouter):**
- `gpt-4-turbo` - Most capable, slower
- `gpt-4` - Very capable
- `gpt-3.5-turbo` - Fast, budget-friendly

**Anthropic Models:**
- `claude-3-opus` - Most capable Claude
- `claude-3-sonnet` - Balanced Claude
- `claude-3-haiku` - Fast Claude

**Other Providers:**
- `mixtral-8x22b` - Mistral's powerful model
- `llama-2-70b` - Meta's open-source Llama

### List Available Models

```bash
# Show all available models
python -m app.cli list-models

# Show models for specific provider
python -m app.cli list-models --provider openrouter
python -m app.cli list-models --provider openai

# Get recommendations for a use case
python -m app.cli list-models --use-case story      # Best for storytelling
python -m app.cli list-models --use-case speed      # Fastest models
python -m app.cli list-models --use-case quality    # Best quality
python -m app.cli list-models --use-case budget     # Most cost-effective
```

## Running Stories

### Using OpenRouter

```bash
# Ensure AI_PROVIDER=openrouter in .env

# Run the story engine
./run.sh

# Or directly
cd backend
source venv/bin/activate
python -m app.cli run-story
```

The engine will display which provider and model are being used:
```
Using OpenRouter with model: deepseek-v3
```

### Switching Models

Simply update your `.env` file and restart:

```bash
# In .env
AI_MODEL=gpt-4-turbo

# Run again
./run.sh
```

## Model Recommendations by Use Case

### For Best Story Quality
```
1. deepseek-v3 (recommended)
2. gpt-4-turbo
3. claude-3-opus
```

### For Fastest Generation
```
1. gpt-3.5-turbo
2. deepseek-chat
3. claude-3-haiku
```

### For Best Value
```
1. deepseek-v3 (great quality + affordable)
2. gpt-3.5-turbo
3. claude-3-haiku
```

### For Maximum Context
```
1. claude-3-opus (200K tokens)
2. claude-3-sonnet (200K tokens)
3. gpt-4-turbo (128K tokens)
```

## Configuration Examples

### Example 1: Deepseek v3 (Recommended)
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=deepseek-v3
AI_TEMPERATURE=0.8
```

### Example 2: Fast & Affordable
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1500
```

### Example 3: Maximum Quality
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=gpt-4-turbo
AI_TEMPERATURE=0.9
AI_MAX_TOKENS=4096
```

### Example 4: Multiple Context (Claude)
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
AI_MODEL=claude-3-opus
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=3000
```

## Switching Back to OpenAI

If you want to use OpenAI directly instead of OpenRouter:

```bash
# In .env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-openai-key
AI_MODEL=gpt-4o-mini
```

Then run:
```bash
./run.sh
```

## Troubleshooting

### "OPENROUTER_API_KEY not found"
- Ensure you've set `OPENROUTER_API_KEY` in your `.env` file
- Check the key doesn't have typos
- Make sure `.env` is in the `backend/` directory

### "Model not found"
- Check the model name is correct (see list above)
- Use `python -m app.cli list-models --provider openrouter` to see valid names
- Model names are case-sensitive

### "Rate limit exceeded"
- OpenRouter enforces rate limits based on your account tier
- Free tier has limitations - consider upgrading
- Add delays between requests or wait a moment

### "Invalid JSON response"
- The model may not have generated valid JSON
- Try a different model with `AI_MODEL=gpt-3.5-turbo`
- Increase temperature slightly: `AI_TEMPERATURE=0.8`

### Slow generation
- Switch to a faster model: `AI_MODEL=gpt-3.5-turbo`
- Reduce max tokens: `AI_MAX_TOKENS=1500`
- Try `claude-3-haiku` for speed

## Code Structure

### New Files Added

- **`app/engine/openrouter_generator.py`** - OpenRouter API implementation
- **`app/utils/model_info.py`** - Model information and recommendations
- **`app/cli.py`** (enhanced) - New `list-models` command

### Modified Files

- **`app/config.py`** - Support for provider selection and OpenRouter configuration
- **`.env.example`** - Updated with OpenRouter defaults
- **`backend/.env`** - Your live configuration (already set up with your API key)

## Advanced: Custom Models

To add support for a custom model not in the list:

```python
# In app/utils/model_info.py, add to AVAILABLE_MODELS["openrouter"]:
ModelInfo(
    short_name="my-model",
    full_path="provider/my-model-path",
    provider="MyProvider",
    description="My custom model",
    max_tokens=2000,
    context_window=8000
)
```

Then use it:
```bash
AI_MODEL=my-model
./run.sh
```

## API Rate Limits

OpenRouter uses rate limiting based on your account:

- **Free tier**: Limited requests per minute
- **Pro tier**: Higher limits
- **Enterprise**: Custom limits

Monitor your usage at [OpenRouter Dashboard](https://openrouter.ai/activity)

## Cost Estimation

Pricing varies by model. Generally:

| Model | Cost | Use Case |
|-------|------|----------|
| deepseek-v3 | 💰 Very cheap | Storytelling |
| gpt-3.5-turbo | 💰 Cheap | Speed |
| gpt-4 | 💵 Moderate | Quality |
| claude-3-opus | 💵💵 Expensive | Best quality |

Check current pricing at [OpenRouter Pricing](https://openrouter.ai/docs/models)

## Getting Help

### Documentation
- [OpenRouter API Docs](https://openrouter.ai/docs/api/chat-completions)
- [Deepseek Documentation](https://deepseek.com)
- Infinite Story Engine: See `AGENTS.md` and `IMPLEMENTATION_SUMMARY.md`

### Common Commands

```bash
# Test your configuration
python -c "from app.config import Config; Config.load(); print('✓ Config OK')"

# List all available models
python -m app.cli list-models

# Run a story
./run.sh

# Test generation with a specific story
python -m app.cli test-generation --story-id veil_of_thornreach
```

## Summary

You're all set! The Infinite Story Engine is now configured to use:

✅ **Provider**: OpenRouter
✅ **Model**: Deepseek v3 (excellent for story generation)
✅ **Temperature**: 0.7 (balanced creativity)
✅ **Max Tokens**: 2000 (detailed responses)

Start generating stories:
```bash
./run.sh
```

Enjoy your adventures! 🚀
