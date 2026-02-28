# Dev 1: Backend API - Phase 2 Integration Tasks

**Timeline**: Day 1-2 of Phase 2
**Priority**: CRITICAL PATH
**Blocker Status**: Current work blocked by merge conflict in main.py

---

## Executive Summary

Phase 2 focuses on **fixing the merge conflict** and **fully integrating all API routes** into the running FastAPI server so the frontend can connect and start using real data.

**Current Status**: 
- ✅ FastAPI structure created
- ✅ Core routes implemented (sessions.py, progress.py, reports.py)
- ❌ main.py has merge conflict
- ❌ Routes not integrated into main FastAPI app
- ❌ API server not functional

---

## Task 1.7: Fix main.py Merge Conflict (CRITICAL - 2 hours)

**Blocker for**: Everything else

### What happened
Two versions of main.py were merged together with conflict markers:
```
<<<<<<< HEAD
# Version A (simpler)
=======
# Version B (more complete)
>>>>>>> origin/master
```

### What you need to do

1. **Read the current main.py**
   - `backend/app/main.py` currently has conflict markers
   - Understand both versions

2. **Choose and clean up**
   - Option A: Use origin/master version (more structured, more fields)
   - Option B: Use HEAD version (simpler, cleaner)
   - **Recommendation**: Use origin/master (version B) - it has better error handling

3. **Remove conflict markers**
   - Delete `<<<<<<< HEAD`, `=======`, `>>>>>>> origin/master`
   - Keep only ONE version

4. **Test it works**
   ```bash
   python -c "from app.main import app; print('✅ main.py imports successfully')"
   ```

### Success Criteria
- ✅ No more conflict markers in file
- ✅ File imports without errors
- ✅ Can start server: `python -m uvicorn app.main:app --reload`

---

## Task 1.8: Integrate All Routes into main.py (CRITICAL - 3 hours)

**After fixing merge conflict**

### What you need to do

In `backend/app/main.py`, after the app initialization, add these route imports:

```python
# After CORS setup, add:

from app.routes.sessions import router as sessions_router
from app.routes.progress import router as progress_router
from app.routes.reports import router as reports_router

# Include routers
app.include_router(sessions_router)
app.include_router(progress_router)
app.include_router(reports_router)
```

### Routes to integrate

**From dev3-backend-features (already created):**

1. **sessions.py** - Session management
   - POST /api/sessions/save
   - GET /api/sessions/{story_id}
   - DELETE /api/sessions/{story_id}

2. **progress.py** - Progress tracking
   - GET /api/progress/{story_id}
   - POST /api/progress (optional)

3. **reports.py** - Content reporting
   - POST /api/reports
   - GET /api/reports (admin)
   - PUT /api/reports/{report_id} (admin)

### Create missing core routes

You still need to create endpoints for:

```python
# Create: app/routes/stories.py

@router.get("/stories")
async def list_stories():
    """List all available stories"""
    # Load from .infinite_story_data/
    pass

@router.get("/stories/{story_id}")
async def get_story(story_id: str):
    """Get story details + start segment"""
    pass

@router.get("/segments/{segment_id}")
async def get_segment(segment_id: str, story_id: str):
    """Get segment + choices"""
    pass

@router.post("/segments/{segment_id}/next")
async def generate_next_scene(segment_id: str, request: GenerateSceneRequest):
    """Generate next scene from choice"""
    pass
```

### Success Criteria
- ✅ All 3 route files imported in main.py
- ✅ New stories.py route file created
- ✅ Server starts: `python -m uvicorn app.main:app --reload`
- ✅ API docs work: http://localhost:8000/api/docs
- ✅ All endpoints listed in docs

---

## Task 1.9: Create Story/Segment Endpoints (5 hours)

**After routes integrated**

### Endpoints to implement

#### GET /api/stories
```python
@router.get("/stories")
async def list_stories():
    """List all available stories"""
    try:
        # Load all stories from .infinite_story_data/
        # Return list with basic metadata
        return {
            "success": True,
            "stories": [...]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}, 500
```

Files to load from:
- `.infinite_story_data/{story_id}/story/{story_id}.json`

#### GET /api/stories/{story_id}
```python
@router.get("/stories/{story_id}")
async def get_story_detail(story_id: str):
    """Get story + start segment + characters + locations"""
    # Load story
    # Load start segment
    # Load all characters
    # Load all locations
    # Return combined response
```

#### GET /api/segments/{segment_id}
```python
@router.get("/segments/{segment_id}")
async def get_segment(segment_id: str, story_id: str):
    """Get segment content + choices"""
    # Load segment
    # Load associated choices
    # Split top 2 vs all
    # Calculate scene counter
    # Return response
```

#### POST /api/segments/{segment_id}/next
```python
@router.post("/segments/{segment_id}/next")
async def generate_next_scene(segment_id: str, request: GenerateSceneRequest):
    """
    Generate next scene from custom choice
    
    This is the AI generation endpoint - leave for Phase 2.5
    For now, return error: "AI generation not yet implemented"
    """
    return {
        "success": False,
        "error": "AI generation endpoint coming in Phase 2.5"
    }, 501
```

