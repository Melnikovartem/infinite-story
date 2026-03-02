# Game Loop & World Creation Analysis

## Overview

This document reviews where new worlds (stories) are created in the current game loop and what needs to be set up to make them playable with old data.

---

## 1. Game Loop Entry Points

### 1.1 Primary Entry Point: `run.sh`

**File**: `run.sh` (executable script at repo root)

```bash
./run.sh [story_name]
```

**What it does**:
- Line 26: Sets default story to `veil_of_thornreach` if no argument provided
- Lines 52-76: **AUTO-CREATES missing story** by running `scripts/save_story.py`
- Line 87: Executes `python -m app.cli run-story <story_name>`

**Key behavior**: If story doesn't exist, it's automatically created from scratch before playing begins.

### 1.2 CLI Entry Point: `app/cli.py`

**Main commands**:

```bash
python -m app.cli run-story [story_id] [--mode immersive|debug] [--resume]
python -m app.cli list-stories
python -m app.cli delete-story <story_id>
python -m app.cli clear-state <story_id>
python -m app.cli test-generation <story_id>
```

**`run_story_async()` function** (lines 277-386):
1. Loads configuration
2. Initializes AI generator
3. Lists available stories (if story_id not provided)
4. Loads story from disk via `Story.load(story_id, story_id)`
5. Creates `StoryRunner` instance
6. Calls `runner.load_all_components(story)` 
7. Either resumes or starts story
8. Runs game loop in immersive or debug mode

---

## 2. World Creation Flow

### 2.1 Where New Worlds Are Created

**Three scenarios**:

#### Scenario A: Auto-Creation (via `run.sh`)

**Entry**: `run.sh` detects missing story
```bash
./run.sh my_new_story
# Script checks if story exists, if not:
PYTHONPATH=backend python backend/scripts/save_story.py my_new_story
```

**File**: `backend/scripts/save_story.py`
- Creates Story object with ID, title, description, genre
- Creates StoryContext (worldbuilding)
- Creates StoryCharacter objects (3+)
- Creates StoryLocation objects (3+)
- Creates starting StorySegment
- Creates 2-3 initial StoryChoice objects
- **Saves everything to `.infinite_story_data/my_new_story/`**

#### Scenario B: Programmatic Creation (tests & fixtures)

**Files**: `backend/tests/fixtures/story_builders.py`

Helper functions that create stories in memory:
- `create_test_story_with_segments()` - Basic structure
- `create_test_story_with_choices()` - With navigation
- `create_test_story_with_characters()` - With characters
- `create_branching_story()` - Complex graph structure
- `create_story_with_multiple_characters()` - Custom characters

**Usage**:
```python
story, segments = create_test_story_with_segments("my_story", segment_count=5)
# Story object created in memory, not saved to disk
```

#### Scenario C: Manual Creation (for migrating old data)

```python
# Create story container
story = Story(
    id="veil_of_thornreach",
    title="Veil of Thornreach",
    description="A dark fantasy...",
    genre="Dark Fantasy",
    start_segment_id="opening_scene"
)

# Create worldbuilding
context = StoryContext(
    story=story,
    id="world_context",
    worldbuilding="The world is..."
)

# Create characters
character = StoryCharacter(
    story=story,
    id="char_001",
    name="Protagonist",
    description="...",
    background="..."
)

# Create locations
location = StoryLocation(
    story=story,
    id="loc_001",
    name="The Forest",
    description="...",
    significance="..."
)

# Create first segment
segment = StorySegment(
    story=story,
    id="opening_scene",
    short_description="You awaken...",
    text_blocks=[...],
    atmosphere="mysterious",
    episode_number=1
)

# Create initial choices
choice1 = StoryChoice(
    story=story,
    id="choice_001",
    from_segment_id="opening_scene",
    to_segment_id=None,  # AI will generate
    text="Look around carefully"
)

# Save all to disk
story.save()
character.save()
location.save()
context.save()
segment.save()
choice1.save()
```

### 2.2 What Gets Created

When a new world (story) is initialized, these components are created:

| Component | Type | Purpose | Required? |
|-----------|------|---------|-----------|
| **Story** | `Story` | Container with metadata | ✅ YES |
| **Opening Segment** | `StorySegment` | First playable scene | ✅ YES |
| **Initial Choices** | `StoryChoice` | 2-3 branching options | ✅ YES |
| **Context** | `StoryContext` | Worldbuilding/rules | ⚠️ RECOMMENDED |
| **Characters** | `StoryCharacter` | 3+ people/beings | ⚠️ RECOMMENDED |
| **Locations** | `StoryLocation` | 3+ places | ⚠️ RECOMMENDED |
| **Text Blocks** | `TextBlock` | Actual narrative content | ⚠️ RECOMMENDED |

