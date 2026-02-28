# Dev 3: Backend Features - Phase 2 Integration Tasks

**Timeline**: Days 2-3 of Phase 2
**Priority**: High (already partially done)
**Status**: All Phase 1 work complete, ready for integration

---

## Executive Summary

Phase 2 focuses on **ensuring session/progress/reporting endpoints are fully integrated** into the main API and **working end-to-end with frontend**.

**Current Status**:
- ✅ Session management 100% complete
- ✅ Progress tracking 100% complete
- ✅ Content reporting 100% complete
- ✅ Auto-save system 100% complete
- ❌ Routes not yet integrated into main.py (waiting for Dev 1)

---

## Task 3.6: Verify Routes Are Integrated (1 hour)

**Once Dev 1 finishes Task 1.8**

### Check main.py has:

```python
# In backend/app/main.py should include:

from app.routes.sessions import router as sessions_router
from app.routes.progress import router as progress_router
from app.routes.reports import router as reports_router

app.include_router(sessions_router)
app.include_router(progress_router)
app.include_router(reports_router)
```

### If not there, tell Dev 1

If routes not in main.py:
1. Tell Dev 1 immediately
2. Your routes are ready in:
   - `app/routes/sessions.py`
   - `app/routes/progress.py`
   - `app/routes/reports.py`

### Success Criteria
- ✅ All 3 routers imported
- ✅ Server starts without errors
- ✅ Endpoints appear in API docs

---

## Task 3.7: Integration Testing with Frontend (3 hours)

**Once backend server running**

### Test Session Endpoints

```python
# tests/test_session_integration.py

def test_save_session():
    """Frontend saves session after choice"""
    response = client.post("/api/sessions/save", json={
        "story_id": "veil_of_thornreach",
        "current_segment_id": "segment_002",
        "visited_segments": ["segment_001", "segment_002"],
        "scene_counter": 2,
        "start_time": "2024-02-28T14:00:00Z"
    })
    assert response.status_code == 200

def test_load_session():
    """Frontend loads saved session"""
    response = client.get("/api/sessions/veil_of_thornreach")
    assert response.status_code == 200
    assert response.json()["session"]["current_segment_id"] == "segment_002"

def test_resume_game():
    """Frontend resumes from saved session"""
    # 1. Save session
    client.post("/api/sessions/save", json={...})
    
    # 2. Load it back
    response = client.get("/api/sessions/veil_of_thornreach")
    
    # 3. Verify can navigate from that position
    assert response.json()["session"]["current_segment_id"] == "segment_002"
```

### Test Progress Endpoints

```python
def test_get_progress():
    """Get story progress info"""
    response = client.get("/api/progress/veil_of_thornreach")
    assert response.status_code == 200
    
    progress = response.json()["progress"]
    assert "scene_counter" in progress
    assert "elapsed_time" in progress
    assert "start_date" in progress
```

### Test Report Endpoints

```python
def test_submit_report():
    """Submit inappropriate content report"""
    response = client.post("/api/reports", json={
        "story_id": "veil_of_thornreach",
        "segment_id": "segment_001",
        "report_type": "inappropriate_content",
        "description": "Offensive language",
        "reporter_email": "user@example.com"
    })
    assert response.status_code == 201
    assert "report_id" in response.json()

def test_get_reports():
    """Admin retrieves all reports"""
    response = client.get("/api/reports")
    assert response.status_code == 200
    assert isinstance(response.json()["reports"], list)
```

### Manual Testing

```bash
# 1. Save a session
curl -X POST http://localhost:8000/api/sessions/save \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "veil_of_thornreach",
    "current_segment_id": "segment_002",
    "visited_segments": ["segment_001", "segment_002"],
    "scene_counter": 2,
    "start_time": "2024-02-28T14:00:00Z"
  }'

# 2. Load it back
curl http://localhost:8000/api/sessions/veil_of_thornreach

# 3. Get progress
curl http://localhost:8000/api/progress/veil_of_thornreach

# 4. Submit a report
curl -X POST http://localhost:8000/api/reports \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "veil_of_thornreach",
    "segment_id": "segment_001",
    "report_type": "inappropriate_content",
    "description": "Test report",
    "reporter_email": "test@example.com"
  }'
```

### Success Criteria
- ✅ Sessions save correctly
- ✅ Sessions load correctly
- ✅ Progress data accurate
- ✅ Reports submitted
- ✅ All manual tests pass

---

## Task 3.8: Auto-Save Integration (2 hours)

**Coordinate with Dev 1 on generation endpoint**

When Dev 1 creates POST /api/segments/{id}/next endpoint:

### Auto-save should trigger after:

1. **Successful choice navigation**
   ```python
   @router.post("/api/segments/{segment_id}/choice/{choice_id}")
   async def select_choice(segment_id: str, choice_id: str):
       # Navigate to segment
       # Then auto-save
       auto_save_manager.save_session(...)
   ```

2. **Successful custom choice generation**
   ```python
   @router.post("/api/segments/{segment_id}/next")
   async def generate_next_scene(segment_id: str):
       # Generate scene
       # Then auto-save
       auto_save_manager.save_session(...)
   ```

