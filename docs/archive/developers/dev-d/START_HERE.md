# Welcome, Developer D!

**Epic:** Generation Pipeline (E1)  
**Duration:** 2 weeks  
**Your Role:** Principal/Senior Engineer, Epic Lead

---

## Your Mission

You're architecting the generation pipeline—the heart of v2. Your team (D, E) will:

1. Build **SegmentContextBuilder** → Walk parent chains, accumulate changes, detect transitions
2. Update **Generation Pipeline** → Decide traverse vs. generate, lock choices, handle errors
3. Enhance **Generator Interface** → Validation, fallbacks
4. Implement **Segment Generation** → Create segments with all fields
5. Complete **Episode Transitions** → Detect when episodes should end

This is what makes v2 work: intelligent, coherent generation based on rich context.

**Blocker:** E0 must be complete (you need the enhanced models)

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read ARCHITECTURE_V2.md** (understand generation flow)
3. **Read EPIC_1_GENERATION.md** (your detailed blueprint)
4. **Review E0 PRs** (understand new fields in StorySegment)

---

## Your Epic Tasks

### E1-1: Segment Context Builder (3 days)

**File:** `backend/app/engine/segment_context_builder.py` (NEW)

Build a system that:
- Walks backward through parent chain to episode start
- Accumulates all `change_notes` from segments
- Detects episode transitions (pacing >= 0.8, segment count >= 18)
- Calculates pacing weight (0.0 to 1.0, exponential curve)
- Assembles generation context dict

See `EPIC_1_GENERATION.md` section "E1-1" for full code and tests.

**Acceptance Criteria:**
- [ ] All 4 methods working
- [ ] `build_context()` returns complete dict
- [ ] Unit tests (5+)
- [ ] Handles edge cases (missing parent, episode boundaries)

### E1-2: Generation Pipeline (3 days)

**File:** `backend/app/engine/story_runner.py` (MODIFY)

Add method:
- `traverse_or_generate()` → Main decision point
  - If choice.to_segment_id is set, traverse (use existing segment)
  - If null, generate (create new one)
  - Lock choice during generation to prevent race conditions
  - Handle errors gracefully

Also add:
- `_generate_segment()` → Create new segment with all fields
- `_build_generation_prompt()` → Rich prompt for AI

See `EPIC_1_GENERATION.md` section "E1-2" for code.

**Acceptance Criteria:**
- [ ] `traverse_or_generate()` handles both cases
- [ ] Choice locking prevents race conditions
- [ ] `_generate_segment()` creates valid segments
- [ ] Outgoing choices created
- [ ] Error handling + unlock on failure
- [ ] Unit tests (4+)

### E1-5: Episode Transition Logic (2 days)

**File:** `backend/app/engine/segment_context_builder.py` (ENHANCE E1-1)

Refine `_should_transition_episode()`:
- Check: end_condition_proximity >= 0.8
- Check: segment_number_in_episode >= 18
- Detect explicit end condition keywords

See `EPIC_1_GENERATION.md` section "E1-5" for tests.

---

## Dev-E's Work (Parallel)

While you build E1-1/2/5, Dev-E will:
- E1-3: Enhance Generator interface (validation, fallbacks)
- E1-4: Segment generation implementation (create segments, tests)

You code review their work. Keep in sync.

---

## Collaboration

- **Daily standup** with Dev-E
- **Code reviews** for Dev-E's PRs
- **Tech lead mentorship** (2x per week)

---

## Key Concepts

### Parent Chain Walking
```
Seg 5 (current)
  ← parent: Seg 4
    ← parent: Seg 3
      ← parent: Seg 2
        ← parent: Seg 1 (episode start)
```

Walk backward until parent_segment_id is null or episode changes.

### Pacing Signal
Exponential: slow at start, fast at end
- Seg 1: 0.0025 (lots of room)
- Seg 10: 0.2500
- Seg 18: 0.8100 (close to end!)

### Generation Context Dict
```python
{
    'previous_segments': [...],    # Last 5 scenes
    'character_states': {...},     # Latest snapshot
    'accumulated_changes': [...],  # All change_notes
    'pacing_weight': 0.6,         # Progress signal
    'should_transition_episode': False,
    # ... more fields
}
```

---

## Key Files

```
backend/app/engine/
  ├── story_runner.py       ← YOU ENHANCE (E1-2)
  ├── generator.py          ← Dev-E enhances (E1-3)
  └── segment_context_builder.py ← YOU CREATE (E1-1)

backend/app/models/
  └── story_segment.py      ← Enhanced by E0
```

---

## Commits

```bash
git commit -m "E1-1: implement segment context builder with episode chaining"
git commit -m "E1-2: add traverse_or_generate pipeline with choice locking"
git commit -m "E1-5: implement episode transition detection logic"
```

---

## Next Action

→ Open `EPIC_1_GENERATION.md` and start on E1-1.

This is the core of the system. Make it solid! 🚀
