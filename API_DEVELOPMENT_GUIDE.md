# FastAPI Integration Guide

This document provides quick reference for building a REST API on top of the existing backend infrastructure.

## Quick Start

### 1. Install FastAPI
```bash
cd backend
pip install fastapi uvicorn
pip freeze > requirements.txt
```

### 2. Basic FastAPI App Structure
```python
# backend/app/api/__init__.py
# (create this directory)

# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes

app = FastAPI(
    title="Infinite Story Engine",
    description="AI-powered interactive storytelling",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.story_router)
app.include_router(routes.segment_router)
app.include_router(routes.choice_router)
app.include_router(routes.state_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Run the API
```bash
cd backend
PYTHONPATH=. python -m uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## Available Model Classes (Direct Import)

```python
from app.models import (
    Story,
    StorySegment,
    StoryChoice,
    StoryCharacter,
    StoryLocation,
    StoryContext,
    User,
    TextBlock,
    TextType,
    CharacterStatus,
    LocationStatus
)
```

All are Pydantic models, ready for FastAPI responses.

---

## Generator Integration

### Initialize Generator
```python
from app.config import Config
from app.engine.openrouter_generator import OpenRouterGenerator
from app.engine.openai_generator import OpenAIGenerator

# Load config from .env
config = Config.load()

# Create appropriate generator
if config.generator.provider == "openrouter":
    generator = OpenRouterGenerator(
        api_key=config.generator.api_key,
        model=config.generator.model,
        temperature=config.generator.temperature,
        max_tokens=config.generator.max_tokens,
        site_url=config.generator.site_url,
        site_name=config.generator.site_name
    )
else:
    generator = OpenAIGenerator(
        api_base=config.generator.base_url,
        api_key=config.generator.api_key,
        model=config.generator.model,
        temperature=config.generator.temperature,
        max_tokens=config.generator.max_tokens
    )
```

### Generate Content
```python
# Async function in your route
async def generate_scene(story_id: str, choice_id: str):
    story = Story.load(story_id, story_id)
    choice = story.get_choice(choice_id)
    current_segment = story.get_segment(choice.from_segment_id)
    
    # This is already implemented in StorySegment
    new_segment = await current_segment.generate_next_scene(
        choice,
        generator
    )
    
    return new_segment
```

---

## API Route Examples

### Story Management Routes

```python
# backend/app/api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models import Story, StorySegment, StoryChoice
from app.config import Config

story_router = APIRouter(prefix="/api/stories", tags=["stories"])

@story_router.get("")
async def list_stories() -> List[Story]:
    """List all available stories"""
    story_ids = Story.list_stories()
    stories = []
    for story_id in story_ids:
        story = Story.load(story_id, story_id)
        if story:
            stories.append(story)
    return stories

@story_router.get("/{story_id}")
async def get_story(story_id: str) -> Story:
    """Get a specific story"""
    story = Story.load(story_id, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@story_router.post("")
async def create_story(
    title: str,
    description: str,
    genre: str = None
) -> Story:
    """Create a new story"""
    story = Story(
        id=f"story_{int(time.time())}",  # Generate ID
        story_id=None,  # Will be set to id
        title=title,
        description=description,
        genre=genre
    )
    story.save()
    return story
```

### Segment Routes

```python
segment_router = APIRouter(prefix="/api/stories/{story_id}/segments", tags=["segments"])

@segment_router.get("/{segment_id}")
async def get_segment(story_id: str, segment_id: str) -> StorySegment:
    """Get a specific segment"""
    segment = StorySegment.load(story_id, segment_id, Story.load(story_id, story_id))
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment

@segment_router.get("/{segment_id}/choices")
async def get_segment_choices(story_id: str, segment_id: str) -> List[StoryChoice]:
    """Get choices for a segment"""
    story = Story.load(story_id, story_id)
    segment = story.get_segment(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return list(segment.outgoing_choices.values())
```

### Choice & Generation Routes

