# Infinite Story Engine v2: Developer Onboarding

**Read this first.** All 11 developers should complete this onboarding before starting your epic-specific work.

## What is the Infinite Story Engine (ISE)?

A Python storytelling engine where users explore AI-generated branching narratives. You choose options, the AI generates new scenes, and the story evolves. It's like an interactive novel where choices matter and the plot adapts to your decisions.

**Core loop:** User sees a scene → chooses an action → AI generates the next scene → repeat.

## The v2 Vision (Why We're Rebuilding)

### The Problem with v1
The original system generated an **exponential branching tree**: each scene has 2 new choices, leading to 2 new scenes, creating 2^depth total segments. After just 15 scenes, you have ~32,000 segments. This is memory-intensive, computationally expensive, and impossible to manage.

### The v2 Solution
**Shared Immutable Segment Graph with Episodes & Compression**

- **Segments are immutable, shared nodes**: When a segment is generated, it's generated once. All users/all sessions share the same segment. This collapses the exponential tree into a DAG (directed acyclic graph).

- **Episodes are narrative overlays**: Instead of segments being "in" an episode, we bake episode context (tone, pacing, character states) *into* the segment generation. Each segment knows: "I'm part of episode 3, I'm scene 8 of this episode, the tone is dark_and_mysterious."

- **Character state is lightweight**: At the start of each episode, capture character snapshots (status, mood, location, etc.). During the episode, track only *changes* (`change_notes`). At episode end, reconcile changes back into the snapshot.

- **Arc compression prevents infinite growth**: After 15 episodes, the system AI picks the "best" narrative branch (considering user sessions, thematic coherence, etc.), archives the alternatives, and continues from the canonical mainline. Growth becomes bounded.

- **Two CLI modes**: 
  - **Immersive mode**: Play the story, see beautiful prose, make choices. (Default)
  - **Debug mode**: Transparent view of segments, choices, state, generation context, and AI reasoning. (For devs/QA)

## Development Environment Setup

### Prerequisites
- **Python 3.13+** (check with `python3 --version`)
- **Git** (check with `git --version`)
- **macOS/Linux** (Windows requires WSL2)

### Step 1: Clone & Navigate
```bash
cd /Users/artemmelnikov/Desktop/_stuff/infinite_story
git status  # Verify you're in the right repo
```

### Step 2: Set Up Python Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

### Step 4: Configure API Keys
```bash
cp .env.example .env
# Edit .env with your OpenAI API key (ask your project lead)
```

### Step 5: Verify Setup
```bash
# Run tests to verify everything works
python -m pytest tests/ -v

# Try running a story (minimal test)
PYTHONPATH=. python -m app.cli list-stories
```

If all tests pass and you see stories listed, you're ready!

## Codebase Map

### Core Directories

```
backend/
├── app/
│   ├── models/              # Data models (Pydantic)
│   │   ├── story_base.py    # Base persistence class
│   │   ├── story.py         # Story container
│   │   ├── story_segment.py # Scene in the story
│   │   ├── story_choice.py  # Link between scenes
│   │   ├── story_character.py
│   │   ├── story_location.py
│   │   ├── story_context.py
│   │   ├── session_state.py # User session (minimal in v2)
│   │   └── [new in v2]
│   │       ├── episode_recap.py   # E0-2
│   │       └── story_arc.py       # E0-3
│   │
│   ├── engine/              # Generation & execution
│   │   ├── story_runner.py  # Game loop & state
│   │   ├── generator.py     # AI interface (abstract)
│   │   ├── openai_generator.py
│   │   ├── openrouter_generator.py
│   │   └── [new in v2]
│   │       ├── segment_context_builder.py  # E1-1
│   │       ├── episode_recap_generator.py  # E2-1
│   │       └── arc_compressor.py          # E2-4
│   │
│   ├── cli.py               # CLI commands (refactor in E3)
│   ├── config.py            # Settings & env vars
│   └── utils/
│       └── prompt_builder.py # [currently empty in v1]
│
├── tests/                   # Test suite
│   ├── test_story_models.py
│   ├── test_story_runner.py
│   ├── conftest.py          # Pytest fixtures
│   └── fixtures/            # Test data
│
├── scripts/
│   └── migrate_v1_to_v2.py  # Data migration (E0-5)
│
├── requirements.txt
├── requirements-dev.txt
└── [other config files]
```

