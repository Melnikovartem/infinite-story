# Dev 1: Backend API - Detailed Task Breakdown

**Total Hours**: 80 (16 hours/day × 5 days)
**Timeline**: Week 1
**Critical Path**: Yes

---

## Task 1.1: FastAPI Project Setup (12 hours)

**Day 1 Morning - Estimated 4 hours**

### What You're Building
Set up a professional FastAPI project structure with proper configuration, error handling, and development tooling.

### Subtasks

#### 1.1.1: Create FastAPI Application Structure (1.5 hours)
- [ ] Create `backend/app/main.py` with FastAPI app initialization
- [ ] Set up CORS middleware (allow all origins for MVP)
- [ ] Create `backend/app/__init__.py`
- [ ] Create `backend/app/config.py` for environment configuration
- [ ] Load environment variables from `.env`

**Code skeleton**:
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Infinite Story Engine",
    description="AI-powered interactive storytelling",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
```

#### 1.1.2: Set Up Dependencies (1 hour)
- [ ] Update `backend/requirements.txt` with FastAPI, Uvicorn, Pydantic
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify installation: `python -c "import fastapi; print(fastapi.__version__)"`
- [ ] Create `backend/pyproject.toml` for modern Python packaging

#### 1.1.3: Environment Configuration (1 hour)
- [ ] Create `backend/.env.example` with all required vars
- [ ] Create `backend/.env` (local, not committed)
- [ ] Load via `python-dotenv` in `config.py`
- [ ] Define Settings class with Pydantic

**Example**:
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Infinite Story Engine"
    debug: bool = True
    api_base_url: str = "http://localhost:8000"
    data_dir: str = ".infinite_story_data"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 1.1.4: Test FastAPI Server Startup (0.5 hours)
- [ ] Run `uvicorn app.main:app --reload` from `backend/` directory
- [ ] Verify server starts on http://localhost:8000
- [ ] Verify `/api/health` endpoint works
- [ ] Create basic test for server startup

**Test example**:
```python
# tests/test_api_basic.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

#### 1.1.5: Set Up Project Structure (1 hour)
- [ ] Create `backend/app/api/` directory
- [ ] Create `backend/app/services/` directory
- [ ] Create `backend/app/utils/` directory
- [ ] Create `__init__.py` files in each
- [ ] Create `backend/tests/` if not exists
- [ ] Create `.gitignore` entries for `__pycache__`, `.env`, `*.pyc`

#### 1.1.6: Create Base Response Model (1.5 hours)
- [ ] Create `backend/app/utils/response_formatter.py`
- [ ] Define response models for success/error
- [ ] Create helper functions for consistent responses
- [ ] Document response format

**Example**:
```python
# app/utils/response_formatter.py
from typing import Any, Optional
from pydantic import BaseModel

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

def success_response(data: Any) -> dict:
    from datetime import datetime
    return {
        "success": True,
        "data": data,
        "error": None,
        "timestamp": datetime.utcnow().isoformat()
    }

def error_response(error: str) -> dict:
    from datetime import datetime
    return {
        "success": False,
        "data": None,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## Task 1.2: Pydantic Data Models (14 hours)

**Days 1-2 - Estimated 14 hours**

### What You're Building
Extend existing Pydantic models (or create new ones) for all story components. These models handle validation and serialization.

### Subtasks

#### 1.2.1: Create API Request/Response Models (4 hours)
- [ ] Create `backend/app/api/models.py` for request/response schemas
- [ ] Define `StoryListResponse`, `StoryDetailResponse`
- [ ] Define `SegmentResponse`, `ChoiceResponse`
- [ ] Define `SessionStateRequest`, `SessionStateResponse`
- [ ] Define `GenerateSceneRequest`, `GenerateSceneResponse`
- [ ] Add examples to each model
- [ ] Write tests for model validation

**Example**:
```python
# app/api/models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class StoryResponse(BaseModel):
    id: str
    title: str
    description: str
    author: str
    start_segment_id: str
    created_at: datetime

class ChoiceResponse(BaseModel):
    id: str
    choice_text: str
    popularity_score: int
    is_custom: bool

class SegmentResponse(BaseModel):
    id: str
    title: str
    content: str
    text_blocks: List[dict]
    character_states: dict
    location_state: dict
    is_generated: bool
    created_at: datetime
    word_count: int
