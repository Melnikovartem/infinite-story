# Infinite Story Engine - Backend Architecture Analysis

## Overview
This is a sophisticated **interactive storytelling engine** that uses AI to dynamically generate narrative content. The system is built on Pydantic for data modeling, uses JSON file storage, and features a CLI interface with Rich terminal UI.

---

## 1. MODEL CLASSES (app/models/)

### Data Model Hierarchy
```
BaseModel (Pydantic)
├── StoryBase
│   ├── Story (top-level container)
│   └── StoryBlock
│       ├── StorySegment (scenes/chapters)
│       ├── StoryChoice (narrative branching)
│       ├── StoryCharacter (character definitions)
│       ├── StoryLocation (location definitions)
│       └── StoryContext (worldbuilding/lore)
└── User (standalone)
```

### Core Models Details

#### 1. **Story** (story.py)
- **Purpose**: Top-level container for an entire narrative
- **Key Fields**:
  - `id`: Unique story identifier
  - `title`: Display name
  - `description`: Story synopsis
  - `genre`: Story genre
  - `user_id`: Creator reference
  - `start_segment_id`: Entry point to story graph
- **Caches**: Maintains private collections of characters, locations, segments, choices, and context
- **Methods**:
  - `add_character()`, `add_location()`, `add_segment()`, `add_choice()`, `add_context()`
  - `get_character()`, `get_location()`, `get_segment()`, `get_choice()`
  - `get_all_*()` variants for retrieving all components
- **Special Pattern**: `story_id` always equals `id`

#### 2. **StorySegment** (story_segment.py)
- **Purpose**: Represents a scene/chapter in the story
- **Key Fields**:
  - `short_description`: Brief summary
  - `atmosphere`: Mood/tone
  - `time_of_day`, `weather`: Scene context
  - `text_blocks`: List of TextBlock objects (narrative content)
  - `characters_present`: List of character IDs in scene
  - `locations_present`: List of location IDs in scene
  - `characters_running_status`: Accumulated character state history
  - `locations_running_status`: Accumulated location state history
  - `incoming_choices`: Choices leading TO this segment
  - `outgoing_choices`: Choices leading FROM this segment
- **Methods**:
  - `get_story_segments_before()`: Traverse story backwards for context
  - `generate_next_scene()`: AI-powered scene generation
  - `add_incoming_choice()`, `add_outgoing_choice()`

#### 3. **StoryChoice** (story_choice.py)
- **Purpose**: Represents a branching decision
- **Key Fields**:
  - `from_segment_id`: Source segment
  - `to_segment_id`: Destination segment (None = AI will generate)
  - `text`: Choice text presented to player
  - `clicks_logged`: Authenticated user clicks
  - `clicks_anonymous`: Anon user clicks
  - `flags`: Content warnings (NSFW, violent)
- **Auto-Registration**: Adds itself to Story's choice cache on init

#### 4. **StoryCharacter** (story_character.py)
- **Purpose**: Character definition/metadata
- **Key Fields**:
  - `name`: Character name
  - `description`: Brief overview
  - `background`: Detailed history
- **Methods**:
  - `get_short_overview()`: Character summary
  - `get_full_overview()`: Full appearances and status history

#### 5. **StoryLocation** (story_location.py)
- **Purpose**: Location/place definition
- **Key Fields**:
  - `name`: Location name
  - `description`: Details about the place
- **Methods**:
  - `get_short_overview()`: Location summary
  - `get_full_overview()`: Full appearances and status history

#### 6. **StoryContext** (story_context.py)
- **Purpose**: Worldbuilding and fundamental truths
- **Key Fields**:
  - `fundamental_truths`: List of core world facts
  - `worldbuilding`: String or Dict of world details
- **Methods**:
  - `get_short_overview()`: World context summary
  - `get_full_overview()`: Full worldbuilding details

#### 7. **User** (user.py)
- **Purpose**: User account model
- **Key Fields**:
  - `id`: User identifier
  - `email`: EmailStr (validated)
  - `username`: Display name
  - `created_at`: Account creation timestamp

### Supporting Types