---

## 3. Game Loop & State Management

### 3.1 The Story Runner Game Loop

**File**: `backend/app/engine/story_runner.py`

**Initialization** (lines 30-43):
```python
def start(self) -> None:
    """Start the story from the beginning."""
    self.load_all_components(self.story)
    self.current_segment = self.story.get_segment(self.story.start_segment_id)
    self.visited_segments.add(self.story.start_segment_id)
```

**Key methods**:

1. **`load_all_components(story)`** (lines 101-193)
   - Loads all Characters from `.infinite_story_data/<story_id>/storycharacter/*.json`
   - Loads all Locations
   - Loads all Segments
   - Loads all Choices
   - **Connects choices to segments** bidirectionally
   - Loads Context
   - **This is where old data would be loaded!**

2. **`get_available_choices()`** (lines 45-70)
   - Returns list of StoryChoice objects from current segment
   - Sorted by click count (popularity)
   - Limited to top 100
   - **Called by UI to show player options**

3. **`make_choice(choice_id)`** (lines 72-92)
   - Validates choice belongs to current segment
   - Loads next segment via choice's `to_segment_id`
   - Updates `current_segment`
   - Adds to `visited_segments`

### 3.2 Game Loop in CLI (Immersive Mode)

**File**: `app/cli.py`, lines 160-201

```python
async def _run_immersive_mode(runner: StoryRunner, generator):
    try:
        while runner.is_running:
            # Display current segment
            if runner.current_segment:
                display_segment_immersive(runner.current_segment)
            
            # Get available choices
            choices = runner.get_available_choices()
            if not choices:
                break  # Story ended
            
            # Get user choice
            choice_id = prompt_choice_immersive(runner.current_segment, choices)
            
            # Execute choice
            await _execute_choice(runner, choice_id, generator, is_debug=False)
            
            # Auto-save state
            runner.save_state()
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
```

### 3.3 Choice Execution & Generation

**File**: `app/cli.py`, lines 253-275

```python
async def _execute_choice(runner: StoryRunner, choice_id: str, generator, is_debug: bool = False):
    choice = runner.story.get_choice(choice_id)
    
    # Two paths:
    if choice.to_segment_id:
        # Path 1: Navigate to existing segment
        runner.make_choice(choice_id)
    else:
        # Path 2: Generate new segment with AI
        with console.status("[bold yellow]Generating next scene...[/bold yellow]"):
            new_segment = await runner.current_segment.generate_next_scene(choice, generator)
            runner.current_segment = new_segment
            runner.visited_segments.add(new_segment.id)
```

---

## 4. Data Persistence & Loading

### 4.1 Storage Structure

**Disk layout**:
```
.infinite_story_data/
├── veil_of_thornreach/          # Story ID directory
│   ├── story/
│   │   └── veil_of_thornreach.json
│   ├── storycontext/
│   │   └── world_context.json
│   ├── storycharacter/
│   │   ├── protagonist.json
│   │   ├── mentor.json
│   │   └── ...
│   ├── storylocation/
│   │   ├── forest.json
│   │   └── ...
│   ├── storysegment/
│   │   ├── opening_scene.json
│   │   ├── seg_12345.json
│   │   └── ...
│   ├── storychoice/
│   │   └── choice_*.json
│   ├── runner_state.json        # Current player position
│   └── sessionstate/            # Multi-user sessions (if used)
```

### 4.2 Loading Old Data

**Pattern** (from `StoryBase`, used by all components):

```python
# Load a single component
character = StoryCharacter.load(story_id="veil_of_thornreach", component_id="protagonist", story=story)

# List all of a type
all_segments = StorySegment.list_all(story_id="veil_of_thornreach")

# Get from cache after loading
story = Story.load("veil_of_thornreach", "veil_of_thornreach")
runner = StoryRunner(story)
runner.load_all_components(story)  # ← This loads everything
```

**Key insight**: `load_all_components()` is the master loading function that restores the entire story world from disk.

### 4.3 Session State

**File**: `.infinite_story_data/<story_id>/runner_state.json`

```json
{
  "current_segment_id": "seg_12345",
  "visited_segments": ["opening_scene", "seg_001", "seg_12345"]
}
```

**Used by**:
- `runner.save_state()` - After each choice
- `runner.load_state()` - On resume (line 363 in cli.py)
- `runner.clear_state()` - Reset to start

---

## 5. Minimal Setup for Old Data

### 5.1 Restore Checklist

To make old data playable again:

✅ **CRITICAL - Must exist**:
1. Story object with valid `id` and `start_segment_id` pointing to an existing segment
2. Opening segment (the one referenced by `start_segment_id`)
3. At least one StoryChoice from opening segment
4. All components saved to `.infinite_story_data/<story_id>/<type>/<id>.json`

