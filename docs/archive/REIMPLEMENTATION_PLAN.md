# Reimplementation Plan: Shared Graph with Narrative Overlays

## Overview

This plan outlines how to transform the current infinite branching system into a **shared segment graph with narrative overlay (episodes/arcs)** system.

### Key Changes
- **Segments are shared across users** (immutable nodes in a DAG)
- **Episodes/arcs are narrative context**, not structural containers
- **Character state is a snapshot + running log** (reconciled at episode recaps)
- **Episode branching** (4a, 4b, 4c variants) at episode boundaries
- **Arc compression** after 10-15 episodes (pick mainline, archive rest)
- **User sessions are just cursors** (current segment + visited segments)

---

## Phase 1: Core Graph Refactoring (Weeks 1-2)

### Goal
Transition from per-user segment generation to shared segment graph with immutable states.

### 1.1 Enhance Segment Model

**File: `backend/app/models/story_segment.py`**

Add new fields:

```python
class SegmentStatus(str, Enum):
    """Segment lifecycle states."""
    UNEXPLORED = "unexplored"      # Placeholder, not generated yet
    GENERATING = "generating"      # Currently being generated (lock)
    GENERATED = "generated"         # Immutable, safe to read/traverse
    ARCHIVED = "archived"           # Soft-deleted during arc compression

class Segment(StoryBlock):
    # ... existing fields ...
    
    # Segment lifecycle
    status: SegmentStatus = SegmentStatus.UNEXPLORED
    parent_segment_id: Optional[str] = None  # Points to generating segment
    parent_choice_id: Optional[str] = None    # Which choice led to this
    
    # Episode context (baked at generation time)
    arc_id: Optional[str] = None
    episode_number: Optional[int] = None
    episode_tone: List[str] = Field(default_factory=list)
    episode_end_condition: Optional[str] = None
    segment_number_in_episode: Optional[int] = None
    pacing_weight: Optional[float] = None
    protagonist_id: Optional[str] = None
    
    # Character state tracking
    character_states: Dict[str, CharacterState] = Field(default_factory=dict)
    # ^^^ Snapshot at episode start
    change_notes: List[Dict[str, str]] = Field(default_factory=list)
    # ^^^ Changes introduced by THIS segment only
    
    # Episode signals
    end_condition_proximity: Optional[float] = None  # 0.0-1.0
    protagonist_alive: bool = True
    triggers_episode_transition: bool = False
```

**Changes:**
- Remove: `incoming_choices`, `outgoing_choices` (these are built by choices, not segments)
- Add: parent tracking, episode context, character state, episode signals
- Status field for immutability

---

### 1.2 Enhance Choice Model

**File: `backend/app/models/story_choice.py`**

```python
class StoryChoice(StoryBlock):
    # ... existing ...
    from_segment_id: Optional[str] = None
    to_segment_id: Optional[str] = None  # null = unexplored
    text: str
    click_count: int = 0
```

**Changes:**
- Keep simple — choices just point to segments
- When `to_segment_id` is null, the choice is "unexplored"
- When set, it's immutable (points to a generated segment)

---

### 1.3 Create Episode Recap Model

**File: `backend/app/models/episode_recap.py` (NEW)**

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class EpisodeRecap(BaseModel):
    """Summary of a completed episode."""
    
    id: str
    arc_id: str
    episode_number: int
    branch_id: str  # Which path through the graph triggered this recap
    trigger_segment_id: str  # Last segment of this episode
    
    # Generated content
    title: str
    summary: str
    
    # State at episode end
    character_states_final: Dict[str, "CharacterState"] = Field(default_factory=dict)
    world_state_changes: List[str] = Field(default_factory=list)
    
    # Narrative hooks for next episode
    narrative_threads: List[str] = Field(default_factory=list)
    
    # Metadata
    segment_count: int
    protagonist_id: str
    protagonist_alive: bool
```

**Stored at:** `.infinite_story_data/<story_id>/episoderecap/<recap_id>.json`

---

### 1.4 Enhance Arc Model

**File: `backend/app/models/story_arc.py` (NEW)**

```python
class ArcCompressionResult(BaseModel):
    """Result of arc compression/mainline selection."""
    mainline_segment_ids: List[str]  # Segments that are canon
    archived_segment_ids: List[str]  # Segments that are hidden
    selected_branch_id: str
    ai_reasoning: str