### Verify auto-save working

```python
def test_auto_save_after_choice():
    """Session auto-saves after selecting choice"""
    # 1. Get initial segment
    response = client.get("/api/segments/segment_001?story_id=veil_of_thornreach")
    
    # 2. Select a choice
    # (This should trigger auto-save)
    
    # 3. Check session was saved
    response = client.get("/api/sessions/veil_of_thornreach")
    assert response.json()["session"]["current_segment_id"] == "segment_002"
```

### Success Criteria
- ✅ Sessions saved after choices
- ✅ Auto-save transparent to frontend
- ✅ Progress tracked automatically

---

## Task 3.9: Error Scenarios & Edge Cases (2 hours)

### Handle these scenarios:

1. **User tries to load non-existent session**
   ```python
   GET /api/sessions/never_started_story
   # Should return 404 or { "found": false }
   ```

2. **Session data corrupted**
   ```python
   # If session JSON invalid, should reset gracefully
   # Not crash the server
   ```

3. **Concurrent access**
   ```python
   # Multiple API calls at same time
   # Should handle safely
   ```

4. **Missing required fields in report**
   ```python
   POST /api/reports
   # Missing "description" field?
   # Should return 400 with clear error
   ```

### Tests

```python
def test_nonexistent_session():
    """Loading non-existent session returns proper response"""
    response = client.get("/api/sessions/story_that_never_existed")
    assert response.status_code == 404 or response.json()["found"] == False

def test_invalid_report_missing_field():
    """Report without required field rejected"""
    response = client.post("/api/reports", json={
        "story_id": "veil_of_thornreach",
        # missing "segment_id"
        "report_type": "inappropriate_content"
    })
    assert response.status_code == 400

def test_concurrent_sessions():
    """Multiple concurrent saves handled safely"""
    # Save from two sources quickly
    # Should not corrupt data
    pass
```

### Success Criteria
- ✅ All error scenarios handled
- ✅ Clear error messages
- ✅ No crashes
- ✅ Data integrity maintained

---

## Task 3.10: End-to-End Game Flow Testing (2 hours)

**Full playthrough with real backend**

### Test complete game flow

```python
def test_complete_game_flow():
    """Play through entire story sequence"""
    story_id = "veil_of_thornreach"
    
    # 1. Get story details
    response = client.get(f"/api/stories/{story_id}")
    assert response.status_code == 200
    start_segment_id = response.json()["start_segment_id"]
    
    # 2. Load first segment
    response = client.get(f"/api/segments/{start_segment_id}?story_id={story_id}")
    assert response.status_code == 200
    
    # 3. Save initial session
    response = client.post("/api/sessions/save", json={
        "story_id": story_id,
        "current_segment_id": start_segment_id,
        "visited_segments": [start_segment_id],
        "scene_counter": 1,
        "start_time": datetime.now(UTC).isoformat()
    })
    assert response.status_code == 200
    
    # 4. Make a choice (navigate)
    # (Will depend on what choices exist)
    
    # 5. Check session updated
    response = client.get(f"/api/sessions/{story_id}")
    assert response.status_code == 200
    assert response.json()["session"]["scene_counter"] == 2
    
    # 6. Get progress
    response = client.get(f"/api/progress/{story_id}")
    assert response.status_code == 200
    
    # 7. Submit report
    response = client.post("/api/reports", json={
        "story_id": story_id,
        "segment_id": start_segment_id,
        "report_type": "inappropriate_content",
        "description": "Test report",
        "reporter_email": "test@example.com"
    })
    assert response.status_code == 201
```

### Success Criteria
- ✅ Full game flow works
- ✅ Sessions persist
- ✅ Progress tracked
- ✅ Reports submitted
- ✅ No errors throughout

---

## Daily Breakdown

### Day 1
- [ ] Review your Phase 1 code
- [ ] Verify endpoints created correctly
- [ ] Wait for Dev 1 to integrate routes

### Day 2
- [ ] Task 3.6: Verify integration (1h)
- [ ] Task 3.7: Integration testing (3h)
- [ ] Fix any issues

### Day 3
- [ ] Task 3.8: Auto-save integration (2h)
- [ ] Task 3.9: Error scenarios (2h)
- [ ] Task 3.10: End-to-end testing (2h)

---

## Commits

```bash
[DEV-3] verify all routes integrated into main.py
[DEV-3] add comprehensive integration tests
[DEV-3] verify auto-save triggers correctly
[DEV-3] handle error scenarios and edge cases
[DEV-3] complete end-to-end testing
```

---

## Success Criteria

- ✅ All endpoints working
- ✅ Sessions persisting
- ✅ Progress tracked
- ✅ Reports submitted
- ✅ Auto-save transparent to user
- ✅ No errors or crashes
- ✅ Full game flow tested

---

## Dependencies

**Waits for**:
- Dev 1: Route integration + segment navigation

**Unblocks**:
- Dev 4: Can save/load games
- Full MVP gameplay

You're the backbone of the user experience! 💪
