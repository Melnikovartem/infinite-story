# Implementation Summary: Shared Graph with Narrative Overlays

## Three Documents Overview

### 1. **VISION.md** — What & Why
- **Audience**: Everyone (designers, developers, users)
- **Purpose**: Understand the philosophy and design
- **Contains**:
  - Core concept and mental model
  - Key design decisions with rationale
  - Comparison to other systems
  - User experience descriptions
  - Known limitations and future enhancements

**Start here if you want to understand the "why."**

---

### 2. **ARCHITECTURE_V2.md** — How (Technical)
- **Audience**: Engineers
- **Purpose**: Technical implementation details
- **Contains**:
  - System overview diagram
  - Data models (Segment, Choice, Episode, etc.)
  - Generation pipeline flow
  - Episode recap generation
  - Arc compression system
  - CLI implementation (both modes)
  - Storage structure
  - Performance considerations
  - Error handling
  - Testing strategy

**Start here if you're implementing or debugging.**

---

### 3. **REIMPLEMENTATION_PLAN.md** — How To Build
- **Audience**: Engineers
- **Purpose**: Step-by-step implementation roadmap
- **Contains**:
  - 7 phases of work (1-5 weeks total)
  - Specific files to create/modify
  - Code examples for each phase
  - Testing requirements
  - Risk analysis
  - Success criteria
  - Rollout strategy

**Start here if you're planning the work.**

---

## Quick Concept Reference

### The System in One Image

```
User picks unexplored choice
    ↓
[Check if episode should end]
    ↓
[Generate new segment OR recap + new episode]
    ↓
[Save immutable segment to shared graph]
    ↓
[Move user cursor to new segment]
    ↓
[After ~15 episodes: compress arc, pick mainline]
    ↓
[Next arc starts from mainline frontier]
```

### Key Terms

| Term | Meaning |
|------|---------|
| **Segment** | Immutable node in the graph. Generated once, shared by all users. |
| **Choice** | Edge in the graph. Points to segment or null (unexplored). |
| **Episode** | ~20 segment chain with shared tone/end_condition. Context baked into segments. |
| **Arc** | ~15 episodes. Compressed to pick mainline, archive rest. |
| **User Session** | Just a cursor: current_segment + visited_segments. |
| **Character State** | Snapshot at episode start + accumulated changes. Reconciled at recap. |
| **Episode Recap** | Generated at episode end. Summarizes what happened, outputs new character snapshot. |
| **Arc Compression** | Every ~15 episodes, pick canonical branch, hide others. World timeline stabilizes. |

---

## Implementation Phases (Quick)

| Phase | Work | Duration | Priority |
|-------|------|----------|----------|
| **1** | Enhance models (Segment, Choice, Episode, Arc, UserSession) | 1 week | Critical |
| **2** | Generation pipeline (context builder, traverse_or_generate) | 1 week | Critical |
| **3** | Episode system (recap generator, character reconciliation) | 1 week | Critical |
| **4** | Arc compression (branch selection, archiving) | 1 week | Important |
| **5** | CLI (two modes: gameplay & exploration) | 1 week | Important |
| **6** | Testing (unit, integration, simulation) | 1-2 weeks | Essential |
| **7** | Docs & finalization | 1 week | After |

**Total: 4-5 weeks** (can be faster with parallel work)

---

## Migration Path

### Current System → New System

**Old:**
```
infinite branching tree
per-user segment generation
no episode/arc structure
simple character states
unlimited growth
```

**New:**
```
shared immutable graph
one generation per segment
episodes (tone/pacing)
arcs (compression/mainline)
snapshot + running log for characters
bounded by compression every 15 episodes
```

### Migration Strategy

1. Create new branch `v2-segment-graph`
2. Implement all phases (1-5 weeks)
3. Migrate existing story data (using migration script)
4. Test thoroughly (phase 6)
5. Merge to main, remove old code
6. Deploy

**Why not feature flags?** This is a major refactor. Simpler to own it completely rather than maintain two systems in parallel.

---

## Rollout Checklist

- [ ] Phase 1: Models enhanced
- [ ] Phase 2: Generation pipeline working
- [ ] Phase 3: Episode system generating recaps
- [ ] Phase 4: Arc compression working
- [ ] Phase 5: CLI updated, both modes working
- [ ] Phase 6: All tests passing
- [ ] Existing story migrated without data loss
- [ ] Performance acceptable (<500ms segment load)
- [ ] Migration script tested
- [ ] Docs updated
- [ ] Demo to stakeholders
- [ ] Deploy to production

