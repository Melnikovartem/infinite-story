# Dev 3: Backend Features - Detailed Task Breakdown

**Total Hours**: 85 (17 hours/day × 5 days)
**Timeline**: Week 1-2
**Start**: Day 1 (no blockers!)

---

## Task 3.1: Session Management System (30 hours)

**Days 1-3 - Estimated 30 hours**

### What You're Building
Complete session persistence system for saving/loading player progress.

### Subtasks

#### 3.1.1: Session State Model (4 hours)
- [ ] Create SessionState model (story_id, current_segment_id, visited_segments, etc.)
- [ ] Add validation (segment exists, visited list is valid)
- [ ] Add to_dict() and from_dict() methods
- [ ] Write tests for model

**Example**:
```python
class SessionState(BaseModel):
    story_id: str
    current_segment_id: str
    visited_segments: List[str]
    scene_counter: int
    start_time: datetime
    last_updated: datetime
```

#### 3.1.2: Save Session Endpoint (5 hours)
- [ ] Implement POST /api/sessions/save
- [ ] Accept SessionState in request
- [ ] Save to `.infinite_story_data/{story_id}/runner_state.json`
- [ ] Return success response with timestamp
- [ ] Handle file I/O errors gracefully
- [ ] Write tests

#### 3.1.3: Load Session Endpoint (5 hours)
- [ ] Implement GET /api/sessions/{story_id}
- [ ] Load from runner_state.json
- [ ] Handle missing session (return 404 or null)
- [ ] Return complete session state
- [ ] Validate loaded state is coherent
- [ ] Write tests

#### 3.1.4: Delete Session Endpoint (3 hours)
- [ ] Implement DELETE /api/sessions/{story_id}
- [ ] Remove runner_state.json from disk
- [ ] Return success/not found response
- [ ] Write tests

#### 3.1.5: Session Validation & Recovery (5 hours)
- [ ] Validate loaded session (segments exist, story exists)
- [ ] Handle corrupted sessions (missing file, invalid JSON)
- [ ] Implement recovery (reset to start segment)
- [ ] Log all session operations
- [ ] Write tests for edge cases

#### 3.1.6: Auto-Load on Story Start (3 hours)
- [ ] Modify GET /api/stories/{story_id} to check for saved session
- [ ] Return session info if exists
- [ ] Let frontend decide to resume or start fresh
- [ ] Write tests

---

## Task 3.2: Progress Tracking System (20 hours)

**Days 2-3 - Estimated 20 hours**

### What You're Building
System to track player progress through the story.

### Subtasks

#### 3.2.1: Scene Counter Model (3 hours)
- [ ] Create SceneCounter model
- [ ] Fields: scene_number (current), total_visited, start_time, elapsed_seconds
- [ ] Add calculation methods (elapsed time, reading pace)
- [ ] Write tests

**Example**:
```python
class SceneCounter(BaseModel):
    scene_number: int
    start_time: datetime
    elapsed_seconds: int
    
    def elapsed_formatted(self) -> str:
        # Return "2h 15m"
        pass
```

#### 3.2.2: Progress Calculation (5 hours)
- [ ] Implement scene counter calculation
- [ ] Count segments visited in order
- [ ] Track elapsed time
- [ ] Estimate story progress (if known total)
- [ ] Write tests

#### 3.2.3: Progress Persistence (5 hours)
- [ ] Save progress with session state
- [ ] Load progress when resuming
- [ ] Update progress after each move/generation
- [ ] Handle time calculation correctly
- [ ] Write tests

#### 3.2.4: Progress Display Support (4 hours)
- [ ] Create GET /api/progress/{story_id} endpoint
- [ ] Return scene counter data
- [ ] Include time metrics
- [ ] Include completion estimate (if available)
- [ ] Write tests

#### 3.2.5: Analytics Collection (Optional, 3 hours)
- [ ] Log segment visits with timestamp
- [ ] Track choice patterns (which choices most popular)
- [ ] Track generation times
- [ ] Prepare for future analytics
- [ ] Write tests

---

## Task 3.3: Content Reporting System (20 hours)

**Days 3-4 - Estimated 20 hours**

### What You're Building
System for players to report inappropriate content.

### Subtasks

#### 3.3.1: Report Model (3 hours)
- [ ] Create Report model
- [ ] Fields: id, story_id, segment_id, type, description, reporter_email, created_at
- [ ] Add validation for report types
- [ ] Write tests

**Report types**: inappropriate_content, bug, other

#### 3.3.2: Save Report Endpoint (4 hours)
- [ ] Implement POST /api/reports
- [ ] Accept report in request
- [ ] Generate unique report ID
- [ ] Save to `.infinite_story_data/reports/`
- [ ] Return success with report ID
- [ ] Write tests

