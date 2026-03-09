# Episode Flush Architecture: Running Changes → Evolved Descriptions

## Overview

Implements proper world evolution through episodes:

1. **During episodes**: Segments accumulate `running_changes` (structured entity state changes)
2. **At episode end**: `EpisodeFlushGenerator` consolidates changes and uses AI to evolve character/location descriptions
3. **Next episode**: Generation context includes evolved descriptions, and `running_changes` show what's been happening
4. **At compression**: Arc compressor has full world context to make informed mainline selections

**Commits**: 
- `b2172a3 implement proper episode flush architecture: running changes -> evolved descriptions`
- `53dc950 add world context to arc compression for informed mainline selection`

---

## Architecture: The Complete Flow

```
┌─ EPISODE START ────────────────────────────────────────────┐
│                                                             │
│ Character/Location models have base descriptions          │
│ (updated from PREVIOUS episode flush or original)         │
│                                                             │
│ current_state: {} (empty, will accumulate during episode) │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─ SEGMENT 1 GENERATION ────────────────────────────────────┐
│                                                             │
│ 1. SegmentContextBuilder.build_context():                 │
│    - Collects episode_running_changes (empty first seg)   │
│    - Includes character/location current_state            │
│    - Passes context to prompt                             │
│                                                             │
│ 2. AI generates scene                                      │
│                                                             │
│ 3. StorySegment created with:                             │
│    - running_changes: [EntityChange(...), ...]            │
│      ├─ EntityChange(entity_id='char_thorne',             │
│      │  property='mood', from_value='hopeful',            │
│      │  to_value='determined')                             │
│      └─ EntityChange(entity_id='loc_veil',                │
│         property='stability', from_value='stable',        │
│         to_value='unstable')                              │
│                                                             │
│ 4. character.current_state += changes                     │
│    location.current_state += changes                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼ (repeat for segments 2...N)
         │
┌─ SEGMENT N: Episode Transition ───────────────────────────┐
│ triggers_episode_transition = True                        │
│ running_changes accumulated from all segments             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─ EPISODE RECAP GENERATION (E2-1) ──────────────────────────┐
│                                                             │
│ EpisodeRecapGenerator.generate_recap():                   │
│ - Creates recap with episode summary, themes, etc.        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─ EPISODE FLUSH (NEW STEP) ────────────────────────────────┐
│                                                             │
│ EpisodeFlushGenerator.flush_episode_changes():            │
│                                                             │
│ 1. Collect all running_changes from all episode segments  │
│ 2. Group by entity (character/location)                   │
│ 3. For each character:                                    │
│    - Build evolution prompt with changes                  │
│    - Call AI: "Evolve this character description based on │
│      these changes"                                       │
│    - Update character.description with evolved text       │
│    - Reset character.current_state = {}                   │
│    - character.save()                                     │
│                                                             │
│ 4. For each location:                                     │
│    - Build evolution prompt with changes                  │
│    - Call AI: "Evolve this location description based on  │
│      these changes"                                       │
│    - Update location.description with evolved text        │
│    - Reset location.current_state = {}                    │
│    - location.save()                                      │
│                                                             │
│ 5. Return summary of flushed entities                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─ NEXT EPISODE, SEGMENT 1 GENERATION ───────────────────────┐
│                                                             │
│ Character/location models NOW have evolved descriptions   │
│                                                             │
│ SegmentContextBuilder.build_context():                    │
│ - Collects episode_running_changes (empty again)          │
│ - Includes evolved character/location descriptions        │
│ - Includes empty current_state (reset at flush)           │
│                                                             │
│ AI generates scene with evolved world:                    │
│ "Thorne, now determined to find the warlord..."          │
│ "The veil, now unstable and dangerous..."                │
│                                                             │
│ New segment gets new running_changes for this episode     │
│ And the cycle continues...                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### EntityChange (NEW - in StorySegment)

```python
class EntityChange(BaseModel):
    entity_id: str           # "char_thorne" or "loc_veil"
    entity_type: str         # "character" or "location"
    entity_name: str         # "Thorne" or "Veil Edge" (for human reference)
    property: str            # "mood", "status", "stability", "description"
    from_value: Optional[str]  # Previous value
    to_value: Optional[str]    # New value
    description: str         # Human-readable: "Thorne's mood changed..."
