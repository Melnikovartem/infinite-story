# Backend Codebase Exploration Summary

**Date**: February 28, 2026  
**Scope**: Complete analysis of backend architecture for API development

---

## Executive Summary

The infinite story engine backend is **production-ready and well-architected**. It features:

- ✅ **8 Pydantic model classes** with full validation
- ✅ **2 AI provider implementations** (OpenAI + OpenRouter)
- ✅ **Async/await architecture** for concurrent operations
- ✅ **JSON file persistence** with auto-serialization
- ✅ **CLI interface** with Rich terminal UI
- ✅ **Scene generation** with state tracking
- ❌ **No web API** yet (ready to build with FastAPI)

**Key Insight**: Minimal changes needed to expose as REST API. All models are Pydantic-compatible.

---

## 1. Model Classes (app/models/)

### Eight Core Models

| Model | Purpose | Key Fields |
|-------|---------|-----------|
| **Story** | Top-level container | id, title, description, genre, start_segment_id |
| **StorySegment** | Scenes/chapters | text_blocks, atmosphere, characters_present, locations_present |
| **StoryChoice** | Branch decisions | from_segment_id, to_segment_id, text, clicks_logged |
| **StoryCharacter** | Character metadata | name, description, background |
| **StoryLocation** | Location metadata | name, description |
| **StoryContext** | Worldbuilding | fundamental_truths, worldbuilding (dict/str) |
| **User** | User accounts | id, email (EmailStr), username, created_at |
| **TextBlock** | Narrative units | type (enum), content, emotion, character |

### Model Hierarchy
```
Pydantic BaseModel
├── StoryBase (persistence layer)
│   ├── Story
│   └── StoryBlock
│       ├── StorySegment
│       ├── StoryChoice
│       ├── StoryCharacter
│       ├── StoryLocation
│       └── StoryContext
└── User (standalone)
```

### TextBlock Types (14 types)
- Narrative: NARRATOR_DESCRIBING, NARRATOR_COMMENTARY, FLASHBACK, DREAM_SEQUENCE
- Dialogue: CHARACTER_SPEECH, CHARACTER_THOUGHT, POEM_OR_SONG, LETTER_OR_NOTE
- Media: SFX, VISUAL_CUE, MEDIA_OVERLAY
- UI: SCENE_TITLE, LOCATION_LABEL, SYSTEM_MESSAGE

---

## 2. Engine Components (app/engine/)

### Four Key Components

#### **TextGenerator** (Abstract Base)
- Async generation with Pydantic validation
- Auto JSON extraction from LLM responses
- Supports 4 response types: world, character, location, scene
- Schema-driven prompts

#### **OpenAIGenerator**
- OpenAI-compatible API
- Custom base URL support (Azure, local endpoints)
- JSON mode enforcement
- Uses httpx.AsyncClient

#### **OpenRouterGenerator**
- Unified API for 30+ models
- Supports: Deepseek, GPT, Claude, Mistral, Llama, etc.
- Built-in model mapping
- Site URL/name tracking

#### **StoryRunner**
- Game loop manager
- State persistence (runner_state.json)
- Choice sorting by engagement
- Segment navigation

---

## 3. CLI Commands (app/cli.py)

Built with Typer + Rich for beautiful terminal UI.

| Command | Purpose |
|---------|---------|
| `list-stories` | Show all available stories |
| `run-story` | Interactive gameplay |
| `test-generation` | Debug scene generation |
| `list-models` | Show available AI models |

**Features**:
- Story selection menu
- Text block formatting
- Top 2 choices + view all option
- Custom choice input
- AI scene generation
- Save/resume functionality
- Auto-save after generation

---

## 4. Configuration System (app/config.py)

### GeneratorConfig
```
provider: "openai" | "openrouter"
api_key: str
model: str
temperature: float (0.0-2.0)
max_tokens: int
base_url: str (for OpenAI)
site_url: str (for OpenRouter, optional)
site_name: str (for OpenRouter, optional)
```

