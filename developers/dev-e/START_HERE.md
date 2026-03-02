# Welcome, Developer E!

**Epic:** Generation Pipeline (E1)  
**Duration:** 2 weeks  
**Your Role:** Mid-Senior Engineer, supporting Epic Lead D

---

## Your Mission

You're completing the generation pipeline. While Dev-D builds the context system, you'll:

1. **E1-3** (2 days): Enhance Generator Interface
   - Update abstract `TextGenerator.generate()` signature
   - Add response validation (required fields per context_type)
   - Implement graceful fallback on validation failure
   - Handle episode context and change_notes fields

2. **E1-4** (3 days): Segment Generation Implementation
   - Implement `_generate_segment()` method (called by E1-2)
   - Create StorySegment with all fields
   - Create 2 outgoing StoryChoice objects
   - Save everything to disk
   - Error handling, logging

You work closely with Dev-D. Coordinate daily.

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_1_GENERATION.md** (focus on E1-3 & E1-4)
3. **Understand** how Dev-D's context builder works (E1-1)

---

## Your Tasks

### E1-3: Enhanced Generator Interface (2 days)

**File:** `backend/app/engine/generator.py` (MODIFY)

Update the abstract base class to:

```python
async def generate(
    self,
    context_type: str,  # "scene", "recap", "arc_context"
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate content based on context"""
```

Add validation:
- For "scene": must have text_blocks, suggested_choices
- For "recap": must have title, summary, key_themes
- etc.

Add `generate_with_fallback()`:
- Tries generation
- Validates response
- On failure, retries with adjusted context
- On repeated failure, returns synthetic response (minimal valid)

See `EPIC_1_GENERATION.md` section "E1-3" for full code.

**Acceptance Criteria:**
- [ ] `generate()` signature updated
- [ ] Response validation for all context types
- [ ] `generate_with_fallback()` implemented
- [ ] Synthetic fallback responses valid
- [ ] Unit tests (4+)

### E1-4: Segment Generation Implementation (3 days)

**File:** `backend/app/engine/story_runner.py` (ENHANCE, called by E1-2)

Implement `_generate_segment()` which:

1. Build prompt from context (very detailed)
2. Call `generator.generate(context_type="scene", context=...)`
3. Create StorySegment with all fields
4. Create 2 StoryChoice objects (outgoing)
5. Save segment and choices to disk
6. Return segment
7. Handle errors gracefully

See `EPIC_1_GENERATION.md` section "E1-4" for code.

**Acceptance Criteria:**
- [ ] `_generate_segment()` creates valid Segment
- [ ] All fields populated (episode, pacing, character_states, etc.)
- [ ] 2 outgoing choices created
- [ ] Save to disk working
- [ ] Error handling + logging
- [ ] Unit tests (5+)
- [ ] Integration tests with E1-1

---

## Collaboration

- **Daily standup** with Dev-D
- **Ask Dev-D** for questions on context building
- **Code reviews** from Dev-D

---

## Key Concepts

### Generation Context Types

```python
context_type = "scene"           # E1 uses this
context_type = "recap"           # E2 uses this
context_type = "arc_context"     # E2 uses this
```

Each has different required fields. Validate strictly.

### Response Validation

```python
required_fields = {
    'scene': ['text_blocks', 'suggested_choices', 'character_states'],
    'recap': ['title', 'summary', 'key_themes'],
}

# Validate response has all required fields
for field in required_fields[context_type]:
    if field not in response:
        raise ValidationError(f"Missing {field}")
```

### Graceful Fallback

```python
try:
    response = await self.generate(...)
    self._validate_response(response)
    return response
except ValidationError:
    # Retry with adjusted context
    # If still fails, return synthetic response
    return self._synthetic_fallback()
```

---

## Key Files

```
backend/app/engine/
  ├── generator.py          ← YOU ENHANCE (E1-3)
  ├── story_runner.py       ← Dev-D adds E1-2, you add to E1-4
  ├── segment_context_builder.py ← Dev-D creates (E1-1)
  ├── openai_generator.py   ← Concrete implementation
  └── openrouter_generator.py ← Another implementation
```

---

## Commits

```bash
git commit -m "E1-3: enhance generator interface with validation and fallbacks"
git commit -m "E1-4: implement segment generation with full context integration"
```

---

## Next Action

→ Open `EPIC_1_GENERATION.md` section E1-3. Start with Generator interface.

Dev-D's context will flow through your generator. Build it solid! ⚡
