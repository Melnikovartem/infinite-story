# Arc and Episode Assignment in the Infinite Story Engine

## Overview

**Arc** and **episode** assignment is a critical part of the Epic 2 implementation. Here's how they work:

- **Arc ID (`arc_id`)**: A unique identifier for a narrative arc. Multiple segments can belong to the same arc. When an arc reaches 15 episodes, it gets compressed (E2-4) and a new arc is created.
- **Episode Number (`episode_number`)**: A counter that increments within an arc. When `triggers_episode_transition=True`, the episode resets and a new episode context is generated (E2-2).

## Key Data Structures

### StorySegment Fields (from `backend/app/models/story_segment.py`)

```python
arc_id: Optional[str] = Field(None)                    # Which narrative arc this belongs to
episode_number: int = Field(0)                         # Episode counter within the arc
episode_tone: str = Field("neutral")                   # Tone from E2-2 generation
episode_end_condition: str = Field("")                 # End condition from E2-2
segment_number_in_episode: int = Field(0)              # Segment count within current episode
triggers_episode_transition: bool = Field(False)       # If True, next segment starts new episode
```

### StoryArc Model (from `backend/app/models/story_arc.py`)

```python
title: str                              # Arc title
episode_ids: List[str]                  # List of episode IDs in this arc
episode_count: int                      # Total episodes in arc
start_segment_id: str                   # First segment of arc
current_segment_id: Optional[str]       # Latest segment in arc
premise: str                            # Core idea of arc
narrative_direction: str                # Where arc is heading
is_compressed: bool                     # Has arc been compressed (15+ episodes)?
compression_result: Optional[...]       # Result of compression if done
```

## Arc/Episode Assignment Flow

### 1. **Story Initialization**

When a story is first created:
1. Create initial `StoryArc` with:
   - `id`: Generated as `arc_{uuid}`
   - `title`: e.g., "Arc 1"
   - `start_segment_id`: Points to first segment
   - `episode_count`: 0 (grows as segments are added)

2. Create initial first segment with:
   - `arc_id`: Set to the initial arc ID
   - `episode_number`: 0 (first episode)
   - `segment_number_in_episode`: 0

### 2. **During Story Execution (Game Loop)**

When user makes a choice and a new segment is generated:

#### A. Context Building
`SegmentContextBuilder.build_context()` determines:
- Current `episode_number`
- Current `segment_number_in_episode`
- `should_transition_episode` flag
- `episode_tone`, `episode_end_condition` from previous episode

#### B. Episode Transition Detection
If `should_transition_episode=True`:
- Call **E2-2: `generate_new_episode_context()`** 
- Generates new tone, end_condition, narrative_direction for next episode
- Returns new episode context to use for new segment

#### C. New Segment Creation (in `StoryRunner._generate_segment()`)
```python
next_episode_number = context['episode_number']
next_segment_number = context['segment_number_in_episode'] + 1

# If transitioning to new episode, generate context first
if should_transition and self.generator and self.current_arc_id:
    new_ep_context = await recap_generator.generate_new_episode_context(
        self.current_arc_id,
        prev_recap
    )
    next_episode_number = context['episode_number'] + 1
    next_episode_tone = new_ep_context.get('tone_tags', [])[0]
    next_episode_end_condition = new_ep_context.get('end_condition', '')
    next_segment_number = 1  # Reset for new episode

# Create new segment with arc_id from parent
new_segment = StorySegment(
    arc_id=self.current_arc_id,           # Propagates parent's arc_id
    episode_number=next_episode_number,   # Incremented on transition
    episode_tone=next_episode_tone,       # From E2-2 or context
    episode_end_condition=next_episode_end_condition,
    segment_number_in_episode=next_segment_number,
    ...
)
```

### 3. **Arc Compression (E2-4)**

When an arc reaches **15 episodes**:
1. Call `ArcCompressor.compress_arc(arc_id)`
2. Find branching points in the narrative
3. Select canonical "mainline" branch with AI
4. Archive alternative branches
5. Create new arc for continuation
6. New segments generated after compression use new arc_id

## Arc and Episode in the System

### Current Arc Tracking (`StoryRunner.current_arc_id`)