### Loading
- Reads `.env` file automatically
- Falls back to environment variables
- Validates required fields by provider
- Sets up logging

### .env Example
```
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-xxx
AI_MODEL=deepseek-v3
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
LOG_LEVEL=INFO
```

---

## 5. Data Storage

### File-Based JSON
- Location: `.infinite_story_data/` directory
- Structure: `.infinite_story_data/{story_id}/{component_type}/{id}.json`
- Component types auto-derived from class names

### Storage Mapping
```
Story → story/
StorySegment → storysegment/
StoryChoice → storychoice/
StoryCharacter → storycharacter/
StoryLocation → storylocation/
StoryContext → storycontext/
```

### Auto-Save
- Components save via `.save()` method
- State persists to `runner_state.json`
- Resume functionality via `load_state()`

---

## 6. Dependencies (Current)

```
pydantic>=2.6.1              # Data validation
httpx>=0.27.0               # Async HTTP
typer>=0.9.0                # CLI framework
rich>=13.7.0                # Terminal UI
python-dotenv>=1.0.0        # .env loading
email-validator>=2.1.0      # Email validation
python-dateutil>=2.8.2      # DateTime utils
typing-extensions>=4.9.0    # Advanced typing
```

### Not Installed (for API)
- ❌ FastAPI
- ❌ uvicorn
- ❌ SQLAlchemy
- ❌ pytest

---

## 7. Architecture Patterns

### Story Object Auto-Registration
```python
class MyBlock(StoryBlock):
    def __init__(self, **data):
        super().__init__(**data)
        self.story.add_segment(self)  # Auto-register
```

### Circular Reference Prevention
- Story object excluded from JSON: `Field(exclude=True)`
- Allows in-memory relationships without serialization issues

### Story Graph as Directed Graph
```
Nodes: StorySegment (scenes)
Edges: StoryChoice (decisions)
Entry: Story.start_segment_id
```

### Generation Flow
1. Build context from previous segments
2. Include worldbuilding + character/location state
3. Pass to TextGenerator with schema
4. Validate response with Pydantic
5. Create StorySegment + 2 StoryChoices
6. Auto-save to disk

---

## 8. What's Ready for API

### Ready to Use Directly
✅ All Pydantic models (drop into FastAPI responses)
✅ Async generators (perfect for endpoints)
✅ StoryRunner (game state management)
✅ Error handling utilities
✅ Config system (DI-ready)

### Ready to Expose
- Story CRUD operations
- Segment & choice navigation
- State save/load
- Scene generation with streaming
- Model information

### Ready for Testing
- All models are Pydantic (easy to mock)
- Generators are async (asyncio-compatible)
- File storage (easy to stub)

---

## 9. Missing for Production API

❌ Web framework (FastAPI)
❌ Database (currently JSON only)
❌ Authentication/Authorization
❌ Request validation middleware
❌ Response serialization HTTP layer
❌ CORS configuration
❌ Rate limiting
❌ Caching strategy
❌ API documentation (OpenAPI/Swagger)

---

## 10. Key Insights for Development

### Separation of Concerns ✅
- **Models**: Pure Pydantic, no framework dependencies
- **Engine**: Async-ready, pluggable generators
- **Storage**: Abstracted, could support DB
- **CLI**: Typer, independent from core logic

### Async Architecture Ready ✅
- All generation is async/await
- httpx for async HTTP
- Perfect for FastAPI integration

### Zero Breaking Changes Needed
- Existing code works as-is
- Can build API layer on top
- Models unchanged for API

### Easy to Extend
- Generator pattern supports custom implementations
- StoryBase abstraction allows DB migration
- Config system supports multiple providers

---

## 11. Quick API Implementation Path

### Step 1: Install Dependencies
```bash
pip install fastapi uvicorn
```

### Step 2: Create app/main.py
```python
from fastapi import FastAPI
from app.api import routes

app = FastAPI()
app.include_router(routes.story_router)
app.include_router(routes.segment_router)
app.include_router(routes.choice_router)
```