#### **TextBlock** (text_types.py)
- **Purpose**: Individual narrative unit
- **Fields**:
  - `type`: TextType enum (see below)
  - `content`: Text content
  - `emotion`: Optional mood indicator
  - `character`: Optional character name (for dialogue)

#### **TextType** Enum (text_types.py)
```
NARRATOR_DESCRIBING        # Scene description
NARRATOR_COMMENTARY        # Author's voice
FLASHBACK                  # Past events
DREAM_SEQUENCE             # Dreams/visions
CHARACTER_SPEECH           # Dialogue
CHARACTER_THOUGHT          # Internal monologue
POEM_OR_SONG               # Verse content
LETTER_OR_NOTE             # Written content
SFX                        # Sound effects
VISUAL_CUE                 # Visual descriptions
MEDIA_OVERLAY              # Special effects
SCENE_TITLE                # Scene heading
LOCATION_LABEL             # Location name
SYSTEM_MESSAGE             # Meta information
```

#### **CharacterStatus** & **LocationStatus** (story_segment.py)
- Track state changes of characters/locations through story progression

---

## 2. ENGINE COMPONENTS (app/engine/)

### **TextGenerator** (generator.py)
- **Abstract Base Class** for AI text generation
- **Key Methods**:
  - `async generate()`: Main generation method
    - Takes: `system_prompt`, `user_prompt`, `context_type`
    - Returns: Typed TextGeneratorResponse
    - Supports: "world", "character", "location", "scene"
  - `async _generate_content()`: Override in subclasses
- **Features**:
  - Automatic JSON extraction from LLM responses
  - Schema validation using Pydantic
  - Comprehensive error handling
  - Default system prompt included
- **Response Types**:
  - `WorldTextGeneratorResponse`: World/setting generation
  - `CharacterTextGeneratorResponse`: Character generation
  - `LocationTextGeneratorResponse`: Location generation
  - `SceneTextGeneratorResponse`: Scene generation

### **OpenAIGenerator** (openai_generator.py)
- **Implementation** of TextGenerator for OpenAI API
- **Config**:
  - Base URL customizable (supports Azure, local endpoints)
  - API key authentication
  - Model selection
  - Temperature & max_tokens control
- **HTTP Client**: httpx.AsyncClient (async requests)
- **API Endpoint**: `/v1/chat/completions`
- **Response Format**: Enforces JSON mode

### **OpenRouterGenerator** (openrouter_generator.py)
- **Implementation** of TextGenerator for OpenRouter unified API
- **Supported Providers**: Deepseek, OpenAI, Anthropic, Mistral, Meta Llama
- **Config**:
  - Site URL & name (for API rate limits)
  - Model mapping (short names to full paths)
  - 30+ models available
- **Example Models**:
  - `deepseek-v3`: Deepseek latest
  - `gpt-4-turbo`: OpenAI GPT-4
  - `claude-3-opus`: Anthropic Claude
  - `mixtral-8x22b`: Mistral

### **StoryRunner** (story_runner.py)
- **Game Loop Manager** for story execution
- **Key Methods**:
  - `start()`: Initialize story from start_segment_id
  - `load_all_components()`: Load all story data from disk
  - `get_available_choices()`: Get choices in current segment
    - Sorts by click count & logged clicks
    - Randomizes if all tied
    - Limits to top 100
  - `make_choice()`: Move to next segment
  - `save_state()`: Persist current position
  - `load_state()`: Resume from saved position
  - `start_from_segment()`: Jump to any segment
- **State Tracking**:
  - `current_segment`: Current position
  - `visited_segments`: Set of visited segment IDs
  - Saved to `runner_state.json`

### **StoryBase** (models/story_base.py)
- **Base Class** for all story components
- **Persistence Layer**:
  - `save()`: Serialize to JSON
  - `load()`: Deserialize from JSON
  - `list_all()`: List all components of a type
  - `delete()`: Remove from disk
- **Storage Structure**:
  - Base: `.infinite_story_data/`
  - Per-story: `.infinite_story_data/{story_id}/`
  - Per-component: `.infinite_story_data/{story_id}/{component_type}/`
  - Example: `.infinite_story_data/veil_of_thornreach/storysegment/opening_scene.json`

