# World Context Integration for Segment Generation

## Overview

Integrated world objects (locations, characters, factions) into the segment generation pipeline with active tracking and episode-end compaction. This ensures every scene generation has access to rich, focused world context.

**Commit**: `cc35a72 add world object context to segment generation with active tracking and episode compaction`

## Changes Made

### 1. StoryArc Model Enhancement (backend/app/models/story_arc.py:127-155)

Added active object tracking and episode evolution fields to **StoryArc**:

#### Section E: WORLD OBJECTS - ACTIVE TRACKING (NEW)
```python
active_locations: List[str]        # Location IDs that are active/important in this arc
active_characters: List[str]       # Character IDs that might appear in this arc
active_factions: List[str]         # Faction/group IDs relevant to this arc
```

**Purpose**: Keeps context focused by selecting which world objects are relevant to each arc, rather than passing all objects to every prompt.

#### Section F: EPISODE RUNNING STATE - CHARACTER & LOCATION EVOLUTION (NEW)
```python
episode_character_descriptions: Dict[str, str]  # character_id -> updated description (from episode end)
episode_location_descriptions: Dict[str, str]   # location_id -> updated description (from episode end)
```

**Purpose**: Stores evolved descriptions of characters and locations at episode boundaries, enabling next episode to see how the world has changed.

### 2. EpisodeRecap Model Enhancement (backend/app/models/episode_recap.py:75-90)

Added world state snapshots to **EpisodeRecap**:

```python
episode_character_descriptions: Dict[str, str]   # Snapshots of character descriptions at episode end
episode_location_descriptions: Dict[str, str]    # Snapshots of location descriptions at episode end
```

**Purpose**: Captures how characters and locations evolved during the episode for use in context building and arc updates.

### 3. EpisodeRecapGenerator Enhancement (backend/app/engine/episode_recap_generator.py:200-210, 819-871)

#### Updated recap generation flow (lines 200-210):
- Added call to `_update_arc_descriptions()` before saving recap
- Pulls running changes from the last segment of the episode
- Updates arc's character and location descriptions based on episode ending state

#### New method: `_update_arc_descriptions()` (lines 819-871)
```python
async def _update_arc_descriptions(
    self,
    arc_id: str,
    episode_segments: List[StorySegment],
    ending_states: Dict[str, 'CharacterState']
) -> None
```

**Flow**:
1. Load the arc for this episode
2. Get running changes from last segment
3. For each active character:
   - Build updated description from ending state
   - Store in `arc.episode_character_descriptions[char_id]`
4. For each active location:
   - Include current state in description
   - Store in `arc.episode_location_descriptions[loc_id]`
5. Save updated arc

**Example**:
```
Character "Thorne" before episode: "A skilled archer with a dark past"
Character "Thorne" after episode:  "A skilled archer with a dark past. (Status: alive, Mood: determined, Loyalty: +0.5)"
```

### 4. SegmentContextBuilder Enhancement (backend/app/engine/segment_context_builder.py:219-237, 1007-1162)

#### Updated context building (lines 219-237):
- Calls `_build_world_context()` to collect world objects
- Passes world context to generation prompts

#### New methods for world context:

**`_build_world_context(arc_id, episode_number, episode_chain)`** (lines 1007-1049)
- Orchestrates location, character, and faction context building
- Returns dict with all world objects

**`_get_locations_context(arc, episode_number)`** (lines 1051-1100)
```
Returns:
{
  'locations_all': [
    {'id': '...', 'name': '...', 'short_desc': '...'},  # All locations, short only
    ...
  ],
  'locations_active': [
    {'id': '...', 'name': '...', 'short_desc': '...', 'full_desc': '...', 'episode_state': '...'},  # Only active
    ...
  ]
}
```

**Logic**:
- ALL locations get short descriptions only (1-2 sentences)
- ACTIVE locations get full descriptions + episode state
- Active location descriptions come from `arc.episode_location_descriptions` (updated at episode end)

**`_get_characters_context(arc, episode_number, episode_chain)`** (lines 1102-1160)
```
Returns:
{
  'characters_all': [
    {'id': '...', 'name': '...', 'summary': '...'},  # All characters, summary only
    ...
  ],
  'characters_episode': [
    {'id': '...', 'name': '...', 'summary': '...', 'full_desc': '...', 'running_changes': [...]},  # Characters that might appear
    ...
  ]
}
```

**Logic**:
- ALL characters get short summaries only
- EPISODE characters (those in active_characters) get full descriptions + running changes
- Full descriptions come from `arc.episode_character_descriptions` (updated at episode end)
- Running changes collected from all segments in current episode