```

#### 1.2.2: Extend Story Model Classes (4 hours)
- [ ] Review existing `app/models/story.py`
- [ ] Add any missing fields to `Story` class
- [ ] Add `to_dict()` and `from_dict()` methods if not present
- [ ] Ensure all models use Pydantic with validation
- [ ] Add type hints to all fields
- [ ] Document each field with docstrings

#### 1.2.3: Ensure Model Serialization (3 hours)
- [ ] Test saving Story to JSON
- [ ] Test loading Story from JSON
- [ ] Handle circular references (exclude StoryBlocks from Story)
- [ ] Create comprehensive serialization tests
- [ ] Verify `.infinite_story_data/` file structure is created correctly

**Test example**:
```python
# tests/test_model_serialization.py
from app.models.story import Story
from app.models.story_segment import StorySegment

def test_story_serialization():
    story = Story(id="test", title="Test", author="Test Author")
    story.save()
    
    loaded = Story.load("test", "test")
    assert loaded.id == story.id
    assert loaded.title == story.title
```

#### 1.2.4: Create TextBlock Type System (3 hours)
- [ ] Define TextBlock type enum (NARRATOR, DIALOGUE, etc.)
- [ ] Create TextBlock model with type-specific fields
- [ ] Add validation for required fields by type
- [ ] Write tests for each TextBlock type
- [ ] Document in code comments

---

## Task 1.3: Core API Endpoints (20 hours)

**Days 2-3 - Estimated 20 hours**

### What You're Building
Implement the 8 main API endpoints that the frontend will call.

### Subtasks

#### 1.3.1: List Stories Endpoint (2 hours)
- [ ] Create `GET /api/stories` endpoint
- [ ] Load all stories from `.infinite_story_data/`
- [ ] Return list with basic metadata
- [ ] Handle no stories case
- [ ] Write integration test
- [ ] Document endpoint (docstring, parameters, responses)

**Implementation**:
```python
# app/api/routes.py
from fastapi import APIRouter, HTTPException
from app.utils.response_formatter import success_response, error_response
from app.models.story import Story

router = APIRouter(prefix="/api")

@router.get("/stories")
async def list_stories():
    """
    Get all available stories.
    
    Returns:
        List of stories with basic metadata
    """
    try:
        stories = Story.list_all("")  # Or however you list them
        return success_response(stories)
    except Exception as e:
        return error_response(str(e)), 500
```

#### 1.3.2: Get Story Details Endpoint (3 hours)
- [ ] Create `GET /api/stories/{story_id}` endpoint
- [ ] Load story and start segment
- [ ] Return story metadata + start segment content
- [ ] Load associated characters and locations
- [ ] Handle story not found error
- [ ] Write integration test

#### 1.3.3: Get Segment Endpoint (3 hours)
- [ ] Create `GET /api/segments/{segment_id}?story_id={story_id}` endpoint
- [ ] Load segment from file
- [ ] Load associated choices
- [ ] Format top 2 choices separately from all choices
- [ ] Calculate scene counter (elapsed time since session start)
- [ ] Write integration test

#### 1.3.4: Navigate to Choice Endpoint (2 hours)
- [ ] Create `POST /api/segments/{segment_id}/choice/{choice_id}` endpoint
- [ ] Validate segment and choice exist
- [ ] Check if choice has destination (to_segment_id)
- [ ] Load destination segment if it exists
- [ ] Return segment or error
- [ ] Write integration test

#### 1.3.5: Session Save/Load Endpoints (4 hours)
- [ ] Create `POST /api/sessions/save` endpoint
- [ ] Create `GET /api/sessions/{story_id}` endpoint
- [ ] Create `DELETE /api/sessions/{story_id}` endpoint
- [ ] Store session state in `.infinite_story_data/{story_id}/runner_state.json`
- [ ] Parse request/response correctly
- [ ] Handle missing sessions gracefully
- [ ] Write tests for all three

#### 1.3.6: Report Content Endpoint (2 hours)
- [ ] Create `POST /api/reports` endpoint
- [ ] Store reports in `.infinite_story_data/reports/`
- [ ] Validate report type
- [ ] Generate report ID
- [ ] Return success response
- [ ] Write test

#### 1.3.7: Health/Status Endpoints (2 hours)
- [ ] Ensure `/api/health` endpoint exists
- [ ] Create `GET /api/status` with server info
- [ ] Create error handler middleware
- [ ] Test 404 handling
- [ ] Test error response format

---

## Task 1.4: AI Generation Integration (20 hours)

**Days 3-4 - Estimated 20 hours**

### What You're Building
Integrate with TextGenerator (OpenRouter API) to generate next scenes from custom choices.

### Subtasks

#### 1.4.1: Create Scene Generation Service (6 hours)
- [ ] Create `backend/app/services/generation_service.py`
- [ ] Implement context building function:
  - Get previous 5-10 segments
  - Get character states
  - Get location state
  - Get worldbuilding (StoryContext)
  - Combine with choice text
- [ ] Write tests for context building
- [ ] Document context structure

**Example**:
```python
# app/services/generation_service.py
from typing import Dict, List
from app.models.story_segment import StorySegment
from app.models.story_context import StoryContext

