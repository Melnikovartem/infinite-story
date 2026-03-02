# Technical Architecture: Shared Segment Graph

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
├──────────────────────────┬──────────────────────────────────────┤
│     Gameplay Mode        │      Exploration Mode (Dev)         │
│  (immersive, minimal)    │  (full context, debugging)          │
└──────────────────────────┴──────────────────────────────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │   CLI Interface       │
                        │  (app/cli.py)         │
                        └───────────┬───────────┘
                                    │
                        ┌───────────▼───────────┐
                        │  Story Runner         │
                        │  (core game loop)     │
                        └───────────┬───────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Segment Context  │      │ Generation       │      │ Episode Recap    │
│ Builder          │      │ Pipeline         │      │ Generator        │
│                  │      │                  │      │                  │
│ - Walk parent    │      │ - AI generation  │      │ - State recap    │
│ - Accumulate     │      │ - JSON parsing   │      │ - Thread summary │
│ - Determine      │      │ - Segment save   │      │ - Title gen      │
│   episode change │      │ - Choice update  │      │                  │
│ - Calc pacing    │      │                  │      │                  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │  AI Text Generator    │
                        │  (OpenAI/OpenRouter)  │
                        └───────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Segment Graph    │      │ Episode System   │      │ Arc Compressor   │
│ (immutable DAG)  │      │ (metadata)       │      │                  │
│                  │      │                  │      │ - Branch select  │
│ Nodes: Segment   │      │ - Recap storage  │      │ - Mainline pick  │
│ Edges: Choice    │      │ - Tone tags      │      │ - Archive old    │
│ Storage: JSON    │      │ - Pacing weight  │      │ - Continue new   │
│                  │      │                  │      │                  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## Data Models

### Core Models (Models Layer)

#### Segment

```python
class Segment(StoryBlock):
    """Immutable node in the segment graph."""
    
    # Identity
    id: str
    status: SegmentStatus  # unexplored, generating, generated, archived
    
    # Graph structure
    parent_segment_id: Optional[str]     # What generated this
    parent_choice_id: Optional[str]      # Which choice
    outgoing_choices: Dict[str, Choice]  # Runtime-built
    
    # Episode context (baked at generation time)
    arc_id: Optional[str]
    episode_number: Optional[int]
    episode_tone: List[str]              # ["betrayal", "arc_heavy"]
    episode_end_condition: Optional[str]  # "protagonist commits to faction"
    segment_number_in_episode: Optional[int]
    pacing_weight: Optional[float]       # 0.0-1.0, exponential toward end
    protagonist_id: Optional[str]        # Who we're viewing from
    
    # Character tracking
    character_states: Dict[str, CharacterState]  # Snapshot from ep start
    change_notes: List[Dict[str, str]]          # This segment's changes
    
    # Content
    text_blocks: List[TextBlock]
    
    # Episode signals
    end_condition_proximity: Optional[float]    # 0.0-1.0
    protagonist_alive: bool
    triggers_episode_transition: bool
```

**Stored at:** `.infinite_story_data/<story_id>/storysegment/<segment_id>.json`

**Immutability:** Once status is `generated`, segment is locked for reading by all users.

---

#### Choice

```python
class Choice(StoryBlock):
    """Immutable edge in the segment graph."""
    
    id: str
    from_segment_id: str
    to_segment_id: Optional[str]  # null = unexplored, value = next segment
    text: str
    click_count: int  # For analytics
```

**Behavior:**
- When `to_segment_id` is `None`, the choice is unexplored
- First user to pick it triggers generation
- Generation sets `to_segment_id` to the new segment
- Subsequent users get the existing segment

---

#### EpisodeRecap

```python
class EpisodeRecap(BaseModel):
    """Generated summary when episode ends."""
    
    id: str
    arc_id: str
    episode_number: int
    trigger_segment_id: str  # Last segment of episode
    
    # Generated by AI
    title: str
    summary: str
    
    # Character state snapshot (becomes input for next episode)
    character_states_final: Dict[str, CharacterState]
    world_state_changes: List[str]
    
    # Narrative seeds for next episode
    narrative_threads: List[str]
    
    # Metadata
    segment_count: int
    protagonist_id: str
    protagonist_alive: bool
```

