# Models Quick Reference

## Currently Configured

```
Provider: OpenRouter
Model: Deepseek v3
Temperature: 0.7
Max Tokens: 2000
API Key: ✓ Configured
```

## Quick Commands

```bash
# List all available models
python -m app.cli list-models

# Get recommendations for story writing
python -m app.cli list-models --use-case story

# Show only OpenRouter models
python -m app.cli list-models --provider openrouter

# Show only OpenAI models
python -m app.cli list-models --provider openai

# Run a story with current config
./run.sh

# Test generation with current config
python -m app.cli test-generation
```

## Switch Models Easily

Edit `backend/.env` and change one line:

```bash
# Try Deepseek (recommended)
AI_MODEL=deepseek-v3

# Try GPT-4 Turbo
AI_MODEL=gpt-4-turbo

# Try Claude 3 Opus
AI_MODEL=claude-3-opus

# Try GPT-3.5 (fast & cheap)
AI_MODEL=gpt-3.5-turbo
```

Then run: `./run.sh`

## Top 3 Models for Storytelling

| Rank | Model | Speed | Quality | Cost |
|------|-------|-------|---------|------|
| 🥇 | deepseek-v3 | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰 |
| 🥈 | gpt-4-turbo | ⚡ | ⭐⭐⭐⭐⭐ | 💵 |
| 🥉 | claude-3-opus | ⚡ | ⭐⭐⭐⭐⭐ | 💵💵 |

## Model Comparison

### Deepseek v3 ⭐ RECOMMENDED
- **Best for**: Story generation, creative writing
- **Speed**: Fast
- **Quality**: Excellent
- **Cost**: Very affordable
- **Context**: 32K tokens
- **Max output**: 4000 tokens

### GPT-4 Turbo
- **Best for**: Complex narratives, high quality
- **Speed**: Moderate
- **Quality**: Excellent
- **Cost**: Moderate
- **Context**: 128K tokens
- **Max output**: 4096 tokens

### Claude 3 Opus
- **Best for**: Long stories, consistency
- **Speed**: Moderate
- **Quality**: Excellent
- **Cost**: Higher
- **Context**: 200K tokens
- **Max output**: 4096 tokens

### GPT-3.5 Turbo
- **Best for**: Quick iteration, budget
- **Speed**: Very Fast
- **Quality**: Good
- **Cost**: Cheap
- **Context**: 4K tokens
- **Max output**: 2048 tokens

### Deepseek Chat
- **Best for**: Fast creative writing
- **Speed**: Very Fast
- **Quality**: Good
- **Cost**: Very affordable
- **Context**: 8K tokens
- **Max output**: 4000 tokens

### Claude 3 Haiku
- **Best for**: Speed-focused, budget
- **Speed**: Fastest
- **Quality**: Good
- **Cost**: Cheap
- **Context**: 200K tokens
- **Max output**: 1024 tokens

## Temperature Settings

Adjust `AI_TEMPERATURE` in `.env`:

```bash
# More deterministic (0.0 = completely deterministic)
AI_TEMPERATURE=0.3

# Balanced (recommended for stories)
AI_TEMPERATURE=0.7

# More creative
AI_TEMPERATURE=0.9

# Very creative
AI_TEMPERATURE=1.2
```

## Max Tokens Settings

Adjust `AI_MAX_TOKENS` in `.env`:

```bash
# Short responses
AI_MAX_TOKENS=1000

# Standard (recommended)
AI_MAX_TOKENS=2000

# Detailed, long scenes
AI_MAX_TOKENS=3000

# Maximum detail
AI_MAX_TOKENS=4000
```

## Recommended Configurations

### Best Quality
```bash
AI_PROVIDER=openrouter
AI_MODEL=gpt-4-turbo
AI_TEMPERATURE=0.8
AI_MAX_TOKENS=3000
```

### Best Speed
```bash
AI_PROVIDER=openrouter
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1500
```

### Best Value (DEFAULT)
```bash
AI_PROVIDER=openrouter
AI_MODEL=deepseek-v3
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
```

### Most Creative
```bash
AI_PROVIDER=openrouter
AI_MODEL=deepseek-v3
AI_TEMPERATURE=0.95
AI_MAX_TOKENS=3000
```

## All Available Models

### OpenRouter (Recommended)
- deepseek-v3 ⭐
- deepseek-chat
- gpt-4-turbo
- gpt-4
- gpt-3.5-turbo
- claude-3-opus
- claude-3-sonnet
- claude-3-haiku
- mixtral-8x22b
- llama-2-70b

### OpenAI (Legacy)
- gpt-4o-mini ⭐
- gpt-4-turbo
- gpt-4
- gpt-3.5-turbo

## Cost Estimation

**Approximate costs per 1000 generation tokens:**

| Model | Cost |
|-------|------|
| deepseek-v3 | $0.001-0.002 |
| gpt-3.5-turbo | $0.002 |
| mixtral-8x22b | $0.005 |
| gpt-4 | $0.015 |
| gpt-4-turbo | $0.03 |
| claude-3-haiku | $0.008 |
| claude-3-sonnet | $0.03 |
| claude-3-opus | $0.15 |

*(Prices may vary - check OpenRouter for current pricing)*

## Troubleshooting

**Q: Stories are too short**
- Increase `AI_MAX_TOKENS=3000`
- Try `AI_TEMPERATURE=0.8`

**Q: Stories are too repetitive**
- Increase `AI_TEMPERATURE=0.9`
- Try a different model

**Q: Generation is too slow**
- Use `AI_MODEL=gpt-3.5-turbo`
- Reduce `AI_MAX_TOKENS=1500`

**Q: Generation is too creative/random**
- Decrease `AI_TEMPERATURE=0.5`
- Try `AI_MODEL=claude-3-sonnet`

**Q: Getting errors about API**
- Check your OpenRouter API key is valid
- Verify rate limits haven't been exceeded
- Try a different model

## Next Steps

1. **Try different models**: Use `AI_MODEL=` to experiment
2. **Adjust temperature**: Fine-tune creativity with `AI_TEMPERATURE`
3. **Monitor costs**: Check your OpenRouter dashboard
4. **Customize prompts**: See `app/engine/generator.py` for system prompts

## Resources

- [OpenRouter Models & Pricing](https://openrouter.ai/docs/models)
- [Full Setup Guide](./OPENROUTER_SETUP.md)
- [Project Documentation](./AGENTS.md)

---

**Current Setup**: ✅ OpenRouter + Deepseek v3
**Ready to generate stories!** 🚀