✅ **STRONGLY RECOMMENDED**:
1. TextBlock objects in segments (actual narrative text)
2. StoryContext (worldbuilding)
3. StoryCharacter objects (3+)
4. StoryLocation objects (3+)

✅ **OPTIONAL**:
1. Episode metadata (`episode_number`, `episode_tone`, etc.) - defaults to 1
2. Character states - can be inferred from presence
3. Advanced fields (`pacing_weight`, `end_condition_proximity`) - auto-computed

### 5.2 Migration Script Pattern

**What would be needed**:

```python
# Load old data from wherever it's stored
old_story = load_from_v1_format()

# Create new Story object
story = Story(
    id=old_story['id'],
    title=old_story['title'],
    description=old_story['description'],
    genre=old_story.get('genre', 'Unknown'),
    start_segment_id=old_story['start_segment_id']
)

# Migrate characters
for old_char in old_story['characters']:
    char = StoryCharacter(
        story=story,
        id=old_char['id'],
        name=old_char['name'],
        description=old_char.get('description', ''),
        background=old_char.get('background', '')
    )
    char.save()

# Migrate segments (most complex)
for old_segment in old_story['segments']:
    # Convert text to TextBlocks
    text_blocks = [
        TextBlock(
            type=TextType.NARRATOR_DESCRIBING,
            content=old_segment['text']
        )
    ]
    
    segment = StorySegment(
        story=story,
        id=old_segment['id'],
        short_description=old_segment.get('summary', 'A scene'),
        text_blocks=text_blocks,
        atmosphere=old_segment.get('atmosphere', 'neutral'),
        episode_number=old_segment.get('episode_number', 1),
        # ... other fields
    )
    segment.save()

# Migrate choices
for old_choice in old_story['choices']:
    choice = StoryChoice(
        story=story,
        id=old_choice['id'],
        from_segment_id=old_choice['from_segment_id'],
        to_segment_id=old_choice.get('to_segment_id'),
        text=old_choice['text']
    )
    choice.save()

# Save story metadata
story.save()
```

---

## 6. Key Integration Points

### 6.1 Where to Hook Old Data

**Option 1: Modify `run.sh`**
- Line 52-76: Instead of auto-creating via `save_story.py`, check if old data exists
- If yes, run migration script
- If no, create new story

**Option 2: Create migration command**
```bash
python -m app.cli migrate-story <old_data_path>
```

**Option 3: Create factory method**
```python
# In story.py
@classmethod
def from_v1_data(cls, old_data_dict) -> 'Story':
    """Create a Story from v1 format data."""
    ...
```

### 6.2 Data Validation Points

**Before game starts** (`cli.py`, lines 359-372):
```python
runner.load_all_components(story)  # ← All components loaded here

if not story.start_segment_id:
    raise ValueError("Story has no start segment")

if not runner.get_available_choices():
    raise ValueError("Start segment has no choices")
```

**Add validation**:
```python
# After loading, validate old data is correct
if not story.get_segment(story.start_segment_id):
    raise ValueError(f"Start segment {story.start_segment_id} not found!")

for choice in story.get_all_choices():
    if not choice.from_segment_id:
        logger.warning(f"Choice {choice.id} has no source segment")
```

---

## 7. Critical Patterns & Gotchas

### 7.1 DO: Pass `story` object when creating components

```python
✅ CORRECT:
segment = StorySegment(story=story, id="seg_1", ...)
character = StoryCharacter(story=story, id="char_1", ...)

❌ WRONG:
segment = StorySegment(story_id="story_1", id="seg_1", ...)  # Auto-registration broken!
```

**Why**: Constructor calls `self.story.add_segment(self)` to register in story's cache.

### 7.2 DO: Connect choices bidirectionally

```python
✅ CORRECT:
segment1.add_outgoing_choice(choice)
segment2.add_incoming_choice(choice)

❌ INCOMPLETE:
# Just creating the choice object without connecting
```

**Why**: `get_available_choices()` reads from `outgoing_choices` dict.

### 7.3 DO: Save to disk after creation

```python
✅ CORRECT:
story.save()
character.save()
segment.save()
choice.save()

❌ WRONG:
# Creating everything but never calling .save()
# Objects exist in memory but not on disk
```

### 7.4 DO: Load all components together

```python
✅ CORRECT:
runner = StoryRunner(story)
runner.load_all_components(story)  # Loads everything and connects
current_segment = story.get_segment(story.start_segment_id)

❌ WRONG:
segment = StorySegment.load(story_id, segment_id)
# segment.outgoing_choices will be empty!
# Must call runner.load_all_components() first
```