**Stored at:** `.infinite_story_data/<story_id>/episoderecap/<recap_id>.json`

**Generated by:** `EpisodeRecapGenerator` when `triggers_episode_transition` is detected

---

#### CharacterState

```python
class CharacterState(BaseModel):
    """State of a character at a point in the story."""
    
    character_id: str
    status: str              # "alive", "dead", "hiding", etc.
    mood: str                # "hopeful", "disillusioned", etc.
    loyalty: str             # faction alignment
    location: str            # where they are
    relationships: Dict[str, str]  # how they feel about others
    knowledge: List[str]     # what they know
```

---

#### UserSession

```python
class UserSession:
    """Simplified: just a cursor on the graph."""
    
    user_id: str
    world_id: str
    current_segment_id: str
    visited_segments: Set[str]
```

**Stored at:** `.infinite_story_data/<story_id>/sessions/<user_id>/session.json`

**No per-user episode tracking, character states, or protagonist tracking.** All of that lives on segments.

---

### Episode Context (Baked Into Segments)

When a segment is generated, it captures:

```
Generation Context Input:
  ├── Arc outline
  ├── Episode tone + end_condition
  ├── Character states (from previous episode recap)
  ├── Pacing weight (where we are in ~20 segment cycle)
  ├── Protagonist ID
  └── Recent segment summaries
```

This context is **saved with the segment**:

```
Segment {
  id: "seg_abc123"
  arc_id: "arc_1_rebellion"
  episode_number: 3
  episode_tone: ["betrayal", "arc_heavy"]
  pacing_weight: 0.65
  ...
}
```

Any user reading this segment will see it in its original episode context. No user-specific context needed.

---

## Generation Pipeline

### Overview

```
User picks unexplored choice
    │
    ├─ Check: episode ending?
    │   └─ Walk parent chain, check signals
    │
    ├─ Generate recap? (if yes)
    │   ├─ Collect segments + changes
    │   ├─ Call AI recap generator
    │   ├─ Save EpisodeRecap
    │   └─ New episode context output
    │
    ├─ Build generation context
    │   ├─ World info
    │   ├─ Arc info
    │   ├─ Episode info (current or new)
    │   ├─ Character snapshot + changes
    │   ├─ Pacing weight
    │   └─ Recent segments
    │
    ├─ Call AI: Generate segment
    │   └─ Returns: text_blocks, choices, change_notes, signals
    │
    ├─ Create Segment (immutable)
    │   ├─ Save to disk
    │   ├── Mark status: generated
    │   └─ Build choices with to_segment_id: null
    │
    ├─ Update Choice
    │   └─ Set to_segment_id = new_segment.id
    │
    └─ Move cursor
        └─ UserSession.current_segment_id = new segment
```

---

### Segment Context Builder

**File:** `backend/app/engine/segment_context_builder.py`