---

## 3. CLI COMMANDS (app/cli.py)

Built with **Typer** and **Rich** for beautiful terminal UI.

### Commands Available

#### **list-stories**
- Lists all available stories
- Displays in formatted table with ID, title, genre, description

#### **run-story**
- Interactive story gameplay
- Features:
  - Story selection from available list
  - Display current segment with formatted text blocks
  - Show top 2 choices or all choices
  - Custom choice input
  - AI scene generation on demand
  - Auto-save after generation
  - Resume from saved state
  - Save/exit or exit without saving

#### **test-generation** `[--story-id]`
- Debug tool for scene generation
- Shows generated content structure
- Displays generated choices preview
- Useful for testing AI models

#### **list-models** `[--provider] [--use-case]`
- Display available AI models
- Filter by provider (openrouter, openai)
- Get recommendations for use cases (story, speed, quality, budget)

### Async Flow
- All AI-heavy operations are async
- Uses `asyncio.run()` for CLI integration
- Generator integration in story loop

---

## 4. CONFIGURATION (app/config.py)

### **GeneratorConfig**
```
provider: "openai" | "openrouter" (default: "openrouter")
api_key: str
base_url: str (default: "https://api.openai.com")
model: str (default: "deepseek-v3")
temperature: float (default: 0.7, range: 0.0-2.0)
max_tokens: int (default: 2000)
site_url: Optional[str] (for OpenRouter)
site_name: Optional[str] (for OpenRouter)
```

### **Config.load()**
- Reads from `.env` file automatically
- Falls back to environment variables
- Validates required fields based on provider
- Sets up logging

### **Logging**
- Configurable via `LOG_LEVEL` env var
- Logger: `"infinite_story"`
- Integrated throughout codebase

---

## 5. DEPENDENCIES (requirements.txt)

### Currently Installed
- **pydantic>=2.6.1**: Data validation & serialization
- **email-validator>=2.1.0**: EmailStr validation
- **python-dateutil>=2.8.2**: Datetime utilities
- **typing-extensions>=4.9.0**: Advanced typing
- **httpx>=0.27.0**: Async HTTP client
- **typer>=0.9.0**: CLI framework
- **rich>=13.7.0**: Terminal UI
- **python-dotenv>=1.0.0**: .env file loading

### NOT Currently Installed
- ❌ **FastAPI**: No web API yet
- ❌ **SQLAlchemy**: Using JSON file storage instead
- ❌ **pytest**: For testing (mentioned in docs but not in requirements)

---

## 6. DATA STORAGE

### File-Based JSON Storage
- **Location**: `.infinite_story_data/` directory
- **Structure**:
  ```
  .infinite_story_data/
  ├── veil_of_thornreach/           # Story ID
  │   ├── story/
  │   │   └── veil_of_thornreach.json
  │   ├── storysegment/
  │   │   ├── opening_scene.json
  │   │   └── ...
  │   ├── storychoice/
  │   │   └── ...
  │   ├── storycharacter/
  │   │   └── ...
  │   ├── storylocation/
  │   │   └── ...
  │   ├── storycontext/
  │   │   └── ...
  │   └── runner_state.json         # Game progress
  └── other_story/
      └── ...
  ```

### Component Type Mapping
- `Story` → `story/`
- `StorySegment` → `storysegment/`
- `StoryChoice` → `storychoice/`
- `StoryCharacter` → `storycharacter/`
- `StoryLocation` → `storylocation/`
- `StoryContext` → `storycontext/`

### Auto-Save Behavior
- Segments auto-save after generation
- State auto-saves after each choice
- Manual save/restore via `runner_state.json`

---

## 7. ARCHITECTURE PATTERNS

### Critical Patterns

#### **Story Object Registration**
All StoryBlock subclasses auto-register with parent Story:
```python
class MyBlock(StoryBlock):
    def __init__(self, **data):
        super().__init__(**data)
        self.story.add_segment(self)  # or add_choice, etc.
```

