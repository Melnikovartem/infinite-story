# Quick Reference: Backend Architecture

## File Locations

```
backend/app/
├── models/               # Data models (Pydantic)
│   ├── story_base.py     # Base class + persistence
│   ├── story.py          # Top-level story container
│   ├── story_segment.py  # Scenes with AI generation
│   ├── story_choice.py   # Branching decisions
│   ├── story_character.py
│   ├── story_location.py
│   ├── story_context.py  # Worldbuilding
│   ├── text_types.py     # TextBlock enum + response schemas
│   └── user.py
├── engine/               # Runtime & AI
│   ├── generator.py      # Abstract base class
│   ├── openai_generator.py
│   ├── openrouter_generator.py
│   └── story_runner.py   # Game loop manager
├── config.py             # Config loading from .env
├── cli.py                # CLI interface (Typer)
└── utils/
    ├── error_handler.py
    └── prompt_builder.py  # (mostly empty)
```

---

## Key Classes & Methods

### Story
```python
story = Story.load(story_id, story_id)
story.get_segment(segment_id)
story.get_choice(choice_id)
story.get_all_segments()
story.get_all_choices()
```

### StorySegment
```python
segment = story.get_segment(id)
segment.text_blocks          # List[TextBlock]
segment.outgoing_choices     # Dict[str, StoryChoice]
segment.characters_running_status  # State history

# Generate new scene
new_segment = await segment.generate_next_scene(choice, generator)
```

### StoryChoice
```python
choice = story.get_choice(id)
choice.text                  # The choice text
choice.from_segment_id       # Source
choice.to_segment_id         # Destination (None = generate)
choice.clicks_logged         # User engagement metrics
```

### StoryRunner
```python
runner = StoryRunner(story)
runner.start()              # Load from start_segment_id
runner.load_state()         # Resume from save
runner.save_state()         # Persist progress
runner.current_segment      # Current position
runner.visited_segments     # Set of visited IDs
runner.make_choice(id)      # Move to next segment
runner.get_available_choices()  # Top 100 sorted by clicks
```

### Config
```python
config = Config.load()      # From .env + env vars
config.generator.provider   # "openai" or "openrouter"
config.generator.model
config.generator.api_key
config.generator.temperature
config.generator.max_tokens
```

### Generators
```python
# OpenRouter (30+ models including GPT, Claude, Deepseek)
gen = OpenRouterGenerator(
    api_key=key,
    model="deepseek-v3",
    temperature=0.7,
    max_tokens=2000
)

# OpenAI (supports custom base URLs like Azure)
gen = OpenAIGenerator(
    api_key=key,
    api_base="https://api.openai.com",
    model="gpt-4o-mini"
)

# Both are async
response = await gen.generate(system_prompt, user_prompt, "scene")
```

---

## Data Storage

### File Structure
```
.infinite_story_data/
└── {story_id}/
    ├── story/
    │   └── {story_id}.json
    ├── storysegment/
    │   └── {segment_id}.json
    ├── storychoice/
    │   └── {choice_id}.json
    ├── storycharacter/
    ├── storylocation/
    ├── storycontext/
    └── runner_state.json        # Saved progress
```

### Saving & Loading
```python
# Save anything
obj.save()  # Auto-determines directory

# Load anything
Story.load(story_id, story_id)
StorySegment.load(story_id, segment_id, story)
StoryChoice.load(story_id, choice_id, story)

# List all of a type
segment_ids = StorySegment.list_all(story_id)
```

---

## Text Blocks

### TextType Enum
```python
from app.models import TextType

TextType.NARRATOR_DESCRIBING   # Scene description
TextType.CHARACTER_SPEECH      # Dialogue
TextType.CHARACTER_THOUGHT     # Internal
TextType.SFX                   # Sound effects
TextType.SCENE_TITLE           # Chapter title
TextType.LOCATION_LABEL        # Where we are
# ... and 8 more types
```

### TextBlock
```python
from app.models import TextBlock

block = TextBlock(
    type=TextType.CHARACTER_SPEECH,
    content="Hello, brave adventurer!",
    character="The Wizard",
    emotion="warm"  # optional
)

# AI generates these; they're in StorySegment.text_blocks
```

---

## AI Generation Flow

### 1. Setup
```python
from app.config import Config
from app.engine.openrouter_generator import OpenRouterGenerator

config = Config.load()  # From .env
generator = OpenRouterGenerator(
    api_key=config.generator.api_key,
    model=config.generator.model,
    temperature=config.generator.temperature,
    max_tokens=config.generator.max_tokens
)
```

### 2. Generate Scene
```python
# This is already built into StorySegment:
new_segment = await current_segment.generate_next_scene(
    choice,
    generator
)
# Returns: StorySegment with text_blocks + outgoing_choices
```