```python
class SegmentContextBuilder:
    """Build generation context for new segment."""
    
    async def build_context(
        self,
        parent_segment: Segment,
        parent_choice: Choice,
        story: Story,
        generator_config: dict
    ) -> SegmentGenerationContext:
        """
        Walk parent chain, determine episode state, build prompt context.
        
        Steps:
        1. Walk up to episode start, collect character snapshot
        2. Walk down, collect all change_notes
        3. Determine: should episode transition?
        4. If yes: generate recap, get new episode context
        5. If no: continue current episode
        6. Calculate pacing weight
        7. Build full prompt context
        """
        
        # Step 1: Episode context
        episode_start_segment, accumulated_changes = self._walk_episode_chain(parent_segment)
        
        if self._should_transition_episode(parent_segment):
            recap = await self._generate_recap(episode_start_segment, parent_segment)
            new_episode_context = await self._generate_new_episode(recap)
            episode_context = new_episode_context
        else:
            episode_context = {
                'arc_id': parent_segment.arc_id,
                'episode_number': parent_segment.episode_number,
                'episode_tone': parent_segment.episode_tone,
                'episode_end_condition': parent_segment.episode_end_condition,
            }
        
        # Step 2: Character states (snapshot + changes)
        character_states = self._reconcile_character_states(
            episode_start_segment.character_states,
            accumulated_changes
        )
        
        # Step 3: Pacing weight (exponential curve toward segment ~20)
        segment_number = (parent_segment.segment_number_in_episode or 0) + 1
        pacing_weight = self._calculate_pacing_weight(segment_number)
        
        # Step 4: Build context dict for prompt
        return SegmentGenerationContext(
            world_info=self._get_world_info(story),
            arc_info=self._get_arc_info(story, episode_context['arc_id']),
            episode_info=episode_context,
            character_states=character_states,
            protagonist_id=parent_segment.protagonist_id,
            pacing_weight=pacing_weight,
            recent_segments=self._get_recent_segments(parent_segment),
            parent_choice_text=parent_choice.text,
        )
    
    def _walk_episode_chain(self, segment: Segment) -> Tuple[Segment, List]:
        """Walk up to episode start, return start segment and accumulated changes."""
        accumulated = []
        current = segment
        
        while current:
            accumulated.extend(current.change_notes)
            if current.segment_number_in_episode == 1:
                return current, accumulated
            
            if current.parent_segment_id:
                current = self.story.get_segment(current.parent_segment_id)
            else:
                return current, accumulated
        
        return segment, accumulated
    
    def _should_transition_episode(self, segment: Segment) -> bool:
        """Check if this segment triggers episode end."""
        if segment.end_condition_proximity and segment.end_condition_proximity >= 0.8:
            return True
        if segment.segment_number_in_episode and segment.segment_number_in_episode >= 18:
            return True
        return False
    
    async def _generate_recap(self, start_segment: Segment, end_segment: Segment) -> EpisodeRecap:
        """Generate recap when episode ends. See EpisodeRecapGenerator."""
        pass
    
    async def _generate_new_episode(self, previous_recap: EpisodeRecap) -> dict:
        """Generate new episode context. See EpisodeRecapGenerator."""
        pass
    
    def _reconcile_character_states(
        self,
        snapshot: Dict[str, CharacterState],
        accumulated_changes: List
    ) -> Dict[str, CharacterState]:
        """Merge snapshot + changes into current states."""
        # For now: return snapshot as-is
        # At episode recap time, AI will reconcile into new snapshot
        return snapshot
    
    def _calculate_pacing_weight(self, segment_number: int) -> float:
        """Exponential curve: slow early, fast late."""
        # Segment 1-5: 0.0-0.1
        # Segment 6-10: 0.1-0.3
        # Segment 11-15: 0.3-0.6
        # Segment 16-18: 0.6-0.85
        # Segment 19-20: 0.85-1.0
        
        if segment_number <= 5:
            return segment_number / 50  # 0-0.1
        elif segment_number <= 10:
            return 0.1 + (segment_number - 5) / 50  # 0.1-0.3
        elif segment_number <= 15:
            return 0.3 + (segment_number - 10) / 20  # 0.3-0.6
        elif segment_number <= 18:
            return 0.6 + (segment_number - 15) / 12  # 0.6-0.85
        else:
            return 0.85 + (segment_number - 18) / 40  # 0.85-1.0
```

---

### Generation Call

```python
async def _generate_segment(
    self,
    context: SegmentGenerationContext,
    generator: TextGenerator
) -> Segment:
    """Call AI to generate segment, parse response, save."""
    
    # Build prompt
    user_prompt = self._build_user_prompt(context)
    system_prompt = self._build_system_prompt(context)
    
    # Generate
    response = await generator.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        context_type="scene"  # Returns SceneTextGeneratorResponse
    )
    
    # Create segment
    segment = Segment(
        story=self.story,
        id=f"seg_{uuid.uuid4()}",
        parent_segment_id=context.parent_segment_id,
        parent_choice_id=context.parent_choice_id,
        status=SegmentStatus.GENERATED,
        
        # Episode context (baked)
        arc_id=context.episode_info['arc_id'],
        episode_number=context.episode_info['episode_number'],
        episode_tone=context.episode_info['episode_tone'],
        episode_end_condition=context.episode_info['episode_end_condition'],
        segment_number_in_episode=context.parent_segment.segment_number_in_episode + 1,
        pacing_weight=context.pacing_weight,
        protagonist_id=context.protagonist_id,
        
        # Character states
        character_states=context.character_states,
        change_notes=response.change_notes,
        
        # Content
        text_blocks=response.text_blocks,
        
        # Episode signals
        end_condition_proximity=response.end_condition_proximity,
        protagonist_alive=response.protagonist_alive,
        triggers_episode_transition=self._should_transition_episode(...),
    )
    
    # Create outgoing choices
    for choice_text in response.next_choices:
        choice = Choice(
            story=self.story,
            id=f"choice_{uuid.uuid4()}",
            from_segment_id=segment.id,
            to_segment_id=None,  # Unexplored
            text=choice_text
        )
    
    # Save
    segment.save()
    for choice in segment.outgoing_choices.values():
        choice.save()
    
    return segment
```

