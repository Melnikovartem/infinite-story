# Arc Transition System (E2-5)

## Overview

The Arc Transition System manages what happens when a story arc completes after 15 episodes. It:

1. **Finalizes** the current arc (marks mainline, archives branches)
2. **Selects** the next arc (from pre-generated futures or generates new ones)
3. **Feeds context** from the completed arc to the next arc (world state, character descriptions, plot hooks)
4. **Transitions** the story runner to continue in the new arc

---

## Flow Diagram

```
Episode 15 Completes
        ↓
EpisodeRecapGenerator.generate_recap()
        ↓
_handle_arc_completion() called
        ↓
ArcTransitionManager.check_and_handle_arc_completion()
        ├─ _finalize_arc()
        │  ├─ Determine mainline (longest segment path)
        │  ├─ Mark mainline segments: is_mainline = True
        │  ├─ Archive non-mainline: status = ARCHIVED
        │  └─ Mark arc: is_finalized = True
        │
        ├─ _get_or_create_next_arc()
        │  ├─ Check for future arcs (is_future_arc=True)
        │  ├─ If found: activate first one
        │  └─ If not found: generate 3 new future arcs
        │
        └─ _feed_context_to_next_arc()
           ├─ Set previous_arc_id reference
           ├─ Copy character descriptions
           ├─ Copy location descriptions
           └─ Add unresolved mysteries as plot hooks
        
Next segment generation (Episode 16, Segment 1)
        ↓
StoryRunner._generate_segment()
        ├─ new_ep_context = generate_new_episode_context()
        ├─ Check next_episode_number > 15
        ├─ _check_arc_transition() → get next active arc
        └─ Update self.current_arc_id
```

---

## Key Components

### 1. ArcTransitionManager (`arc_transition_manager.py`)

Main orchestrator for arc completion and transition.

**Key Methods:**

- `check_and_handle_arc_completion(arc_id, episode_number)` - Main entry point
  - Returns the next arc ID or None
  
- `_finalize_arc(arc_id)` - Marks mainline and archives branches
  - Determines mainline using `_determine_mainline()`
  - Walks backward from leaf segments using `_walk_backward_to_root()`
  
- `_get_or_create_next_arc(completed_arc_id)` - Gets or generates next arc
  - Checks for future arcs first
  - Calls `_generate_future_arcs()` if none exist
  
- `_feed_context_to_next_arc()` - Transfers narrative context
  - Copies character/location descriptions
  - Creates arc summary
  - Carries forward unresolved mysteries

### 2. Model Changes

#### StorySegment
- Added `is_mainline: bool` - Marks segments in the canonical path

#### StoryArc
- Added `is_finalized: bool` - Arc has completed finalization
- Added `mainline_segment_count: int` - Number of mainline segments
- Added `is_future_arc: bool` - Pre-generated arc not yet active
- Added `is_active: bool` - Currently active for segment generation
- Added `previous_arc_id: str` - Reference to previous arc
- Added `previous_arc_summary: str` - Summary of previous arc's narrative

### 3. Integration Points

#### EpisodeRecapGenerator
- After saving recap (line 209): calls `_handle_arc_completion()`
- New method `_handle_arc_completion()` triggers the transition system

#### StoryRunner
- In `_generate_segment()`: when `next_episode_number > 15`
  - Calls `_check_arc_transition()`
  - Updates `self.current_arc_id`
  - Uses `next_arc_id` for segment creation

---

## Mainline Determination Algorithm

The "mainline" is the canonical narrative path. It's determined as the **longest chain of segments**.

**Algorithm:**

1. Build parent → child mapping from all arc segments
2. Find all leaf segments (no children in arc)
3. For each leaf, walk backward to root using `parent_segment_id`
4. Select the path with the most segments (most developed = canonical)

**Rationale:**

- Users' choices create branches at each segment
- The most explored/developed path is typically the "intended" mainline
- This approach doesn't require AI analysis or user voting
- Alternative branches (less developed) get archived

**Example:**

```
Segment A (start)
├─ Choice 1 → Segment B
│              ├─ Choice 2 → Segment D
│              └─ Choice 3 → Segment E
│                           └─ Choice 5 → Segment G (LEAF)
│
└─ Choice 4 → Segment C
               └─ Choice 6 → Segment F (LEAF)

Paths found:
1. A → B → D → ? (dead end)
2. A → B → E → G (length 4) ← MAINLINE (longest)
3. A → C → F (length 3)

Result: Segments A, B, E, G marked as is_mainline=True
        Segments C, D, F archived
```

---

## Context Feeding

When transitioning from completed arc to next arc:

### 1. Previous Arc Reference
```python
next_arc.previous_arc_id = completed_arc_id
```
Allows the story to track narrative continuity.

### 2. Character Evolution
```python
next_arc.episode_character_descriptions = 
    dict(completed_arc.episode_character_descriptions)
```
Characters carry forward evolved descriptions from the previous arc.

**Example:**
```
Previous Arc - Thorne:
"A proud knight seeking redemption after a betrayal"

After Episode 15 (evolved):
"A once-proud knight, now humble and scarred by betrayal,
 learning to trust again"

Next Arc - Thorne:
(Starts with evolved description from previous arc)
```

### 3. Location Evolution
```python
next_arc.episode_location_descriptions = 
    dict(completed_arc.episode_location_descriptions)
```
Locations maintain their state from the previous arc.

### 4. Plot Continuity
```python
next_arc.plot_hooks.extend(
    completed_arc.unresolved_mysteries
)
```
Unresolved mysteries from the previous arc become plot hooks for the next.

### 5. Arc Summary
```python
next_arc.previous_arc_summary = 
    await self._build_arc_summary(completed_arc_id)
```
A concise narrative summary of the mainline path, used for:
- Providing narrative context to AI generators
- Reminding users of what happened
- Maintaining story coherence

---

## Future Arc Generation

When no pre-generated future arcs exist:

1. `_generate_future_arcs()` is called
2. Calls `ArcGenerator.generate_future_arcs(previous_arc=completed_arc, count=3)`
3. Creates 3 new arc outlines with context from the completed arc
4. Marks them as `is_future_arc=True`
5. Saves to disk
6. Returns first one's ID

These future arcs are generated during the active arc and saved, so the next arc is ready immediately when the current arc completes.

---

## Arc Completion Threshold

**Constant:** `ARC_COMPLETION_THRESHOLD = 15` (episodes)

After episode 15 completes, the next episode triggers:
1. Episode 16, Segment 1 starts generation
2. `generate_new_episode_context()` is called for episode 16
3. `_check_arc_transition()` detects `next_episode_number > 15`
4. Arc transition is executed
5. Remaining segments of episode 16+ go into the new arc

---

## Error Handling

If any step fails:

- **Arc not found:** Log warning, continue without transition
- **Mainline determination fails:** Use longest path available
- **Arc generation fails:** Continue in current arc, log error
- **Context feeding fails:** Log warning, new arc starts without context

The system is designed to be resilient - failures don't break the story, they just reduce narrative quality.

---

## Future Enhancements

1. **AI-Based Mainline Selection:** Use AI to choose the "best" branch based on narrative coherence, not just length

2. **User Voting:** Allow users to vote on which branch should be canonical

3. **Multi-Branch Continuity:** Keep multiple branches as separate "alternate realities" rather than archiving

4. **Arc Metrics:** Track arc completion stats (number of branches, mainline length, archive rate)

5. **Context Quality:** Measure how well context transfers between arcs

6. **Dynamic Thresholds:** Adjust episode count threshold based on story type/user preference