class StoryArc(StoryBlock):
    """Container for arc metadata and compression."""
    
    id: str
    world_id: str
    arc_number: int
    
    title: str
    description: str
    key_events: List[str]
    
    status: str  # "planned" | "active" | "compressed"
    compression: Optional[ArcCompressionResult] = None
```

**Stored at:** `.infinite_story_data/<story_id>/storyarc/<arc_id>.json`

---

### 1.5 Simplify UserSession Model

**File: `backend/app/models/session_state.py` (SIMPLIFY)**

```python
class UserSession:
    """Simplified: just a cursor on the segment graph."""
    
    user_id: str
    world_id: str
    current_segment_id: str
    visited_segments: Set[str] = Field(default_factory=set)
    
    def add_visited(self, segment_id: str):
        self.visited_segments.add(segment_id)
    
    def move_to(self, segment_id: str):
        self.current_segment_id = segment_id
        self.add_visited(segment_id)
```

**What's removed:**
- Per-user episode tracking
- Per-user character states
- Per-user protagonist tracking (this lives on segments now)

---

### 1.6 Migrate Existing Data (Script)

**File: `backend/scripts/migrate_v1_to_v2.py` (NEW)**

This is important! We need to migrate existing stories from the old format to the new one.

```python
"""
Migrate stories from infinite branching to shared segment graph format.

Old format: Each segment is an isolated node with hard choices
New format: Segments are immutable, shared, with episode context

Strategy:
1. Load existing story
2. Build segment graph from existing segments/choices
3. Assign episode numbers and arc info (default: first 20 = ep 1, etc.)
4. Assign default protagonist (first character present in segment 1)
5. Create empty character_states for all segments
6. Mark all segments as "generated"
7. Save in new format
"""

def migrate_story(story_id: str):
    pass  # Implementation details in phase 1 tasks
```

---

## Phase 2: Generation Pipeline Refactoring (Weeks 2-3)

### Goal
Implement new generation flow: check for unexplored choice → determine episode context → generate segment with shared state.

### 2.1 Create Segment Context Builder

**File: `backend/app/engine/segment_context_builder.py` (NEW)**

```python
class SegmentContextBuilder:
    """
    Builds generation context for a new segment.
    
    Walks parent chain to:
    1. Collect episode context
    2. Accumulate character state changes
    3. Determine if episode should transition
    4. Calculate pacing pressure
    """
    
    def build_context(self, parent_segment: Segment, parent_choice: Choice, 
                      generator_params: dict) -> dict:
        """
        Returns context dict for passing to AI generation.
        
        Includes:
        - Episode context (tone, end_condition, pacing)
        - Character states (snapshot + accumulated changes)
        - Arc info
        - Recent segment summaries
        - Pacing instructions
        """
        pass
    
    def _walk_parent_chain(self, segment: Segment) -> Tuple[Segment, List[dict]]:
        """Find episode start and accumulated changes."""
        pass
    
    def _should_transition_episode(self, parent_segment: Segment) -> bool:
        """Check if parent segment signals end of episode."""
        pass
    
    def _generate_new_episode_context(self, arc: StoryArc, 
                                      previous_recap: EpisodeRecap) -> dict:
        """Generate tone, end_condition, etc. for next episode."""
        pass
```

### 2.2 Update Segment Generation

**File: `backend/app/engine/story_runner.py`**

Modify `make_choice()` or create new `traverse_or_generate()`:

```python
async def traverse_or_generate(self, choice_id: str) -> Segment:
    """
    When user picks a choice:
    1. If choice.to_segment_id is set → return existing segment
    2. If null → check lock, generate, update choice, return
    """
    choice = self.story.get_choice(choice_id)
    current = self.current_segment
    
    if not choice.from_segment_id == current.id:
        raise ValueError("Choice not from current segment")
    
    # TRAVERSE (segment already exists)
    if choice.to_segment_id:
        next_segment = self.story.get_segment(choice.to_segment_id)
        self.current_segment = next_segment
        self.visited_segments.add(next_segment.id)
        return next_segment
    
    # GENERATE (new segment needed)
    # 1. Lock to prevent duplicate generation
    choice.status = "generating"
    choice.save()
    
    try:
        # 2. Build context
        context = SegmentContextBuilder().build_context(
            current, choice, self.config
        )
        
        # 3. Generate with AI
        new_segment = await self._generate_segment(context)
        
        # 4. Link choice
        choice.to_segment_id = new_segment.id
        choice.save()
        
        # 5. Move cursor
        self.current_segment = new_segment
        self.visited_segments.add(new_segment.id)
        
        return new_segment
        
    except Exception as e:
        # Unlock on failure
        choice.status = None
        choice.save()
        raise
