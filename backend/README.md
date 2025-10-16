# Infinite Story Engine - Backend

An AI-powered interactive storytelling engine that generates infinite branching narratives.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 3. Run the Story

```bash
# From the project root
./run.sh

# Or from the backend directory
PYTHONPATH=. python -m app.cli run-story
```

## How It Works

### The Story Engine

The engine generates infinite branching stories using AI. When you make a choice:

1. If the choice leads to an **existing segment**, you navigate to it
2. If the choice has **no destination** (`to_segment_id=None`), the AI generates a new scene based on:
   - Previous story segments (context)
   - Current character and location states
   - Worldbuilding and story rules
   - Your choice text

### Playing a Story

When you run the story, you can:

- **Select from top 2 choices** - Most popular/likely paths
- **View all choices** - See every available option
- **Write custom choices** - Type your own action (AI generates the next scene!)
- **Save and exit** - Save your progress and continue later
- **Exit without saving** - End without saving progress

### Auto-Save Feature

The system automatically saves your progress after:
- Every AI-generated scene
- Manual save (option 5)

Your session is automatically resumed the next time you run the story!

### Example Session

```
================================================================================

The Last Sanctuary

The ancient trees of Thornreach Grove sway gently in the evening breeze...

================================================================================

What would you like to do?
1. Investigate the weakening wards with Eira and Brother Cellen
2. Venture into The Veil to understand its nature
3. Show all options
4. Write your own choice
5. Exit

Select an option: 4
Enter your choice: Ask Nyx about the Memory Weaver's whereabouts

Generating next scene...
Scene generated successfully!
```

## Project Structure

```
backend/
├── app/
│   ├── models/          # Data models (Story, Segment, Choice, etc.)
│   ├── engine/          # Story runner and AI generation
│   ├── utils/           # Utilities and helpers
│   ├── config.py        # Configuration management
│   └── cli.py           # Command-line interface
├── tests/               # Test suite
├── scripts/             # Utility scripts (e.g., save_story.py)
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
└── pytest.ini           # Test configuration
```

## Configuration Options

Edit `.env` to customize:

```bash
OPENAI_API_KEY=sk-...           # Your OpenAI API key (required)
OPENAI_BASE_URL=...             # API endpoint (default: https://api.openai.com)
OPENAI_MODEL=gpt-4o-mini        # Model to use
OPENAI_TEMPERATURE=0.7          # Creativity (0.0-2.0)
OPENAI_MAX_TOKENS=2000          # Max response length
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_story_models.py

# Run with verbose output
python -m pytest -v

# Run a specific test
python -m pytest tests/test_story_models.py::test_story_creation -v
```

### Creating New Stories

Use the `scripts/save_story.py` script as a template:

```python
from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_choice import StoryChoice
# ... create your story components and save them
```

### CLI Commands

```bash
# List all available stories
PYTHONPATH=. python -m app.cli list-stories

# Run a story interactively
PYTHONPATH=. python -m app.cli run-story
```

## How AI Generation Works

The system uses a sophisticated prompt-building process:

1. **Context Assembly** (`StorySegment._generate_scene_prompt()`):
   - Story context (worldbuilding, fundamental truths)
   - Previous segments (up to 10 segments back)
   - Current segment's full state
   - Character states and backgrounds
   - Location states and descriptions
   - The player's choice text

2. **AI Generation** (`OpenAIGenerator.generate()`):
   - Sends context to OpenAI API with structured schema
   - Requests JSON response with specific fields
   - Validates and parses response into `SceneTextGeneratorResponse`

3. **Scene Creation** (`generate_next_scene()`):
   - Creates new `StorySegment` from AI response
   - Generates 2 new `StoryChoice` objects for next decisions
   - Updates character/location running states
   - Saves everything to disk

## Storage

Stories are stored as JSON files in `.infinite_story_data/`:

```
.infinite_story_data/
└── story_id/
    ├── story/
    │   └── story_id.json
    ├── storysegment/
    │   ├── segment_1.json
    │   └── segment_2.json
    ├── storychoice/
    │   ├── choice_1.json
    │   └── choice_2.json
    ├── storycharacter/
    ├── storylocation/
    └── storycontext/
```

## Troubleshooting

### "OPENAI_API_KEY environment variable is required"

Create a `.env` file in the `backend/` directory with your API key:
```bash
cp .env.example .env
# Edit .env and add your key
```

### "Story has no start segment"

Make sure your story has a `start_segment_id` that points to a valid segment.

### "Failed to generate content"

Check:
- Your API key is valid
- You have sufficient API credits
- The OpenAI service is accessible
- Your network connection is working

### Tests Failing

Make sure you've activated the virtual environment and installed all dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Contributing

When adding new features:

1. Write tests in `tests/`
2. Update this README if adding user-facing changes
3. Update CLAUDE.md if changing architecture
4. Follow existing code patterns (Pydantic models, async/await, etc.)

## License

[Add your license here]
