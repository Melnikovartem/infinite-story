# Epic 2: Episodes & Arc System

**For Developers F, G**  
**Duration:** 2 weeks (parallel to E1 & E3)  
**Blocker:** Epic 0 must be complete (E1 helpful but not required)  
**Deliverable:** Episode recaps, character reconciliation, arc compression with mainline selection

---

## What You're Building

The v2 system uses episodes to bound infinite growth:

1. **Episode Recap Generator** → At end of episode, summarize what happened, capture character states
2. **New Episode Context** → When starting next episode, AI picks tone, end condition, narrative direction
3. **Character State Reconciliation** → Apply all `change_notes` from episode to character snapshot
4. **Arc Compressor** → After 15 episodes, pick canonical mainline branch, archive others
5. **Archive State Handling** → Query system respects archived segments

This is what prevents exponential explosion: after 15-20 segments, pause, summarize, compress.

---

## Files You'll Touch

### Core Files (Read to Understand)
- `backend/app/models/episode_recap.py` → Created by E0 (read structure)
- `backend/app/models/story_arc.py` → Created by E0 (read structure)
- `backend/app/models/story_segment.py` → Enhanced by E0 (understand fields)
- `backend/app/engine/story_runner.py` → Game loop (you'll call into it)

### Files You'll Create
- `backend/app/engine/episode_recap_generator.py` → **NEW** (E2-1, E2-2, E2-3)
- `backend/app/engine/arc_compressor.py` → **NEW** (E2-4)

### Files You'll Modify
- `backend/app/models/story.py` → Archive handling (E2-5)

---

## Task Breakdown

### E2-1: Episode Recap Generator (Dev-F, 3 days)

**What:** At end of episode, generate a summary and capture final character states.

**File:** `backend/app/engine/episode_recap_generator.py` (CREATE NEW)

**Why:** Episodes are narrative pauses. At the end, we summarize what happened, capture character states, and use that as the foundation for the next episode. This creates story coherence.

**Code Structure:**

```python
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.models import Story, StorySegment, EpisodeRecap, CharacterState
from app.engine.generator import TextGenerator

class EpisodeRecapGenerator:
    """Generate episode summaries and character state snapshots"""
    
    def __init__(self, story: Story, generator: TextGenerator):
        self.story = story
        self.generator = generator
    
    async def generate_recap(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> EpisodeRecap:
        """
        Generate a recap for completed episode.
        
        Steps:
        1. Walk episode backward to collect all segments
        2. Extract all character changes
        3. Build recap prompt with context
        4. Call AI to generate title, summary, themes
        5. Reconcile character states (apply changes)
        6. Create EpisodeRecap object
        7. Save to disk
        
        Returns the EpisodeRecap.
        """
        # 1. Collect segments in this episode
        episode_segments = self._walk_episode_segments(
            episode_number, 
            arc_id
        )
        
        if not episode_segments:
            raise ValueError(f"No segments found for episode {episode_number}")
        
        # 2. Extract all changes and metadata
        all_changes = self._collect_changes(episode_segments)
        starting_states = self._extract_starting_states(episode_segments)
        
        # 3. Build recap prompt
        recap_prompt = self._build_recap_prompt(
            episode_segments,
            all_changes,
            episode_number,
            arc_id
        )
        
        # 4. Call AI
        recap_response = await self.generator.generate(
            context_type="recap",
            context=recap_prompt
        )
        
        # 5. Reconcile character states
        ending_states = self._reconcile_character_states(
            starting_states,
            all_changes
        )
        
        # 6. Create EpisodeRecap
        recap = EpisodeRecap(
            story_id=self.story.id,
            episode_number=episode_number,
            arc_id=arc_id,
            title=recap_response['title'],
            summary=recap_response['summary'],
            key_themes=recap_response.get('key_themes', []),
            tone=episode_segments[0].episode_tone or "neutral",
            segment_ids=[seg.id for seg in episode_segments],
            starting_character_states=starting_states,
            ending_character_states=ending_states,
        )
        
        # 7. Save
        recap.save()
        
        return recap
    
    def _walk_episode_segments(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> List[StorySegment]:
        """
        Collect all segments belonging to this episode.
        
        Walk from latest segment backward until episode number changes
        or arc changes (if specified).
        """
        segments = []
        
        # Find latest segment in this episode
        latest = self._find_latest_segment(episode_number, arc_id)
        if not latest:
            return []
        
        # Walk backward to episode start
        current = latest
        while (current and 
               current.episode_number == episode_number and
               (arc_id is None or current.arc_id == arc_id)):
            segments.insert(0, current)  # Prepend for chronological order
            
            if not current.parent_segment_id:
                break
            
            current = self.story.get_segment(current.parent_segment_id)
        
        return segments
    
    def _find_latest_segment(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> Optional[StorySegment]:
        """Find the most recent segment in episode"""
        all_segments = self.story.list_segments()
        
        matching = [
            seg for seg in all_segments
            if seg.episode_number == episode_number and
               (arc_id is None or seg.arc_id == arc_id)
        ]
        
        return max(matching, key=lambda s: s.id) if matching else None
    
    def _collect_changes(self, segments: List[StorySegment]) -> List[str]:
        """Extract all change_notes from segment chain"""
        all_changes = []
        for seg in segments:
            all_changes.extend(seg.change_notes)
        return all_changes
    
    def _extract_starting_states(
        self,
        segments: List[StorySegment]
    ) -> Dict[str, CharacterState]:
        """Extract character states from first segment of episode"""
        if not segments:
            return {}
        
        # First segment of episode has the starting state snapshot
        return segments[0].character_states
    
    def _build_recap_prompt(
        self,
        segments: List[StorySegment],
        changes: List[str],
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> str:
        """Build prompt for AI to generate recap"""
        
        # Summarize key scenes
        scene_summaries = [
            f"Scene {i+1}: {seg.get_short_overview()}"
            for i, seg in enumerate(segments[:10])  # First 10 scenes
        ]
        
        prompt = f"""
You are a narrative summarizer. Generate a recap for the following episode:

EPISODE {episode_number}
Arc: {arc_id or '(unassigned)'}
Total Scenes: {len(segments)}

KEY SCENES:
{chr(10).join(scene_summaries)}

CHARACTER CHANGES THIS EPISODE:
{chr(10).join(changes) or '(no explicit changes recorded)'}

Generate a 2-3 paragraph narrative recap that:
1. Captures the core story arc of the episode
2. Summarizes how characters evolved
3. Sets up thematic threads for next episode

Respond with JSON:
{{
    "title": "Episode Title",
    "summary": "2-3 paragraphs...",
    "key_themes": ["theme1", "theme2", ...]
}}
"""
        return prompt
    
    def _reconcile_character_states(
        self,
        starting_states: Dict[str, CharacterState],
        changes: List[str]
    ) -> Dict[str, CharacterState]:
        """
        Apply all changes to character states.
        
        Reconciliation logic:
        1. Start with episode snapshot
        2. For each change note, parse it
        3. Apply to character state
        4. If contradictory, ask AI to resolve
        
        Returns updated character states.
        """
        final_states = {}
        
        # Start with snapshots
        for char_id, state in starting_states.items():
            final_states[char_id] = state.copy()  # Shallow copy
        
        # Apply changes
        for change in changes:
            # Simple parsing: "CharName's mood changed to angry"
            # More complex logic would parse these more carefully
            # For now, trust the changes are valid
            # (Full reconciliation would call AI to verify contradictions)
            pass
        
        return final_states
```

**Unit Tests:**

```python
def test_walk_episode_segments(sample_story):
    """Collect all segments in an episode"""
    seg1 = StorySegment(
        story=sample_story,
        id="seg_1",
        episode_number=1
    )
    seg2 = StorySegment(
        story=sample_story,
        id="seg_2",
        episode_number=1,
        parent_segment_id="seg_1"
    )
    seg3 = StorySegment(
        story=sample_story,
        id="seg_3",
        episode_number=2,
        parent_segment_id="seg_2"
    )
    
    generator = EpisodeRecapGenerator(sample_story, mock_generator)
    segments = generator._walk_episode_segments(1)
    
    assert len(segments) == 2
    assert segments[0].id == "seg_1"
    assert segments[1].id == "seg_2"

def test_generate_recap_full(sample_story):
    """Full recap generation"""
    # Create episode 1 segments
    seg1 = StorySegment(
        story=sample_story,
        id="seg_1",
        episode_number=1,
        change_notes=["Alice gains courage"]
    )
    seg2 = StorySegment(
        story=sample_story,
        id="seg_2",
        episode_number=1,
        parent_segment_id="seg_1",
        change_notes=["Bob betrays Alice"]
    )
    
    generator = EpisodeRecapGenerator(sample_story, mock_generator)
    recap = await generator.generate_recap(1)
    
    assert recap.episode_number == 1
    assert "seg_1" in recap.segment_ids
    assert "seg_2" in recap.segment_ids
    assert len(recap.key_themes) > 0
```

**Acceptance Criteria:**
- [ ] `_walk_episode_segments()` collects correct segments
- [ ] `_collect_changes()` extracts all change notes
- [ ] `_reconcile_character_states()` applies changes (basic)
- [ ] `generate_recap()` creates valid EpisodeRecap
- [ ] Save/load working
- [ ] Unit tests passing (4+ tests)

---

### E2-2: New Episode Generation (Dev-F, 2 days)

**What:** When starting a new episode, AI generates the tone, end condition, and narrative direction.

**Add to `episode_recap_generator.py`:**

```python
async def generate_new_episode_context(
    self,
    arc_id: str,
    previous_recap: Optional[EpisodeRecap] = None
) -> Dict[str, Any]:
    """
    Generate context for a new episode.
    
    Returns:
    {
        'tone_tags': ['dark_and_mysterious', 'suspenseful'],
        'end_condition': 'Alice must decide between love and duty',
        'narrative_direction': 'Tension builds as secrets are revealed',
    }
    """
    # Get arc and previous recaps
    arc = self.story.get_arc(arc_id)
    if not arc:
        raise ValueError(f"Arc {arc_id} not found")
    
    # Build prompt
    prompt = self._build_episode_generation_prompt(
        arc,
        previous_recap
    )
    
    # Call AI
    response = await self.generator.generate(
        context_type="episode_context",
        context=prompt
    )
    
    return {
        'tone_tags': response.get('tone_tags', []),
        'end_condition': response.get('end_condition', ''),
        'narrative_direction': response.get('narrative_direction', ''),
    }

def _build_episode_generation_prompt(
    self,
    arc: StoryArc,
    previous_recap: Optional[EpisodeRecap]
) -> str:
    """Build prompt for new episode context"""
    
    prev_context = ""
    if previous_recap:
        prev_context = f"""
PREVIOUS EPISODE ({previous_recap.episode_number}):
Title: {previous_recap.title}
Summary: {previous_recap.summary}
Key Themes: {', '.join(previous_recap.key_themes)}

"""
    
    prompt = f"""
You are a narrative architect designing episodes for a story arc.

ARC: {arc.title}
Premise: {arc.premise}
Direction: {arc.narrative_direction}

{prev_context}

Generate context for the NEXT EPISODE:
1. Pick a primary tone (dark_and_mysterious, hopeful, tense, etc.)
2. Define the episode's end condition (what should resolve)
3. Describe narrative direction (what should happen)

The episode will have ~15-20 scenes.

Respond with JSON:
{{
    "tone_tags": ["tone1", "tone2"],
    "end_condition": "What must happen by episode end",
    "narrative_direction": "The story moves toward..."
}}
"""
    return prompt
```

**Acceptance Criteria:**
- [ ] `generate_new_episode_context()` works
- [ ] Returns dict with tone, end_condition, narrative_direction
- [ ] Unit tests passing (2+ tests)

---

### E2-3: Character State Reconciliation (Dev-G, 2 days)

**What:** Apply change_notes to character snapshot, handling contradictions.

**Add to `episode_recap_generator.py`:**

```python
async def reconcile_character_states_with_ai(
    self,
    starting_states: Dict[str, CharacterState],
    changes: List[str]
) -> Dict[str, CharacterState]:
    """
    Advanced reconciliation: if changes contradict, ask AI to resolve.
    
    Example:
    - Starting: Alice is hopeful
    - Changes: "Alice loses hope", "Alice finds hope again"
    - Result: Ask AI which is final state, why
    """
    
    final_states = dict(starting_states)
    
    # Detect potential contradictions
    contradictions = self._detect_contradictions(changes)
    
    if contradictions:
        # Ask AI to resolve
        resolution = await self._resolve_contradictions_with_ai(
            starting_states,
            changes,
            contradictions
        )
        # Apply resolution
        final_states = resolution
    else:
        # Simple: apply all changes in order
        for change in changes:
            self._apply_single_change(final_states, change)
    
    return final_states

def _detect_contradictions(self, changes: List[str]) -> List[tuple]:
    """Find contradictory statements"""
    contradictions = []
    
    for i, change1 in enumerate(changes):
        for change2 in changes[i+1:]:
            if self._are_contradictory(change1, change2):
                contradictions.append((change1, change2))
    
    return contradictions

def _are_contradictory(self, change1: str, change2: str) -> bool:
    """Simple check: do these changes contradict?"""
    # Keyword-based: "dead" vs "alive", "betrays" vs "trusts", etc.
    contradictory_pairs = [
        ("dead", "alive"),
        ("betrays", "trusts"),
        ("hates", "loves"),
    ]
    
    lower1 = change1.lower()
    lower2 = change2.lower()
    
    for word1, word2 in contradictory_pairs:
        if (word1 in lower1 and word2 in lower2) or \
           (word2 in lower1 and word1 in lower2):
            return True
    
    return False

async def _resolve_contradictions_with_ai(
    self,
    starting_states,
    changes,
    contradictions
) -> Dict[str, CharacterState]:
    """Ask AI to decide which version is canon"""
    
    prompt = f"""
Reconcile these character state changes.

Starting state: {starting_states}

Changes recorded:
{chr(10).join(changes)}

Contradictions to resolve:
{chr(10).join([f"- '{c1}' vs '{c2}'" for c1, c2 in contradictions])}

For each contradiction, decide which is the final state
(the one that actually happened). Respond with the final
character states as JSON.
"""
    
    response = await self.generator.generate(
        context_type="reconcile",
        context=prompt
    )
    
    return response.get('final_states', starting_states)
```

**Acceptance Criteria:**
- [ ] `reconcile_character_states_with_ai()` implemented
- [ ] Contradiction detection working
- [ ] AI fallback working
- [ ] Unit tests (3+ tests)

---

### E2-4: Arc Compressor (Dev-G, 4 days)

**What:** After 15 episodes, pick the canonical mainline branch and archive others.

**File:** `backend/app/engine/arc_compressor.py` (CREATE NEW)

**Why:** After 15 episodes, the segment graph has branched significantly. Arc compression:
1. Finds all divergent branches (from user sessions)
2. Picks the "best" one (most narratively coherent, most visited, etc.)
3. Archives the alternatives
4. Continues from mainline only

This bounds growth: instead of 2^15 segments, you have ~20 * 15 = 300 segments.

**Code:**

```python
from typing import List, Dict, Set, Optional, Tuple
from app.models import Story, StorySegment, StoryArc, ArcCompressionResult
from app.engine.generator import TextGenerator
from enum import Enum

class BranchQuality(Enum):
    MAINLINE = "mainline"
    POPULAR = "popular"
    INTERESTING = "interesting"
    NICHE = "niche"

class ArcCompressor:
    """Compress arc after 15 episodes"""
    
    def __init__(self, story: Story, generator: TextGenerator):
        self.story = story
        self.generator = generator
    
    async def compress_arc(self, arc_id: str) -> ArcCompressionResult:
        """
        Compress arc by selecting mainline and archiving alternatives.
        
        Steps:
        1. Find all branches in this arc (from user sessions)
        2. Select candidates (top N by popularity, random M)
        3. Summarize each branch
        4. Call AI to pick best (most coherent, thematic)
        5. Archive non-mainline segments
        6. Save compression result
        7. Return result
        """
        arc = self.story.get_arc(arc_id)
        if not arc:
            raise ValueError(f"Arc {arc_id} not found")
        
        # 1. Find branches
        branches = self._find_branches_in_arc(arc_id)
        
        if len(branches) <= 1:
            # No compression needed
            return None
        
        # 2. Select candidates (top 3 + random 2)
        candidates = self._select_candidates(branches)
        
        # 3. Summarize branches
        branch_summaries = [
            await self._summarize_branch(branch)
            for branch in candidates
        ]
        
        # 4. AI selection
        mainline_branch_id = await self._ai_select_mainline(
            arc,
            branch_summaries
        )
        
        # 5. Archive non-mainline
        mainline_segments = set(candidates[mainline_branch_id])
        archived_segments = []
        
        for i, candidate in enumerate(candidates):
            if i != mainline_branch_id:
                # Archive these segments
                for seg_id in candidate:
                    seg = self.story.get_segment(seg_id)
                    seg.status = SegmentStatus.ARCHIVED
                    seg.save()
                    archived_segments.append(seg_id)
        
        # 6. Save compression result
        result = ArcCompressionResult(
            arc_id=arc_id,
            mainline_branch_segments=list(mainline_segments),
            archived_segments=archived_segments,
            selection_rationale="Branch selected by AI analysis for narrative coherence"
        )
        
        # 7. Mark arc as compressed
        arc.is_compressed = True
        arc.compression_result = result
        arc.save()
        
        return result
    
    def _find_branches_in_arc(self, arc_id: str) -> List[List[str]]:
        """
        Find divergent branches from user sessions.
        
        For each episode in arc, find all different paths users took.
        """
        all_segments = self.story.list_segments()
        arc_segments = [
            seg for seg in all_segments
            if seg.arc_id == arc_id
        ]
        
        if not arc_segments:
            return []
        
        # Group by episode
        episodes = {}
        for seg in arc_segments:
            ep = seg.episode_number
            if ep not in episodes:
                episodes[ep] = []
            episodes[ep].append(seg)
        
        # For each episode, find divergence points
        # (simplified: just return all distinct chains)
        branches = []
        
        for seg in arc_segments:
            if not seg.parent_segment_id:
                # Start of arc, begin a branch chain
                chain = self._walk_forward_from(seg.id)
                branches.append(chain)
        
        return branches
    
    def _walk_forward_from(self, segment_id: str) -> List[str]:
        """Walk forward from segment through all descendants"""
        chain = [segment_id]
        seg = self.story.get_segment(segment_id)
        
        # For simplicity: follow first choice always
        # (Real implementation would explore all paths)
        if hasattr(seg, 'outgoing_choices') and seg.outgoing_choices:
            first_choice = list(seg.outgoing_choices.values())[0]
            if first_choice.to_segment_id:
                chain.extend(
                    self._walk_forward_from(first_choice.to_segment_id)
                )
        
        return chain
    
    def _select_candidates(
        self,
        branches: List[List[str]]
    ) -> List[List[str]]:
        """Select top N by length + random M"""
        if len(branches) <= 3:
            return branches
        
        # Top 3 longest
        sorted_branches = sorted(
            branches,
            key=len,
            reverse=True
        )
        candidates = sorted_branches[:3]
        
        # Add random 2
        import random
        others = sorted_branches[3:]
        if others:
            candidates.extend(random.sample(others, min(2, len(others))))
        
        return candidates
    
    async def _summarize_branch(self, branch: List[str]) -> str:
        """Create text summary of a branch"""
        segments = [self.story.get_segment(seg_id) for seg_id in branch]
        
        summary = f"""
Branch with {len(branch)} segments:
{chr(10).join([seg.get_short_overview() for seg in segments[:5]])}
{"..." if len(segments) > 5 else ""}
"""
        return summary
    
    async def _ai_select_mainline(
        self,
        arc: StoryArc,
        branch_summaries: List[str]
    ) -> int:
        """Ask AI which branch is best"""
        
        prompt = f"""
You are a narrative architect selecting a canonical storyline.

ARC: {arc.title}
Premise: {arc.premise}

We have {len(branch_summaries)} divergent branches.
Select which should be the mainline (canon) version.

Consider:
1. Narrative coherence with arc premise
2. Character development consistency
3. Thematic resonance

BRANCH OPTIONS:
{chr(10).join([
    f"Option {i}: {summary}"
    for i, summary in enumerate(branch_summaries)
])}

Respond with JSON:
{{
    "selected_branch": 0,
    "reasoning": "Why this branch..."
}}
"""
        
        response = await self.generator.generate(
            context_type="select_branch",
            context=prompt
        )
        
        return response.get('selected_branch', 0)
```

**Acceptance Criteria:**
- [ ] `_find_branches_in_arc()` finds divergent paths
- [ ] `_select_candidates()` picks top branches
- [ ] `_summarize_branch()` creates readable summaries
- [ ] `_ai_select_mainline()` calls AI to pick
- [ ] Archive mechanism marks segments as ARCHIVED
- [ ] `compress_arc()` full flow working
- [ ] Unit tests (4+ tests)
- [ ] Integration test: compression on real arc

---

### E2-5: Archive State Handling (Dev-F or G, 2 days)

**What:** Make sure queries exclude archived segments by default.

**File:** `backend/app/models/story.py` (MODIFY)

**Changes:**

```python
class Story(BaseModel):
    # ... existing code ...
    
    def get_segment(
        self,
        segment_id: str,
        include_archived: bool = False
    ) -> Optional[StorySegment]:
        """Get segment, excluding archived by default"""
        seg = self._load_segment(segment_id)  # Load from disk
        
        if seg and seg.status == SegmentStatus.ARCHIVED:
            if not include_archived:
                return None
        
        return seg
    
    def get_available_choices(
        self,
        segment_id: str
    ) -> List[StoryChoice]:
        """Get choices from segment, excluding archived destinations"""
        seg = self.get_segment(segment_id)
        if not seg:
            return []
        
        choices = []
        for choice_id in seg.outgoing_choices:
            choice = self._load_choice(choice_id)
            
            # Exclude if destination is archived
            if choice.to_segment_id:
                dest = self.get_segment(choice.to_segment_id)
                if dest is None and not dest.status == SegmentStatus.ARCHIVED:
                    continue
            
            choices.append(choice)
        
        return choices
```

**Acceptance Criteria:**
- [ ] `get_segment()` respects include_archived flag
- [ ] `get_available_choices()` excludes archived
- [ ] All game loop code updated
- [ ] Unit tests (3+ tests)

---

## Key Concepts for E2

### Episode Cycles
1. Play ~15-20 scenes
2. Detect end condition (pacing >= 0.8, explicit signal, etc.)
3. Generate recap (title, summary, themes)
4. Reconcile character changes
5. Generate new episode context
6. Continue from new episode 1

### Arc Compression Timeline
- Episodes 1-15: Generate freely, build branches
- Episode 15 end: Trigger compression
  - Find all branches
  - Select mainline
  - Archive others
- Episode 16+: Continue on mainline only

### Character State Flow
```
Episode Start:
  char_states = snapshot

During Episode:
  change_notes = [
    "Alice learns secret",
    "Alice becomes angry",
  ]

Episode End (Recap):
  Apply changes to snapshot
  Save new snapshot
  Use for next episode
```

---

## Definition of Done for Epic 2

- [ ] E2-1: EpisodeRecap generator (walk, collect, generate, save)
- [ ] E2-2: New episode context generation
- [ ] E2-3: Character state reconciliation (simple + AI version)
- [ ] E2-4: Arc compressor (find, select, archive)
- [ ] E2-5: Archive handling in queries
- [ ] All tests passing (pytest -v)
- [ ] Integration test: full episode cycle with recap and compression
- [ ] Code review completed
- [ ] PR merged to main

---

## Common Pitfalls

1. **Infinite recursion** → Add visited set when walking branches
2. **Character contradictions** → Use AI fallback
3. **Orphaned archived segments** → Update all queries
4. **Compression destroying data** → Create ArcCompressionResult backup
5. **Episode infinite loops** → Hard limit on segment count

---

## Next: Integration with E1

Once E2 is merged:
- E1's generation pipeline can call E2's recap generation
- Episode transitions trigger recap at the right time
- New episode context feeds into next generation