```

### 2.3 Episode Transition at Generation Time

**File: `backend/app/engine/segment_context_builder.py`**

```python
def _should_transition_episode(self, parent_segment: Segment) -> bool:
    """
    Determine if episode should end when generating new segment from parent.
    
    Triggers if:
    1. Parent has end_condition_proximity >= 0.8, OR
    2. Parent is segment ~20 of episode, OR
    3. Parent's end_condition is explicitly met
    """
    if parent_segment.end_condition_proximity is None:
        return False
    
    # Strong signal from parent
    if parent_segment.end_condition_proximity >= 0.8:
        return True
    
    # Segment count limit
    if parent_segment.segment_number_in_episode and \
       parent_segment.segment_number_in_episode >= 18:
        return True
    
    return False

def _generate_new_episode_context(self, arc: StoryArc, 
                                  previous_recap: EpisodeRecap) -> dict:
    """
    Generate episode for new branch.
    
    Gets:
    - Random tone word from pool
    - Arc storyline
    - Previous episode recap
    - Recaps of 1-2 prior episodes in arc
    
    AI generates:
    - tone_tags (2-3)
    - end_condition
    - suggested narrative arc
    """
    pass
```

---

## Phase 3: Episode Recap System (Weeks 3-4)

### Goal
Implement episode-end detection, recap generation, and state reconciliation.

### 3.1 Episode Recap Generation

**File: `backend/app/engine/episode_recap_generator.py` (NEW)**

```python
class EpisodeRecapGenerator:
    """
    When a segment triggers episode transition:
    1. Walk back to episode start
    2. Collect all change_notes
    3. Call AI to generate recap
    4. Save recap
    5. Return new episode context
    """
    
    async def generate_recap(self, trigger_segment: Segment, 
                            generator: TextGenerator) -> EpisodeRecap:
        """
        Build recap from the chain of segments in the completed episode.
        
        Inputs to AI:
        - Episode tone/end_condition
        - Segment chain (or summaries)
        - All change_notes accumulated
        - Arc context
        
        Outputs from AI:
        - title, summary
        - character_states_final
        - world_state_changes
        - narrative_threads
        """
        pass
    
    def _walk_episode_chain(self, segment: Segment) -> List[Segment]:
        """Walk up parent chain until episode start."""
        pass
    
    def _reconcile_character_states(self, segment_chain: List[Segment],
                                   all_change_notes: List[dict]) -> dict:
        """
        Reconcile character states from snapshot + all changes.
        
        For each character:
        1. Start with episode start snapshot
        2. Apply all change_notes in order
        3. Result is final state
        """
        pass
```

### 3.2 Character State Reconciliation

This is complex. Let me think through an example:

```
Episode 1 starts:
  character_states: { "eira": { status: "alive", mood: "hopeful" } }

Segment 1: change_notes: [{ char: "eira", note: "learned she's a mage" }]
Segment 5: change_notes: [{ char: "eira", note: "betrayed by mentor" }]
Segment 19: change_notes: [{ char: "eira", note: "swore revenge" }]

Recap reconciles:
  eira's final state = {
    status: "alive",
    mood: "determined",  // evolved from hopeful → betrayed → revenge
    knowledge: [...added during episode...]
    relationships: {...updated...}
  }