```python
class StoryRunner:
    def __init__(self, story: Story, generator=None):
        self.current_arc_id: Optional[str] = None

    def start(self):
        # Initialize from start segment
        if self.current_segment.arc_id:
            self.current_arc_id = self.current_segment.arc_id
        
    def start_from_segment(self, segment_id: str):
        # Initialize from any segment
        segment = self.story.get_segment(segment_id)
        if segment.arc_id:
            self.current_arc_id = segment.arc_id
```

**Why it matters**: New segments inherit `arc_id` from `self.current_arc_id`, not from parent segment. This ensures all segments in an arc have the same arc_id value.

### Archive Safety (E2-5)

Archived segments (after compression) are safe by default:

```python
# In Story.get_segment()
def get_segment(self, segment_id: str, include_archived: bool = False):
    segment = StorySegment.load(...)
    if segment and segment.is_archived and not include_archived:
        return None  # Safe: archived segments hidden by default
    return segment
```

Only explicit `include_archived=True` allows access to archived segments.

## CLI/API Integration

### Story Creation (Not Currently in CLI)
Happens via API routes or internal story creation:
```python
# Example: backend/app/routes/stories.py
# No dedicated "create story" endpoint yet - stories are created with initial arc
```

### Running a Story (CLI)
```bash
python -m app.cli run-story story_name [--mode immersive|debug] [--resume]
```

Flow:
1. Load story
2. Initialize `StoryRunner` with generator
3. Call `runner.start()` → loads start segment, sets `current_arc_id`
4. Enter game loop
5. On choice → check for episode transition → generate new arc/episode context → create segment with inherited arc_id

## World Generation Status

**Not implemented in CLI yet.** The infrastructure exists:
- `StoryContext` model has `fundamental_truths` and `worldbuilding` fields
- Prompt builder integrates world context into generation
- But no CLI command to create/manage worlds

Would involve:
```bash
python -m app.cli create-world story_name [options]
```

## Testing Examples

From `backend/tests/conftest.py`:

```python
# Creating segments with arc/episode info
def create_test_story_with_episodes():
    story = factory_story()
    
    # Arc 1, Episode 1
    seg1 = factory_segment(story, id="seg_1", arc_id="arc_1", episode_number=1)
    seg2 = factory_segment(story, id="seg_2", arc_id="arc_1", episode_number=1, 
                          parent_segment_id="seg_1")
    
    # Arc 1, Episode 2 (after transition)
    seg3 = factory_segment(story, id="seg_3", arc_id="arc_1", episode_number=2,
                          parent_segment_id="seg_2", triggers_episode_transition=True)
    
    return story, [seg1, seg2, seg3]
```

## Summary: Assignment Rules

1. **First segment of story**: 
   - `arc_id` = new arc ID (generated)
   - `episode_number` = 0
   - `segment_number_in_episode` = 0

2. **Within same episode**:
   - `arc_id` = inherited from parent
   - `episode_number` = same as parent
   - `segment_number_in_episode` = parent + 1

3. **Episode transition** (when `triggers_episode_transition=True`):
   - `arc_id` = inherited from `StoryRunner.current_arc_id`
   - `episode_number` = parent + 1 (from E2-2 context)
   - `segment_number_in_episode` = 1 (reset for new episode)
   - First, **E2-2 generates new episode context** (tone, end_condition, direction)

4. **Arc compression** (after 15 episodes):
   - Call E2-4 `compress_arc(arc_id)`
   - Archive alternative branches
   - Create new arc for continuation
   - New segments use new `arc_id`

5. **Safe archive handling** (E2-5):
   - Archived segments excluded by default in `Story.get_segment()`
   - Must explicitly pass `include_archived=True` to access them
   - `Story.get_available_choices()` filters out archived destinations

## Files Involved

- **Core models**: `story_segment.py`, `story_arc.py`, `story.py`
- **Game loop**: `story_runner.py` (tracks `current_arc_id`, calls E2-2 on transitions)
- **Context building**: `segment_context_builder.py` (detects transitions)
- **Episode generation**: `episode_recap_generator.py` (E2-2)
- **Arc compression**: `arc_compressor.py` (E2-4)
- **CLI**: `cli.py` (run-story command)
- **Tests**: `test_episode_recap_generator.py`, `test_arc_compressor.py`, `test_story_arc.py`, conftest.py
