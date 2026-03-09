# Arc Enhancement Proposal: Adding Lore and Parameters to StoryArc

## Current State

The `StoryArc` model in `backend/app/models/story_arc.py` currently has:

**Existing Fields:**
```python
# Basic Info
title: str                          # Arc title
description: str                    # General description

# Tracking
episode_ids: List[str]              # Episodes in this arc
episode_count: int                  # Number of episodes
start_segment_id: str               # First segment
current_segment_id: Optional[str]   # Latest segment

# Thematic Guidance
premise: str                        # Core idea (e.g., "Power corrupts")
narrative_direction: str            # Where arc is heading

# Compression Status
is_compressed: bool                 # Has been compressed?
compression_result: Optional[...]   # Compression details
```

## Problems

1. **Arc context NOT used during generation** - Segments are generated without access to arc lore, premises, or thematic direction. The `_build_generation_prompt()` in `story_runner.py` only includes:
   - Episode tone/end-condition
   - Previous segments
   - Character states
   - Accumulated changes
   - **Missing: Arc premise, direction, lore, themes**

2. **No arc lore fields** - While `premise` and `narrative_direction` exist, there's no:
   - Detailed lore/worldbuilding specific to the arc
   - Key themes or symbolic elements
   - Character arcs/growth targets
   - Plot hooks or unresolved mysteries
   - Conflict drivers

3. **Arc metadata incomplete** - Missing:
   - Arc tone/mood (different from episode tone)
   - Central conflict description
   - Key locations/setting details for this arc
   - Important NPCs specific to arc
   - Timeline/urgency information

## Proposed Enhancement

### Add Fields to StoryArc

```python
class StoryArc(StoryBase):
    # ... existing fields ...
    
    # ============================================================================
    # LORE & THEMATIC GUIDANCE
    # ============================================================================
    
    # Core Identity
    premise: str = Field(
        "",
        description="Central idea (e.g., 'Power corrupts the innocent')"
    )
    narrative_direction: str = Field(
        "",
        description="Where the arc is heading overall"
    )
    
    # NEW: Detailed Lore
    lore: str = Field(
        "",
        description="Detailed worldbuilding/lore specific to this arc (500+ chars)"
    )
    central_conflict: str = Field(
        "",
        description="The main conflict driving this arc"
    )
    themes: List[str] = Field(
        default_factory=list,
        description="Key themes (e.g., ['betrayal', 'redemption', 'power'])"
    )
    
    # NEW: Narrative Elements
    unresolved_mysteries: List[str] = Field(
        default_factory=list,
        description="Questions the arc should answer or raise"
    )
    plot_hooks: List[str] = Field(
        default_factory=list,
        description="Key plot points or hooks still to be explored"
    )
    character_arc_goals: Dict[str, str] = Field(
        default_factory=dict,
        description="Character ID -> growth goal for this arc"
    )
    
    # NEW: Arc Tone & Mood
    arc_tone: str = Field(
        "neutral",
        description="Overall arc tone (different from episode tone)"
    )
    arc_mood: str = Field(
        "",
        description="Dominant emotional mood (e.g., 'tense', 'mysterious')"
    )
    
    # NEW: Environmental/Setting Context
    primary_locations: List[str] = Field(
        default_factory=list,
        description="Key location IDs featured in this arc"
    )
    arc_specific_npcs: Dict[str, str] = Field(
        default_factory=dict,
        description="NPC ID -> role in this arc (e.g., 'antagonist', 'mentor')"
    )
    
    # NEW: Pacing & Timeline
    urgency_level: str = Field(
        "moderate",
        description="Urgency of arc conflict (low/moderate/high/critical)"
    )
    expected_episode_range: tuple[int, int] = Field(
        (10, 15),
        description="Expected episode count (min, max) for arc resolution"
    )
    
    # NEW: Constraints & Guidelines
    tone_consistency: bool = Field(
        True,
        description="Should tone remain consistent across episodes?"
    )
    generation_guidelines: str = Field(
        "",
        description="Special instructions for AI generation specific to this arc"
    )
```

### Example Usage

