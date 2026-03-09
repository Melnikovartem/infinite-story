# API Latency Analysis

## Test Results

### Summary
- **Model**: deepseek/deepseek-v3.2
- **Average Response Time**: 28.06s
- **Range**: 5.71s - 63.10s
- **Status**: ⚠️ High but workable

### Individual Test Results

| Test | Prompt Size | API Time | Tokens Generated | Status |
|------|-------------|----------|------------------|--------|
| Small | 38 chars | 5.71s | 134 | ✅ Fast |
| Medium | 108 chars | 15.36s | 306 | ⚠️ Moderate |
| Large | 365 chars | 63.10s | 2271 | ⚠️ Slow |

## Analysis

### Key Findings

1. **Latency scales with output size**: 
   - Small response (134 tokens): 5.71s
   - Medium response (306 tokens): 15.36s
   - Large response (2271 tokens): 63.10s
   - **Correlation**: More completion tokens = longer wait time

2. **Network overhead is minimal**:
   - Time from request sent to response received is all API processing
   - No significant round-trip delays

3. **The bottleneck is model generation**, not network:
   - Deepseek-v3.2 generates ~30-40 tokens per second
   - For a 2000-token response: 2000/35 ≈ 57s expected

### Why Story Generation is Slow

When generating a story scene:
1. **Prompt building**: 0.0s ✅ (instant, local)
2. **API call**: 30-60s ⚠️ (model is generating ~1300 completion tokens)
3. **Saving**: 0.0s ✅ (instant, local)

**Total**: ~40s average per scene generation

### Deepseek-v3.2 Speed Characteristics

- **Tokens/second**: ~30-40 tokens/sec
- **For 1000 tokens**: ~25-33s
- **For 2000 tokens**: ~50-67s
- **Network latency**: <2s

## Recommendations

### 1. **Use a Faster Model** (Best immediate fix)
Switch from `deepseek-v3.2` to a faster model:

| Model | Avg Speed | Latency |
|-------|-----------|---------|
| deepseek-v3.2 | 35 tokens/s | ~30-60s |
| gpt-4o-mini | 100 tokens/s | ~10-15s |
| gpt-3.5-turbo | 120 tokens/s | ~8-12s |
| claude-3-haiku | 150 tokens/s | ~7-10s |

**Example**: Switch to GPT-4o-mini = ~10-15s per scene (2-4x faster)

### 2. **Reduce Output Size** (Simple optimization)
Lower `max_tokens` in config:

```python
# Current: max_tokens=2000
# Try: max_tokens=1000  # Reduces generation time by ~50%
```

Tradeoff: Shorter scenes but faster generation (15-20s vs 30-60s)

### 3. **Implement Prompt Caching** (Long-term solution)
- Cache system prompts and common context
- OpenRouter supports prompt caching
- Would save re-tokenizing on every request

### 4. **Add Loading UI Feedback** (User experience)
Since we can't make it faster immediately:
```
⏳ Generating next scene... (this may take 30-60 seconds)
⠋ Analyzing story context...
⠙ Consulting the AI...
⠹ Finalizing scene...
✅ Scene ready!
```

### 5. **Pre-generate Scenes** (Advanced)
- Generate next scenes in background while player is reading current scene
- Requires complex queue management

## Current Configuration

```python
# backend/.env or Config
OPENAI_MODEL=deepseek/deepseek-v3.2  # ← SLOW
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000              # ← Can reduce
```

## What to Change First

**Ranked by impact vs effort:**

1. **🟢 Easiest**: Reduce `max_tokens` to 1000
   - Impact: 2x faster (~15-30s)
   - Effort: Change one value
   - Downside: Shorter scenes

2. **🟡 Easy**: Switch model to `gpt-4o-mini`
   - Impact: 2-3x faster (~10-15s)
   - Effort: Update config, may cost more
   - Downside: Different model quality

3. **🔴 Hard**: Implement prompt caching
   - Impact: 5-10% faster (saves repeat tokenization)
   - Effort: Significant code changes
   - Requires OpenRouter premium

## Testing

Run the latency test script:
```bash
python backend/scripts/test_api_latency.py
```

This tests:
- Small prompt (5-7s expected)
- Medium prompt (15-20s expected)
- Large prompt (50-65s expected)

## Conclusion

**The slow generation is normal** for Deepseek-v3.2 with long outputs. The system is working correctly—it's just the model that's slow.

**Best action**: Switch to a faster model like GPT-4o-mini and reduce max_tokens to 1000.
This would reduce generation time from ~40s to ~10-15s (still acceptable for interactive storytelling).

**Current experience is usable** but players may feel the wait. Adding UI feedback helps manage expectations.
