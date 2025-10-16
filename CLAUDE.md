# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **infinite interactive storytelling engine** where users can explore branching narratives in a modular story world. The system uses AI to generate story content dynamically as users make choices.

**Key Concepts:**
- Stories are composed of modular blocks: **Segments** (scenes), **Choices** (decisions), **Characters**, **Locations**, and **Context** (worldbuilding)
- Users see the 2 most popular choices, can view all choices, or write custom choices
- AI generates new segments based on context, previous segments, and user choices

## Tech Stack

- **Backend**: Python 3.13+ with Pydantic for data modeling
- **Storage**: JSON files in `.infinite_story_data/` (no database yet)
- **CLI**: Typer with Rich for terminal UI
- **Testing**: pytest with async support
- **AI Generation**: TextGenerator base class (OpenAI implementation expected)

## Common Commands

### Running the Application
```bash
# Run the default story (veil_of_thornreach)
./run.sh

# Run a specific story
./run.sh <story_name>
```

### Development
```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_story_models.py

# Run specific test
python -m pytest tests/test_story_models.py::test_story_creation -v

# Run CLI commands directly
PYTHONPATH=. python -m app.cli list-stories
PYTHONPATH=. python -m app.cli run-story
```

## Architecture

### Data Model Hierarchy

```
StoryBase (base class for all story objects)
├── Story (top-level container)
└── StoryBlock (requires a Story object)
    ├── StorySegment (a scene in the story)
    ├── StoryChoice (connection between segments)
    ├── StoryCharacter (character definition)
    ├── StoryLocation (location definition)
    └── StoryContext (worldbuilding & fundamental truths)
```

**Critical Pattern**: All StoryBlock subclasses:
1. Must receive a `story` parameter in `__init__`
2. Automatically register themselves with the parent Story via `story.add_X(self)`
3. Are excluded from serialization (`exclude=True`) to prevent circular references

### Storage System

- **Base directory**: `.infinite_story_data/<story_id>/<component_type>/<component_id>.json`
- Example: `.infinite_story_data/veil_of_thornreach/storysegment/opening_scene.json`
- Component types are auto-derived from class names (e.g., `StorySegment` → `storysegment`)

**Key Methods** (in `StoryBase`):
- `save()`: Serialize to JSON
- `load(story_id, component_id, **data)`: Load from JSON
- `list_all(story_id)`: List all components of a type
- `delete()`: Remove from disk

### Story Graph Structure

Stories form a directed graph:
- **Nodes**: `StorySegment` instances
- **Edges**: `StoryChoice` instances
- **Entry point**: `Story.start_segment_id`

Each `StorySegment` has:
- `outgoing_choices`: Dict[str, StoryChoice] (where the player can go next)
- `incoming_choices`: Dict[str, StoryChoice] (how they got here)

These are **runtime-only** dictionaries built by `StoryRunner.load_all_components()` by matching `from_segment_id` and `to_segment_id` on choices.

### AI Generation Flow

When generating a new scene (`StorySegment.generate_next_scene()`):
1. Build context from:
   - Previous segments (via `get_story_segments_before()`)
   - Story context (worldbuilding)
   - Character states (`characters_running_status`)
   - Location states (`locations_running_status`)
   - The connecting choice text
2. Pass to `TextGenerator.generate()` with `context_type="scene"`
3. Parse response into `SceneTextGeneratorResponse`
4. Create new `StorySegment` with generated text blocks
5. Create 2 new `StoryChoice` objects leading from the new segment
6. Save everything to disk

**Important**: The `characters_running_status` and `locations_running_status` accumulate state changes over time, creating a history of character/location states throughout the story.

### Text Block System

Story segments contain lists of `TextBlock` objects with typed content:
- **Narrative**: `NARRATOR_DESCRIBING`, `NARRATOR_COMMENTARY`, `FLASHBACK`, `DREAM_SEQUENCE`
- **Dialogue**: `CHARACTER_SPEECH`, `CHARACTER_THOUGHT`, `POEM_OR_SONG`, `LETTER_OR_NOTE`
- **Media**: `SFX`, `VISUAL_CUE`, `MEDIA_OVERLAY`
- **UI**: `SCENE_TITLE`, `LOCATION_LABEL`, `SYSTEM_MESSAGE`