```

### StorySegment (UPDATED)

```python
running_changes: List[EntityChange]  # NEW
  # Structured changes that occurred in this segment
  # These accumulate during the episode
  # At episode-end, EpisodeFlushGenerator processes these

change_notes: List[str]  # Already existed
  # Human-readable notes (parallel to running_changes)
```

### StoryCharacter (UPDATED)

```python
description: str  # Evolves at episode-end through flush

current_state: Dict[str, Any]  # NEW
  # Current state during episode: {'mood': '...', 'status': '...', 'location': '...', ...}
  # Reset to {} at episode-end flush
  # Accumulates as segments update it based on running_changes
```

### StoryLocation (UPDATED)

```python
description: str  # Evolves at episode-end through flush

current_state: Dict[str, Any]  # NEW
  # Current state during episode: {'stability': '...', 'accessibility': '...', ...}
  # Reset to {} at episode-end flush
  # Accumulates as segments update it based on running_changes
```

### SegmentContextBuilder (UPDATED)

```python
context['episode_running_changes']  # NEW
  # All EntityChange objects from segments so far this episode
  # Passed to prompt so AI knows what's been happening
```

---

## EpisodeFlushGenerator: The Key Component

Located in: `backend/app/engine/episode_flush_generator.py`

### Main Method: `flush_episode_changes()`

**Input**:
- `episode_segments`: All segments that were generated this episode
- `episode_number`: Which episode is being flushed
- `arc_id`: Optional arc context

**Process**:
1. Collect all `running_changes` from all segments
2. Group changes by entity_id and entity_type
3. For each character: evolve description with AI
4. For each location: evolve description with AI
5. Save updated character/location models
6. Reset their `current_state` for next episode

**Output**:
```python
{
    'flushed_characters': {
        'char_thorne': 'A skilled archer seeking...',
        'char_nyx': 'A mysterious figure now...'
    },
    'flushed_locations': {
        'loc_veil': 'A barrier now showing...',
        'loc_grove': 'An ancient forest now...'
    },
    'changes_summary': 'Character descriptions updated for 2 entities, ...'
}
```

### AI Evolution Prompts

**For Characters**:
```
ORIGINAL DESCRIPTION:
A skilled archer with a dark past

BACKGROUND:
Once served a warlord, now seeks redemption

CHANGES DURING EPISODE 1:
- Thorne's mood changed from hopeful to determined
- Thorne discovered the warlord still lives

TASK:
Write evolved description (2-3 sentences) that:
1. Incorporates original traits
2. Reflects episode changes
3. Maintains continuity
4. Shows growth/change

EVOLVED DESCRIPTION:
[AI writes new description incorporating changes]
```

**For Locations**:
```
ORIGINAL DESCRIPTION:
A barrier where reality grows thin

CHANGES DURING EPISODE 1:
- Veil stability changed from stable to unstable
- Veil accessibility became breached

TASK:
Write evolved description (2-3 sentences) that:
1. Incorporates original features
2. Reflects episode changes
3. Maintains geographical consistency
4. Shows how location was affected

