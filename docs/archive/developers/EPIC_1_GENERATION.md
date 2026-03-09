# Epic 1: Generation Pipeline

**For Developers D, E**  
**Duration:** 2 weeks (parallel to E2 & E3)  
**Blocker:** Epic 0 must be complete  
**Deliverable:** Full segment generation with episode transitions, context building, AI integration

---

## What You're Building

The v2 generation pipeline creates new story segments intelligently:

1. **Context Builder** → Walk backward through parent chain, accumulate character state changes, detect episode transitions
2. **Enhanced Generator Interface** → Updated AI interface that handles episode context and validation
3. **Generation Pipeline** → Main loop: check if choice leads to existing segment or needs generation
4. **Segment Generation** → Create new segment with all fields, save choices
5. **Episode Transitions** → Detect when episode should end, signal next episode

This is the **heart of v2**: what makes it different from v1 is smarter, more coherent generation based on accumulated context.

---

## Files You'll Touch

### Core Files (Read to Understand)
- `backend/app/models/story_segment.py` → Enhanced by E0 (read for new fields)
- `backend/app/engine/story_runner.py` → Main game loop (you'll enhance)
- `backend/app/engine/generator.py` → AI interface (you'll enhance)
- `backend/app/models/story_choice.py` → Read structure

### Files You'll Create
- `backend/app/engine/segment_context_builder.py` → **NEW** (E1-1)

### Files You'll Modify
- `backend/app/engine/story_runner.py` → Add generation methods (E1-2, E1-4)
- `backend/app/engine/generator.py` → Enhanced interface (E1-3)

---

## Task Breakdown

### E1-1: Segment Context Builder (Dev-D, 3 days)

**What:** Walks backward through the parent chain, accumulates state changes, detects episode transitions, calculates pacing.

**File:** `backend/app/engine/segment_context_builder.py` (CREATE NEW)

**Why It Matters:** The AI needs to know:
- What happened in previous scenes (story continuity)
- How characters have changed (state accumulation)
- When the episode should end (pacing signals)
- What the overall tone is (episode context)

**Code Structure:**

```python
from typing import Dict, List, Optional, Any
from app.models import Story, StorySegment, EpisodeRecap
from app.models.story_segment import SegmentStatus

class SegmentContextBuilder:
    """Build rich context for segment generation"""
    
    def __init__(self, story: Story):
        self.story = story
    
    def build_context(
        self,
        current_segment_id: str,
        user_choice: str  # The choice text the user made
    ) -> Dict[str, Any]:
        """
        Build generation context for new segment.
        
        Returns:
        {
            'previous_segments': [...],  # Last 3-5 scenes
            'character_states': {...},   # Latest character snapshot
            'accumulated_changes': [...],  # All change_notes in chain
            'episode_context': {...},    # Tone, end_condition, pacing
            'should_transition': bool,   # Start new episode?
            'pacing_weight': 0.0-1.0,   # Progress to episode end
            'protagonist_id': 'char_1',  # Main character this episode
        }
        """
        # 1. Get the current segment
        current_seg = self.story.get_segment(current_segment_id)
        if not current_seg:
            raise ValueError(f"Segment {current_segment_id} not found")
        
        # 2. Walk backward to episode start
        episode_chain = self._walk_episode_chain(current_segment_id)
        
        # 3. Accumulate character changes
        accumulated_changes = self._accumulate_changes(episode_chain)
        
        # 4. Detect episode transition
        should_transition = self._should_transition_episode(
            current_seg, 
            accumulated_changes
        )
        
        # 5. Calculate pacing weight
        pacing = self._calculate_pacing_weight(
            current_seg, 
            should_transition
        )
        
        # 6. Assemble context
        return {
            'previous_segments': [
                self.story.get_segment(seg_id).get_short_overview()
                for seg_id in episode_chain[-5:]  # Last 5 scenes
            ],
            'character_states': current_seg.character_states,
            'accumulated_changes': accumulated_changes,
            'episode_number': current_seg.episode_number,
            'episode_tone': current_seg.episode_tone,
            'episode_end_condition': current_seg.episode_end_condition,
            'segment_number_in_episode': current_seg.segment_number_in_episode,
            'should_transition_episode': should_transition,
            'pacing_weight': pacing,
            'protagonist_id': current_seg.protagonist_id,
            'user_choice': user_choice,
        }
    
    def _walk_episode_chain(self, segment_id: str) -> List[str]:
        """
        Walk backward from segment to episode start.
        
        Returns list of segment IDs in order from start to current.
        """
        chain = []
        current = self.story.get_segment(segment_id)
        episode_num = current.episode_number
        
        while current and current.episode_number == episode_num:
            chain.insert(0, current.id)  # Prepend (we're walking backward)
            
            if not current.parent_segment_id:
                break
            
            current = self.story.get_segment(current.parent_segment_id)
        
        return chain
    
    def _accumulate_changes(self, segment_chain: List[str]) -> List[str]:
        """Collect all change_notes from segment chain"""
        all_changes = []
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            all_changes.extend(seg.change_notes)
        return all_changes
    
    def _should_transition_episode(
        self,
        current_segment: StorySegment,
        changes: List[str]
    ) -> bool:
        """
        Decide if this segment should end the episode.
        
        Triggers if:
        1. end_condition_proximity >= 0.8 (AI said we're near end)
        2. segment_number_in_episode >= 18 (hard limit)
        3. Changes mention explicit end condition
        """
        # Check proximity
        if current_segment.end_condition_proximity >= 0.8:
            return True
        
        # Check segment count (max ~20 per episode)
        if current_segment.segment_number_in_episode >= 18:
            return True
        
        # Check for explicit end condition keywords
        end_keywords = ['chapter', 'end', 'conclusion', 'climax']
        for change in changes:
            if any(kw in change.lower() for kw in end_keywords):
                return True
        
        return False
    
    def _calculate_pacing_weight(
        self,
        segment: StorySegment,
        will_transition: bool
    ) -> float:
        """
        Calculate pacing weight (0.0 to 1.0).
        
        0.0 = start of episode
        1.0 = end of episode
        
        Used by AI to understand how much "room" is left.
        """
        if will_transition:
            return 0.9  # Very close to end
        
        # Exponential curve: slow at start, fast at end
        seg_num = segment.segment_number_in_episode
        max_segments = 20
        
        # Quadratic: (seg_num / max)^2 gives nonlinear progression
        weight = (seg_num / max_segments) ** 2
        return min(weight, 0.99)
```

**Unit Tests (at least these):**

```python
def test_walk_episode_chain(sample_story):
    """Walk backward to episode start"""
    # Create 3 connected segments in episode 1
    seg1 = StorySegment(story=sample_story, id="seg_1", episode_number=1)
    seg2 = StorySegment(
        story=sample_story, 
        id="seg_2", 
        episode_number=1, 
        parent_segment_id="seg_1"
    )
    seg3 = StorySegment(
        story=sample_story,
        id="seg_3",
        episode_number=1,
        parent_segment_id="seg_2"
    )
    
    builder = SegmentContextBuilder(sample_story)
    chain = builder._walk_episode_chain("seg_3")
    
    assert chain == ["seg_1", "seg_2", "seg_3"]

def test_accumulate_changes(sample_story):
    """Collect all changes in chain"""
    seg1 = StorySegment(
        story=sample_story,
        id="seg_1",
        change_notes=["Alice is sad"]
    )
    seg2 = StorySegment(
        story=sample_story,
        id="seg_2",
        parent_segment_id="seg_1",
        change_notes=["Alice finds hope"]
    )
    
    builder = SegmentContextBuilder(sample_story)
    changes = builder._accumulate_changes(["seg_1", "seg_2"])
    
    assert changes == ["Alice is sad", "Alice finds hope"]

def test_should_transition_on_proximity(sample_story):
    """Transition when proximity >= 0.8"""
    seg = StorySegment(
        story=sample_story,
        id="seg_1",
        end_condition_proximity=0.85
    )
    builder = SegmentContextBuilder(sample_story)
    
    assert builder._should_transition_episode(seg, []) is True

def test_calculate_pacing_weight(sample_story):
    """Pacing increases quadratically"""
    builder = SegmentContextBuilder(sample_story)
    
    seg_5 = StorySegment(
        story=sample_story, 
        id="seg_5",
        segment_number_in_episode=5
    )
    weight_5 = builder._calculate_pacing_weight(seg_5, False)
    
    seg_15 = StorySegment(
        story=sample_story,
        id="seg_15",
        segment_number_in_episode=15
    )
    weight_15 = builder._calculate_pacing_weight(seg_15, False)
    
    # Should be nonlinear: weight_15 > weight_5
    assert weight_15 > weight_5
    assert weight_5 < weight_15 < 1.0

def test_build_context_full(sample_story):
    """Full context building"""
    seg = StorySegment(
        story=sample_story,
        id="seg_1",
        episode_number=2,
        episode_tone="dark_and_mysterious",
        protagonist_id="alice"
    )
    builder = SegmentContextBuilder(sample_story)
    context = builder.build_context("seg_1", "Go forward boldly")
    
    assert context['episode_number'] == 2
    assert context['user_choice'] == "Go forward boldly"
    assert context['protagonist_id'] == "alice"
    assert 'pacing_weight' in context
```

**Acceptance Criteria:**
- [ ] All 4 internal methods working (`_walk_episode_chain`, `_accumulate_changes`, etc.)
- [ ] `build_context()` returns complete context dict
- [ ] Episode transition detection working correctly
- [ ] Pacing weight calculation verified (nonlinear)
- [ ] Unit tests passing (5+ tests)
- [ ] Handles edge cases (missing parent, archived segments)

---

### E1-2: Update Generation Pipeline (Dev-D, 3 days)

**What:** Add the main loop that decides whether to traverse to existing segment or generate new one.

**File:** `backend/app/engine/story_runner.py` (MODIFY)

**Key Method:**

```python
async def traverse_or_generate(
    self,
    choice: StoryChoice
) -> StorySegment:
    """
    When user makes a choice, either:
    1. Traverse to existing destination (if to_segment_id is set)
    2. Generate new segment (if to_segment_id is null)
    
    Returns the destination segment.
    """
    # Case 1: Choice already has a destination
    if choice.to_segment_id:
        dest = self.story.get_segment(choice.to_segment_id)
        if not dest:
            raise ValueError(f"Destination segment {choice.to_segment_id} not found")
        return dest
    
    # Case 2: Choice needs generation
    # Lock the choice to prevent duplicate generation
    choice.lock()  # Add a `locked: bool` field to StoryChoice
    
    try:
        # Build context
        builder = SegmentContextBuilder(self.story)
        context = builder.build_context(
            self.current_segment_id,
            choice.text
        )
        
        # Generate new segment
        new_segment = await self._generate_segment(context)
        
        # Link choice to new segment
        choice.to_segment_id = new_segment.id
        choice.save()
        
        return new_segment
    
    except Exception as e:
        # Unlock on failure so retry is possible
        choice.unlock()
        raise e
    finally:
        choice.unlock()  # Always unlock

async def _generate_segment(self, context: Dict[str, Any]) -> StorySegment:
    """
    Generate a new segment using AI and context.
    
    This is called by traverse_or_generate when a choice
    has no destination yet.
    """
    # Build prompt (detailed below)
    prompt = self._build_generation_prompt(context)
    
    # Call AI generator
    response = await self.generator.generate(
        context_type="scene",
        context=prompt
    )
    
    # Create segment
    new_segment = StorySegment(
        story=self.story,
        id=self._generate_segment_id(),
        text_blocks=response['text_blocks'],
        episode_number=context['episode_number'],
        episode_tone=context['episode_tone'],
        episode_end_condition=context['episode_end_condition'],
        segment_number_in_episode=context['segment_number_in_episode'] + 1,
        pacing_weight=response.get('pacing_weight', context['pacing_weight']),
        protagonist_id=context['protagonist_id'],
        parent_segment_id=self.current_segment_id,
        character_states=response.get('character_states', {}),
        change_notes=response.get('change_notes', []),
        end_condition_proximity=response.get(
            'end_condition_proximity', 
            0.0
        ),
        triggers_episode_transition=context['should_transition_episode'],
        status=SegmentStatus.GENERATED,
    )
    
    # Create 2 outgoing choices
    for choice_text in response['suggested_choices']:
        choice = StoryChoice(
            story=self.story,
            id=self._generate_choice_id(),
            from_segment_id=new_segment.id,
            to_segment_id=None,  # Will be generated later
            text=choice_text,
        )
        choice.save()
    
    # Save segment
    new_segment.save()
    
    return new_segment

def _build_generation_prompt(self, context: Dict) -> str:
    """
    Build a detailed system + user prompt for generation.
    
    Includes:
    - Previous scene summaries
    - Character states
    - Episode tone & context
    - Pacing signal
    - User choice
    """
    prev_scenes = "\n".join(context['previous_segments'])
    
    prompt = f"""
You are a creative storyteller continuing a narrative.

EPISODE CONTEXT:
- Episode: {context['episode_number']}
- Tone: {context['episode_tone']}
- End Condition: {context['episode_end_condition']}
- Scene {context['segment_number_in_episode']} of ~20
- Pacing: {context['pacing_weight']:.1%} toward episode end

PREVIOUS SCENES:
{prev_scenes}

CHARACTER STATES:
{json.dumps(context['character_states'], indent=2)}

ACCUMULATED CHANGES THIS EPISODE:
{chr(10).join(context['accumulated_changes']) or '(none yet)'}

USER CHOSE: "{context['user_choice']}"

Generate the next scene that:
1. Follows naturally from the choice
2. Respects character states and changes
3. Maintains the episode tone
4. Advances toward the end condition
5. Leaves room for {20 - context['segment_number_in_episode']} more scenes

Respond with JSON:
{{
    "text_blocks": [
        {{"type": "NARRATOR_DESCRIBING", "content": "..."}},
        ...
    ],
    "character_states": {{"char_id": {{"mood": "...", ...}}}},
    "change_notes": ["Character X did Y", ...],
    "pacing_weight": 0.5,
    "end_condition_proximity": 0.3,
    "suggested_choices": ["Option 1", "Option 2"]
}}
"""
    return prompt
```

**Acceptance Criteria:**
- [ ] `traverse_or_generate()` implemented and handles both cases
- [ ] Choice locking mechanism prevents race conditions
- [ ] `_generate_segment()` creates valid StorySegment
- [ ] Outgoing choices created and saved
- [ ] Error handling: failures unlock choice for retry
- [ ] Unit tests passing (4+ tests)
- [ ] Integration test: full flow from choice to new segment

---

### E1-3: Enhanced Generator Interface (Dev-E, 2 days)

**What:** Update the abstract `TextGenerator` class to handle episode context and validate responses.

**File:** `backend/app/engine/generator.py` (MODIFY)

**Changes:**

```python
class TextGenerator(ABC):
    """Abstract base class for AI generation"""
    
    @abstractmethod
    async def generate(
        self,
        context_type: str,  # "scene", "recap", "arc_context"
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate content based on context.
        
        Args:
            context_type: Type of generation ("scene", "recap", etc.)
            context: Full context dict with all needed info
        
        Returns:
            Validated response dict with required fields:
            - For scene: text_blocks, character_states, change_notes, 
                        pacing_weight, suggested_choices
            - For recap: title, summary, key_themes
            - For arc_context: tone_tags, end_condition, narrative_direction
        
        Raises:
            ValidationError if response missing required fields
        """
        pass
    
    async def generate_with_fallback(
        self,
        context_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate with graceful fallback if validation fails.
        
        Tries multiple times with adjusted prompts before giving up.
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = await self.generate(context_type, context)
                self._validate_response(context_type, response)
                return response
            
            except ValidationError as e:
                if attempt < max_retries - 1:
                    # Retry with adjusted context
                    context['_retry_attempt'] = attempt + 1
                    continue
                else:
                    # Fall back to synthetic response
                    return self._synthetic_fallback(context_type, context)
    
    def _validate_response(self, context_type: str, response: dict):
        """Validate that response has all required fields"""
        required_fields = {
            'scene': ['text_blocks', 'suggested_choices'],
            'recap': ['title', 'summary', 'key_themes'],
            'arc_context': ['tone_tags', 'end_condition', 'narrative_direction'],
        }
        
        if context_type not in required_fields:
            raise ValueError(f"Unknown context_type: {context_type}")
        
        required = required_fields[context_type]
        for field in required:
            if field not in response:
                raise ValidationError(
                    f"Response missing required field: {field}"
                )
    
    def _synthetic_fallback(
        self,
        context_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a minimal valid response when AI fails"""
        if context_type == 'scene':
            return {
                'text_blocks': [
                    {
                        'type': 'NARRATOR_DESCRIBING',
                        'content': 'The scene continues. You feel a moment of pause before the next event unfolds.',
                    }
                ],
                'character_states': context.get('character_states', {}),
                'change_notes': [],
                'pacing_weight': context.get('pacing_weight', 0.5),
                'suggested_choices': [
                    'Continue forward',
                    'Take a different approach',
                ]
            }
        elif context_type == 'recap':
            return {
                'title': f"Episode {context.get('episode_number', 1)}",
                'summary': 'The episode unfolds as the story progresses.',
                'key_themes': []
            }
        else:
            return {}
```

**Acceptance Criteria:**
- [ ] `generate()` signature updated with context_type
- [ ] Response validation for all context types
- [ ] Graceful fallback on validation failure
- [ ] Synthetic fallback responses valid
- [ ] Unit tests (4+ tests)
- [ ] Integration test with mock generator

---

### E1-4: Segment Generation Implementation (Dev-E, 3 days)

**What:** Implement the full `_generate_segment()` method with error handling.

(Already partially covered in E1-2, so this focuses on completion and testing)

**Acceptance Criteria:**
- [ ] `_generate_segment()` creates complete StorySegment
- [ ] All fields populated (text_blocks, character_states, etc.)
- [ ] Outgoing choices created (2 per segment)
- [ ] Save to disk successful
- [ ] Error handling: graceful failures, logging
- [ ] Unit tests (5+ tests)
- [ ] Integration tests with E1-1 (context + generation)
- [ ] No orphaned API calls (retries on failure)

---

### E1-5: Episode Transition Logic (Dev-D, 2 days)

**What:** Complete the `_should_transition_episode()` logic with all detection methods.

(Partially covered in E1-1, this refines and tests thoroughly)

**Acceptance Criteria:**
- [ ] Proximity check working (>= 0.8 triggers)
- [ ] Segment count check working (>= 18 triggers)
- [ ] Explicit keyword detection working
- [ ] Unit tests (4+ tests covering all triggers)
- [ ] Integration test: full episode from start to transition

---

## Key Concepts for E1

### Parent Chain Walking
```
Segment 5 (current)
  └─ parent: Segment 4
      └─ parent: Segment 3
          └─ parent: Segment 2
              └─ parent: Segment 1 (episode start)
```

Walk backward until `parent_segment_id` is null or episode number changes.

### Change Accumulation
Each segment has a `change_notes: List[str]` field. As you walk the chain, collect all changes. At episode end, reconcile these into the character state snapshot.

```python
changes = [
    "Alice learns about the prophecy",
    "Alice becomes determined",
    "Alice confronts the guardian",
]
# These inform the next generation and recap
```

### Pacing Signal
Tell the AI how much room is left. Exponential curve:
- Segment 1 of 20: pacing = 0.0025
- Segment 5 of 20: pacing = 0.0625
- Segment 10 of 20: pacing = 0.25
- Segment 15 of 20: pacing = 0.5625
- Segment 18 of 20: pacing = 0.8100

AI uses this to pace the story: fewer grand events near the start, more near the end.

---

## Definition of Done for Epic 1

- [ ] E1-1: SegmentContextBuilder fully working (all methods, tests)
- [ ] E1-2: Generation pipeline handles traverse & generate (tests passing)
- [ ] E1-3: Generator interface enhanced with validation (fallbacks working)
- [ ] E1-4: Segment generation creates complete segments (no orphans)
- [ ] E1-5: Episode transition logic detects all triggers
- [ ] All tests passing (pytest -v)
- [ ] Integration test: full flow from context to segment to choices
- [ ] Code review completed
- [ ] PR merged to main

---

## Common Pitfalls to Avoid

1. **Circular parent chains** → Add a visited set when walking
2. **Orphaned API calls** → Always unlock choice on error
3. **Missing validation fields** → Use fallback responses
4. **Race conditions** → Choice locking prevents simultaneous generation
5. **Memory explosion** → Don't keep full segments in memory, use IDs

---

## Next: E2 & E3 Can Now Run in Parallel

Once E1 is merged, E2 (episodes) and E3 (CLI) can start using the generation pipeline.