#### **Circular Reference Prevention**
- Story object excluded from serialization in StoryBlock: `Field(exclude=True)`
- Allows in-memory relationships without serialization issues

#### **Story Graph Structure**
```
Story
├── Segments (nodes)
│   └── StorySegment
│       ├── incoming_choices (runtime-only)
│       └── outgoing_choices (runtime-only)
└── Choices (edges)
    └── StoryChoice
        ├── from_segment_id
        └── to_segment_id
```

#### **Generator Flow**
1. Build context from previous segments + worldbuilding
2. Pass to `TextGenerator.generate()`
3. AI returns JSON response
4. Pydantic validates response
5. Create StorySegment + 2 new StoryChoices
6. Save to disk

#### **State Accumulation**
- `characters_running_status`: Cumulative character states through story
- `locations_running_status`: Cumulative location states through story
- Used for context in scene generation

---

## 8. EXISTING INFRASTRUCTURE

### What's Ready to Build On
✅ Pydantic models with full validation
✅ JSON persistence layer
✅ Multiple AI provider support (OpenAI + OpenRouter)
✅ Async/await architecture
✅ CLI with Rich UI
✅ Scene generation with validation
✅ Story state management & resumption
✅ Character/location/context tracking

### What's Missing for API
❌ FastAPI or similar web framework
❌ Database integration (currently JSON only)
❌ API authentication/authorization
❌ Request/response serialization for HTTP
❌ Error handling for HTTP layer
❌ CORS configuration
❌ API documentation (OpenAPI/Swagger)

---

## 9. KEY INSIGHTS FOR API BUILDING

### Separation of Concerns
- **Models**: Pure Pydantic, no framework dependencies
- **Engine**: Async-ready, pluggable generators
- **Storage**: Abstracted in StoryBase, could support database
- **CLI**: Typer, could be complemented with FastAPI

### Ready-to-Expose Endpoints
1. **Story Management**
   - GET /stories
   - GET /stories/{story_id}
   - POST /stories (create)
   - PUT /stories/{story_id}

2. **Segments & Choices**
   - GET /stories/{story_id}/segments/{segment_id}
   - GET /stories/{story_id}/choices
   - POST /stories/{story_id}/choices (make choice)

3. **Game State**
   - GET /stories/{story_id}/state
   - POST /stories/{story_id}/state (save)
   - DELETE /stories/{story_id}/state (clear)

4. **Scene Generation**
   - POST /stories/{story_id}/generate (from choice)

### Async-Ready
All core generation logic is async, perfect for FastAPI

### Model Reusability
Can directly use Pydantic models as FastAPI response models

---

## 10. CONFIGURATION EXAMPLE

### .env file structure
```
# AI Provider Setup
AI_PROVIDER=openrouter           # or 'openai'
OPENROUTER_API_KEY=your-key      # if using openrouter
OPENAI_API_KEY=your-key          # if using openai
AI_MODEL=deepseek-v3             # model name
AI_TEMPERATURE=0.7               # 0.0-2.0
AI_MAX_TOKENS=2000               # max output length

# OpenRouter specific (optional)
OPENROUTER_SITE_URL=https://mysite.com
OPENROUTER_SITE_NAME=My Story Engine

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR

# Optional for custom base URLs
OPENAI_BASE_URL=https://api.openai.com
```

---

## Summary Table

| Layer | Component | Status | Tech |
|-------|-----------|--------|------|
| **Models** | 8 model classes | ✅ Complete | Pydantic |
| **Validation** | TextBlock types, Choices flags | ✅ Complete | Pydantic |
| **Storage** | JSON file-based | ✅ Complete | Pathlib |
| **AI Generation** | TextGenerator + 2 providers | ✅ Complete | httpx (async) |
| **Runtime** | StoryRunner | ✅ Complete | Async/await |
| **CLI** | 4 commands | ✅ Complete | Typer + Rich |
| **Config** | Multi-provider support | ✅ Complete | Pydantic |
| **API** | ❌ None yet | ⏳ TODO | FastAPI (planned) |
| **Database** | ❌ No SQL | ⏳ Consider | SQLAlchemy (optional) |