EVOLVED DESCRIPTION:
[AI writes new description incorporating changes]
```

---

## Integration Points

### 1. During Segment Generation

**File**: `backend/app/engine/segment_context_builder.py`

**New field in context**:
```python
context['episode_running_changes'] = [
    {
        'entity_id': 'char_thorne',
        'property': 'mood',
        'from_value': 'hopeful',
        'to_value': 'determined',
        'description': 'Thorne mood changed...'
    },
    # ... more changes from earlier segments
]
```

**Method**: `_collect_episode_running_changes(segment_chain)`

### 2. At Episode End

**File**: `backend/app/engine/episode_recap_generator.py`

**After recap generation**, add:
```python
flush_gen = EpisodeFlushGenerator(self.story, self.generator)
flush_result = await flush_gen.flush_episode_changes(
    episode_segments=episode_segments,
    episode_number=episode_number,
    arc_id=arc_id
)
```

### 3. During Arc Compression

**File**: `backend/app/engine/arc_compressor.py`

**New method**: `_build_world_context_for_compression(arc)`

**Enhanced prompt** now includes:
```
=== WORLD STATE AT COMPRESSION ===

CHARACTERS (evolved through episodes):
- Thorne: A skilled archer now determined...
  State: mood: determined, status: alive, ...

LOCATIONS (evolved through episodes):
- Veil Edge: A barrier now unstable...
  State: stability: unstable, accessibility: breached, ...

FACTIONS:
- faction_druids
- faction_court
```

---

## Example: Full Episode Flow

### Episode Start
```
Character "Thorne":
  description: "A skilled archer with a dark past"
  current_state: {}

Location "Veil Edge":
  description: "A barrier where reality grows thin"
  current_state: {}
```

### Segment 1
```
Generation context includes:
  episode_running_changes: []  # Empty, first segment

AI generates scene → segment created with:
  running_changes: [
    EntityChange(
      entity_id='char_thorne',
      property='mood',
      from_value='hopeful',
      to_value='determined'
    ),
    EntityChange(
      entity_id='loc_veil',
      property='stability',
      from_value='stable',
      to_value='unstable'
    )
  ]

After generation:
  character.current_state = {'mood': 'determined'}
  location.current_state = {'stability': 'unstable'}
```

### Segment 2
```
Generation context includes:
  episode_running_changes: [
    {entity_id: 'char_thorne', property: 'mood', ...},
    {entity_id: 'loc_veil', property: 'stability', ...}
  ]

AI generates next scene with context of what's changed
New segment has new running_changes

character.current_state = {'mood': 'determined', 'location': 'veil_edge'}
location.current_state = {'stability': 'unstable', 'accessibility': 'breached'}
```

### Segment 3...N (episode continues)

Running changes accumulate...

### Episode End - Flush

```
EpisodeFlushGenerator.flush_episode_changes():

1. Collect all running_changes:
   [
     {char_thorne: mood from hopeful to determined},
     {char_thorne: location to veil_edge},
     {char_nyx: mood to cautious},
     {loc_veil: stability to unstable},
     {loc_veil: accessibility to breached},
     ...
   ]

2. AI Evolution Prompts:

   For Thorne:
   "A skilled archer with a dark past.
    [Changes: mood determined, location veil_edge, ...]
    → Write evolved description"
   
   Result: "A determined archer seeking the warlord, 
           recently arrived at the unstable veil edge."

   For Veil Edge:
   "A barrier where reality grows thin.
    [Changes: stability unstable, accessibility breached, ...]
    → Write evolved description"
   
   Result: "A barrier once stable, now destabilized with 
          breaches to other realms showing."

3. Update models:
   character.description = "A determined archer seeking..."
   location.description = "A barrier now destabilized..."
   character.current_state = {}  # Reset
   location.current_state = {}   # Reset
   Save both models
```

### Next Episode, Segment 1

```
Character "Thorne":
  description: "A determined archer seeking the warlord..."  # EVOLVED!
  current_state: {}  # Reset

Location "Veil Edge":
  description: "A barrier now destabilized with breaches..."  # EVOLVED!
  current_state: {}  # Reset

Generation context:
  episode_running_changes: []  # Empty again, new episode
  
But prompts now use evolved descriptions:
"Thorne, a determined archer seeking the warlord,
 arrives at the Veil Edge, a barrier now destabilized..."