---

## Key Files to Create/Modify

### New Files

```
backend/app/engine/
  ├── segment_context_builder.py (episode context, pacing)
  ├── episode_recap_generator.py (recap generation)
  ├── arc_compressor.py (mainline selection)

backend/app/models/
  ├── episode_recap.py (recap model)
  ├── story_arc.py (arc model)

backend/app/
  ├── cli_display.py (gameplay + exploration modes)
  ├── cli_dev_commands.py (dev tools)

backend/scripts/
  ├── migrate_v1_to_v2.py (data migration)

backend/tests/
  ├── test_segment_graph.py (new tests)
  ├── test_episode_system.py (new tests)
  ├── test_migration.py (new tests)
```

### Modified Files

```
backend/app/models/
  ├── story_segment.py (add episode context, states)
  ├── story_choice.py (add status field)
  ├── session_state.py (simplify to cursor)

backend/app/engine/
  ├── story_runner.py (add traverse_or_generate)
  ├── generator.py (enhance for recaps)

backend/app/
  ├── cli.py (two modes, new loop)
  ├── config.py (CLI mode settings)

backend/
  ├── requirements.txt (if new dependencies)
```

---

## Success Criteria

✅ **All existing story data migrates without loss**
✅ **Can traverse shared segment graph**
✅ **Episode transitions work seamlessly**
✅ **Character state accumulates through episodes**
✅ **Recaps generate coherent titles/summaries**
✅ **Arc compression picks reasonable mainlines**
✅ **All new tests pass**
✅ **CLI works in both modes**
✅ **Performance acceptable (<500ms)**

---

## Open Questions for Team

1. **Difficulty**: How hard are episode transitions and recaps?
2. **Feasibility**: Arc compression is complex. Worth doing now or defer?
3. **UX**: Should gameplay mode hide episode transitions completely or show subtle banners?
4. **Migration**: Do we need to preserve old branches during migration, or start fresh?
5. **Compression**: Who decides mainline — AI only, or with community input?

---

## Reading Order

1. **Start with VISION.md** if you're new
2. **Reference ARCHITECTURE_V2.md** while coding
3. **Follow REIMPLEMENTATION_PLAN.md** day-to-day

---

## Key Insights

### Why This Design?

Traditional systems either:
- **Books**: Fixed, no uniqueness
- **CYOA**: Branching, but permament
- **Procedural**: Unique, but incoherent
- **MMO stories**: Shared, but rigid

**Our system:**
- Fixed world (shared)
- Branching journeys (per-user)
- Guided narrative (episodes/arcs)
- Coherent story (immutable segments)
- Stable state (compression)

### Why Immutable Segments?

Prevents:
- Narrative fragmentation (same location has same state for all)
- Duplication (no re-generation)
- Inconsistency (segment text doesn't change)

Enables:
- Sharing (same segment for all who pick same choice)
- Coherence (real world with real paths)
- Debugging (trace issues to generation context)

### Why Episode Transitions at Generation Time?

Prevents:
- Per-user episode state (no duplication)
- Episode containers (no new data structure)

Enables:
- Seamless transitions (no UI interruption)
- Branch variants (4a, 4b, 4c)
- Flexibility (episodes follow the graph structure)

### Why Compression?

Prevents:
- Combinatorial explosion (2^15 paths = 32K branches)
- Infinite growth (world becomes unplayable)

Enables:
- Narrative closure (arc has an ending)
- World stability (next arc has stable starting point)
- Intentional "jitter" (gods choosing reality)

---

## Glossary

**Segment** - A scene. Immutable once generated.
**Choice** - A decision point. Points to a segment or unexplored.
**Episode** - ~20 segments with shared tone/pacing/end_condition. Context baked into segments.
**Arc** - ~15 episodes. Has an arc compression event.
**Compression** - Every ~15 episodes, pick canonical branch, archive others.
**Recap** - Summary generated at episode end.
**Running Log** - Accumulated changes within an episode.
**Snapshot** - Character states at episode start.
**Pacing Weight** - 0.0-1.0 value indicating where we are in episode.
**User Session** - Cursor on the graph (current_segment + visited).
**Mainline** - The canonical path selected during compression.

---

## For Questions

Refer to the specific docs:
- **"Why this design?"** → VISION.md
- **"How do I implement X?"** → ARCHITECTURE_V2.md
- **"What's the task this week?"** → REIMPLEMENTATION_PLAN.md
- **"What's the term?"** → This document (glossary)
