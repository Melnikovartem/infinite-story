# Welcome, Developer F!

**Epic:** Episodes & Arc System (E2)  
**Duration:** 2 weeks  
**Your Role:** Senior Engineer, Epic Lead

---

## Your Mission

You're leading the episode & arc system. Your team (F, G) will:

1. **E2-1** (3 days): Episode Recap Generator
   - Walk episode backward, collect all segments
   - Accumulate character change_notes
   - Call AI to generate title, summary, themes
   - Create EpisodeRecap and save

2. **E2-2** (2 days): New Episode Context
   - When starting new episode, AI picks tone, end_condition, direction
   - Considers arc premise and previous recaps
   - Returns metadata for next episode

3. **E2-5** (2 days): Archive Handling
   - Update queries to respect archived status
   - Exclude archived by default
   - Allow `include_archived=True` for recovery

This bounds infinite growth: after ~15 episodes, pause, summarize, compress.

**Blocker:** E0 complete, E1 helpful (uses generation pipeline)

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_2_EPISODES.md** (your blueprint)
3. **Review E0 & E1** (understand models and generation)

---

## Your Epic Tasks

### E2-1: Episode Recap Generator (3 days)

**File:** `backend/app/engine/episode_recap_generator.py` (NEW)

Build:
- `_walk_episode_segments()` → Collect all segments in episode
- `_collect_changes()` → Extract all change_notes
- `_extract_starting_states()` → Character snapshot from episode start
- `_build_recap_prompt()` → Rich prompt for AI
- `generate_recap()` → Full recap generation and save

See `EPIC_2_EPISODES.md` section "E2-1" for full code and tests.

**Acceptance Criteria:**
- [ ] Walks episode backward correctly
- [ ] Collects changes from all segments
- [ ] Builds comprehensive recap prompt
- [ ] Creates EpisodeRecap and saves
- [ ] Unit tests (4+)

### E2-2: New Episode Context (2 days)

**File:** `backend/app/engine/episode_recap_generator.py` (ADD)

Implement:
- `generate_new_episode_context()` → Create next episode metadata
  - Pick tone word from pool
  - Consider previous recap and arc premise
  - Call AI to generate: tone_tags, end_condition, narrative_direction
  - Return metadata

See `EPIC_2_EPISODES.md` section "E2-2" for code.

**Acceptance Criteria:**
- [ ] `generate_new_episode_context()` works
- [ ] Returns tone, end_condition, narrative_direction
- [ ] Unit tests (2+)

### E2-5: Archive State Handling (2 days)

**File:** `backend/app/models/story.py` (MODIFY)

Update Story class:
- `get_segment(segment_id, include_archived=False)` → Respect status
- `get_available_choices(segment_id)` → Exclude archived destinations
- Update all query methods to use new flags

See `EPIC_2_EPISODES.md` section "E2-5" for code.

**Acceptance Criteria:**
- [ ] `get_segment()` respects `include_archived` flag
- [ ] `get_available_choices()` excludes archived
- [ ] All game loop queries updated
- [ ] Unit tests (3+)

---

## Dev-G's Work (Parallel)

While you lead E2-1/2/5, Dev-G will:
- E2-3: Character State Reconciliation
- E2-4: Arc Compressor

You code review their work. Keep aligned.

---

## Collaboration

- **Daily standup** with Dev-G
- **Code reviews** for Dev-G's PRs
- **Coordinate with E1 lead** (Dev-D) on generation timing

---

## Key Concepts

### Episode Cycle
```
Play scenes (Gen generates them)
  → Accumulate change_notes
    → Detect end condition (pacing >= 0.8, etc.)
      → Generate recap
        → Reconcile character states
          → Generate new episode context
            → Start new episode
```

### Recap Generation
```
Input: All segments + changes from episode
  ↓
AI: "Summarize this episode in narrative form"
  ↓
Output: EpisodeRecap (title, summary, themes, final char states)
  ↓
Save to disk
```

---

## Key Files

```
backend/app/engine/
  └── episode_recap_generator.py ← YOU CREATE

backend/app/models/
  ├── episode_recap.py  ← Created by E0 (read structure)
  ├── story_arc.py      ← Created by E0
  └── story.py          ← YOU ENHANCE (E2-5)
```

---

## Commits

```bash
git commit -m "E2-1: implement episode recap generator with AI summarization"
git commit -m "E2-2: add new episode context generation"
git commit -m "E2-5: update queries to respect archived segments"
```

---

## Next Action

→ Open `EPIC_2_EPISODES.md` section E2-1. Start with recap generation.

You're creating the episode boundaries that prevent infinite growth! 📚
