# Segment Context Builder - Current Implementation

## Overview

The `SegmentContextBuilder` (in `backend/app/engine/segment_context_builder.py`) is the **heart of generation context** in the system. It's called before every new segment is generated to provide the AI with all the information it needs to write the next scene.

**File**: `backend/app/engine/segment_context_builder.py` (227 lines)

## What It Does

Walks **backward through the parent chain** from the current segment to the episode start, collecting:
1. All previous segments in the current episode
2. Character state changes
3. Pacing information
4. Episode transition triggers

## Main Entry Point

```python
def build_context(
    self,
    current_segment_id: str,
    user_choice: str
) -> Dict[str, Any]:
    """Build generation context for a new segment."""
```

**Called from**: `StoryRunner._generate_segment()` via `SegmentContextBuilder(self.story).build_context(...)`

## Returned Context Dictionary

```python
{
    # Story progression
    'previous_segments': [
        "Segment 1 overview",
        "Segment 2 overview",
        # ... last 5 scenes
    ],
    
    # Character information
    'character_states': {
        "char_1": {"mood": "angry", "health": "wounded", ...},
        "char_2": {"location": "throne_room", ...},
        # Latest snapshot from current segment
    },
    'accumulated_changes': [
        "Character A confronted Character B",
        "A secret was revealed",
        "The barrier fell",
        # All change_notes from entire episode
    ],
    
    # Episode metadata
    'episode_number': 1,                    # Which episode we're in
    'episode_tone': "tense",                # Tone from segment
    'episode_end_condition': "The king must decide",  # From segment
    'segment_number_in_episode': 5,         # Scene count in episode
    
    # Transition signals
    'should_transition_episode': False,     # Should next segment start new episode?
    'pacing_weight': 0.125,                 # 0.0-1.0 progress through episode
    
    # Character focus
    'protagonist_id': "char_1",             # Main character this episode
    
    # User input
    'user_choice': "Confront the traitor",  # What user chose
}
```

## The Four Helper Methods

### 1. `_walk_episode_chain(segment_id)`

**Purpose**: Collect all segments in the current episode

**Algorithm**:
```
Start at current segment
Walk backward via parent_segment_id
Stop when episode_number changes or no parent exists
Return list in chronological order (start → current)
```

**Example**:
```
Current: Segment 5 (Episode 1)
    ↓ parent
Segment 4 (Episode 1)
    ↓ parent
Segment 3 (Episode 1)
    ↓ parent
Segment 2 (Episode 1)
    ↓ parent
Segment 1 (Episode 1)
    ↓ parent
None (start of chain)

Returns: [Seg1, Seg2, Seg3, Seg4, Seg5]
```

**Key Details**:
- Prevents circular references with visited set
- Logs warning if circular reference detected
- Returns empty list if segment not found

### 2. `_accumulate_changes(segment_chain)`

**Purpose**: Collect all character/location changes that happened this episode

**Algorithm**:
```
For each segment in the chain:
    Extract change_notes
    Add to accumulated list
Return combined list
```

**Example**:
```
Segment 1: ["The king entered the hall"]
Segment 2: ["A hooded figure appeared"]
Segment 3: ["The figure revealed themselves as the lost prince"]
Segment 4: ["Guards moved to arrest the prince"]
Segment 5: ["The king stayed their hands"]

Result: [
    "The king entered the hall",
    "A hooded figure appeared",
    "The figure revealed themselves as the lost prince",
    "Guards moved to arrest the prince",
    "The king stayed their hands"
]
```

**Used for**: Detecting episode transitions and informing AI of episode context

### 3. `_should_transition_episode(current_segment, changes)`

**Purpose**: Decide if the **next** segment should start a new episode

**Triggers episode transition if ANY of these are true**:

#### Rule 1: End condition proximity >= 0.8
```python
if current_segment.end_condition_proximity >= 0.8:
    return True
```
AI explicitly said "we're near the end condition" when generating this segment

#### Rule 2: Hard segment limit (max ~20 scenes per episode)
```python
if current_segment.segment_number_in_episode >= 18:
    return True
```
Safety valve to prevent infinitely long episodes

#### Rule 3: End condition keywords in changes
```python
end_keywords = ['chapter', 'end', 'conclusion', 'climax', 'finale']
for change in changes:
    if any(kw in change.lower() for kw in end_keywords):
        return True
```
Simple keyword matching to detect narrative endings

**Example**:
```
Segment 15, episode_number=1
- end_condition_proximity = 0.75 (not yet)
- segment_number_in_episode = 15 (< 18)
- changes don't have keywords
→ should_transition = False

User makes choice...

Segment 16, episode_number=1
- end_condition_proximity = 0.85 (CLOSE!)
- segment_number_in_episode = 16
- changes: ["The prophecy was fulfilled"]
→ should_transition = True

Next segment created with:
- episode_number = 2 (incremented)
- segment_number_in_episode = 1 (reset)
- E2-2 generates new tone/end_condition
```

### 4. `_calculate_pacing_weight(segment, will_transition)`

**Purpose**: Signal to AI how much "room" is left in the episode

**Algorithm**:

If transitioning: return 0.9 (very close to end)

Otherwise:
```python
weight = (segment_number_in_episode / 20) ^ 2
```