**`_get_factions_context(arc)`** (lines 1162-1162)
```
Returns:
{
  'factions_active': [
    {'id': '...', ...},
    ...
  ]
}
```

## Architecture: The Flow

### Segment Generation Context Building

```
SegmentContextBuilder.build_context()
├─ Load current arc
├─ Call _build_world_context()
│  ├─ _get_locations_context()
│  │  ├─ Get all locations (short desc only)
│  │  └─ For active locations: get full desc from arc.episode_location_descriptions
│  ├─ _get_characters_context()
│  │  ├─ Get all characters (summary only)
│  │  ├─ For active characters: get full desc from arc.episode_character_descriptions
│  │  └─ Collect running_changes from episode segments
│  └─ _get_factions_context()
│     └─ Get active factions
└─ Return context with locations_all, locations_active, characters_all, characters_episode, factions_active
```

### Episode Compaction (At Episode End)

```
EpisodeRecapGenerator.generate_recap()
├─ Collect all episode segments
├─ Extract character changes and states
├─ Generate recap via AI
├─ Call _update_arc_descriptions()
│  ├─ Get last segment's running_changes
│  ├─ For each active character:
│  │  └─ Update arc.episode_character_descriptions[char_id] with new state
│  ├─ For each active location:
│  │  └─ Update arc.episode_location_descriptions[loc_id] with current_state
│  └─ Save arc
└─ Save recap with episode_character_descriptions and episode_location_descriptions
```

## Data Flow: World Objects in Prompts

### What Goes Into Generation Prompts

**Short descriptions** (for reference/grounding):
```
All locations (short): 
  - The Veil Edge: "A barrier where reality grows thin"
  - Thornreach Grove: "An ancient forest shrouded in mystery"
  
All characters (summary):
  - Thorne: "A skilled archer with a dark past"
  - Nyx: "A mysterious figure who appears in shadows"
```

**Full descriptions + running state** (for active objects):
```
Active locations (full):
  - The Veil Edge: "A barrier where reality grows thin, where the fabric between worlds thins.
                    Proximity to the veil causes strange phenomena..."
    Current state: "Fluctuating with unstable magical energy"

Active characters (full):
  - Thorne: "A skilled archer with a dark past. Once served a warlord, now seeks redemption...
             (Status: alive, Mood: determined, Loyalty: +0.5)"
    Running changes: ["Thorne discovers the warlord still lives", "Thorne vows to stop him"]
```

## Key Design Principles

### 1. **Information Density**
- **All objects**: Brief, summary-level (saves tokens, prevents noise)
- **Active objects**: Complete details + evolution (enables rich generation)

### 2. **Episode-Level Tracking**
- Descriptions update at episode END, not segment-by-segment
- Reduces noise while capturing meaningful evolution
- Next episode starts with current world state baked in

### 3. **Running Changes Collection**
- Segments record `running_changes` list (AI-identified world impacts)
- Episode context collects these for active characters/locations
- Gives AI real-time feedback on what's changing

### 4. **Safe Defaults**
- All fields have defaults (empty lists/dicts)
- Existing arcs without active tracking still work
- No breaking changes to existing stories

## Integration Points

### For Context Builders
When building segment context, world data now available as:
```python
context = await builder.build_context(segment_id, user_choice)
context['locations_all']      # All locations, short
context['locations_active']   # Active locations, full
context['characters_all']     # All characters, summary
context['characters_episode'] # Episode characters, full + changes
context['factions_active']    # Relevant factions
```

### For Prompt Builders
Insert world objects into prompts:
```
=== WORLD OBJECTS ===

LOCATIONS (all):
{locations_all}

ACTIVE LOCATIONS (this arc):
{locations_active}

CHARACTERS (all):
{characters_all}

CHARACTERS THAT MIGHT APPEAR (this episode):
{characters_episode}

ACTIVE FACTIONS:
{factions_active}
```

### For Arc Generators
When creating/updating arcs, populate active objects:
```python
arc.active_locations = ["loc_veil_edge", "loc_thornreach"]
arc.active_characters = ["char_thorne", "char_nyx"]
arc.active_factions = ["faction_warlords", "faction_druids"]
arc.save()
```

### For Episode End Hooks
After episode recap generation, arc is auto-updated:
```python
# Character evolved during episode
arc.episode_character_descriptions["char_thorne"] = "A skilled archer... (Status: alive, Mood: determined, Loyalty: +0.5)"

# Location changed
arc.episode_location_descriptions["loc_veil_edge"] = "A barrier... Current state: Fluctuating with unstable magical energy"
```

## Testing & Verification

### Manual Testing Steps

1. **Create story with world**:
   ```bash
   python -m app.cli create-story-ai test_world --title "Test" --description "..."
   ```