---

## Episode System

### Episode Recap Generation

**File:** `backend/app/engine/episode_recap_generator.py`

```python
class EpisodeRecapGenerator:
    """Generate recap when episode ends."""
    
    async def generate_recap(
        self,
        trigger_segment: Segment,
        generator: TextGenerator
    ) -> EpisodeRecap:
        """
        Walk back to episode start, collect all changes, generate recap.
        """
        
        # Collect episode chain
        episode_chain = self._walk_episode_chain(trigger_segment)
        
        # Collect all change notes
        all_changes = []
        for seg in episode_chain:
            for note in seg.change_notes:
                all_changes.append((seg.id, note))
        
        # Build recap prompt
        recap_prompt = self._build_recap_prompt(
            trigger_segment.episode_tone,
            trigger_segment.episode_end_condition,
            episode_chain,
            all_changes
        )
        
        # AI generates recap
        response = await generator.generate(
            system_prompt="You are a narrative summarizer...",
            user_prompt=recap_prompt,
            context_type="episode_recap"
        )
        
        # Create recap
        recap = EpisodeRecap(
            id=f"recap_{uuid.uuid4()}",
            arc_id=trigger_segment.arc_id,
            episode_number=trigger_segment.episode_number,
            trigger_segment_id=trigger_segment.id,
            title=response.title,
            summary=response.summary,
            character_states_final=response.character_states_final,
            world_state_changes=response.world_state_changes,
            narrative_threads=response.narrative_threads,
            segment_count=len(episode_chain),
            protagonist_id=trigger_segment.protagonist_id,
            protagonist_alive=trigger_segment.protagonist_alive,
        )
        
        # Save
        recap.save()
        
        return recap
    
    async def generate_new_episode_context(
        self,
        arc: StoryArc,
        previous_recap: EpisodeRecap,
        generator: TextGenerator
    ) -> dict:
        """Generate tone, end_condition, narrative hooks for new episode."""
        
        # Pick random tone
        tone_word = random.choice(TONE_POOL)
        
        # Get arc storyline and older recaps
        arc_storyline = arc.description
        older_recaps = self._get_arc_recap_history(arc)
        
        # Build prompt
        prompt = f"""
        You are generating the next episode in an unfolding story.
        
        Arc: {arc_storyline}
        Previous episode: {previous_recap.title}
        Summary: {previous_recap.summary}
        Tone word: {tone_word}
        
        Older episode summaries:
        {chr(10).join(f"- Episode {r.episode_number}: {r.title}" for r in older_recaps)}
        
        Generate:
        1. tone_tags: List of 2-3 words describing this episode's tone
        2. end_condition: What should trigger the end of this episode?
        3. narrative_direction: What themes should be explored?
        """
        
        response = await generator.generate(
            system_prompt="...",
            user_prompt=prompt,
            context_type="episode_plan"
        )
        
        return {
            'arc_id': arc.id,
            'episode_number': previous_recap.episode_number + 1,
            'episode_tone': response.tone_tags,
            'episode_end_condition': response.end_condition,
            'narrative_direction': response.narrative_direction,
        }
```

---

## Arc Compression

**File:** `backend/app/engine/arc_compressor.py`