Cycle continues with new running_changes accumulating...
```

---

## Key Design Decisions

### 1. **Running Changes are Structured**
- Not just strings, but EntityChange objects
- Track entity_id, property, from/to values
- Easier to process, group, and reason about

### 2. **Current State is Episode-Local**
- Characters/locations have `current_state` dict
- Tracks mood, status, location, stability, etc.
- Reset at episode-end when descriptions are flushed
- Prevents descriptions from growing indefinitely

### 3. **AI Evolves, Not Appends**
- AI synthesizes changes into new description
- Doesn't append "(mood: determined, location: X)"
- Results in natural, narrative prose
- Example: "Thorne became determined" not "Thorne (mood: determined)"

### 4. **Flush Happens After Recap, Not During**
- Episode recap summarizes the episode
- Flush consolidates changes into updated descriptions
- Next episode starts with evolved world state
- Clean separation of concerns

### 5. **World Context for Compression**
- Compressor AI sees evolved character/location states
- Makes informed mainline selection
- Ensures coherence across branch merge

---

## Files Changed

```
backend/app/models/story_segment.py
├─ Lines 37-69: Added EntityChange model
├─ Line 145-152: Added running_changes field

backend/app/models/story_character.py
├─ Line 63-71: Added current_state field

backend/app/models/story_location.py
├─ Line 18-28: Added current_state field

backend/app/engine/segment_context_builder.py
├─ Lines 161-164: Added episode_running_changes to context
├─ Lines 1040-1071: Added _collect_episode_running_changes() method

backend/app/engine/episode_flush_generator.py
└─ NEW FILE: Complete episode flush implementation

backend/app/engine/arc_compressor.py
├─ Lines 243-290: Enhanced _ai_select_mainline with world context
└─ Lines 303-343: Added _build_world_context_for_compression()
```

---

## Integration Checklist

- [x] Add EntityChange model to StorySegment
- [x] Add running_changes field to StorySegment
- [x] Add current_state to StoryCharacter
- [x] Add current_state to StoryLocation
- [x] Create EpisodeFlushGenerator
- [x] Update SegmentContextBuilder to collect running_changes
- [x] Update ArcCompressor to use world context
- [ ] **TODO**: Update episode recap generator to call flush_episode_changes()
- [ ] **TODO**: Update segment generation to populate running_changes
- [ ] **TODO**: Update segment generation to update character/location current_state
- [ ] **TODO**: Test end-to-end with real story generation

---

## Next Steps

1. **Hook up episode flush in episode_recap_generator.py**:
   - After recap generation, call EpisodeFlushGenerator
   - Log flush results

2. **Populate running_changes during generation**:
   - Scene generator needs to create EntityChange objects
   - Based on AI's character_status_change and location_status_change

3. **Update current_state during generation**:
   - After segment creation, update character/location current_state
   - Based on running_changes and segment status updates

4. **Test with AI generation**:
   - Generate multi-segment episodes
   - Trigger episode end
   - Verify descriptions are flushed
   - Check next episode uses evolved descriptions
   - Verify running_changes appear in next segment context

5. **Monitor description evolution**:
   - Ensure descriptions stay coherent across episodes
   - Verify AI isn't making inconsistent changes
   - Adjust prompts if needed

---

## Example Test Scenario

1. Create story: "The Rise of Thorne"
2. Define active characters: [Thorne, Nyx]
3. Define active locations: [Veil Edge, Forest]
4. Generate Episode 1 Segment 1
   - Thorne discovers something important
   - Veil becomes unstable
5. Generate Episode 1 Segment 2
   - Thorne meets Nyx
   - They investigate the veil
6. Complete Episode 1 (trigger transition)
   - Generate recap
   - **Flush episode changes** ← Descriptions should evolve here
7. Generate Episode 2 Segment 1
   - Check: Does context show evolved descriptions?
   - Does Thorne prompt mention their discovery?
   - Does Veil prompt mention instability?
   - Are running_changes empty (new episode)?
8. Verify: World state evolved across episode boundary

---

**Status**: ✅ COMPLETE - All architecture implemented, ready for integration with generation pipeline