```

**Implementation approach:**
- Keep change_notes as simple strings initially
- At recap time, AI reads the chain and interprets what the final state should be
- Prompt includes both snapshot and all changes

---

## Phase 4: Arc Compression (Week 4)

### Goal
Implement branch selection and mainline canonicalization after 10-15 episodes.

### 4.1 Arc Compression Engine

**File: `backend/app/engine/arc_compressor.py` (NEW)**

```python
class ArcCompressor:
    """
    After ~15 episodes in an arc:
    1. Identify all branches (paths through segment graph)
    2. Get candidates: top N by popularity + M random
    3. Generate summaries for each
    4. AI picks mainline
    5. Archive non-mainline segments
    6. Continue from mainline into next arc
    """
    
    async def compress_arc(self, arc: StoryArc, generator: TextGenerator) -> ArcCompressionResult:
        """Compress arc, return mainline selection."""
        
        # 1. Find all branches
        branches = self._find_branches_in_arc(arc)
        
        # 2. Select candidates
        popular = branches.sorted_by_traversals()[:5]
        random = branches.sample(3)
        candidates = popular + random
        
        # 3. Summarize each
        summaries = []
        for branch in candidates:
            summary = self._summarize_branch(branch)
            summaries.append((branch.id, summary))
        
        # 4. AI picks winner
        mainline_id = await self._ai_select_mainline(
            arc, summaries, generator
        )
        
        # 5. Archive non-mainline
        non_mainline = [b.id for b in branches if b.id != mainline_id]
        for seg_id in self._get_all_segments_in_branches(non_mainline):
            segment = self.story.get_segment(seg_id)
            segment.status = SegmentStatus.ARCHIVED
            segment.save()
        
        # 6. Return result
        return ArcCompressionResult(
            mainline_segment_ids=self._get_mainline_path(mainline_id),
            archived_segment_ids=self._get_all_segments_in_branches(non_mainline),
            selected_branch_id=mainline_id,
            ai_reasoning="..."
        )
    
    def _find_branches_in_arc(self, arc: StoryArc) -> List[Branch]:
        """Identify all paths through arc (using visited_segment data from sessions)."""
        pass
    
    def _summarize_branch(self, branch: Branch) -> str:
        """Generate summary of branch for AI evaluation."""
        pass
    
    async def _ai_select_mainline(self, arc: StoryArc, summaries: List[Tuple], 
                                  generator: TextGenerator) -> str:
        """Ask AI which branch is canon."""
        pass
```

### 4.2 Archive State Handling

Update Story queries to exclude archived segments by default:

```python
# In story.py
def get_segment(self, segment_id: str, include_archived: bool = False) -> Optional[Segment]:
    """Get segment, optionally including archived."""
    segment = self._segments.get(segment_id)
    if segment and segment.status == SegmentStatus.ARCHIVED and not include_archived:
        return None
    return segment

def get_available_choices(self, segment_id: str) -> List[Choice]:
    """Get choices from segment, excluding those to archived."""
    segment = self.get_segment(segment_id)
    if not segment:
        return []
    
    return [
        c for c in segment.outgoing_choices.values()
        if c.to_segment_id is None or \
           self.get_segment(c.to_segment_id) is not None  # Exclude archived
    ]
```

---

## Phase 5: CLI Updates (Week 3, in parallel with phase 3-4)

### Goal
Update CLI to work with new segment graph + episode system with two distinct modes.

### 5.1 Two CLI Modes

**Mode A: Gameplay Mode (Default)** — Immersive, minimal context

```
═══════════════════════════════════════════════════════════════
                    THE VEIL OF THORNREACH
═══════════════════════════════════════════════════════════════

The cobblestone streets shimmer in the failing light. You can hear the 
distant sound of crowds gathering. Something is happening in the market.

—————————————————————————————————————————————————————————————————

1. Head toward the marketplace
2. Ask a nearby merchant what's going on
3. Find shelter and observe from afar

Your choice:
```

**Features:**
- Just story text + numbered choices
- No metadata, logs, or context
- Optional subtle episode/arc indicators (very minimal)
- Immersive full-screen experience
- Suitable for actual storytelling

**Mode B: Exploration Mode** — Full context, debugging, logs

```
═══════════════════════════════════════════════════════════════════════════════
                           EXPLORATION MODE
═══════════════════════════════════════════════════════════════════════════════

[WORLD] veil_of_thornreach    [ARC] 1: The Rebellion    [EPISODE] 3    [TONE] betrayal, arc_heavy
[PROTAGONIST] Eira            [PACING] 0.65              [PROXIMITY] 0.7

───────────────────────────────────────────────────────────────────────────────
SEGMENT seg_abc123 [ep:3, seg:14/~20, parent: seg_xyz789, status: generated]
───────────────────────────────────────────────────────────────────────────────