```python
class ArcCompressor:
    """Compress arc after 15 episodes, pick mainline."""
    
    async def compress_arc(
        self,
        arc: StoryArc,
        generator: TextGenerator
    ) -> ArcCompressionResult:
        """
        1. Find all branches
        2. Select candidates (popular + random)
        3. Summarize
        4. AI picks
        5. Archive non-mainline
        6. Save result
        """
        
        # Find branches (using user sessions)
        branches = self._find_branches_in_arc(arc)
        
        # Select candidates
        popular = sorted(branches, key=lambda b: b.traversal_count)[-5:]
        random_branches = random.sample(branches, min(3, len(branches)))
        candidates = list(set(popular + random_branches))
        
        # Summarize each
        summaries = []
        for branch in candidates:
            path = self._get_branch_path(branch)
            summary = self._summarize_path(path)
            summaries.append((branch.id, summary))
        
        # AI picks winner
        mainline_id = await self._ai_select_mainline(arc, summaries, generator)
        
        # Archive non-mainline
        non_mainline = [b for b in branches if b.id != mainline_id]
        for branch in non_mainline:
            path = self._get_branch_path(branch)
            for seg_id in path:
                segment = self.story.get_segment(seg_id)
                segment.status = SegmentStatus.ARCHIVED
                segment.save()
        
        # Save result
        result = ArcCompressionResult(
            mainline_segment_ids=self._get_branch_path(mainline_id),
            archived_segment_ids=self._get_all_archived_segment_ids(non_mainline),
            selected_branch_id=mainline_id,
            ai_reasoning="...",
        )
        
        arc.compression = result
        arc.status = "compressed"
        arc.save()
        
        return result
```

---

## CLI Interface

### Two Modes

#### Gameplay Mode

```python
async def display_gameplay_mode(segment: Segment, config: Config):
    """Immersive mode: story + choices only."""
    
    # Optional: episode transition banner
    if segment.segment_number_in_episode == 1:
        console.print("\n" + "="*80)
        console.print(f"[EPISODE {segment.episode_number}]")
        console.print("="*80 + "\n")
    
    # Story
    for block in segment.text_blocks:
        if block.type == TextType.SCENE_TITLE:
            console.print(f"\n[bold cyan]{block.content}[/bold cyan]")
        elif block.type == TextType.NARRATOR_DESCRIBING:
            console.print(f"\n{block.content}")
        # ... etc
    
    # Choices
    console.print("\n[bold]What would you like to do?[/bold]")
    for i, choice in enumerate(segment.outgoing_choices.values(), 1):
        console.print(f"{i}. {choice.text}")
```

#### Exploration Mode

```python
async def display_exploration_mode(segment: Segment, runner: StoryRunner, config: Config):
    """Debug mode: full context."""
    
    # Header
    header = f"[WORLD] {runner.story.id}    [ARC] {segment.arc_id}    [EP] {segment.episode_number}    [TONE] {', '.join(segment.episode_tone)}\n"
    header += f"[PROTAGONIST] {segment.protagonist_id}    [PACING] {segment.pacing_weight:.2f}    [PROXIMITY] {segment.end_condition_proximity:.2f}"
    console.print(header, style="dim")
    
    # Segment info
    console.print(f"SEGMENT {segment.id} [status: {segment.status}, ep:{segment.episode_number}, seg:{segment.segment_number_in_episode}/~20]", style="dim")
    
    # Character states
    console.print("\nCHARACTER STATES (snapshot):")
    for char_id, state in segment.character_states.items():
        console.print(f"  {char_id}: {state.status}, mood: {state.mood}, loyalty: {state.loyalty}")
    
    # Change notes
    if segment.change_notes:
        console.print("\nCHANGE NOTES:")
        for note in segment.change_notes:
            console.print(f"  {note['character']}: {note['note']}")
    
    # Choices
    console.print("\nCHOICES:")
    for i, choice in enumerate(segment.outgoing_choices.values(), 1):
        status = f"→ {choice.to_segment_id}" if choice.to_segment_id else "→ null [UNEXPLORED]"
        console.print(f"{i}. {choice.text} {status}")
    
    # Dev commands
    console.print("\nDEV COMMANDS:")
    console.print(f"{len(segment.outgoing_choices)+1}. Show segment chain")
    console.print(f"{len(segment.outgoing_choices)+2}. Show episode recaps")
    console.print(f"{len(segment.outgoing_choices)+3}. Toggle protagonist death")
```

