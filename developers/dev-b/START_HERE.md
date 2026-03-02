# Welcome, Developer B!

**Epic:** Data Layer Foundation (E0)  
**Duration:** 1 week  
**Your Role:** Senior Engineer, supporting Epic Lead A

---

## Your Mission

You're part of the foundation team. While Dev-A leads, you'll:

1. **E0-3** (1 day): Create the `StoryArc` model
   - Data structure for arcs, episodes, compression metadata
   - Serialization/deserialization
   - Unit tests

2. **E0-4** (1 day): Simplify the `UserSession` model
   - Remove per-user episode tracking (now in segments)
   - Remove character state tracking (now in recaps)
   - Keep minimal state: user_id, visited segments, current location
   - Update all code that references old fields

Your work unblocks E1/E2/E3 teams who depend on clean data models.

---

## First Steps

1. **Read ONBOARDING.md** (in `/developers/`)
2. **Read EPIC_0_DATA_LAYER.md** (in `/developers/`)
   - Focus on E0-3 and E0-4 sections
3. **Coordinate with Dev-A** (your lead)

---

## Your Tasks

### E0-3: Create StoryArc Model (1 day)

**File:** `backend/app/models/story_arc.py` (NEW)

See `EPIC_0_DATA_LAYER.md` section "E0-3" for full spec and code examples.

**Acceptance Criteria:**
- [ ] StoryArc model created
- [ ] ArcCompressionResult model created
- [ ] Save/load working
- [ ] Unit tests passing (3+)
- [ ] Code review by Dev-A

### E0-4: Simplify UserSession Model (1 day)

**File:** `backend/app/models/session_state.py` (MODIFY)

See `EPIC_0_DATA_LAYER.md` section "E0-4" for details.

**What to Remove:**
- `character_states` (now in segments & recaps)
- `episode_number` (now in segments)
- `protagonist_id` (now in segments)
- Per-user episode tracking (no longer needed)

**What to Keep:**
- `user_id`, `story_id`
- `current_segment_id`
- `visited_segments`, `visited_choices`

**What to Add:**
- Helper methods: `add_visited()`, `move_to()`

**Acceptance Criteria:**
- [ ] Unnecessary fields removed
- [ ] Minimal session object created
- [ ] All code referencing old fields updated
- [ ] Unit tests updated and passing
- [ ] Code review by Dev-A

---

## Collaboration

- **Daily standup** with Dev-A and Dev-C
- **Code review** from Dev-A (you code review Dev-C's work)
- **Ask Dev-A** if you hit questions or blockers

---

## Key Resources

- `EPIC_0_DATA_LAYER.md` → E0-3 and E0-4 sections
- `ARCHITECTURE_V2.md` → Data model hierarchy
- `backend/app/models/story_segment.py` → Reference for Pydantic patterns

---

## Commit Examples

```bash
git commit -m "E0-3: create storyarc model with compression metadata"
git commit -m "E0-4: simplify usersession, remove per-user episode tracking"
```

---

## Next Action

→ Open `EPIC_0_DATA_LAYER.md` section E0-3. Start with StoryArc model.

Good luck! 💪
