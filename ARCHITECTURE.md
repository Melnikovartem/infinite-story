# Architecture

Technical overview of the Infinite Story Engine's core abstractions and data flow.

## Data Model Hierarchy

Everything inherits from `StoryBase`, which provides JSON file persistence.

```
StoryBase                         # Base class: save/load/delete to JSON files
├── Story                         # Top-level container (title, description, start_segment_id)
└── StoryBlock                    # Requires a parent Story
    ├── StorySegment              # A scene: text blocks + character/location states
    ├── StoryChoice               # An edge: connects from_segment -> to_segment
    ├── StoryCharacter            # Character definition + running_status history
    ├── StoryLocation             # Location definition + running_status history
    └── StoryContext              # Worldbuilding: rules, fundamental truths
```

**Key pattern**: All `StoryBlock` subclasses take a `story` parameter on creation and auto-register with the parent `Story` object. The `story` field is excluded from serialization to avoid circular references.

```python
story = Story(id="my_story", title="My Story", ...)
segment = StorySegment(story=story, id="seg_1", ...)    # auto-registers
choice = StoryChoice(story=story, id="c_1", from_segment_id="seg_1", ...)
```

## Story Graph

Stories form a directed graph:

- **Nodes** = `StorySegment` (scenes)
- **Edges** = `StoryChoice` (decisions connecting segments)
- **Entry point** = `Story.start_segment_id`

Each segment has runtime-only dictionaries (built by `StoryRunner.load_all_components()`):

- `outgoing_choices: Dict[str, StoryChoice]` -- where the player can go
- `incoming_choices: Dict[str, StoryChoice]` -- how they got here

A choice with `to_segment_id=None` means the destination doesn't exist yet. Selecting it triggers AI generation.

## Storage

JSON files on disk, organized by story and component type:

```
.infinite_story_data/
└── <story_id>/
    ├── story/<story_id>.json
    ├── storysegment/<segment_id>.json
    ├── storychoice/<choice_id>.json
    ├── storycharacter/<character_id>.json
    ├── storylocation/<location_id>.json
    ├── storycontext/<context_id>.json
    └── runner_state.json              # saved session state
```

Component type directories are auto-derived from class names (`StorySegment` -> `storysegment`).

**Persistence API** (on `StoryBase`):
- `save()` -- serialize to JSON file
- `load(story_id, component_id)` -- load from JSON file
- `list_all(story_id)` -- list all components of this type
- `delete()` -- remove from disk

## Text Block System

Segments contain lists of `TextBlock` objects. Each block has a `type`, `content`, and optional `emotion`/`character` fields.

| Category | Types |
|----------|-------|
| Narrative | `NARRATOR_DESCRIBING`, `NARRATOR_COMMENTARY`, `FLASHBACK`, `DREAM_SEQUENCE` |
| Dialogue | `CHARACTER_SPEECH`, `CHARACTER_THOUGHT`, `POEM_OR_SONG`, `LETTER_OR_NOTE` |
| Media | `SFX`, `VISUAL_CUE`, `MEDIA_OVERLAY` |
| UI | `SCENE_TITLE`, `LOCATION_LABEL`, `SYSTEM_MESSAGE` |

See [docs/text_types.md](docs/text_types.md) for full reference and [docs/text_story_example.md](docs/text_story_example.md) for a complete example scene.

## AI Generation Flow

When a player selects a choice with no destination (`to_segment_id=None`), `StorySegment.generate_next_scene()` runs:

1. **Build context** from:
   - Previous segments (via `get_story_segments_before()`)
   - Story context (worldbuilding rules & truths)
   - Character states (`characters_running_status` -- accumulated history)
   - Location states (`locations_running_status` -- accumulated history)
   - The connecting choice text
2. **Call** `TextGenerator.generate()` with `context_type="scene"`
3. **Parse** response into `SceneTextGeneratorResponse`
4. **Create** new `StorySegment` with generated text blocks
5. **Create** 2 new `StoryChoice` objects leading from the new segment
6. **Save** everything to disk

The `TextGenerator` is an abstract base class. Implementations:
- `OpenRouterGenerator` -- calls OpenRouter API (recommended, supports 10+ models)
- `OpenAIGenerator` -- calls OpenAI API directly

## State Management

`StoryRunner` manages the game loop:

- `load_all_components()` -- loads all segments/choices from disk, builds the graph
- `save_state()` -- saves current segment + visited segments to `runner_state.json`
- `load_state()` -- resumes from saved state
- `clear_state()` -- deletes saved state

Auto-save triggers after every AI-generated scene.

## Overview Methods

All `StoryBlock` subclasses implement:
- `get_short_overview()` -- brief description for lists/UI
- `get_full_overview()` -- detailed context string for AI prompts

These are critical for generation quality -- they provide the AI with rich context about characters, locations, and world state.

## Key Files

| File | Role |
|------|------|
| `app/models/story_base.py` | Base persistence layer |
| `app/models/story.py` | Story container with component caches |
| `app/models/story_segment.py` | Scene model + AI generation logic |
| `app/models/story_choice.py` | Choice model (graph edges) |
| `app/engine/story_runner.py` | Game loop and state management |
| `app/engine/generator.py` | Abstract TextGenerator interface |
| `app/engine/openrouter_generator.py` | OpenRouter API implementation |
| `app/routes/` | FastAPI route handlers |
| `app/cli.py` | Typer CLI commands |
| `app/config.py` | Configuration from .env |
| `app/utils/prompt_builder.py` | Prompt construction for AI |