class SceneGenerationService:
    
    @staticmethod
    def build_context(
        story_id: str,
        from_segment_id: str,
        choice_text: str,
        previous_segments_count: int = 5
    ) -> Dict[str, str]:
        """Build context for AI generation."""
        # Get previous segments
        previous_segs = StorySegment.get_story_segments_before(
            story_id, from_segment_id, previous_segments_count
        )
        
        # Get current segment
        current_seg = StorySegment.load(story_id, from_segment_id)
        
        # Get worldbuilding
        context = StoryContext.load(story_id, "world_rules")
        
        # Build prompt
        return {
            "story_context": context.get_full_overview(),
            "previous_segments": [s.get_full_overview() for s in previous_segs],
            "current_segment": current_seg.get_full_overview(),
            "character_states": current_seg.character_states,
            "location_state": current_seg.location_state,
            "player_choice": choice_text
        }
```

#### 1.4.2: Implement Generate Next Scene Endpoint (8 hours)
- [ ] Create `POST /api/segments/{segment_id}/next` endpoint
- [ ] Accept choice_text and context options
- [ ] Build context using SceneGenerationService
- [ ] Call TextGenerator.generate()
- [ ] Parse response into SceneTextGeneratorResponse
- [ ] Create new StorySegment from response
- [ ] Create 2 new StoryChoice objects
- [ ] Save everything to disk
- [ ] Return new segment and choices
- [ ] Handle generation errors gracefully
- [ ] Write integration test

**Endpoint**:
```python
@router.post("/segments/{segment_id}/next")
async def generate_next_scene(
    segment_id: str,
    request: GenerateSceneRequest  # Has story_id, choice_text, context options
):
    """
    Generate next scene from a custom player choice.
    
    This endpoint:
    1. Builds context from previous segments
    2. Calls AI to generate next scene
    3. Creates new segment and choices
    4. Saves to disk
    5. Returns the new segment
    """
    try:
        # Build context
        context = SceneGenerationService.build_context(
            request.story_id,
            segment_id,
            request.choice_text,
            request.context.previous_segments_count
        )
        
        # Generate
        response = await TextGenerator.generate(context)
        
        # Create segment and choices
        new_segment = StorySegment.create_from_generation(...)
        new_choices = [...]
        
        return success_response({
            "new_segment": new_segment.to_dict(),
            "new_choices": [c.to_dict() for c in new_choices]
        })
    except Exception as e:
        return error_response(str(e)), 500
```

#### 1.4.3: Add Character/Location State Management (4 hours)
- [ ] Update character_states in new segment
- [ ] Update location_state in new segment
- [ ] Accumulate character running_status history
- [ ] Accumulate location running_status history
- [ ] Write tests for state updates

#### 1.4.4: Error Handling and Retry Logic (2 hours)
- [ ] Handle OpenRouter API timeouts
- [ ] Handle parsing errors from AI response
- [ ] Implement retry logic (3 attempts)
- [ ] Log all generation attempts
- [ ] Return meaningful error messages to frontend

---

## Task 1.5: Testing & Documentation (14 hours)

**Day 4-5 - Estimated 14 hours**

### What You're Building
Comprehensive tests for all endpoints and complete API documentation.

### Subtasks

#### 1.5.1: Write API Endpoint Tests (6 hours)
- [ ] Test each endpoint with valid input
- [ ] Test error cases (404, 400, 500)
- [ ] Test with real stories from `.infinite_story_data/`
- [ ] Test session save/load cycle
- [ ] Test generation endpoint with mocked AI
- [ ] Achieve 80%+ code coverage
- [ ] Mock TextGenerator to avoid API calls in tests

**Test structure**:
```python
# tests/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture
def mock_generator(monkeypatch):
    def mock_generate(*args, **kwargs):
        return SceneTextGeneratorResponse(...)
    monkeypatch.setattr("app.services.generation_service.TextGenerator.generate", mock_generate)

