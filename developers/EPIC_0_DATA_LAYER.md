# Epic 0: Data Layer Foundation

**For Developers A, B, C**  
**Duration:** 1 week  
**Blocker:** None (start first)  
**Deliverable:** Enhanced data models, migration script, test infrastructure

---

## What You're Building

The v2 system replaces an exponential branching tree with a **shared immutable segment graph**. To support this, you need to:

1. **Enhance StorySegment** with episode/arc context fields
2. **Create EpisodeRecap** model for episode summaries
3. **Create StoryArc** model for arc metadata
4. **Simplify UserSession** to only track visits
5. **Write a migration script** to convert existing v1 data
6. **Build test infrastructure** for other teams to use

These models form the foundation that E1 (generation), E2 (episodes), E3 (CLI), and E4 (testing) all depend on.

---

## Files You'll Touch

### Core Files (Read to Understand)
- `backend/app/models/story_base.py` → Base persistence class (don't modify)
- `backend/app/models/story_segment.py` → **YOU ENHANCE** (E0-1)
- `backend/app/models/session_state.py` → **YOU SIMPLIFY** (E0-4)

### Files You'll Create
- `backend/app/models/episode_recap.py` → **NEW** (E0-2)
- `backend/app/models/story_arc.py` → **NEW** (E0-3)
- `backend/scripts/migrate_v1_to_v2.py` → **NEW** (E0-5)
- `backend/tests/conftest.py` → **ENHANCE** (E0-6)
- `backend/tests/fixtures/` → **NEW FIXTURES** (E0-6)

### Files You DON'T Touch
- `backend/app/cli.py` → Handled by E3
- `backend/app/engine/` → Handled by E1/E2
- `backend/frontend/` → Separate project

---

## Task Breakdown & Code Patterns

### E0-1: Enhance StorySegment Model (Dev-A, 3 days)

**What:** Add 20+ new fields to `StorySegment` to support episodes, arcs, and character state tracking.

**File:** `backend/app/models/story_segment.py`

**New Fields to Add:**

```python
# Status enum (at top of file)
from enum import Enum

class SegmentStatus(str, Enum):
    UNEXPLORED = "unexplored"      # Not yet generated
    GENERATING = "generating"      # In progress
    GENERATED = "generated"        # Ready
    ARCHIVED = "archived"          # Replaced by compression

# In StorySegment class, add these fields:

# -- Parent/History Tracking --
parent_segment_id: Optional[str] = Field(
    None, 
    description="Which segment came before this one"
)
parent_choice_id: Optional[str] = Field(
    None,
    description="Which choice led to this segment"
)

# -- Episode Context --
arc_id: Optional[str] = Field(
    None,
    description="Which story arc this segment belongs to"
)
episode_number: int = Field(
    1,
    description="Which episode (1-indexed)"
)
episode_tone: Optional[str] = Field(
    None,
    description="Tone tag for this episode (e.g., 'dark_and_mysterious')"
)
episode_end_condition: Optional[str] = Field(
    None,
    description="What should happen at end of episode"
)
segment_number_in_episode: int = Field(
    1,
    description="Position within episode (1-indexed, max ~20)"
)
pacing_weight: float = Field(
    0.0,
    ge=0.0,
    le=1.0,
    description="How close to episode end (0.0=start, 1.0=end)"
)

# -- Character & Location State --
protagonist_id: Optional[str] = Field(
    None,
    description="Main character this episode"
)
character_states: Dict[str, Dict[str, Any]] = Field(
    default_factory=dict,
    description="State snapshot of each character at this segment"
)
change_notes: List[str] = Field(
    default_factory=list,
    description="Lightweight notes about character/location changes"
)
locations_running_status: Dict[str, Dict[str, Any]] = Field(
    default_factory=dict,
    description="State of locations at this segment"
)

# -- Episode Completion Signals --
end_condition_proximity: float = Field(
    0.0,
    ge=0.0,
    le=1.0,
    description="How close (0.0=far, 1.0=end condition met)"
)
protagonist_alive: bool = Field(
    True,
    description="Is the protagonist still alive (for death endings)"
)
triggers_episode_transition: bool = Field(
    False,
    description="Should this segment end the episode and start a new one"
)

# -- Immutability --
status: SegmentStatus = Field(
    default=SegmentStatus.UNEXPLORED,
    description="State of this segment"
)
```

**Implementation Steps:**

1. Open `backend/app/models/story_segment.py`
2. Add the `SegmentStatus` enum at the top
3. Add all fields listed above to the `StorySegment` class
4. Ensure all new fields are optional or have defaults (backward compatibility!)
5. Add an `@property` to prevent modification after GENERATED:

```python
@property
def is_locked(self) -> bool:
    """Segment cannot be modified after generation"""
    return self.status == SegmentStatus.GENERATED

def validate_locked(self):
    """Raise error if locked"""
    if self.is_locked:
        raise ValueError(f"Segment {self.id} is locked after generation")
```

6. Update the `save()` method to preserve status
7. Write unit tests:

```python
def test_segment_creation():
    """Segment created with defaults"""
    seg = StorySegment(story=sample_story, id="seg_1", ...)
    assert seg.episode_number == 1
    assert seg.status == SegmentStatus.UNEXPLORED
    assert seg.character_states == {}

def test_segment_immutability():
    """Cannot modify generated segment"""
    seg = StorySegment(story=sample_story, id="seg_1", ...)
    seg.status = SegmentStatus.GENERATED
    with pytest.raises(ValueError):
        seg.validate_locked()  # Should fail

def test_segment_serialization():
    """Save and load with new fields"""
    seg = StorySegment(
        story=sample_story,
        id="seg_1",
        episode_number=2,
        pacing_weight=0.5,
        character_states={"char_1": {"mood": "sad"}}
    )
    seg.save()
    loaded = StorySegment.load("test_story", "seg_1")
    assert loaded.episode_number == 2
    assert loaded.character_states == {"char_1": {"mood": "sad"}}
```

**Acceptance Criteria:**
- [ ] All 20+ fields added with correct types
- [ ] Backward compatible (existing segments still load)
- [ ] Status enum working, immutability logic functional
- [ ] Save/load preserves all fields
- [ ] Unit tests passing (6+ tests)

---

### E0-2: Create EpisodeRecap Model (Dev-A, 1 day)

**What:** New model to summarize an episode's narrative journey.

**File:** `backend/app/models/episode_recap.py` (CREATE NEW)

**Code:**

```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.story_base import StoryBase

class CharacterState(BaseModel):
    """Snapshot of a character's state at a point in time"""
    id: str
    name: str
    status: str  # e.g., "alive", "dead", "missing"
    mood: str  # e.g., "hopeful", "desperate", "angry"
    loyalty: float = Field(0.0, ge=-1.0, le=1.0)  # -1 (enemy) to 1 (ally)
    location: Optional[str] = None
    relationships: Dict[str, str] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)

class EpisodeRecap(StoryBase):
    """Summary of an entire episode"""
    story_id: str
    episode_number: int
    arc_id: Optional[str] = None
    
    # Narrative summary
    title: str  # Auto-generated, e.g., "The Betrayal"
    summary: str  # 2-3 paragraph narrative recap
    
    # Character states at start and end
    starting_character_states: Dict[str, CharacterState] = Field(
        default_factory=dict
    )
    ending_character_states: Dict[str, CharacterState] = Field(
        default_factory=dict
    )
    
    # Segments & choices
    segment_ids: List[str] = Field(default_factory=list)
    choice_ids: List[str] = Field(default_factory=list)
    
    # Thematic reflection
    key_themes: List[str] = Field(default_factory=list)
    tone: str  # e.g., "dark_and_mysterious"
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generator_model: str = "gpt-4o-mini"
    
    def get_short_overview(self) -> str:
        """Brief summary for UI"""
        return f"Episode {self.episode_number}: {self.title}"
    
    def get_full_overview(self) -> str:
        """Detailed view for AI prompts"""
        return f"""
Episode {self.episode_number}: {self.title}

Tone: {self.tone}
Key Themes: {', '.join(self.key_themes)}

Summary:
{self.summary}

Characters:
{self._format_characters()}
"""
    
    def _format_characters(self) -> str:
        """Format character states for display"""
        lines = []
        for char_id, state in self.ending_character_states.items():
            lines.append(
                f"  {state.name}: {state.status}, {state.mood} "
                f"(loyalty: {state.loyalty:+.1f})"
            )
        return "\n".join(lines)
```

**Unit Tests:**

```python
def test_episode_recap_creation():
    """Create a recap with character states"""
    char_state = CharacterState(
        id="char_1", name="Alice", status="alive", mood="hopeful"
    )
    recap = EpisodeRecap(
        story_id="test_story",
        episode_number=1,
        title="The Beginning",
        summary="Alice begins her journey...",
        ending_character_states={"char_1": char_state}
    )
    assert recap.episode_number == 1
    assert len(recap.ending_character_states) == 1

def test_episode_recap_serialization():
    """Save and load recap"""
    # ... create recap, save, load, verify
```

**Acceptance Criteria:**
- [ ] EpisodeRecap model created with all fields
- [ ] CharacterState model created and integrated
- [ ] Save/load working
- [ ] Unit tests passing (3+ tests)

---

### E0-3: Create StoryArc Model (Dev-B, 1 day)

**What:** New model representing a collection of episodes (a longer story arc).

**File:** `backend/app/models/story_arc.py` (CREATE NEW)

**Code:**

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.story_base import StoryBase
from datetime import datetime

class ArcCompressionResult(BaseModel):
    """Result of arc compression after 15 episodes"""
    arc_id: str
    compressed_at: datetime = Field(default_factory=datetime.utcnow)
    
    mainline_branch_segments: List[str]  # Canonical path
    archived_segments: List[str]  # Replaced segments
    
    selection_rationale: str  # Why this branch was chosen
    compression_model: str = "gpt-4o-mini"

class StoryArc(StoryBase):
    """A collection of connected episodes forming a narrative arc"""
    story_id: str
    
    title: str  # e.g., "The Rise of the Northern Kingdom"
    description: str
    
    episode_ids: List[str] = Field(default_factory=list)
    episode_count: int = 0
    
    start_segment_id: str  # First segment of this arc
    current_segment_id: Optional[str] = None  # Latest segment
    
    # Thematic guidance
    premise: str  # Core idea (e.g., "Power corrupts the innocent")
    narrative_direction: str  # Guideline for where arc is heading
    
    # Compression status
    is_compressed: bool = False
    compression_result: Optional[ArcCompressionResult] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_short_overview(self) -> str:
        return f"{self.title} ({self.episode_count} episodes)"
    
    def get_full_overview(self) -> str:
        return f"""
Arc: {self.title}

Premise: {self.premise}
Direction: {self.narrative_direction}

Episodes: {self.episode_count}
Compressed: {self.is_compressed}

Description:
{self.description}
"""
```

**Acceptance Criteria:**
- [ ] StoryArc model created with all fields
- [ ] ArcCompressionResult model created
- [ ] Save/load working
- [ ] Unit tests passing (3+ tests)

---

### E0-4: Simplify UserSession Model (Dev-B, 1 day)

**What:** The v1 session tracked per-user episode state (bloat). v2 only tracks visits.

**File:** `backend/app/models/session_state.py` (MODIFY)

**Current (v1) probably has:**
```python
class UserSession(BaseModel):
    user_id: str
    world_id: str
    current_segment_id: str
    visited_segments: List[str]
    
    # ❌ REMOVE THESE:
    character_states: Dict[str, Dict]  # Already in EpisodeRecap
    episode_number: int  # Already in Segment
    protagonist_id: str  # Already in Segment
    # ... other bloat
```

**New (v2):**
```python
class UserSession(StoryBase):
    """Minimal session state: just the journey path"""
    story_id: str
    user_id: str
    
    # Current position
    current_segment_id: str
    
    # Journey so far
    visited_segments: List[str] = Field(default_factory=list)
    visited_choices: List[str] = Field(default_factory=list)
    
    # Helpers
    def add_visited(self, segment_id: str, choice_id: Optional[str] = None):
        if segment_id not in self.visited_segments:
            self.visited_segments.append(segment_id)
        if choice_id and choice_id not in self.visited_choices:
            self.visited_choices.append(choice_id)
    
    def move_to(self, segment_id: str):
        self.current_segment_id = segment_id
        self.add_visited(segment_id)
```

**Acceptance Criteria:**
- [ ] Unnecessary fields removed
- [ ] Minimal session object created
- [ ] All code referencing old fields updated
- [ ] Tests updated and passing

---

### E0-5: Create Migration Script (Dev-C, 2 days)

**What:** Script that converts existing v1 segments to v2 format.

**File:** `backend/scripts/migrate_v1_to_v2.py` (CREATE NEW)

**Pseudocode:**

```python
#!/usr/bin/env python3
"""
Migrate v1 stories to v2 format.

Usage:
  python migrate_v1_to_v2.py veil_of_thornreach
  python migrate_v1_to_v2.py --all
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

def migrate_story(story_id: str):
    """Migrate a single story from v1 to v2"""
    print(f"Migrating {story_id}...")
    
    # 1. Load all v1 segments
    v1_dir = Path(f".infinite_story_data/{story_id}/storysegment")
    segments = {}
    for seg_file in v1_dir.glob("*.json"):
        with open(seg_file) as f:
            segments[seg_file.stem] = json.load(f)
    
    # 2. For each segment, add v2 fields
    for seg_id, seg_data in segments.items():
        seg_data["episode_number"] = 1  # Default to episode 1
        seg_data["segment_number_in_episode"] = len(segments)  # Placeholder
        seg_data["pacing_weight"] = 0.0
        seg_data["status"] = "generated"
        seg_data["character_states"] = {}
        seg_data["change_notes"] = []
        seg_data["protagonist_id"] = None
        seg_data["arc_id"] = None
        # ... etc
        
        # Save with new fields
        output_file = v1_dir / f"{seg_id}.json"
        with open(output_file, "w") as f:
            json.dump(seg_data, f, indent=2)
    
    # 3. Create default EpisodeRecap for episode 1
    # ... (extract characters from segments, create recap)
    
    # 4. Create default StoryArc
    # ... (create arc with episode 1)
    
    print(f"✅ {story_id} migrated")

def rollback_story(story_id: str):
    """Restore from backup"""
    backup_dir = Path(f".infinite_story_data_v1_backup/{story_id}")
    if not backup_dir.exists():
        print(f"❌ No backup found for {story_id}")
        return
    
    # Restore from backup...
    print(f"✅ {story_id} restored from backup")

if __name__ == "__main__":
    # Parse CLI args
    # Backup existing data
    # Run migration
    # Validate
    pass
```

**Acceptance Criteria:**
- [ ] Loads all v1 segments
- [ ] Adds all new v2 fields with sensible defaults
- [ ] Creates default EpisodeRecap for episode 1
- [ ] Creates default StoryArc
- [ ] Validates no data loss
- [ ] Backup created before migration
- [ ] Rollback script works
- [ ] Tested on `veil_of_thornreach`

---

### E0-6: Test Infrastructure (Dev-C, 1 day)

**What:** Set up pytest fixtures, factories, and test utilities.

**Files:**
- `backend/tests/conftest.py` (CREATE/ENHANCE)
- `backend/tests/fixtures/` (CREATE DIRECTORY)

**conftest.py:**

```python
import pytest
from app.models import Story, StorySegment, StoryChoice

@pytest.fixture
def sample_story():
    """Create a minimal test story"""
    return Story(
        id="test_story",
        title="Test Story",
        start_segment_id="opening"
    )

@pytest.fixture
def sample_segment(sample_story):
    """Create a test segment"""
    return StorySegment(
        story=sample_story,
        id="seg_1",
        text_blocks=[],
        episode_number=1
    )

@pytest.fixture
def sample_choice(sample_story):
    """Create a test choice"""
    return StoryChoice(
        story=sample_story,
        id="choice_1",
        from_segment_id="seg_1",
        to_segment_id="seg_2",
        text="Go forward"
    )

@pytest.fixture
def temp_data_dir(tmp_path):
    """Use temp directory for test data"""
    import os
    old_data_dir = os.environ.get("DATA_DIR")
    os.environ["DATA_DIR"] = str(tmp_path)
    yield tmp_path
    if old_data_dir:
        os.environ["DATA_DIR"] = old_data_dir

def factory_story(id: str = "test", **kwargs):
    """Factory function for creating stories"""
    return Story(id=id, title=kwargs.get("title", "Test"), **kwargs)

def factory_segment(story: Story, id: str = "seg_1", **kwargs):
    """Factory function for segments"""
    return StorySegment(story=story, id=id, **kwargs)
```

**Acceptance Criteria:**
- [ ] conftest.py has 5+ fixtures
- [ ] Factory functions created
- [ ] Async testing configured
- [ ] Mock generators available
- [ ] All existing tests still pass

---

## Key Concepts

### Immutability Lock
Once a segment is `GENERATED`, it cannot be modified. This prevents accidental changes and ensures all users see the same content.

```python
def modify_segment(seg: StorySegment, new_text: str):
    if seg.status == SegmentStatus.GENERATED:
        raise ValueError("Cannot modify generated segment")
    seg.text = new_text
```

### Character State Snapshot
At episode start, capture full character state. During episode, only store *changes* in `change_notes`. At recap, reconcile changes back to state.

### Pacing Weight
A numeric signal (0.0-1.0) of progress toward episode end. Used in:
- Generation (AI knows how much "room" is left)
- Episode transition detection (when > 0.8, consider ending episode)

---

## Definition of Done for Epic 0

- [ ] E0-1: StorySegment enhanced (all fields, unit tests)
- [ ] E0-2: EpisodeRecap model created (serialization, tests)
- [ ] E0-3: StoryArc model created (serialization, tests)
- [ ] E0-4: UserSession simplified (old fields removed, code updated)
- [ ] E0-5: Migration script created, tested on real data
- [ ] E0-6: Test infrastructure ready (fixtures, factories, utils)
- [ ] All tests passing (pytest -v)
- [ ] Code review completed (epic lead approval)
- [ ] PR merged to main

---

## Next Steps for E1/E2/E3/E4

Once E0 is complete:
- **E1** uses the enhanced models to build generation pipeline
- **E2** uses models to implement episode recaps & compression
- **E3** uses models to update CLI
- **E4** uses fixtures to write comprehensive tests

This foundation is critical. Don't cut corners! 🏗️