```python
# Creating an arc with full lore
arc = StoryArc(
    id="arc_1",
    title="The Rise of the Northern Kingdom",
    premise="Power corrupts the innocent",
    narrative_direction="Building toward betrayal and fall",
    
    # NEW FIELDS
    lore="""
    The Northern Kingdom has existed for 200 years under the House of Winter.
    Recent prophecies suggest a child born under the red star will bring change.
    Old magic stirs in the mountains. The Winter lineage has never produced twins.
    """,
    
    central_conflict="The protagonist must choose: protect the heir or prevent civil war",
    themes=["power", "duty", "betrayal", "legacy"],
    
    unresolved_mysteries=[
        "Who sent the assassin in episode 2?",
        "What is the red star prophecy really about?",
        "Why did the king banish his brother?"
    ],
    
    plot_hooks=[
        "The hidden heir in the mountains",
        "The prophecy woman's cryptic warning",
        "The traitor in the council"
    ],
    
    character_arc_goals={
        "char_protagonist": "learn to trust despite past betrayal",
        "char_king": "balance power with compassion"
    },
    
    arc_tone="regal_and_ominous",
    arc_mood="tense with underlying dread",
    
    primary_locations=["loc_winterhold", "loc_northgate", "loc_prophecy_temple"],
    arc_specific_npcs={
        "npc_advisor": "confidant and political ally",
        "npc_prophecy_woman": "mysterious guide"
    },
    
    urgency_level="high",
    expected_episode_range=(12, 15),
    
    generation_guidelines="""
    Maintain aristocratic speech patterns. Reference winter/cold imagery.
    Every scene should hint at the prophecy. Show paranoia in court interactions.
    """
)
```

## Integration Points

### 1. Segment Generation (High Priority)

**File**: `backend/app/engine/story_runner.py`

Current `_build_generation_prompt()`:
```python
EPISODE CONTEXT:
- Episode: {context['episode_number']}
- Tone: {context['episode_tone']}
- End Condition: {context['episode_end_condition']}
```

**Add arc context**:
```python
async def _generate_segment(self, context: Dict[str, Any]) -> StorySegment:
    # Load the arc to get lore/themes
    arc = StoryArc.load(self.story.id, self.current_arc_id)
    
    prompt = self._build_generation_prompt(context, arc=arc)
    # ... rest of generation ...
```

Updated prompt:
```python
def _build_generation_prompt(self, context: Dict[str, Any], arc: Optional[StoryArc]) -> str:
    prompt = f"""...
ARC CONTEXT:
- Arc: {arc.title}
- Premise: {arc.premise}
- Themes: {', '.join(arc.themes)}
- Central Conflict: {arc.central_conflict}
- Lore: {arc.lore}
- Unresolved Mysteries: {arc.unresolved_mysteries}

Keep consistent with arc tone: {arc.arc_tone}
Advanced toward: {arc.narrative_direction}
{arc.generation_guidelines}
..."""
    return prompt
```

### 2. Episode Recap Generation (Medium Priority)

**File**: `backend/app/engine/episode_recap_generator.py`

Currently E2-2 generates:
```python
{
    'tone_tags': ['tense', 'mysterious'],
    'end_condition': 'A major revelation',
    'narrative_direction': '...'
}
```

**Enhance to include arc consistency**:
```python
async def generate_new_episode_context(
    self,
    arc_id: str,
    prev_recap: Optional[EpisodeRecap]
) -> Dict[str, Any]:
    # Load arc to ensure episode context aligns with arc
    arc = StoryArc.load(self.story.id, arc_id)
    
    # Generate episode tone that fits arc_tone
    # Ensure narrative_direction progresses toward arc resolution
    # Keep themes consistent across episodes
    context = {
        'tone_tags': [...],  # Must align with arc.arc_tone
        'end_condition': '...',
        'narrative_direction': '...',  # Should progress toward arc.narrative_direction
        'maintains_arc_themes': True,  # Explicit flag
        'character_development_focus': [...]  # Align with arc.character_arc_goals
    }
    return context
```

### 3. Arc Compression (Medium Priority)

**File**: `backend/app/engine/arc_compressor.py`