### Key utilities needed

Create `backend/app/utils/story_loader.py`:

```python
from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_choice import StoryChoice

class StoryLoader:
    @staticmethod
    def list_all_stories() -> List[Story]:
        """Load all stories from disk"""
        pass
    
    @staticmethod
    def load_story(story_id: str) -> Story:
        """Load single story"""
        pass
    
    @staticmethod
    def load_segment(story_id: str, segment_id: str) -> StorySegment:
        """Load segment with choices"""
        pass
    
    @staticmethod
    def load_choices_for_segment(story_id: str, segment_id: str) -> List[StoryChoice]:
        """Load all choices for a segment"""
        pass
```

### Success Criteria
- ✅ All 4 endpoints implemented
- ✅ Can list stories from disk
- ✅ Can load story details
- ✅ Can load segments and choices
- ✅ API docs show all endpoints
- ✅ Frontend can call endpoints

---

## Task 1.10: Add Error Handling & Response Formatting (2 hours)

**Throughout integration**

### Standard response format

```python
# All success responses
{
    "success": true,
    "data": { ... },
    "error": null,
    "timestamp": "2024-02-28T10:30:00Z"
}

# All error responses
{
    "success": false,
    "data": null,
    "error": "Error message",
    "timestamp": "2024-02-28T10:30:00Z"
}
```

Use the existing `response_formatter.py` for this.

### Error codes
- 400: Bad request
- 404: Not found
- 500: Server error

### Success Criteria
- ✅ All responses follow format
- ✅ Proper HTTP status codes
- ✅ Helpful error messages
- ✅ No unhandled exceptions

---

## Task 1.11: Test All Endpoints (2 hours)

**Before frontend integration**

### Manual testing

```bash
# 1. Start server
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload

# 2. Test endpoints
curl http://localhost:8000/api/stories
curl http://localhost:8000/api/stories/veil_of_thornreach
curl "http://localhost:8000/api/segments/opening_scene?story_id=veil_of_thornreach"

# 3. Check API docs
# Visit: http://localhost:8000/api/docs
```

### Write integration tests

```python
# tests/test_api_endpoints_integration.py

def test_list_stories():
    response = client.get("/api/stories")
    assert response.status_code == 200
    assert "stories" in response.json()

def test_get_story():
    response = client.get("/api/stories/veil_of_thornreach")
    assert response.status_code == 200
    assert response.json()["id"] == "veil_of_thornreach"

def test_get_segment():
    response = client.get("/api/segments/opening_scene?story_id=veil_of_thornreach")
    assert response.status_code == 200
    assert "segment" in response.json()
    assert "choices" in response.json()
```

### Success Criteria
- ✅ All endpoints return 200 OK
- ✅ Responses match API_CONTRACTS.md
- ✅ Integration tests passing
- ✅ API docs page loads correctly

---

## Daily Breakdown

### Day 1
- [ ] Task 1.7: Fix merge conflict (2h)
- [ ] Task 1.8: Integrate routes (3h)
- [ ] Task 1.9: Create story endpoints (start, 5h)

### Day 2
- [ ] Task 1.9: Finish story endpoints (5h)
- [ ] Task 1.10: Error handling (2h)
- [ ] Task 1.11: Testing (2h)
- [ ] Verify server runs: `python -m uvicorn app.main:app --reload` ✅

---

## Commits

```bash
[DEV-1] fix main.py merge conflict - use origin/master version
[DEV-1] integrate session, progress, and report routes
[DEV-1] add stories and segments route file
[DEV-1] implement list stories and get story detail endpoints
[DEV-1] implement segment and choices endpoints
[DEV-1] add error handling and response formatting
[DEV-1] add integration tests for all endpoints
```

---

## Blocking Dev 4

Frontend can't connect to real API until:
- ✅ main.py merge conflict fixed
- ✅ All routes integrated into main.py
- ✅ Server starts and runs
- ✅ API endpoints respond with correct data

Once this is done, Dev 4 changes `USE_MOCK = false` and frontend connects to real backend!

---

## Files to modify/create

**Modify:**
- `backend/app/main.py` - fix conflict + add route imports

**Create:**
- `backend/app/routes/stories.py` - story/segment endpoints
- `backend/app/utils/story_loader.py` - disk loading utilities
- `backend/tests/test_api_endpoints_integration.py` - integration tests

**Reference:**
- `backend/app/routes/sessions.py` - already created
- `backend/app/routes/progress.py` - already created
- `backend/app/routes/reports.py` - already created
- `backend/app/utils/response_formatter.py` - already exists

---

## Success = Frontend Works

When this is complete:
1. Backend server running on http://localhost:8000
2. All API endpoints functional
3. Frontend can switch to real API
4. Full end-to-end story playback works!

Good luck! This unblocks the entire project. 🚀