### Step 3: Create app/api/routes.py
```python
from fastapi import APIRouter
from app.models import Story

router = APIRouter(prefix="/api/stories")

@router.get("")
async def list_stories():
    return [Story.load(id, id) for id in Story.list_stories()]

@router.get("/{story_id}")
async def get_story(story_id: str):
    return Story.load(story_id, story_id)
```

### Step 4: Run
```bash
uvicorn app.main:app --reload
```

### Step 5: Access Docs
```
http://localhost:8000/docs
```

---

## 12. File Structure Reference

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── story_base.py      (← Persistence)
│   │   ├── story.py           (← Top-level)
│   │   ├── story_block.py     (← Mixin)
│   │   ├── story_segment.py   (← Scenes + Generation)
│   │   ├── story_choice.py    (← Choices)
│   │   ├── story_character.py
│   │   ├── story_location.py
│   │   ├── story_context.py
│   │   ├── text_types.py      (← Enums + Schemas)
│   │   └── user.py
│   ├── engine/
│   │   ├── generator.py           (← Abstract)
│   │   ├── openai_generator.py
│   │   ├── openrouter_generator.py
│   │   └── story_runner.py        (← Game Loop)
│   ├── config.py             (← Config Loading)
│   ├── cli.py                (← CLI Interface)
│   └── utils/
│       ├── error_handler.py
│       └── prompt_builder.py
├── tests/
├── .env
├── .env.example
├── requirements.txt
└── .infinite_story_data/     (← Data Storage)
```

---

## 13. Documentation Files Created

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | **Complete architecture deep-dive** (read this first) |
| `QUICK_REFERENCE.md` | Quick lookup for classes, methods, patterns |
| `API_DEVELOPMENT_GUIDE.md` | Step-by-step guide for building FastAPI |
| `BACKEND_EXPLORATION_SUMMARY.md` | This file - executive summary |

---

## 14. Recommendations

### For API Development
1. **Start with FastAPI** - Pydantic models integrate perfectly
2. **Keep existing models** - Don't refactor, extend
3. **Add middleware** - Error handling, CORS, logging
4. **Use Depends** - For config injection in routes
5. **Stream generations** - Use `EventSourceResponse` for long waits

### For Scale
1. **Add caching** - Cache story/segment lookups
2. **Consider DB** - SQLAlchemy layer over StoryBase
3. **Add auth** - User tracking via JWT
4. **Rate limit** - OpenRouter + OpenAI cost controls
5. **Monitor** - Track generation success rates

### For Quality
1. **Add pytest** - Test models + routes
2. **Add mypy** - Type checking
3. **Add pre-commit** - Linting + formatting
4. **Add logging** - Already integrated, extend for API
5. **Add docs** - FastAPI auto-generates from docstrings

---

## Summary Table

| Aspect | Status | Tech |
|--------|--------|------|
| **Models** | ✅ Complete | Pydantic |
| **Persistence** | ✅ Complete | JSON files |
| **AI Backends** | ✅ Complete (2) | httpx async |
| **Game Logic** | ✅ Complete | StoryRunner |
| **CLI** | ✅ Complete | Typer + Rich |
| **Configuration** | ✅ Complete | .env + Pydantic |
| **Testing Hooks** | ✅ In Place | pytest-ready |
| **Web API** | ❌ Not Started | FastAPI (ready) |
| **Database** | ❌ Not Needed Yet | JSON (extensible) |
| **Auth** | ❌ Not Implemented | User model exists |

---

## Next Steps

1. **Read** `ARCHITECTURE.md` for complete details
2. **Review** `QUICK_REFERENCE.md` for API endpoints
3. **Follow** `API_DEVELOPMENT_GUIDE.md` for implementation
4. **Install** FastAPI & uvicorn
5. **Create** app/main.py with routes
6. **Test** with auto-docs at `/docs`

---

## Conclusion

This is a **well-engineered system** ready for API development. The core logic is solid, models are properly structured, and the async architecture is production-ready. Building a REST API requires minimal changes and can leverage existing components directly.

**Estimated effort to working API**: 1-2 hours with FastAPI.