---

## Storage Structure

```
.infinite_story_data/
└── veil_of_thornreach/
    ├── story/
    │   └── veil_of_thornreach.json
    │
    ├── storysegment/
    │   ├── seg_abc123.json
    │   ├── seg_def456.json
    │   └── ...
    │
    ├── storychoice/
    │   ├── choice_1.json
    │   ├── choice_2.json
    │   └── ...
    │
    ├── episoderecap/
    │   ├── recap_ep1_branch1.json
    │   ├── recap_ep2_branch1.json
    │   └── ...
    │
    ├── storyarc/
    │   ├── arc_1_rebellion.json
    │   └── arc_2_siege.json
    │
    ├── sessions/
    │   ├── user_123/
    │   │   └── session.json
    │   └── user_456/
    │       └── session.json
    │
    └── storycharacter/
        ├── eira.json
        └── ...
```

---

## Performance Considerations

### Segment Access

- **Cached in memory** during Story load (via `Story._segments`)
- **Lazy query** if not in cache
- **Archived segments hidden** by default (excluded from traversal)

### Generation Context

- **Walk parent chain**: O(n) where n = segment_number_in_episode (~20)
- **Character reconciliation**: O(k) where k = number of characters in changes (< 20)
- **Total**: ~O(20 + 20) = O(1) practically

### Recap Generation

- **Single AI call** for episode end
- **Walks episode chain**: O(20)
- **Total**: One API call per episode end

### Arc Compression

- **Single AI call** to pick mainline from summaries
- **Segment updates**: O(total segments in arc)
- **Batch save**: Efficient disk writes

---

## Error Handling

### Generation Failures

```python
try:
    segment = await generate_segment(context)
except APIError as e:
    # Log, show user message, allow retry
    # Choice.to_segment_id stays null
    # User can choose again
except ValidationError as e:
    # AI response malformed
    # Graceful fallback
    # Allow regeneration
```

### Character State Inconsistencies

```python
# At recap time, AI reconciles all changes
# If reconciliation fails, use snapshot + manual review
# Never corrupt segment state
```

---

## Testing Strategy

### Unit Tests

- `test_segment_immutability`: Segments don't change once generated
- `test_shared_traversal`: Two users picking same choice reach same segment
- `test_context_building`: Correct context passed to AI
- `test_episode_transition`: Episode ending detected, recap generated
- `test_character_accumulation`: Changes accumulate correctly

### Integration Tests

- `test_full_generation_flow`: End-to-end generation
- `test_episode_recap`: Recap generation + new episode
- `test_arc_compression`: Mainline selection + archive
- `test_cli_gameplay_mode`: User can play in gameplay mode
- `test_cli_exploration_mode`: Full context visible in exploration mode

### Simulation Tests

- `test_multiple_users`: Multiple sessions traversing same graph
- `test_concurrent_generation`: Same choice picked simultaneously (locking)
- `test_branch_divergence`: Different branches have different episodes
- `test_compression_stability`: Compressed arc is stable, can continue

---

## Scalability

### Horizontal

- **Stateless generation**: Can scale to multiple generation workers
- **Session storage**: Minimal, easily sharded
- **Segment graph**: Read-heavy, immutable, easy to replicate

### Vertical

- **Memory**: Segments loaded on-demand, not all at once
- **Storage**: JSON files can move to database if needed
- **Computation**: Each generation is independent

### Practical Limits

- **Segment count**: 100K+ segments manageable
- **Concurrent users**: 100+ concurrent sessions practical
- **Generation throughput**: 10+ parallel AI calls practical

---

## Future Improvements

### Phase 2: Distributed Locking

Use Redis to prevent duplicate generation on same choice from multiple workers.

### Phase 3: Database Backend

Move from JSON files to PostgreSQL for better querying, transactions.

### Phase 4: Caching

Cache episode recaps, generation contexts, segment summaries for faster retrieval.

### Phase 5: Streaming

Stream segment generation to user in real-time instead of waiting for completion.

### Phase 6: Branching Awareness

Let characters be aware they're in branching timelines. "I remember when it went differently..."