NARRATIVE:
  The cobblestone streets shimmer in the failing light. You can hear the 
  distant sound of crowds gathering. Something is happening in the market.

CHARACTER STATES (snapshot from episode start):
  eira:   status=alive, mood=disillusioned, loyalty=rebel-aligned
  thorne: status=alive, mood=angry, loyalty=rebel-leader

CHANGE NOTES (this episode):
  seg_3:  eira learned about rebel plans
  seg_7:  thorne grew suspicious of council
  seg_14: eira confronted thorne about his motives

───────────────────────────────────────────────────────────────────────────────
CHOICES:
───────────────────────────────────────────────────────────────────────────────

1. Head toward the marketplace
   → to_segment: null [UNEXPLORED - will generate]

2. Ask a nearby merchant what's going on
   → to_segment: seg_def456 [GENERATED - shared]

3. Find shelter and observe from afar
   → to_segment: null [UNEXPLORED - will generate]

4. [DEV] Show full context
5. [DEV] Show segment chain
6. [DEV] Toggle protagonist death
7. [GAMEPLAY] Switch to Gameplay Mode

Your choice:
```

**Features:**
- Full segment metadata
- Character states + change notes
- Episode/arc/pacing info
- Segment graph status (generated vs unexplored)
- Dev commands for testing
- Detailed logs

### 5.2 Mode Configuration

**File: `backend/app/config.py` (ENHANCE)**

```python
class CLIConfig(BaseModel):
    """CLI display settings."""
    mode: Literal["gameplay", "exploration"] = "gameplay"
    show_episode_transitions: bool = True
    show_pacing: bool = False  # Only in exploration
    show_character_states: bool = False  # Only in exploration
    show_segment_id: bool = False  # Only in exploration
    verbose_logs: bool = False
    
class Config(BaseModel):
    generator: GeneratorConfig
    cli: CLIConfig = Field(default_factory=CLIConfig)
```

**Environment variables:**

```bash
CLI_MODE=gameplay              # or "exploration"
SHOW_EPISODE_TRANSITIONS=true
SHOW_PACING=false
VERBOSE_LOGS=false
```

### 5.3 Update run_story Loop

**File: `backend/app/cli.py`**

```python
async def run_story_async(story_name: str = None, mode: str = "gameplay"):
    # ... load config, generator, story ...
    
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Load or create session
    if not runner.load_state():
        runner.start()
    
    while True:
        # 1. Display current segment (mode-dependent)
        if mode == "gameplay":
            display_gameplay_mode(runner.current_segment)
        else:
            display_exploration_mode(runner.current_segment, runner)
        
        # 2. Get choices
        choices = runner.get_available_choices()
        if not choices:
            print("Story has ended")
            break
        
        # 3. Show menu (mode-dependent)
        if mode == "gameplay":
            show_gameplay_menu(choices)
        else:
            show_exploration_menu(choices)
        
        choice_id = get_user_choice()
        
        # Handle mode-specific commands
        if choice_id.startswith("[DEV]"):
            handle_dev_command(choice_id, runner, mode)
            continue
        
        # 4. NEW: traverse_or_generate
        try:
            next_segment = await runner.traverse_or_generate(choice_id)
            runner.save_state()
            
        except Exception as e:
            # Handle error gracefully
            show_error(e, mode)
            continue
```

### 5.4 Display Functions

**File: `backend/app/cli_display.py` (NEW)**

```python
def display_gameplay_mode(segment: Segment):
    """Immersive mode: just the story."""
    
    # Optional: Episode transition banner
    if segment.segment_number_in_episode == 1:
        console.print("\n" + "="*80)
        console.print(f"[EPISODE {segment.episode_number}]")
        console.print("="*80 + "\n")
    
    # Story content only
    for block in segment.text_blocks:
        if block.type == "scene_title":
            console.print(f"\n[bold cyan]{block.content}[/bold cyan]")
        elif block.type == "narrator_describing":
            console.print(f"\n{block.content}")
        elif block.type == "character_speech":
            console.print(f"\n[bold]{block.character}:[/bold] {block.content}")
        elif block.type == "sfx":
            console.print(f"\n[italic]{block.content}[/italic]")