### 3. What Happens Internally
1. Builds context from previous segments
2. Includes story worldbuilding
3. Tracks character/location state changes
4. Calls generator with JSON schema
5. Parses response into StorySegment
6. Creates 2 new StoryChoices
7. Saves everything to disk

---

## CLI Commands

```bash
cd backend && PYTHONPATH=. python -m app.cli

# List stories
python -m app.cli list-stories

# Play story (interactive)
python -m app.cli run-story

# Test AI generation
python -m app.cli test-generation --story-id veil_of_thornreach

# List available AI models
python -m app.cli list-models
python -m app.cli list-models --provider openrouter
python -m app.cli list-models --use-case story
```

---

## Configuration (.env)

```bash
# Required for AI generation
AI_PROVIDER=openrouter              # or 'openai'
OPENROUTER_API_KEY=sk-xxx...
OPENAI_API_KEY=sk-xxx...            # if using OpenAI
AI_MODEL=deepseek-v3                # Model name
AI_TEMPERATURE=0.7                  # Creativity (0.0-2.0)
AI_MAX_TOKENS=2000                  # Response length

# Optional
OPENROUTER_SITE_URL=https://mysite.com
OPENROUTER_SITE_NAME=My App
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
```

---

## Dependencies

```
pydantic>=2.6.1           # Data validation
httpx>=0.27.0            # Async HTTP
typer>=0.9.0             # CLI
rich>=13.7.0             # Terminal UI
python-dotenv>=1.0.0     # .env loading
email-validator>=2.1.0   # Email validation
python-dateutil>=2.8.2   # Datetime
typing-extensions>=4.9.0 # Advanced typing
```

**Not installed (but needed for API):**
- fastapi
- uvicorn
- pytest (for testing)

---

## Common Patterns

### Load Full Story
```python
story = Story.load(story_id, story_id)
runner = StoryRunner(story)
runner.load_all_components(story)  # Load all segments, choices, etc.
runner.start()  # Go to start_segment_id
```

### Navigate Story
```python
# Get current segment's choices
choices = runner.current_segment.outgoing_choices

# Show top 2
for choice in list(choices.values())[:2]:
    print(choice.text)

# Make a choice
if choice.to_segment_id:
    # Go to existing segment
    runner.make_choice(choice.id)
else:
    # Generate new scene
    new_segment = await choice.from_segment.generate_next_scene(
        choice,
        generator
    )
```

### Save Progress
```python
runner.save_state()  # Saves to runner_state.json

# Later...
runner2 = StoryRunner(story)
runner2.load_state()  # Resume from saved position
```

---

## API Integration Checklist

For building REST API:

- [ ] Install FastAPI & Uvicorn
- [ ] Create `app/api/` directory
- [ ] Create route modules (stories, segments, choices, etc.)
- [ ] Use existing models directly as response types
- [ ] Use existing generators in route handlers
- [ ] Use StoryRunner for state management
- [ ] Create error handling wrapper
- [ ] Add CORS middleware
- [ ] Test with FastAPI's auto-docs at `/docs`

See `API_DEVELOPMENT_GUIDE.md` for full examples.

---

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Generation
```bash
python -m app.cli test-generation --story-id veil_of_thornreach
```

### Inspect Story Structure
```python
from app.models import Story
story = Story.load("veil_of_thornreach", "veil_of_thornreach")

print(f"Segments: {len(story.get_all_segments())}")
print(f"Choices: {len(story.get_all_choices())}")
print(f"Start: {story.start_segment_id}")

seg = story.get_segment(story.start_segment_id)
print(f"Text blocks: {len(seg.text_blocks)}")
print(f"Outgoing choices: {len(seg.outgoing_choices)}")
```

---

## Performance Notes

- **Story loading**: O(n) where n = number of components
- **Choice sorting**: Top 100 by clicks, O(n log n)
- **Generation**: Async HTTP, typically 10-60 seconds per scene
- **Storage**: File I/O, consider caching for production

---

## Known Limitations

1. **JSON storage only**: No database integration yet
2. **No authentication**: user_id field exists but not enforced
3. **No concurrency control**: Multiple writers could conflict
4. **Linear story graph**: No episodic limits yet
5. **Prompt building**: Inline in StorySegment, not in prompt_builder.py

---

## Next Steps for API

1. Create `app/main.py` with FastAPI app
2. Create `app/api/routes.py` with route handlers
3. Add `fastapi` and `uvicorn` to requirements.txt
4. Test with `python -m uvicorn app.main:app --reload`
5. Access `/docs` for auto-generated API documentation
6. (Optional) Add authentication, database, caching

