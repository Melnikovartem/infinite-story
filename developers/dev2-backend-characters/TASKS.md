# Dev 2: Backend Characters - Detailed Task Breakdown

**Total Hours**: 40 (8-10 hours/day × 4-5 days)
**Timeline**: Week 1.5-2
**Start After**: Dev 1 completes Task 1.2 (models defined)

---

## Task 2.1: Character Model Refinement (10 hours)

**Days 1-2 - Estimated 10 hours**

### What You're Building
Extend the StoryCharacter model with avatar system, color management, and state tracking.

### Subtasks

#### 2.1.1: Avatar System (4 hours)
- [ ] Define avatar shape enum (square, circle, triangle, diamond, star, pentagon)
- [ ] Define color palette (6 distinct colors)
- [ ] Add avatar_shape and avatar_color fields to StoryCharacter
- [ ] Add validation for valid shapes and colors
- [ ] Write tests for avatar validation

**Example**:
```python
from enum import Enum

class AvatarShape(str, Enum):
    SQUARE = "square"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    STAR = "star"
    PENTAGON = "pentagon"

class StoryCharacter(BaseModel):
    id: str
    name: str
    avatar_shape: AvatarShape
    avatar_color: str  # Hex color #XXXXXX
    description: str
```

#### 2.1.2: Character State Structure (3 hours)
- [ ] Define CharacterState model for single segment
- [ ] Fields: emotion, status (present/absent/mentioned), notes
- [ ] Create running_status as List[CharacterState]
- [ ] Add methods to get character state at specific segment
- [ ] Write tests for state tracking

#### 2.1.3: Character Serialization (3 hours)
- [ ] Add to_dict() method to StoryCharacter
- [ ] Add from_dict() class method
- [ ] Test save/load cycle
- [ ] Ensure avatar data persists
- [ ] Test edge cases (missing colors, invalid shapes)

---

## Task 2.2: Character State Persistence (15 hours)

**Days 2-3 - Estimated 15 hours**

### What You're Building
System to track and update character states through story progression.

### Subtasks

#### 2.2.1: State Update Methods (5 hours)
- [ ] Create update_character_state() method
- [ ] Takes: character_id, segment_id, emotion, status, notes
- [ ] Appends to running_status
- [ ] Handles duplicate updates (merge or replace)
- [ ] Write comprehensive tests

#### 2.2.2: Bulk State Loading (5 hours)
- [ ] Create method to load all characters for story
- [ ] Create method to get character at specific segment
- [ ] Create method to track character arc (all states in order)
- [ ] Optimize for performance (caching if needed)
- [ ] Write tests

#### 2.2.3: State Consistency (5 hours)
- [ ] Validate state coherence (character can't be in two places)
- [ ] Handle character appearances/disappearances
- [ ] Track emotional progression
- [ ] Add data migration if needed (old format → new format)
- [ ] Write validation tests

---

## Task 2.3: Generation Integration (15 hours)

**Days 3-4 - Estimated 15 hours**

### What You're Building
Integration of characters with AI generation system.

### Subtasks

#### 2.3.1: Character Context Building (5 hours)
- [ ] Create method to extract character context for generation
- [ ] Include character descriptions
- [ ] Include current emotional state
- [ ] Include recent actions
- [ ] Include relationships (if tracked)
- [ ] Write tests

**Example**:
```python
def build_character_context(story_id: str, segment_id: str) -> str:
    """Build character information for AI generation."""
    characters = load_story_characters(story_id)
    context = ""
    
    for char in characters:
        state = char.get_state_at_segment(segment_id)
        context += f"{char.name} ({state.emotion}): {state.notes}\n"
    
    return context
```

#### 2.3.2: Post-Generation Character Updates (5 hours)
- [ ] Extract character updates from generation response
- [ ] Parse character emotional changes
- [ ] Track location changes
- [ ] Update running_status for all characters
- [ ] Save updated characters to disk
- [ ] Write tests with mocked generation response

#### 2.3.3: Character Endpoint (Optional, 5 hours)
- [ ] Create GET /api/characters/{character_id} endpoint (if needed)
- [ ] Return character info + state history
- [ ] Return character arc through story
- [ ] Write tests

---

## Success Checklist

- [ ] Avatar system working (shapes + colors)
- [ ] Character states persisting across segments
- [ ] State updates integrated with generation
- [ ] All tests passing (80%+ coverage)
- [ ] Serialize/deserialize working
- [ ] Ready for Dev 4 to display in UI

---

## Daily Progress

### Day 1
- [ ] Task 2.1.1: Avatar system (4h)
- [ ] Task 2.1.2: Character state structure (3h)
- [ ] Total: ~7 hours

### Day 2
- [ ] Task 2.1.3: Serialization (3h)
- [ ] Task 2.2.1: State update methods (5h)
- [ ] Total: ~8 hours (cumulative 15)

### Day 3
- [ ] Task 2.2.2: Bulk state loading (5h)
- [ ] Task 2.2.3: State consistency (5h)
- [ ] Total: ~10 hours (cumulative 25)

### Day 4
- [ ] Task 2.3.1-2.3.3: Generation integration (15h)
- [ ] Testing & bug fixes
- [ ] Total: ~15 hours (cumulative 40)

---

## Commit Strategy

```bash
[DEV-2] add avatar shape and color system
[DEV-2] add character state model and tracking
[DEV-2] implement character serialization
[DEV-2] add character state update methods
[DEV-2] implement character context building
[DEV-2] integrate characters with generation
```

---

Good luck! 🚀
