# Quick Reference: Shared Graph System

## Data Model Diagram

```
                    SEGMENT (Immutable Node)
                    ┌─────────────────────────┐
                    │ id                      │
                    │ status: generated       │
                    │ parent_segment_id       │
                    │ parent_choice_id        │
                    │                         │
    EPISODE         │ arc_id                  │ EPISODE CONTEXT
    CONTEXT         │ episode_number          │ (Baked at gen time)
    ────────────    │ episode_tone            │ ────────────────
                    │ episode_end_condition   │
                    │ segment_number_in_ep    │
                    │ pacing_weight           │
                    │ protagonist_id          │
                    │                         │
    CHARACTER       │ character_states        │ CHARACTER STATE
    STATE           │ change_notes            │ (Snapshot + Log)
    ──────────      │                         │ ──────────────
                    │ text_blocks             │
                    │ end_condition_proximity │
                    │ protagonist_alive       │
                    │ triggers_ep_transition  │
                    └────────┬────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
            ┌──────────────┐  ┌──────────────┐
            │ CHOICE 1     │  │ CHOICE 2     │
            │ (unexplored) │  │ (generated)  │
            │ to_seg: null │  │ to_seg: ID   │
            └──────────────┘  └──────────────┘
                    │                 │
      (when picked) │                 │ (when picked)
                    │                 │
                    ▼                 ▼
          [Generate new]        [Use existing]
```

---

## Generation Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────┐
│ USER PICKS CHOICE (to_segment_id == null)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ LOCK CHOICE             │
        │ (prevent duplicate)     │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────────────────────┐
        │ BUILD GENERATION CONTEXT                        │
        │                                                 │
        │ 1. Walk parent chain to find episode start      │
        │    └─ Collect character snapshot               │
        │    └─ Collect accumulated change_notes         │
        │                                                 │
        │ 2. Check: should episode end?                  │
        │    ├─ If YES:                                  │
        │    │   ├─ Generate recap                       │
        │    │   ├─ Generate new episode context         │
        │    │   └─ Use new context                      │
        │    └─ If NO:                                   │
        │        └─ Continue current episode             │
        │                                                 │
        │ 3. Calculate pacing_weight (0.0-1.0)          │
        │                                                 │
        │ 4. Build prompt:                               │
        │    ├─ World info                               │
        │    ├─ Arc info                                 │
        │    ├─ Episode info                             │
        │    ├─ Character states                         │
        │    ├─ Protagonist POV                          │
        │    ├─ Recent segments                          │
        │    ├─ Player's choice text                     │
        │    └─ Pacing instruction                       │
        │                                                 │
        └────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ AI GENERATES SEGMENT    │
        │                         │
        │ Input: prompt           │
        │ Output:                 │
        │  ├─ text_blocks         │
        │  ├─ choices             │
        │  ├─ change_notes        │
        │  ├─ end_condition_prox  │
        │  ├─ protagonist_alive   │
        │  └─ signal: end_ep?     │
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────────────┐
        │ CREATE SEGMENT (IMMUTABLE)              │
        │                                         │
        │ Save with:                              │
        │ ├─ Episode context (baked)             │
        │ ├─ Character states (snapshot)         │
        │ ├─ Change notes (this seg only)        │
        │ ├─ Pacing weight                       │
        │ └─ Status: GENERATED                   │
        │                                         │
        │ Create outgoing choices:                │
        │ └─ to_segment_id: null (all unexplored)│
        │                                         │
        └────────────┬────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ UPDATE CHOICE           │
        │ to_segment_id = new_seg │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ MOVE USER CURSOR        │
        │ UserSession.current = X │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │ SAVE STATE              │
        └────────────────────────┘
```

---

## Episode Recap (When End Triggered)

```
SEGMENT N (end_condition_proximity ≈ 1.0)
    │
    └─ Triggers episode transition
         │
         ▼