When compressing, preserve arc lore:
```python
async def compress_arc(self, arc_id: str) -> Optional[ArcCompressionResult]:
    arc = StoryArc.load(self.story.id, arc_id)
    
    # ... find mainline branch ...
    
    # Create new arc for continuation
    next_arc = StoryArc(
        id=f"arc_{uuid.uuid4().hex[:8]}",
        title=f"{arc.title} - Continued",
        # Carry forward themes and ongoing mysteries
        themes=arc.themes,
        unresolved_mysteries=arc.unresolved_mysteries,
        # Update based on what was resolved
        # ...
    )
    next_arc.save()
```

### 4. CLI Commands (Lower Priority)

Add commands to manage arc lore:
```bash
python -m app.cli create-arc story_name --title "Arc 1" --premise "..." --lore "..."
python -m app.cli update-arc story_name arc_id --themes "betrayal,redemption" 
python -m app.cli view-arc story_name arc_id
```

### 5. Story Context Integration (Medium Priority)

**File**: `backend/app/engine/segment_context_builder.py`

Add arc context to `build_context()`:
```python
def build_context(self, current_segment_id: str, user_choice: str):
    # ... existing code ...
    
    # NEW: Load arc context
    arc = StoryArc.load(self.story.id, current_seg.arc_id)
    
    return {
        # ... existing fields ...
        'arc_premise': arc.premise if arc else None,
        'arc_themes': arc.themes if arc else [],
        'arc_lore': arc.lore if arc else None,
        'central_conflict': arc.central_conflict if arc else None,
    }
```

## Migration Strategy

### Phase 1: Add Fields (Safe)
- Add all new fields to `StoryArc` model with sensible defaults
- Existing arcs will use defaults
- No breaking changes

### Phase 2: Use in Generation (Gradual)
- Update `_build_generation_prompt()` to include arc context
- Test with new stories first
- Monitor quality improvements

### Phase 3: E2-2 Enhancement (Iterative)
- Update `generate_new_episode_context()` to consider arc lore
- Ensure episode tone aligns with arc tone

### Phase 4: CLI Tools (As Needed)
- Add commands for arc creation/management
- Allow lore editing between episodes

## Example Arc Definitions

### Arc 1: Political Intrigue
```python
StoryArc(
    title="The Game of Thrones",
    premise="In the struggle for power, everyone has secrets",
    themes=["betrayal", "ambition", "honor"],
    central_conflict="Multiple factions vie for the throne",
    lore="Three noble houses compete after the king's death...",
    urgency_level="high",
    generation_guidelines="Every scene should have hidden agendas. Trust is rare."
)
```

### Arc 2: Quest
```python
StoryArc(
    title="The Prophecy Unfolds",
    premise="Destiny is written, but choices are free",
    themes=["fate", "heroism", "self-discovery"],
    central_conflict="The protagonist must reach the Forbidden Temple",
    unresolved_mysteries=[
        "What lies in the temple?",
        "Why was the prophecy hidden?",
        "Can it be changed?"
    ],
    plot_hooks=["The betrayer", "The guardian", "The secret truth"],
    urgency_level="critical",
    expected_episode_range=(14, 18)
)
```

## Questions for You

1. **Should arc_tone and arc_mood override episode_tone?** Or always coexist?
2. **Should character_arc_goals feed into E2-3 (reconciliation)?** To track character growth?
3. **Should unresolved_mysteries be automatically checked at episode transitions?** To ensure they're being advanced?
4. **Should there be an arc "success criteria"** to know when it should compress?
5. **Should lore be AI-generated** (given premise + previous arcs) or user-provided?
6. **Should arc_specific_npcs be linked to full Character objects** or just IDs + role descriptions?

## Files That Would Change

1. `backend/app/models/story_arc.py` - Add fields
2. `backend/app/engine/story_runner.py` - Use arc in prompt building
3. `backend/app/engine/episode_recap_generator.py` - Ensure episode context aligns
4. `backend/app/engine/segment_context_builder.py` - Pass arc context
5. `backend/app/cli.py` - Add arc management commands (optional)
6. Tests - Update test fixtures and add arc-specific tests

## Backward Compatibility

All new fields have defaults:
- `lore: str = ""`
- `themes: List[str] = []`
- `arc_tone: str = "neutral"`
- `generation_guidelines: str = ""`
- Etc.

Existing arcs will work fine with minimal guidance.