```python
choice_router = APIRouter(prefix="/api/stories/{story_id}/choices", tags=["choices"])

@choice_router.post("/{choice_id}/execute")
async def make_choice(
    story_id: str,
    choice_id: str,
    config: Config = Depends(lambda: Config.load())
) -> StorySegment:
    """Execute a choice and get the next segment"""
    story = Story.load(story_id, story_id)
    choice = story.get_choice(choice_id)
    
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")
    
    if choice.to_segment_id:
        # Navigate to existing segment
        return story.get_segment(choice.to_segment_id)
    else:
        # Generate new scene
        current_segment = story.get_segment(choice.from_segment_id)
        
        # Initialize generator based on config
        if config.generator.provider == "openrouter":
            generator = OpenRouterGenerator(...)
        else:
            generator = OpenAIGenerator(...)
        
        new_segment = await current_segment.generate_next_scene(
            choice,
            generator
        )
        new_segment.save()
        
        return new_segment

@choice_router.post("/{choice_id}/custom")
async def create_custom_choice(
    story_id: str,
    choice_id: str,
    custom_text: str,
    config: Config = Depends(lambda: Config.load())
) -> StorySegment:
    """Create a custom choice and generate next scene"""
    story = Story.load(story_id, story_id)
    current_segment = story.get_segment(...)
    
    # Create choice from custom text
    choice = StoryChoice(
        story=story,
        id=f"custom_{uuid.uuid4()}",
        from_segment_id=current_segment.id,
        to_segment_id=None,
        text=custom_text
    )
    
    # Generate next scene
    generator = ...  # Initialize
    new_segment = await current_segment.generate_next_scene(
        choice,
        generator
    )
    
    return new_segment
```

### State Management Routes

```python
state_router = APIRouter(prefix="/api/stories/{story_id}/state", tags=["state"])

@state_router.get("")
async def get_state(story_id: str) -> dict:
    """Get current game state"""
    runner = StoryRunner(Story.load(story_id, story_id))
    if runner.load_state():
        return {
            "current_segment_id": runner.current_segment.id,
            "visited_segments": list(runner.visited_segments)
        }
    return None

@state_router.post("")
async def save_state(story_id: str, current_segment_id: str) -> dict:
    """Save game state"""
    runner = StoryRunner(Story.load(story_id, story_id))
    runner.current_segment = runner.story.get_segment(current_segment_id)
    runner.save_state()
    return {"status": "saved"}

@state_router.delete("")
async def clear_state(story_id: str) -> dict:
    """Clear game state"""
    runner = StoryRunner(Story.load(story_id, story_id))
    runner.clear_state()
    return {"status": "cleared"}
```

---

## Error Handling

### Use Existing Error Handler
```python
from app.utils.error_handler import ErrorHandler, ErrorType, handle_api_error

try:
    # Some operation
    new_segment = await current_segment.generate_next_scene(choice, generator)
except Exception as e:
    error_type, technical_msg = handle_api_error(e)
    message, suggestion = ErrorHandler.handle_error(
        error_type,
        e,
        "Generating next scene"
    )
    raise HTTPException(
        status_code=500,
        detail=message
    )
```

### Custom HTTPException Handling
```python
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }
```

---

## Async Pattern Usage

All routes should be `async` to leverage StoryRunner's async capabilities:

```python
# Good
@router.get("/segment/{segment_id}")
async def get_segment(segment_id: str):
    return Story.load(...)

# Also works but less efficient
@router.get("/segment/{segment_id}")
def get_segment(segment_id: str):
    return Story.load(...)

# Required for generation
@router.post("/generate")
async def generate(choice_id: str):
    # Must be async because of await
    result = await segment.generate_next_scene(...)
    return result
```

---

## Database Considerations

### Current State
- Everything uses JSON file storage
- Pydantic models handle serialization

### Migration Path (Optional)
If you want to add database support:

1. **Keep Pydantic models** - they're perfect for serialization
2. **Add SQLAlchemy layer** in `app/models/database.py`
3. **Use StoryBase abstraction** - modify `save()` and `load()` methods
4. **Minimal changes** to existing code

Example approach:
```python
# In StoryBase.save()
def save(self):
    if USE_DATABASE:
        db.session.add(self)
        db.session.commit()
    else:
        # Existing JSON logic
        json.dump(...)
```

---

## Testing Routes

```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_stories():
    response = client.get("/api/stories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_story():
    response = client.get("/api/stories/veil_of_thornreach")
    assert response.status_code == 200
    assert response.json()["id"] == "veil_of_thornreach"

@pytest.mark.asyncio
async def test_generate_scene():
    response = client.post(
        "/api/stories/veil_of_thornreach/choices/choice_1/execute"
    )
    assert response.status_code == 200
    assert "short_description" in response.json()
```

---

## Environment for API

Update `.env` file:
```bash
# Existing
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-...
AI_MODEL=deepseek-v3

# New for API
FASTAPI_ENV=development
FASTAPI_DEBUG=true
FASTAPI_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
DATABASE_URL=sqlite:///./test.db  # Optional, if adding DB
```

---

## Deployment

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### With Docker
```dockerfile
FROM python:3.13

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## Summary

The existing backend is **well-structured** for API development:

✅ Models are Pydantic - drop into FastAPI responses  
✅ Async architecture - ready for concurrent requests  
✅ Generators are async - perfect for streaming endpoints  
✅ Storage abstracted - easy to add database layer  
✅ Error handling exists - extend for HTTP layer  

**Minimal changes needed** to expose existing functionality!