┌────────────────────────────────────┐
│ EPISODE RECAP GENERATION           │
│                                    │
│ Input:                             │
│  ├─ All segments from ep start     │
│  ├─ All change_notes accumulated  │
│  ├─ Episode tone + end_condition   │
│  ├─ Arc context                    │
│  └─ Earlier episode recaps (arc)   │
│                                    │
│ AI Process:                        │
│  ├─ Read segment chain             │
│  ├─ Read all changes               │
│  ├─ Synthesize what happened       │
│  └─ Output:                        │
│      ├─ title                      │
│      ├─ summary                    │
│      ├─ character_states_final     │
│      ├─ world_state_changes        │
│      └─ narrative_threads          │
│                                    │
│ Save: EpisodeRecap to disk         │
│                                    │
└────────────┬───────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│ NEW EPISODE GENERATION             │
│                                    │
│ Input:                             │
│  ├─ Random tone word               │
│  ├─ Arc storyline                  │
│  ├─ Previous episode recap         │
│  └─ Older episode recaps (context) │
│                                    │
│ AI Outputs:                        │
│  ├─ tone_tags: [str]               │
│  ├─ end_condition: str             │
│  └─ narrative_direction: str       │
│                                    │
└────────────┬───────────────────────┘
             │
             ▼
   Next segment uses new
   episode context (4a/4b/4c)
```

---

## Arc Compression (Every ~15 Episodes)

```
ARC N COMPLETE (~15 episodes)
    │
    ▼
┌─────────────────────────────────┐
│ FIND ALL BRANCHES               │
│                                 │
│ Query user sessions:            │
│  ├─ User A took path: 1→2→5→... │
│  ├─ User B took path: 1→2→3→... │
│  └─ User C took path: 1→4→6→... │
│                                 │
│ Identify unique branches:       │
│  └─ [path_a, path_b, path_c]   │
│                                 │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ SELECT CANDIDATES               │
│                                 │
│ Pick:                           │
│  ├─ Top N by popularity         │
│  │  (most traversed)            │
│  └─ M random ones               │
│     (diversity)                 │
│                                 │
│ Result: 5-8 candidate branches  │
│                                 │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ SUMMARIZE BRANCHES              │
│                                 │
│ For each candidate:             │
│  ├─ Trace path through graph    │
│  ├─ Collect segment summaries   │
│  ├─ Collect episode recaps      │
│  └─ Generate branch summary     │
│                                 │
│ Result: {branch_id: summary}... │
│                                 │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ AI SELECTS MAINLINE             │
│                                 │
│ Input:                          │
│  ├─ Branch summaries            │
│  ├─ Arc storyline               │
│  └─ Character arcs              │
│                                 │
│ AI outputs:                     │
│  └─ mainline_branch_id          │
│                                 │
│ Reasoning:                      │
│  ├─ Narrative coherence         │
│  ├─ Character consistency       │
│  └─ Arc completion              │
│                                 │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ ARCHIVE NON-MAINLINE            │
│                                 │
│ For each non-mainline branch:   │
│  ├─ Get all segment IDs in path │
│  ├─ Mark status: ARCHIVED       │
│  └─ Save to disk                │
│                                 │
│ Effect:                         │
│  └─ Hidden from traversal       │
│     (but recoverable)           │
│                                 │
└─────────────────┬───────────────┘
                  │
                  ▼
┌─────────────────────────────────┐
│ SAVE COMPRESSION RESULT         │
│                                 │
│ Arc.compression = {             │
│   mainline_ids: [seg...],       │
│   archived_ids: [seg...],       │
│   selected_branch_id: "...",    │
│   ai_reasoning: "..."           │
│ }                               │
│                                 │
│ Arc.status = "compressed"       │
│                                 │
└─────────────────┬───────────────┘
                  │
                  ▼
        ARC N+1 STARTS
        (from mainline frontier)
```

---

## Character State Through Episodes

```
EPISODE 1 START
    │
    ├─ character_states: {
    │    "eira": { status: "alive", mood: "hopeful", ... }
    │  }
    │
    ▼
SEGMENT 1
    ├─ change_notes: [{ eira: "learned about curse" }]
    │
    ▼
SEGMENT 3
    ├─ change_notes: [{ eira: "learned about curse" }, 
    │                 { eira: "betrayed by mentor" }]
    │
    ▼
SEGMENT 19 (triggers ep end)
    ├─ change_notes: [accumulated all changes]
    │
    ▼
EPISODE 1 RECAP
    │
    ├─ Input: snapshot + all change_notes
    ├─ AI reconciles: what's eira's final state?
    │
    └─ character_states_final: {
         "eira": { status: "alive", 
                   mood: "determined",  ◄─ evolved from "hopeful"
                   location: "outskirts",
                   relationships: { "mentor": "hostile" },
                   knowledge: ["curse origin", "betrayal"] }
       }
       
    ▼