---

## 8. Summary: What Needs to Happen

### For Playing Old Data:

1. **Load** old story files from storage
2. **Transform** to new Story/Segment/Choice model format
3. **Validate** that story structure is correct:
   - Story has a `start_segment_id`
   - Start segment exists
   - Start segment has outgoing choices
4. **Save** all components to `.infinite_story_data/<story_id>/`
5. **Run** `python -m app.cli run-story <story_id>`

### For Supporting Old Data in Code:

1. **Create migration script** (`scripts/migrate_v1_to_v2.py` or similar)
2. **Add validation** in `StoryRunner.start()` to check data integrity
3. **Hook into `run.sh`** to detect and migrate old data automatically
4. **Log warnings** for incomplete data (missing context, characters, etc.)

### Key Files to Modify:

- `run.sh` - Add migration logic
- `app/cli.py` - Add migration command
- `app/engine/story_runner.py` - Add data validation
- Create: `scripts/migrate_from_old_format.py`

---

## 9. Current State of Code

### What Already Exists:

✅ `Story.load()` and `.save()` - Persistence working  
✅ `StoryRunner.load_all_components()` - Comprehensive loader  
✅ All component types defined - Story, Segment, Choice, Character, Location, Context  
✅ Test fixtures - Show how to create stories programmatically  
✅ Session state - Can resume from saved position  

### What Needs to be Built:

❌ Migration script to convert old data format  
❌ Validation in game loop to catch bad data early  
❌ Auto-detection in `run.sh` for old data  
❌ Documentation on old data format requirements  

---

## 10. Example: Complete Old Data Restoration

```python
# In scripts/restore_old_story.py

import json
from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_choice import StoryChoice
from app.models.story_character import StoryCharacter
from app.models.story_context import StoryContext
from app.models.text_types import TextBlock, TextType

def restore_story(old_data_path: str, story_id: str):
    """Restore an old story from JSON files."""
    
    # Load old data structure
    with open(old_data_path, 'r') as f:
        old_data = json.load(f)
    
    # Create story container
    story = Story(
        id=story_id,
        title=old_data.get('title', 'Untitled'),
        description=old_data.get('description', ''),
        genre=old_data.get('genre', 'Unknown'),
        start_segment_id=old_data.get('start_segment_id')
    )
    
    # Restore context
    if 'context' in old_data:
        context = StoryContext(
            story=story,
            id='main_context',
            worldbuilding=old_data['context']
        )
        context.save()
    
    # Restore characters
    for char_data in old_data.get('characters', []):
        char = StoryCharacter(
            story=story,
            id=char_data['id'],
            name=char_data['name'],
            description=char_data.get('description', ''),
            background=char_data.get('background', '')
        )
        char.save()
    
    # Restore segments (with text blocks)
    for seg_data in old_data.get('segments', []):
        text_blocks = [
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content=seg_data.get('text', '')
            )
        ]
        
        segment = StorySegment(
            story=story,
            id=seg_data['id'],
            short_description=seg_data.get('summary', ''),
            text_blocks=text_blocks,
            atmosphere=seg_data.get('atmosphere', 'neutral'),
            episode_number=seg_data.get('episode_number', 1)
        )
        segment.save()
    
    # Restore choices and connect
    for choice_data in old_data.get('choices', []):
        choice = StoryChoice(
            story=story,
            id=choice_data['id'],
            from_segment_id=choice_data['from_segment_id'],
            to_segment_id=choice_data.get('to_segment_id'),
            text=choice_data['text']
        )
        choice.save()
    
    # Save story metadata
    story.save()
    
    print(f"✅ Restored story '{story_id}' to .infinite_story_data/")
    print(f"   Characters: {len(old_data.get('characters', []))}")
    print(f"   Segments: {len(old_data.get('segments', []))}")
    print(f"   Choices: {len(old_data.get('choices', []))}")

if __name__ == '__main__':
    import sys
    restore_story(sys.argv[1], sys.argv[2])
```

---

## Conclusion

The game loop is **well-structured** for loading and playing worlds. The key entry point for new worlds is:

1. **Creation**: Story components created (either via `save_story.py`, fixtures, or migration)
2. **Disk Storage**: Everything saved to `.infinite_story_data/<story_id>/`
3. **Loading**: `StoryRunner.load_all_components()` restores the complete world
4. **Playing**: Game loop displays current segment, gets choices, executes selection
5. **Persistence**: Session state saved after each choice for resumption

To support old data, you need to:
- Transform old format → new format
- Ensure all required fields are present
- Save to `.infinite_story_data/` structure
- Optionally add validation in `StoryRunner.start()`

The architecture is already in place; it just needs old data migrated into it.