2. **Check arc creation**:
   - Verify arc has empty `active_locations`, `active_characters` lists
   - Populate these manually or via generator

3. **Generate segments**:
   ```bash
   python -m app.cli run-story test_world
   ```
   - Context should include world objects
   - Check logs for `_build_world_context` execution

4. **Complete episode**:
   - Generate multiple segments to complete episode
   - Trigger episode transition
   - Verify `_update_arc_descriptions()` ran in logs
   - Check arc saved with updated descriptions

5. **Verify next episode context**:
   - Generate first segment of next episode
   - New context should use updated character/location descriptions

### What to Look For

✅ **Success indicators**:
- No errors in `_build_world_context()` execution
- World context keys present in generated context dict
- Arc descriptions updated after episode recap
- Next episode uses updated descriptions
- Prompts include location/character information

❌ **Failure indicators**:
- `Failed to build world context` warning logs
- Missing keys in context dict
- Arc descriptions unchanged after episode
- Descriptions not appearing in prompts

## Next Steps

### Immediate (Required for full integration)
1. **Update prompt builders** to use new world context keys
2. **Populate active tracking** in arc generators
3. **Test end-to-end** segment generation with world context
4. **Monitor token usage** with expanded context

### Short-term (Optimization)
1. **Implement faction model** properly (currently placeholder)
2. **Add faction descriptions** to context
3. **Smarter active object selection** (use episode themes to pick relevant characters)
4. **Location state tracking** (more detailed than just `current_state`)

### Medium-term (Enhancement)
1. **Character relationship evolution** tracking
2. **Location importance scoring** (which locations matter to this episode?)
3. **Faction alignment tracking** in character states
4. **Historical location/character snapshots** for reference

## Files Modified

```
backend/app/models/story_arc.py
├─ Lines 127-155: Added active_locations, active_characters, active_factions
└─ Lines 134-155: Added episode_character_descriptions, episode_location_descriptions

backend/app/models/episode_recap.py
├─ Lines 75-90: Added episode_character_descriptions, episode_location_descriptions

backend/app/engine/segment_context_builder.py
├─ Lines 219-237: Added world context building call
├─ Lines 1007-1049: New _build_world_context() method
├─ Lines 1051-1100: New _get_locations_context() method
├─ Lines 1102-1160: New _get_characters_context() method
└─ Lines 1162-1181: New _get_factions_context() method

backend/app/engine/episode_recap_generator.py
├─ Lines 200-210: Added _update_arc_descriptions() call
└─ Lines 819-871: New _update_arc_descriptions() method
```

## Example: Full Flow

### Starting State
```
Arc: "The Rise of the Northern Kingdom"
active_characters: ["char_thorne", "char_nyx"]
active_locations: ["loc_veil_edge", "loc_thornreach"]
episode_character_descriptions: {}  # Empty at arc start
episode_location_descriptions: {}
```

### Segment 1 Generation
```
Context includes:
- locations_all: All 12 locations with short descriptions
- locations_active: Veil Edge + Thornreach (full descriptions from location model)
- characters_all: All 8 characters with summaries
- characters_episode: Thorne + Nyx (full backgrounds)

Prompt: "Generate scene with these characters and locations..."
Result: "Thorne and Nyx meet at the Veil Edge..."
```

### Segment 2, 3... N (same episode)
```
Running changes accumulate:
- "Thorne discovers the warlord still lives"
- "Nyx warns about the veil instability"
- "Veil Edge shows signs of breaking down"

Context updated with running_changes
```

### Episode End - Recap Generation
```
Recap generated with theme exploration, character arcs, etc.

_update_arc_descriptions() runs:
- Last segment has: running_changes = ["Thorne vows to stop the warlord", "Veil Edge breached"]
- Character Thorne's ending state: status=alive, mood=determined, loyalty=0.5
- Location Veil Edge's ending state: current_state="Breached, portal to veil open"

Arc updated:
  episode_character_descriptions["char_thorne"] = 
    "A skilled archer seeking redemption... (Status: alive, Mood: determined, Loyalty: +0.5)"
  episode_location_descriptions["loc_veil_edge"] = 
    "A barrier where reality grows thin... Current state: Breached, portal to veil open"

Arc saved with new descriptions
```

### Episode 2, Segment 1 Generation
```
New context built with:
- locations_active: Veil Edge now has updated description: "... Current state: Breached, portal to veil open"
- characters_episode: Thorne has updated description: "... (Status: alive, Mood: determined, Loyalty: +0.5)"

Prompt now includes: "The veil is breached... Thorne, now determined to stop the warlord..."

Generation continues from world state at episode end
```

---

**Status**: ✅ COMPLETE - All changes integrated, committed, ready for prompt builder updates