EPISODE 2 START
    │
    └─ character_states: { snapshot from episode 1 recap }
       ├─ "eira": { status: "alive", mood: "determined", ... }
       │
       └─ (same process repeats for episode 2)
```

---

## CLI Modes Side-by-Side

```
┌─────────────────────────────┬─────────────────────────────┐
│     GAMEPLAY MODE           │     EXPLORATION MODE        │
├─────────────────────────────┼─────────────────────────────┤
│                             │                             │
│ ═══════════════════════════ │ ═════════════════════════════│
│  THE VEIL OF THORNREACH     │  EXPLORATION MODE           │
│ ═══════════════════════════ │ ═════════════════════════════│
│                             │                             │
│ The cobblestone streets     │ [WORLD] veil_of_thornreach  │
│ shimmer in fading light...  │ [ARC] 1: The Rebellion      │
│                             │ [EP] 3   [TONE] betrayal   │
│                             │ [PROTAGONIST] Eira          │
│                             │ [PACING] 0.65 [PROX] 0.7   │
│                             │                             │
│ ───────────────────────────┬┤ ─────────────────────────────│
│                             │                             │
│ 1. Head toward marketplace  │ SEGMENT seg_abc123          │
│ 2. Ask a merchant           │ [ep:3, seg:14/~20]          │
│ 3. Find shelter             │                             │
│                             │ NARRATIVE:                  │
│ Your choice:                │ The cobblestone streets...  │
│                             │                             │
│                             │ CHARACTER STATES:           │
│                             │ eira: alive, mood=sad       │
│                             │ thorne: alive, mood=angry   │
│                             │                             │
│                             │ CHANGES THIS EPISODE:       │
│                             │ seg_3: learned rebel plans  │
│                             │ seg_14: confronted thorne   │
│                             │                             │
│                             │ CHOICES:                    │
│                             │ 1. marketplace              │
│                             │    → null [UNEXPLORED]     │
│                             │ 2. ask merchant             │
│                             │    → seg_def456 [SHARED]    │
│                             │ 3. find shelter             │
│                             │    → null [UNEXPLORED]     │
│                             │                             │
│                             │ DEV COMMANDS:               │
│                             │ 4. Show segment chain       │
│                             │ 5. Show recaps              │
│                             │ 6. Toggle protagonist death │
│                             │                             │
└─────────────────────────────┴─────────────────────────────┘

Immersive, clean             Full context, debugging
```

---

## File Changes Summary

```
NEW FILES:
  backend/app/engine/
    ├─ segment_context_builder.py
    ├─ episode_recap_generator.py
    └─ arc_compressor.py
  
  backend/app/models/
    ├─ episode_recap.py
    └─ story_arc.py
  
  backend/app/
    ├─ cli_display.py
    └─ cli_dev_commands.py
  
  backend/scripts/
    └─ migrate_v1_to_v2.py
  
  backend/tests/
    ├─ test_segment_graph.py
    ├─ test_episode_system.py
    └─ test_migration.py

MODIFIED FILES:
  backend/app/models/
    ├─ story_segment.py (add episode context)
    ├─ story_choice.py (add status)
    └─ session_state.py (simplify)
  
  backend/app/engine/
    ├─ story_runner.py (add traverse_or_generate)
    └─ generator.py (enhance)
  
  backend/app/
    ├─ cli.py (two modes)
    └─ config.py (add CLI settings)
```

---

## State Transitions

```
SEGMENT STATE:
  unexplored
    ├─ (pick choice)
    ▼
  generating
    ├─ (generation complete)
    ▼
  generated
    ├─ (arc compression)
    └─ (if non-mainline)
    ▼
  archived

CHOICE STATE:
  choice.to_segment_id = null
    ├─ (first pick)
    ▼
  to_segment_id = segment.id
    └─ (locked, always same)

EPISODE RECAP STATE:
  (episode triggers end)
    ├─ (collect chain)
    ├─ (generate recap)
    └─ (save EpisodeRecap)
    ▼
  Recap.character_states_final
    └─ (becomes input for next episode)

