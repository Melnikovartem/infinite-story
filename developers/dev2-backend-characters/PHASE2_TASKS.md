# Dev 2: Backend Characters - Phase 2 Integration Tasks

**Timeline**: Days 2-3 of Phase 2
**Priority**: Medium (depends on Dev 1)
**Status**: All Phase 1 work complete, ready for integration

---

## Executive Summary

Phase 2 focuses on **integrating character system into story generation** and **providing character data to frontend**.

**Current Status**:
- ✅ Character avatar system 100% complete
- ✅ Character state tracking 100% complete
- ✅ 51 tests passing
- ❌ Not yet integrated into generation flow
- ❌ Character endpoints not created

---

## Task 2.4: Create Character Data Endpoints (2 hours)

**Starts when Dev 1 has API structure ready**

### Endpoint 1: GET /api/characters/{character_id}

```python
@router.get("/api/characters/{character_id}")
async def get_character(character_id: str, story_id: str):
    """Get character details + state history"""
    # Load character from disk
    # Include full state arc
    # Return with avatar info
    return {
        "character": {
            "id": "eira",
            "name": "Eira",
            "description": "...",
            "avatar_shape": "circle",
            "avatar_color": "#FF6B6B",
            "background": "...",
            "running_status": [
                {
                    "segment_id": "segment_001",
                    "emotion": "concerned",
                    "status": "present",
                    "notes": "Worried about wards"
                },
                ...
            ]
        }
    }
```

### Endpoint 2: GET /api/stories/{story_id}/characters

```python
@router.get("/api/stories/{story_id}/characters")
async def list_story_characters(story_id: str):
    """Get all characters for a story"""
    return {
        "characters": [
            {
                "id": "eira",
                "name": "Eira",
                "avatar_shape": "circle",
                "avatar_color": "#FF6B6B",
                "description": "..."
            },
            ...
        ]
    }
```

### Success Criteria
- ✅ Character data accessible via API
- ✅ Avatar info returned with each character
- ✅ State history available
- ✅ Frontend can display character data

---

## Task 2.5: Integrate into Generation Pipeline (3 hours)

**Waits for Dev 1 to implement POST /api/segments/{id}/next**

When generation endpoint is created, Dev 2 needs to:

### Step 1: Hook character context into generation

In Dev 1's generation code:

```python
# When generating next scene:
from app.utils.character_context_builder import CharacterContextBuilder

# Build character context
character_context = CharacterContextBuilder.integrate_character_context_into_prompt(
    base_prompt=generation_prompt,
    characters=story_characters,
    current_segment_id=current_segment_id,
    include_instructions=True
)

# Pass to AI
response = await text_generator.generate(character_context)
```

### Step 2: Update character states after generation

```python
# After AI generates scene:
from app.utils.character_state_manager import CharacterStateManager

# Parse character updates from response
character_updates = extract_character_updates(response.content)

# Update each character
for char_id, update in character_updates.items():
    char = load_character(char_id)
    CharacterStateManager.update_character_state(
        character=char,
        segment_id=new_segment_id,
        emotion=update.emotion,
        status=update.status,
        notes=update.notes
    )
    char.save()
```

### Success Criteria
- ✅ Character context feeds into generation
- ✅ Character states update after generation
- ✅ No errors in state tracking
- ✅ Character emotional arcs make sense

---

## Task 2.6: Frontend Character Display Support (1 hour)

**Coordinate with Dev 4**

Make sure frontend can:

1. **Display characters with avatars**
   ```typescript
   // Frontend receives:
   {
     "id": "eira",
     "name": "Eira",
     "avatar_shape": "circle",
     "avatar_color": "#FF6B6B"
   }
   
   // Frontend renders:
   <CharacterAvatar shape="circle" color="#FF6B6B" name="Eira" />
   ```

2. **Show character states in segment**
   ```typescript
   // From segment response:
   "character_states": {
     "eira": {
       "name": "Eira",
       "emotion": "concerned",
       "status": "present"
     }
   }
   
   // Frontend shows this in the UI
   ```

3. **Track character presence**
   - Which characters are in scene
   - Their emotional states
   - Appear consistently

### Success Criteria
- ✅ Frontend can display all character info
- ✅ Avatars render correctly
- ✅ Emotional states visible
- ✅ Character presence tracked

---

## Task 2.7: Testing & Validation (2 hours)

### Test character integration

```python
# tests/test_character_integration.py

def test_character_in_segment_response():
    """Verify character data in segment response"""
    response = client.get("/api/segments/segment_001?story_id=veil_of_thornreach")
    assert response.status_code == 200
    
    segment = response.json()["segment"]
    assert "character_states" in segment
    assert "eira" in segment["character_states"]
    assert segment["character_states"]["eira"]["emotion"] == "concerned"

def test_character_endpoint():
    """Test character retrieval"""
    response = client.get("/api/characters/eira?story_id=veil_of_thornreach")
    assert response.status_code == 200
    
    char = response.json()["character"]
    assert char["avatar_shape"] == "circle"
    assert char["avatar_color"].startswith("#")
    assert len(char["running_status"]) > 0
```

### Manual testing

1. **Get a story**
   ```bash
   curl http://localhost:8000/api/stories/veil_of_thornreach
   ```

2. **Check character data included**
   ```bash
   curl "http://localhost:8000/api/segments/segment_001?story_id=veil_of_thornreach"
   # Should include character_states
   ```

3. **Get individual character**
   ```bash
   curl "http://localhost:8000/api/characters/eira?story_id=veil_of_thornreach"
   # Should show avatar info + state history
   ```

### Success Criteria
- ✅ All endpoints tested
- ✅ Character data correct
- ✅ Avatar info present
- ✅ No missing data

---

## Daily Breakdown

### Day 1 (while Dev 1 works on API)
- [ ] Review character system code
- [ ] Prepare character endpoints
- [ ] Prepare integration code
- [ ] Wait for Dev 1 to finish main.py + routes

### Day 2
- [ ] Task 2.4: Create character endpoints (2h)
- [ ] Task 2.6: Coordinate with Dev 4 (1h)
- [ ] Prepare integration code (1h)

### Day 3
- [ ] Task 2.5: Integrate with generation (3h)
- [ ] Task 2.7: Testing & validation (2h)
- [ ] Verify character states working

---

## Commits

```bash
[DEV-2] add character data endpoints
[DEV-2] integrate character context into generation flow
[DEV-2] add character state updates after generation
[DEV-2] add character integration tests
```

---

## Success Criteria

- ✅ Characters load from API
- ✅ Avatar data returns correctly
- ✅ Character states tracked through story
- ✅ Emotional arcs make narrative sense
- ✅ Frontend can display all character info
- ✅ All tests passing

---

## Dependencies

**Waits for**:
- Dev 1: Main API structure + generation endpoint

**Unblocks**:
- Dev 4: Can display characters
- Dev 5: Can style character avatars

This is the secret sauce of good storytelling! 🎭