def test_list_stories():
    response = client.get("/api/stories")
    assert response.status_code == 200
    assert "stories" in response.json()

def test_generate_scene(mock_generator):
    response = client.post(
        "/api/segments/segment_001/next",
        json={"story_id": "veil_of_thornreach", "choice_text": "..."}
    )
    assert response.status_code == 201
    assert "new_segment" in response.json()
```

#### 1.5.2: Write Service Tests (3 hours)
- [ ] Test context building (various segment counts)
- [ ] Test session save/load
- [ ] Test file I/O operations
- [ ] Test error handling
- [ ] Use fixtures for test data

#### 1.5.3: Create API Documentation (3 hours)
- [ ] Add docstrings to all endpoints
- [ ] Include examples in docstrings
- [ ] Verify FastAPI auto-docs work at `/docs`
- [ ] Document status codes
- [ ] Document error responses

#### 1.5.4: Performance & Optimization (2 hours)
- [ ] Identify slow queries/loads
- [ ] Add caching where appropriate
- [ ] Optimize file I/O
- [ ] Benchmark common operations
- [ ] Document performance notes

---

## Task 1.6: Final Integration & Handoff (2 hours)

**Day 5 - Estimated 2 hours**

### Subtasks
- [ ] Run full test suite: `python -m pytest tests/ -v --cov=app`
- [ ] Fix any failing tests
- [ ] Ensure all endpoints documented
- [ ] Create summary of what's implemented
- [ ] Prepare handoff notes for Dev 2 & Dev 3
- [ ] Merge to master and create branch for next phase

---

## Daily Checklist

### Day 1
- [ ] Task 1.1.1-1.1.6: FastAPI setup complete
- [ ] Server runs on localhost:8000
- [ ] `/api/health` endpoint works
- [ ] 4-6 hours of work logged

### Day 2
- [ ] Task 1.2.1-1.2.4: Models complete
- [ ] All models have tests
- [ ] Models serialize/deserialize correctly
- [ ] 14 hours of work completed (cumulative ~18)

### Day 3
- [ ] Task 1.3.1-1.3.7: Core endpoints implemented
- [ ] All endpoints return proper responses
- [ ] 7-8 endpoints working (missing generation)
- [ ] 20 hours of work completed (cumulative ~38)

### Day 4
- [ ] Task 1.4.1-1.4.4: AI generation integrated
- [ ] Generate next scene endpoint working
- [ ] Context building working
- [ ] Character/location state updating
- [ ] 20 hours of work completed (cumulative ~58)

### Day 5
- [ ] Task 1.5 & 1.6: Tests, docs, final polish
- [ ] 80%+ test coverage
- [ ] All endpoints documented
- [ ] Ready for Dev 2 & Dev 3 integration
- [ ] 22 hours of work completed (cumulative 80)

---

## Commit Strategy

Commit frequently with proper messages:

```bash
# Day 1
[DEV-1] init fastapi project structure
[DEV-1] add cors middleware and health endpoint
[DEV-1] create environment configuration

# Day 2
[DEV-1] add pydantic models for api requests/responses
[DEV-1] extend story models with serialization
[DEV-1] add textblock type system

# Day 3
[DEV-1] implement list stories endpoint
[DEV-1] implement get story details endpoint
[DEV-1] implement get segment endpoint
[DEV-1] implement session endpoints

# Day 4
[DEV-1] create scene generation service
[DEV-1] implement generate next scene endpoint
[DEV-1] add character/location state management

# Day 5
[DEV-1] add comprehensive api tests
[DEV-1] add service tests
[DEV-1] add api documentation
```

---

## Success!

When Dev 1 is done:
- Backend API fully functional
- All endpoints tested and documented
- Dev 2 can start character work
- Dev 3 can integrate state persistence
- Dev 4 can start connecting frontend to real APIs
- Timeline on track for MVP

Estimated completion: **Friday evening, Week 1**

Good luck! 🚀