def display_exploration_mode(segment: Segment, runner: StoryRunner):
    """Debug mode: full context."""
    
    # Header with all context
    header = f"[WORLD] {runner.story.id}    [ARC] {segment.arc_id}    [EP] {segment.episode_number}    [TONE] {', '.join(segment.episode_tone)}\n"
    header += f"[PROTAGONIST] {segment.protagonist_id}    [PACING] {segment.pacing_weight:.2f}    [PROXIMITY] {segment.end_condition_proximity:.2f}"
    
    console.print(header, style="dim")
    console.print("─" * 100)
    
    # Segment info
    console.print(f"SEGMENT {segment.id} [ep:{segment.episode_number}, seg:{segment.segment_number_in_episode}/~20, parent: {segment.parent_segment_id}, status: {segment.status}]", style="dim")
    console.print("─" * 100)
    
    # Story content
    console.print("\nNARRATIVE:", style="bold")
    for block in segment.text_blocks:
        # ... format block
    
    # Character states
    console.print("\nCHARACTER STATES (snapshot from episode start):", style="bold")
    for char_id, state in segment.character_states.items():
        console.print(f"  {char_id}: status={state.status}, mood={state.mood}, loyalty={state.loyalty}")
    
    # Change notes
    if segment.change_notes:
        console.print("\nCHANGE NOTES (this episode):", style="bold")
        for note in segment.change_notes:
            console.print(f"  seg_?: {note['character']} {note['note']}")
    
    # Episode info
    console.print("\nEPISODE INFO:", style="bold")
    console.print(f"  Tone: {', '.join(segment.episode_tone)}")
    console.print(f"  End condition: {segment.episode_end_condition}")
    console.print(f"  Progress: {segment.end_condition_proximity:.1%} done")
    console.print(f"  Protagonist alive: {segment.protagonist_alive}")

def show_gameplay_menu(choices: List[Choice]):
    """Simple numbered list."""
    console.print("\nWhat would you like to do?")
    for i, choice in enumerate(choices, 1):
        console.print(f"{i}. {choice.text}")
    console.print(f"{len(choices)+1}. Save and exit")
    console.print(f"{len(choices)+2}. Exit without saving")

def show_exploration_menu(choices: List[Choice]):
    """Detailed menu with segment info."""
    console.print("\nCHOICES:")
    console.print("─" * 100)
    
    for i, choice in enumerate(choices, 1):
        if choice.to_segment_id:
            status = f"→ {choice.to_segment_id} [GENERATED - shared]"
        else:
            status = "→ null [UNEXPLORED - will generate]"
        
        console.print(f"{i}. {choice.text}")
        console.print(f"   {status}")
    
    console.print(f"\n{len(choices)+1}. [GAMEPLAY] Switch to Gameplay Mode")
    console.print(f"{len(choices)+2}. [DEV] Show segment chain")
    console.print(f"{len(choices)+3}. [DEV] Show full recaps")
    console.print(f"{len(choices)+4}. [DEV] Trigger protagonist death")
    console.print(f"{len(choices)+5}. Save and exit")
    console.print(f"{len(choices)+6}. Exit without saving")
```

### 5.5 Dev Commands

**File: `backend/app/cli_dev_commands.py` (NEW)**

```python
async def handle_dev_command(command: str, runner: StoryRunner, mode: str):
    """Handle exploration mode dev commands."""
    
    if command == "show_segment_chain":
        segment = runner.current_segment
        chain = []
        while segment:
            chain.append(f"  {segment.id} [ep:{segment.episode_number}]")
            if segment.parent_segment_id:
                segment = runner.story.get_segment(segment.parent_segment_id)
            else:
                break
        
        console.print("SEGMENT CHAIN (parent → child):")
        for s in reversed(chain):
            console.print(s)
    
    elif command == "show_recaps":
        # Show episode recaps for current arc
        arc_id = runner.current_segment.arc_id
        recaps = load_episode_recaps(arc_id)
        
        for recap in recaps:
            console.print(f"\n[EPISODE {recap.episode_number}] {recap.title}")
            console.print(recap.summary)
            console.print("Character state changes:")
            for char_id, state in recap.character_states_final.items():
                console.print(f"  {char_id}: {state.mood}")
    
    elif command == "toggle_death":
        segment = runner.current_segment
        segment.protagonist_alive = not segment.protagonist_alive
        console.print(f"[DEV] Protagonist death toggled: {segment.protagonist_alive}")