### What Each Directory Does

- **app/models/** → Data structures & persistence (loading/saving JSON)
- **app/engine/** → AI generation, game loop, state management
- **app/cli.py** → User-facing commands
- **tests/** → Unit & integration tests
- **scripts/** → One-time utilities (migrations, setup)

### What NOT to Modify (Don't Touch!)

- `frontend/` → Separate React app (not in scope)
- `data/` → Old data files (ignore)
- `docs/` → Old documentation (use new docs in project root instead)
- `.git/` → Never manually edit

## Git Workflow

### Before Starting Work
```bash
# Make sure you're on main and up to date
git checkout main
git pull origin main

# Create a feature branch for your epic
git checkout -b dev-A-epic-0-data-layer
# OR for a specific task
git checkout -b dev-A-e0-1-segment-model
```

### Commit Style
- **Keep it short & lowercase** → `add episode context fields to segment model`
- **Reference task if available** → `E0-1: add episode context fields`
- **No AI watermarks** → Don't add "Generated with Claude" or "Co-Authored-By"

### Example Commits
```bash
# Good ✅
git commit -m "E0-1: add episode context fields to segment model"

# Good ✅
git commit -m "E0-2: implement episoderecap save/load serialization"

# Avoid ❌
git commit -m "Update model (WIP)"

# Avoid ❌
git commit -m "Generated with Claude Code"
```

### Push & Create PR
```bash
git push origin dev-A-epic-0-data-layer

# Then use GitHub to create a PR, or use gh CLI:
gh pr create --title "E0: Data Layer Foundation" --body "..."
```

## Key Terms Glossary

### Story Structure
- **Story** → Top-level container for everything
- **Segment** (SceneSegment) → A single scene/node in the story graph
- **Choice** → A link from one segment to another (user decision)
- **Character** → Named person in the story
- **Location** → Named place in the story
- **Context** → Worldbuilding info (cultures, magic systems, history)

### v2 Concepts
- **Episode** → A ~15-segment arc with unified tone & narrative direction
- **Arc** → Collection of episodes forming a larger narrative (e.g., "The Fall" arc)
- **Segment Status** → UNEXPLORED (new), GENERATING (in progress), GENERATED (ready), ARCHIVED (replaced)
- **Character State** → Snapshot of character info at a point in time (status, mood, location)
- **Change Notes** → Lightweight notes about character/location changes (no full reserialization)
- **Pacing Weight** → Numeric signal (0.0-1.0) of how close the episode is to its end condition
- **Arc Compression** → Process of picking a canonical mainline branch and archiving others after 15 episodes

### System Concepts
- **TextGenerator** → Abstract base class for AI generation (OpenAI, OpenRouter, etc.)
- **StoryRunner** → Game loop: display scene → get user input → generate/traverse → save state
- **Immutability Lock** → Once a segment is GENERATED, its content cannot change
- **Graph Walking** → Process of following parent links backward through the segment chain

## Common Development Tasks

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run a Specific Test File
```bash
python -m pytest tests/test_story_models.py -v
```

### Run a Specific Test
```bash
python -m pytest tests/test_story_models.py::test_segment_creation -v
```

### Run the Story Engine (Immersive Mode)
```bash
./run.sh
# Or manually:
cd backend
PYTHONPATH=. python -m app.cli run-story
```

### Run Debug Mode (after E3 is done)
```bash
PYTHONPATH=. python -m app.cli run-story --debug
```

### List All Stories
```bash
cd backend
PYTHONPATH=. python -m app.cli list-stories
```

### Check Code Style (optional, not required)
```bash
# If you use black/flake8:
black backend/app/ backend/tests/
flake8 backend/app/ --max-line-length=100
```

## Code Patterns from v1 (Learn These!)

### Pydantic Model Pattern
```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    id: str = Field(..., description="Unique identifier")
    name: str = Field(default="Unknown")
    value: int = Field(default=0, ge=0, le=100)
    
    class Config:
        # Allows computed properties, prevents unexpected attributes
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}
```

### JSON Save/Load Pattern (All models inherit from StoryBase)
```python
# Save to disk
segment = StorySegment(...)
segment.save()  # Automatically saves to:
# .infinite_story_data/{story_id}/storysegment/{segment_id}.json

# Load from disk
loaded = StorySegment.load(story_id="my_story", component_id="seg_1")

# List all
all_segments = StorySegment.list_all(story_id="my_story")
```

### StoryBase Pattern (All StoryBlock objects do this)
```python
from app.models.story_base import StoryBase

class StorySegment(StoryBase):
    story: Story = Field(..., exclude=True)  # Excluded from JSON!
    id: str
    text_blocks: List[TextBlock]
    
    def __init__(self, story: Story, **data):
        super().__init__(**data)
        self.story = story
        story.add_segment(self)  # Auto-register with parent
```

### Async Generator Pattern (Used in generation)
```python
from app.engine.generator import TextGenerator

class MyGenerator(TextGenerator):
    async def generate(self, context_type: str, context: dict) -> dict:
        """Generate scene content via AI API"""
        # Build prompt from context
        prompt = self._build_prompt(context)
        
        # Call API
        response = await self._call_api(prompt)
        
        # Parse & validate response
        parsed = self._parse_response(response)
        
        return parsed
```

### Test Pattern with Fixtures
```python
import pytest
from app.models import Story, StorySegment

@pytest.fixture
def sample_story():
    """Create a test story"""
    return Story(id="test", title="Test Story")

@pytest.fixture
def sample_segment(sample_story):
    """Create a test segment"""
    return StorySegment(
        story=sample_story,
        id="seg_1",
        text_blocks=[...]
    )

def test_segment_saves(sample_segment):
    """Test that segment saves to disk"""
    sample_segment.save()
    loaded = StorySegment.load("test", "seg_1")
    assert loaded.id == "seg_1"
```

## Documentation Files to Read

### Start With These (Required)
1. **VISION.md** → High-level philosophy & design decisions
2. **ARCHITECTURE_V2.md** → Technical architecture & data models
3. **QUICK_REFERENCE.md** → Diagrams, checklists, performance targets

### Then Read Your Epic-Specific Briefing
- **EPIC_0_DATA_LAYER.md** → If you're Dev-A, B, or C
- **EPIC_1_GENERATION.md** → If you're Dev-D or E
- **EPIC_2_EPISODES.md** → If you're Dev-F or G
- **EPIC_3_CLI.md** → If you're Dev-H or I
- **EPIC_4_TESTING.md** → If you're Dev-J or K

### Reference Documentation
- **DEVELOPMENT_TASKS.md** → All 26 tasks broken down
- **DEVELOPER_ASSIGNMENTS.md** → Roles & responsibilities
- **README_V2_SYSTEM.md** → Navigation guide

## Quick Checklist

- [ ] Python 3.13+ installed
- [ ] Cloned repo, navigated to backend/
- [ ] Virtual environment created and activated
- [ ] `pip install -r requirements.txt` successful
- [ ] `.env` file created with API key
- [ ] `pytest tests/ -v` passes (no failures)
- [ ] Can run `PYTHONPATH=. python -m app.cli list-stories`
- [ ] Read VISION.md and ARCHITECTURE_V2.md
- [ ] Read your epic-specific briefing document
- [ ] Know your first task (check your START_HERE.md)

## Getting Help

- **Technical questions about code?** → Check ARCHITECTURE_V2.md, then ask your epic lead
- **Stuck on a task?** → Post in team Slack, include task ID (E0-1, E1-3, etc.)
- **Clarification on requirements?** → Message your project manager
- **Need more context?** → Read QUICK_REFERENCE.md diagrams

---

**Welcome aboard! You're building something cool.** ✨

Next: Read your epic-specific briefing document in `developers/EPIC_X_*.md`
