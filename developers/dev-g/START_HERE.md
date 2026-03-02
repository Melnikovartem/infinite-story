# Welcome, Developer G!

**Epic:** Episodes & Arc System (E2)  
**Duration:** 2 weeks  
**Your Role:** Mid-Senior Engineer, supporting Epic Lead F

---

## Your Mission

You're completing the episode & arc system. While Dev-F builds recaps, you'll:

1. **E2-3** (2 days): Character State Reconciliation
   - Apply change_notes to character snapshots
   - Detect contradictions ("betrays" vs "trusts")
   - Use AI to resolve conflicts
   - Return final character states for recap

2. **E2-4** (4 days): Arc Compressor
   - Find branches in arc from user sessions
   - Select top candidates (by popularity + random)
   - Summarize each branch
   - Call AI to pick mainline (most coherent)
   - Archive non-mainline segments
   - Save compression metadata

This is what prevents exponential explosion: after 15 episodes, compress the graph.

**Blocker:** E0 complete, E1 helpful

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_2_EPISODES.md** (focus on E2-3 & E2-4)
3. **Understand** Dev-F's recap generator (E2-1)

---

## Your Tasks

### E2-3: Character State Reconciliation (2 days)

**File:** `backend/app/engine/episode_recap_generator.py` (ADD)

Implement reconciliation that:

1. Start with episode snapshot
2. Apply all change_notes in order
3. Detect contradictions (death vs alive, betrays vs trusts)
4. If contradictions found, call AI to resolve
5. Return final character states

```python
async def reconcile_character_states_with_ai(
    starting_states,   # Snapshot at episode start
    changes,          # All change_notes from episode
) -> Dict[str, CharacterState]:
    """Apply changes, handling contradictions"""
    
    # Detect contradictions
    contradictions = self._detect_contradictions(changes)
    
    if contradictions:
        # Ask AI to decide which is final
        return await self._resolve_contradictions_with_ai(...)
    else:
        # Simple: apply all changes in order
        return apply_changes(starting_states, changes)
```

See `EPIC_2_EPISODES.md` section "E2-3" for full code.

**Acceptance Criteria:**
- [ ] `reconcile_character_states_with_ai()` implemented
- [ ] Contradiction detection working
- [ ] AI fallback working
- [ ] Unit tests (3+)

### E2-4: Arc Compressor (4 days)

**File:** `backend/app/engine/arc_compressor.py` (NEW)

Build an arc compressor that:

1. `_find_branches_in_arc()` → Find divergent paths from user sessions
2. `_select_candidates()` → Pick top N + random M
3. `_summarize_branch()` → Create text summary of branch
4. `_ai_select_mainline()` → AI picks best branch
5. `compress_arc()` → Full flow
   - Archive non-mainline segments
   - Save ArcCompressionResult
   - Mark arc as compressed

See `EPIC_2_EPISODES.md` section "E2-4" for full code and tests.

**Acceptance Criteria:**
- [ ] `_find_branches_in_arc()` finds divergent paths
- [ ] `_select_candidates()` picks top branches
- [ ] `_summarize_branch()` works
- [ ] `_ai_select_mainline()` calls AI correctly
- [ ] Archive mechanism marks segments ARCHIVED
- [ ] `compress_arc()` full flow working
- [ ] Unit tests (4+)
- [ ] Integration test: full compression

---

## Collaboration

- **Daily standup** with Dev-F
- **Ask Dev-F** for questions on reconciliation
- **Code reviews** from Dev-F

---

## Key Concepts

### Contradiction Detection

```python
changes = [
    "Alice dies",
    "Alice wakes up",  # Contradiction!
]

contradictory_pairs = [
    ("dead", "alive"),
    ("betrays", "trusts"),
    ("hates", "loves"),
]
```

### Branch Finding

```
Arc segments form a DAG (directed acyclic graph):
  Seg 1 (start)
    ├─ Seg 2a → Seg 3a → Seg 4a (Branch A)
    └─ Seg 2b → Seg 3b → Seg 4b (Branch B)

Users took different paths. Find them.
```

### Compression

```
Inputs:
  - All branches (multiple paths from same start)
  - User sessions (which paths were taken)

AI Selection:
  - "Which branch is most narratively coherent?"
  - "Which fits the arc premise best?"
  - "Which advances the themes?"

Output:
  - Mainline: Seg 1 → 2a → 3a → 4a → ...
  - Archived: Seg 2b, 3b, 4b, ...
  - Continue story from mainline only
```

---

## Key Files

```
backend/app/engine/
  ├── arc_compressor.py ← YOU CREATE
  └── episode_recap_generator.py ← You enhance with E2-3

backend/app/models/
  ├── story_segment.py (status = ARCHIVED field)
  ├── story_arc.py     (compression_result field)
  └── story.py         (queries exclude archived)
```

---

## Commits

```bash
git commit -m "E2-3: implement character state reconciliation with AI conflict resolution"
git commit -m "E2-4: create arc compressor for mainline selection and archival"
```

---

## Next Action

→ Open `EPIC_2_EPISODES.md` section E2-3. Start with reconciliation.

You're compressing the infinite tree into a manageable graph! 🎯