Each block has `type`, `content`, and optional `emotion` and `character` fields.

## Key Files

- **`app/models/story_base.py`**: Base persistence layer for all story objects
- **`app/models/story.py`**: Top-level Story container with component caches
- **`app/models/story_segment.py`**: Core story scene with AI generation logic
- **`app/engine/story_runner.py`**: Game loop and state management
- **`app/engine/generator.py`**: Abstract AI text generation interface
- **`app/cli.py`**: CLI commands for running stories
- **`app/utils/prompt_builder.py`**: (Currently empty - prompt building is inline in StorySegment)

## Testing Notes

- Tests use pytest with asyncio support (`asyncio_default_fixture_loop_scope = function`)
- Tests are in `backend/tests/`
- Key test files:
  - `test_story_models.py`: Data model validation
  - `test_story_segment.py`: Segment logic and generation
  - `test_story_runner.py`: Story execution flow
  - `test_generator.py`: AI generation mocking

## Important Patterns

### Creating Story Objects

Always create StoryBlock objects with a `story` parameter:

```python
story = Story(id="my_story", title="My Story", ...)
segment = StorySegment(story=story, id="seg_1", ...)
choice = StoryChoice(story=story, id="choice_1", from_segment_id="seg_1", ...)
```

The objects auto-register with the story's internal caches.

### Loading a Complete Story

```python
story = Story.load(story_id, story_id)
runner = StoryRunner(story)
runner.start()  # This calls load_all_components() to build the graph
```

### Overview Methods

All StoryBlock subclasses must implement:
- `get_short_overview()`: Brief description for lists
- `get_full_overview()`: Detailed context for AI prompts

These are used heavily in AI generation to provide rich context.

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the `backend/` directory:

```bash
# Copy the example file
cp backend/.env.example backend/.env

# Edit with your API key
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

Configuration is loaded via `app/config.py` which uses `python-dotenv` to read `.env` files.

## Running the Story Engine

The story engine now supports full AI generation:

1. **Set up API key**: Create `.env` file with your OpenAI API key
2. **Run the story**: `./run.sh` or `cd backend && PYTHONPATH=. python -m app.cli run-story`
3. **Make choices**:
   - Select from top 2 choices
   - View all available choices
   - Write custom choices (AI generates the next scene)
4. **AI Generation**: When a choice has no destination (`to_segment_id=None`), the system automatically calls `generate_next_scene()` to create the next segment

## Story State Persistence

The system now supports saving and loading story sessions:

**State Management Methods** (in `StoryRunner`):
- `save_state()`: Saves current segment and visited segments to `runner_state.json`
- `load_state()`: Loads previous session state
- `clear_state()`: Deletes saved state
- `start_from_segment(segment_id)`: Start from any segment

**Auto-Save**: The CLI automatically saves state after each AI-generated scene.

**State File Location**: `.infinite_story_data/<story_id>/runner_state.json`

## Known Issues / TODOs

- ✅ ~~Custom choice handling~~ - IMPLEMENTED
- ✅ ~~Core game loop with AI generation~~ - IMPLEMENTED
- ✅ ~~Configuration management~~ - IMPLEMENTED
- ✅ ~~Story state persistence~~ - IMPLEMENTED
- ✅ ~~Resume story from segment~~ - IMPLEMENTED
- ✅ ~~Unique ID generation for segments/choices~~ - IMPLEMENTED (uses UUID + counter)
- ❌ Prompt building is currently inline in `StorySegment._generate_scene_prompt()` rather than in `prompt_builder.py`
- ❌ Frontend exists but is empty scaffolding
- ❌ Episode system (to prevent infinite tree depth) is planned but not implemented