#### 3.3.3: Report Retrieval (4 hours)
- [ ] Implement GET /api/reports (admin only, skip auth for MVP)
- [ ] List all reports
- [ ] Filter by story_id, report_type, date range
- [ ] Return paginated results
- [ ] Write tests

#### 3.3.4: Report Handling (5 hours)
- [ ] Implement GET /api/reports/{report_id}
- [ ] Implement DELETE /api/reports/{report_id}
- [ ] Implement PUT /api/reports/{report_id} (mark reviewed)
- [ ] Track report status (new, reviewed, resolved)
- [ ] Write tests

#### 3.3.5: Report Analysis (4 hours)
- [ ] Create method to get most reported segments
- [ ] Create method to identify problematic content
- [ ] Generate report summary
- [ ] Prepare for moderation dashboard
- [ ] Write tests

---

## Task 3.4: Auto-Save System (12 hours)

**Days 4-5 - Estimated 12 hours**

### What You're Building
Automatic session saving after key events.

### Subtasks

#### 3.4.1: Auto-Save Triggers (4 hours)
- [ ] Hook into POST /api/segments/{id}/next
- [ ] Save session after successful generation
- [ ] Save after choice navigation
- [ ] Track save times
- [ ] Write tests

#### 3.4.2: Graceful Failure Handling (4 hours)
- [ ] Don't fail generation if save fails
- [ ] Log save failures
- [ ] Notify frontend of save status
- [ ] Implement retry logic
- [ ] Write tests

#### 3.4.3: Save Optimization (2 hours)
- [ ] Debounce saves (don't save twice in 10 seconds)
- [ ] Compress old saves
- [ ] Clean up saves older than 30 days
- [ ] Performance testing
- [ ] Write tests

#### 3.4.4: Multi-Device Support (2 hours)
- [ ] Support resuming from different devices
- [ ] Store last-accessed timestamp
- [ ] Identify most recent session
- [ ] Document device sync behavior
- [ ] Write tests

---

## Task 3.5: Integration & Testing (3 hours)

**Day 5 - Estimated 3 hours**

### Subtasks
- [ ] Integration tests for full session lifecycle
- [ ] Test auto-save during gameplay
- [ ] Test progress tracking accuracy
- [ ] Test report submission and retrieval
- [ ] 75%+ code coverage
- [ ] Performance testing (load time, save time)

---

## Daily Progress

### Day 1
- [ ] Task 3.1.1-3.1.2: Session basics (9h)
- [ ] Task 3.2.1: Scene counter model (3h)
- [ ] Task 3.3.1: Report model (3h)
- [ ] Total: ~15 hours

### Day 2
- [ ] Task 3.1.3-3.1.4: Load/delete endpoints (8h)
- [ ] Task 3.2.2: Progress calculation (5h)
- [ ] Task 3.3.2: Save report (4h)
- [ ] Total: ~17 hours (cumulative 32)

### Day 3
- [ ] Task 3.1.5-3.1.6: Validation & recovery (6h)
- [ ] Task 3.2.3: Progress persistence (5h)
- [ ] Task 3.3.3: Report retrieval (4h)
- [ ] Total: ~15 hours (cumulative 47)

### Day 4
- [ ] Task 3.2.4-3.2.5: Progress endpoints (7h)
- [ ] Task 3.3.4: Report handling (5h)
- [ ] Task 3.4.1-3.4.2: Auto-save triggers (8h)
- [ ] Total: ~20 hours (cumulative 67)

### Day 5
- [ ] Task 3.4.3-3.4.4: Optimization (4h)
- [ ] Task 3.5: Testing & integration (3h)
- [ ] Bug fixes and polish (5h)
- [ ] Total: ~12 hours (cumulative 79)

**Note**: Some tasks can overlap; aim for 85 total.

---

## Commit Strategy

```bash
[DEV-3] add session state model and endpoints
[DEV-3] implement save/load/delete session functionality
[DEV-3] add session validation and recovery
[DEV-3] add scene counter and progress tracking
[DEV-3] implement progress persistence
[DEV-3] add content reporting system
[DEV-3] implement report retrieval and handling
[DEV-3] add auto-save system with graceful failure
[DEV-3] add comprehensive tests for all features
```

---

## Success Checklist

- [ ] Can save game progress
- [ ] Can resume from saved progress
- [ ] Scene counter accurate
- [ ] Reports submitted and stored
- [ ] Auto-save working silently
- [ ] 75%+ test coverage
- [ ] Integration tests passing

---

Good luck! 🚀