**Quadratic curve** (slower at start, accelerating toward end):

```
Segment#  →  Weight
1         →  0.0025    (very early, lots of room)
5         →  0.0625    (early)
10        →  0.25      (halfway)
15        →  0.5625    (getting close)
18        →  0.8100    (very close)
19        →  0.9025    (almost done)
20        →  1.00      (capped at 0.99)
```

**Used for**: AI knows pacing ("you have 15 scenes left" vs "you have 2 scenes left")

## Data Flow Example

### User makes choice in Segment 5 of Episode 1

```
StoryRunner._generate_segment() called
    │
    ├─ build_context() called
    │
    ├─ _walk_episode_chain("segment_5")
    │   └─ Returns: ["seg_1", "seg_2", "seg_3", "seg_4", "seg_5"]
    │
    ├─ _accumulate_changes(chain)
    │   └─ Returns: ["King entered", "Prince revealed", "Guards moved", ...]
    │
    ├─ _should_transition_episode(seg_5, changes)
    │   ├─ Check proximity (0.65, no transition)
    │   ├─ Check segment count (5 < 18, no transition)
    │   ├─ Check keywords (none found)
    │   └─ Returns: False
    │
    ├─ _calculate_pacing_weight(seg_5, False)
    │   └─ Returns: (5/20)^2 = 0.0625
    │
    └─ Return context dict:
        {
            'previous_segments': ["Seg 1 overview", "Seg 2 overview", ...],
            'character_states': {...},
            'accumulated_changes': [...],
            'episode_number': 1,
            'episode_tone': 'tense',
            'episode_end_condition': 'King must decide',
            'segment_number_in_episode': 5,
            'should_transition_episode': False,
            'pacing_weight': 0.0625,
            'protagonist_id': 'char_1',
            'user_choice': 'Confront the traitor'
        }

Then in _generate_segment():
    ├─ Build prompt with context
    ├─ Call AI generator
    ├─ Create new segment with:
    │   ├─ episode_number = 1 (same)
    │   ├─ segment_number_in_episode = 6 (incremented)
    │   ├─ episode_tone = 'tense' (same)
    │   └─ pacing_weight = 0.0625 (in prompt)
    └─ Save segment
```

## What It Doesn't Include (Gaps)

### Missing: Arc Context
- No `arc_id` included
- No arc lore, premise, themes
- No arc-level narrative direction
- No arc-specific character goals

### Missing: World Context
- No `StoryContext` (fundamental_truths, worldbuilding)
- No environmental/setting information
- No weather, time of day historical context

### Missing: Character Development Tracking
- No explicit character arc goals
- No long-term character journey tracking
- No relationship states between characters

### Missing: Advanced Pacing
- Pacing only based on segment count
- No "dramatic intensity" signal
- No "mystery resolution progress"

### Missing: Episode State
- No explicit "episode goals" tracking
- No "subplots resolution status"
- No "tension/release cycles"

## Integration with Prompt Building

The context is then used in `StoryRunner._build_generation_prompt()`:

```python
def _build_generation_prompt(self, context: Dict[str, Any]) -> str:
    prev_scenes = "\n".join(context['previous_segments'])
    changes_str = "\n".join(context['accumulated_changes'])
    
    prompt = f"""You are a creative storyteller continuing a narrative.

EPISODE CONTEXT:
- Episode: {context['episode_number']}
- Tone: {context['episode_tone']}
- End Condition: {context['episode_end_condition']}
- Scene {context['segment_number_in_episode']} of ~20
- Pacing: {context['pacing_weight']:.1%} toward episode end

PREVIOUS SCENES:
{prev_scenes}

CHARACTER STATES:
{json.dumps(context.get('character_states', {}), indent=2)}

ACCUMULATED CHANGES THIS EPISODE:
{changes_str}

USER CHOSE: "{context['user_choice']}"

Generate the next scene that:
1. Follows naturally from the choice
2. Respects character states and changes
3. Maintains the episode tone
4. Advances toward the end condition
5. Leaves room for {20 - context['segment_number_in_episode']} more scenes

Respond with a brief scene description (2-3 sentences).
"""
    return prompt
```

## Summary

| Aspect | Current | Notes |
|--------|---------|-------|
| **Backward chain walking** | ✅ Complete | Walks parent chain to episode start |
| **Change accumulation** | ✅ Complete | Collects all change_notes |
| **Episode transitions** | ✅ Complete | Detects via proximity/count/keywords |
| **Pacing weight** | ✅ Complete | Quadratic curve signals |
| **Arc context** | ❌ Missing | No arc lore/themes/direction |
| **World context** | ❌ Missing | No fundamental_truths/worldbuilding |
| **Character arcs** | ❌ Missing | No growth goals tracking |
| **Advanced pacing** | ❌ Missing | Only segment count based |
| **Episode state** | ❌ Missing | No goal/subplot tracking |

## Next Steps for Enhancement

1. **Add arc loading**: Load `StoryArc` and include lore/themes
2. **Add world context**: Load `StoryContext` and include worldbuilding
3. **Add character arcs**: Track growth goals from arc
4. **Enhance pacing**: Consider intensity, mystery progress
5. **Add episode state**: Track goals, subplots, tension cycles