```

---

## Phase 6: Testing & Validation (Week 4-5)

### Goal
Ensure new system works end-to-end.

### 6.1 New Test Suite

**File: `backend/tests/test_segment_graph.py` (NEW)**

```python
def test_segment_immutability():
    """Once generated, segment cannot change."""
    pass

def test_shared_segment_traversal():
    """Two users picking same choice reach same segment."""
    pass

def test_episode_context_baking():
    """Segment stores episode context at generation time."""
    pass

def test_episode_transition_at_generation():
    """Different choices from same parent can start different episodes."""
    pass

def test_character_state_accumulation():
    """Change notes accumulate through episode chain."""
    pass

def test_episode_recap_generation():
    """Recap correctly reconciles character states."""
    pass

def test_arc_compression():
    """Compression picks mainline and archives others."""
    pass
```

### 6.2 Migration Validation

**File: `backend/tests/test_migration.py` (NEW)**

```python
def test_migrate_existing_story():
    """Existing story migrates to new format without data loss."""
    pass

def test_migrated_story_is_traversable():
    """Can still play migrated story."""
    pass
```

---

## Phase 7: Documentation & Finalization (Week 5)

### Goal
Update all docs, create architecture overview.

### 7.1 Update Vision Docs

See `VISION.md` section below.

### 7.2 Architecture Diagram

Create visual showing:
- Segment DAG (immutable, shared)
- Episode overlays (context, not containers)
- User sessions as cursors
- Compression event

---

## Implementation Order (Priority)

**Critical Path:**

1. **Phase 1.1** - Enhance Segment model (requires: understanding)
2. **Phase 1.2** - Enhance Choice model (quick)
3. **Phase 1.3** - Episode Recap model (quick)
4. **Phase 1.4** - Arc model (quick)
5. **Phase 1.5** - Simplify UserSession (quick)
6. **Phase 1.6** - Migration script (medium)
7. **Phase 2.1** - Context builder (critical)
8. **Phase 2.2** - Update generation (critical)
9. **Phase 2.3** - Episode transition logic (critical)
10. **Phase 3.1** - Recap generation (critical)
11. **Phase 4.1** - Arc compression (important but can defer)
12. **Phase 5.1** - CLI updates (medium)
13. **Phase 6** - Testing (essential before release)
14. **Phase 7** - Docs (after code)

---

## Rollout Strategy

### Option A: Branch and Replace
- Create new branch `v2-segment-graph`
- Implement all phases
- At completion, merge to main, disable old code
- Pros: Clean break, no confusion
- Cons: Days of dual maintenance

### Option B: Feature Flags
- Implement on main in parallel
- Use config flag: `USE_SEGMENT_GRAPH=true/false`
- Test both paths simultaneously
- At completion, remove old code
- Pros: Safer transition, can A/B test
- Cons: More code complexity during transition

### Recommendation
**Option A** — cleaner, simpler. This is a major refactor. Better to own it completely.

---

## Risk Areas

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Migration loses data | Critical | Test thoroughly, keep old data format readable |
| Episode transitions break continuity | High | AI-test narrative quality, human review |
| Compression picks wrong branch | Medium | Review mainline candidates before compression |
| Performance: graph traversal | Medium | Cache segment access, lazy load |
| Locking prevents concurrent generation | Low | Use distributed lock (Redis) if scaling |

---

## Timeline

- **Phase 1-2**: 2 weeks
- **Phase 3-4**: 2 weeks (in parallel)
- **Phase 5**: 1 week (in parallel)
- **Phase 6**: 1-2 weeks
- **Phase 7**: 1 week

**Total: 4-5 weeks** for full implementation and testing.

(Can be faster with more developers working in parallel.)

---

## Success Criteria

- [ ] All existing story data migrates without loss
- [ ] Can traverse shared segment graph
- [ ] Episode transitions work seamlessly
- [ ] Character state accumulates correctly through episodes
- [ ] Recaps generate coherent titles/summaries
- [ ] Arc compression picks reasonable mainlines
- [ ] All new tests pass
- [ ] CLI works end-to-end
- [ ] Performance acceptable (segment loading <500ms)