ARC COMPRESSION STATE:
  (after 15 episodes)
    ├─ (find branches)
    ├─ (select candidates)
    ├─ (AI picks mainline)
    └─ (archive rest)
    ▼
  Arc.compression = result
  Arc.status = "compressed"
```

---

## Common Mistakes to Avoid

### ❌ Per-User Segments
```python
# WRONG: generating different segments for different users
def generate_segment_for_user(user_id, choice):
    segment = ai_generate()  # One per user
    save_to_user_folder(segment, user_id)
```

### ✅ Shared Segments
```python
# RIGHT: generating once, shared by all
def generate_segment(choice):
    segment = ai_generate()  # One total
    save_to_shared_graph(segment)
    # All users who pick this choice see same segment
```

---

### ❌ Per-User Episodes
```python
# WRONG: user session tracks episode state
class UserSession:
    episode_number = 3
    episode_tone = ["betrayal"]
    pacing_weight = 0.65
```

### ✅ Episode Context Baked in Segments
```python
# RIGHT: episode is just metadata on segment
class Segment:
    episode_number = 3
    episode_tone = ["betrayal"]
    pacing_weight = 0.65

class UserSession:
    current_segment_id = "seg_abc"  # That's it
    visited_segments = [...]
```

---

### ❌ Updating Segment Content
```python
# WRONG: changing segment after it's generated
segment.text_blocks = new_blocks  # DON'T DO THIS
segment.save()
```

### ✅ Immutable Segments
```python
# RIGHT: segments never change after generated
segment = Segment(...)
segment.status = GENERATED
segment.save()  # Lock it

# If you need different content, generate a new segment
# under different choices/contexts
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Load segment from cache | <10ms | In-memory |
| Load segment from disk | <100ms | JSON read |
| Walk episode chain | <50ms | O(20) |
| Generate segment (AI) | 5-10s | API call |
| Generate recap (AI) | 3-5s | API call |
| Compress arc (AI) | 10-20s | One call |
| Arc compression total | <5min | All segments updated |

---

## Debugging Checklist

### Segment Not Generating
- [ ] Choice.to_segment_id is null? (Should trigger generation)
- [ ] Is segment.status stuck in "generating"? (Check lock)
- [ ] Did AI fail? (Check logs)
- [ ] Parent segment loaded? (Walk parent chain)

### Episode Recap Missing
- [ ] Did segment have triggers_episode_transition = true?
- [ ] Is end_condition_proximity >= 0.8?
- [ ] Check EpisodeRecap files in disk

### Character State Wrong
- [ ] Check snapshot at episode start (correct?)
- [ ] Check all change_notes accumulated (complete?)
- [ ] Check recap reconciliation (AI output correct?)

### Archive Hiding Segments
- [ ] Is segment.status == ARCHIVED? (Check)
- [ ] Are queries excluding archived? (Check Story.get_segment)
- [ ] Can you recover archived segment? (Should be possible)

---

## Database Growth Estimates

```
After 1000 users, ~20K traversals:

Segment count:     ~2K
  Storage:         ~200 MB (100KB per segment)

Choice count:      ~4K (2 per segment)
  Storage:         ~100 KB

Episode recaps:    ~50-100 (depends on branches)
  Storage:         ~1 MB

User sessions:     1000
  Storage:         ~1 MB

Total:             ~202 MB per arc
```

Scale to 3 arcs: ~600 MB
Practical limit: 10+ arcs, 2+ GB storage

---

## Testing Quick Reference

### Unit Tests
```
test_segment_immutability()
  └─ Segment.status = GENERATED → locked

test_shared_traversal()
  └─ User A picks choice → seg X
     User B picks same choice → same seg X

test_context_building()
  └─ Context has all needed fields

test_episode_transition()
  └─ EP end triggers recap + new episode

test_character_reconciliation()
  └─ Snapshot + changes = final state
```

### Integration Tests
```
test_full_generation_flow()
  └─ Choice → context → generate → save

test_episode_recap()
  └─ Recap generated → final states correct

test_arc_compression()
  └─ Mainline picked → others archived

test_cli_modes()
  └─ Gameplay mode works
  └─ Exploration mode works
```

### Simulation Tests
```
test_multiple_users()
  └─ 10 sessions, same graph

test_concurrent_generation()
  └─ Same choice picked simultaneously

test_branch_divergence()
  └─ Different branches → different episodes
```
