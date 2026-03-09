# Arc Transition System - Integration Checklist

## ✅ Completed Tasks

### 1. New Files Created
- ✅ `backend/app/engine/arc_transition_manager.py` - Main orchestrator class

### 2. Model Updates
- ✅ `backend/app/models/story_segment.py`
  - Added `is_mainline: bool` field

- ✅ `backend/app/models/story_arc.py`
  - Added `is_finalized: bool`
  - Added `mainline_segment_count: int`
  - Added `is_future_arc: bool`
  - Added `is_active: bool`
  - Added `previous_arc_id: Optional[str]`
  - Added `previous_arc_summary: str`

### 3. Integration Points
- ✅ `backend/app/engine/episode_recap_generator.py`
  - Line 209: Added call to `_handle_arc_completion()`
  - New method: `_handle_arc_completion()` - triggers transition system
  - Increments `arc.episode_count` to track episode progress

- ✅ `backend/app/engine/story_runner.py`
  - In `_generate_segment()` (line ~410-440):
    - Added `next_arc_id` tracking
    - Added arc transition check when `next_episode_number > 15`
    - Added `_check_arc_transition()` method
  - Uses `next_arc_id` for segment creation (line 449)

### 4. Documentation
- ✅ `ARC_TRANSITION_SYSTEM.md` - Comprehensive system documentation
- ✅ This checklist

---

## 🔧 Testing TODO

Before merging to master, test the following:

### Unit Tests Needed
- [ ] `test_arc_transition_manager.py`
  - [ ] Test mainline determination algorithm
  - [ ] Test arc finalization (mainline marking, archiving)
  - [ ] Test context feeding
  - [ ] Test future arc generation
  - [ ] Test error handling

- [ ] `test_episode_recap_generator_integration.py`
  - [ ] Test arc completion trigger after episode 15
  - [ ] Test episode count increment
  - [ ] Test transition to new arc

- [ ] `test_story_runner_arc_transition.py`
  - [ ] Test `_check_arc_transition()`
  - [ ] Test arc_id updates during segment generation
  - [ ] Test transition detection on episode 16

### Integration Tests
- [ ] Full arc lifecycle (1-15 episodes)
  - [ ] Generate episodes 1-14 in arc 1
  - [ ] Complete episode 15, verify finalization
  - [ ] Check mainline segments marked correctly
  - [ ] Verify non-mainline archived
  - [ ] Start episode 16, verify arc transition
  - [ ] Verify context fed to arc 2
  - [ ] Verify character descriptions carried forward
  - [ ] Verify unresolved mysteries in new plot hooks

- [ ] Multiple arcs (3+ arcs)
  - [ ] Complete arc 1 and transition to arc 2
  - [ ] Complete arc 2 and transition to arc 3
  - [ ] Verify context chain (arc1 → arc2 → arc3)

- [ ] Future arc pre-generation
  - [ ] Verify 3 future arcs generated when none exist
  - [ ] Verify first future arc activated
  - [ ] Verify remaining future arcs still available

### Edge Cases
- [ ] No future arcs available, generation fails
  - [ ] Should continue in current arc, not crash
  
- [ ] Arc not found during completion
  - [ ] Should log warning, continue gracefully
  
- [ ] Segments without proper parent_segment_id
  - [ ] Mainline determination should handle
  
- [ ] Single branch arc (no alternatives)
  - [ ] Entire arc marked as mainline

---

## 📋 Migration Instructions

If upgrading an existing story:

1. **Backup existing data**
   ```bash
   cp -r data/story_id data/story_id.backup
   ```

2. **Add new fields to existing arcs**
   - Run migration script (if provided) to add new fields with defaults
   - Or manually update each arc file to include:
     ```json
     {
       "is_finalized": false,
       "mainline_segment_count": 0,
       "is_future_arc": false,
       "is_active": true,
       "previous_arc_id": null,
       "previous_arc_summary": ""
     }
     ```

3. **Add new field to existing segments**
   - Add `"is_mainline": false` to each segment file

4. **Verify arc episode counts**
   - Check that existing arcs have correct `episode_count` values
   - If counts are 0, manually update based on segment count

---

## 🚀 Deployment Checklist

- [ ] All tests passing
- [ ] Code review complete
- [ ] No breaking changes to existing APIs
- [ ] Logging configured correctly
- [ ] Error handling verified
- [ ] Documentation reviewed
- [ ] Backward compatibility confirmed

---

## 📊 Monitoring After Deployment

Track these metrics:

1. **Arc Completion**
   - How many arcs reach episode 15?
   - Average episode count per arc
   - Failure rate of arc finalization

2. **Mainline Selection**
   - Distribution of mainline path lengths
   - Number of archived vs. mainline segments
   - Are longest paths being selected correctly?

3. **Context Feeding**
   - Are character descriptions transferring correctly?
   - Are location descriptions maintained?
   - Are unresolved mysteries becoming plot hooks?

4. **Next Arc Generation**
   - Time to generate 3 future arcs
   - Quality of generated arcs (user feedback)
   - Are pre-generated arcs being used or regenerated?

---

## 🐛 Known Issues / TODOs

- [ ] Consider adding caching for `_get_all_arcs()` if many arcs exist
- [ ] Future enhancement: AI-based mainline selection for better coherence
- [ ] Consider user voting on mainline selection
- [ ] Track arc completion metrics and trends

