# Dev 4: Frontend Core - Phase 2 Real API Integration

**Timeline**: Day 2-3 of Phase 2 (starts after Dev 1 finishes)
**Priority**: High
**Dependency**: Waiting for Dev 1 to complete backend integration

---

## Executive Summary

Phase 2 focuses on **connecting the frontend to the real backend API** and **switching from mock data to real story data**.

**Current Status**:
- ✅ Frontend fully functional with mock API
- ❌ Backend API not running yet (waiting for Dev 1 to fix main.py)
- ❌ Frontend still uses mock data

**Your Job**: Replace mock API calls with real backend calls

---

## Task 5.5: Switch to Real API (Start when Dev 1 confirms server running)

**Duration**: 1 hour

### Step 1: Update API Service

Edit `frontend/src/services/api.ts`:

```typescript
// Current (line ~4):
const USE_MOCK = true

// Change to:
const USE_MOCK = false
```

That's it! The wrapper service will automatically use real API calls.

### Step 2: Verify Backend Running

Before switching, ensure:
```bash
# Terminal with backend running should show:
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Reload is enabled
```

### Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.X.X  ready in XXX ms
➜  Local:   http://localhost:5173/
```

### Step 4: Test in Browser

1. Go to http://localhost:5173
2. You should see **real stories** from backend (not mock data)
3. Click on a story
4. Try playing (selecting choices)

### Success Criteria
- ✅ Backend running on :8000
- ✅ Frontend running on :5173
- ✅ Stories load from real API
- ✅ Can navigate through story
- ✅ No console errors

---

## Task 5.6: Fix Real API Integration Issues (3-4 hours)

**When you hit problems**

### Common issues and fixes

#### Issue 1: "Cannot GET /api/stories"
**Cause**: Backend endpoint not returning correct response format

**Fix**:
```typescript
// Check what backend is returning:
// Open DevTools → Network tab
// Click on "stories" request
// Check Response tab

// Then compare to expected in frontend/src/types/index.ts
```

#### Issue 2: "Story not found" or "Segment not found"
**Cause**: Story IDs in mock data don't match backend

**Fix**:
```typescript
// Check what stories backend actually has:
// Visit: http://localhost:8000/api/docs
// Try "list_stories" endpoint
// Copy the actual story_id from response

// Update mockStories in mockApi.ts to match (for reference)
```

#### Issue 3: "Cannot read property 'choices' of undefined"
**Cause**: Segment response format doesn't match expected

**Fix**:
```typescript
// Check API_CONTRACTS.md for expected format
// Verify backend is returning:
// {
//   "segment": {...},
//   "choices": { "top_2": [...], "all": [...] }
// }
```

#### Issue 4: Choices not clickable or navigation not working
**Cause**: Frontend trying to call non-existent endpoints

**Fix**:
```typescript
// Check which endpoints exist in API docs:
// http://localhost:8000/api/docs

// Tell Dev 1 if any are missing
```

### Testing strategy

1. **Open DevTools** (F12)
2. **Go to Network tab**
3. **Refresh page** - watch all API calls
4. **Check Response** for each call
5. **Compare to API_CONTRACTS.md**

### If endpoints missing

Check with Dev 1:
- GET /api/stories ← must exist
- GET /api/stories/{id} ← must exist
- GET /api/segments/{id} ← must exist
- POST /api/sessions/save ← should work
- GET /api/sessions/{story_id} ← should work
- POST /api/reports ← should work

---

## Task 5.7: Handle Loading & Error States (2 hours)

**While waiting for backend / fixing issues**

### Update loading states

```typescript
// src/contexts/StoryContext.tsx

// Add proper loading states
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

// When fetching from API
setLoading(true)
try {
  const data = await fetch(...)
  setError(null)
} catch (err) {
  setError(err.message)
} finally {
  setLoading(false)
}
```

### Display loading skeleton

Show loading state while API responds:
```typescript
if (loading) {
  return <div className="skeleton-screen">Loading...</div>
}
```

### Display errors nicely

```typescript
if (error) {
  return (
    <div className="error-message">
      <p>⚠️ {error}</p>
      <button onClick={() => retry()}>Try Again</button>
    </div>
  )
}
```

### Success Criteria
- ✅ Loading spinners appear while fetching
- ✅ Error messages display clearly
- ✅ Retry buttons work
- ✅ No blank screens

---

## Task 5.8: Verify Session Persistence (1 hour)

**After basic API integration works**

### Test save/load

1. **Start playing a story**
2. **Advance to scene 3-4**
3. **Refresh the page** - should resume from where you left off
4. **Close and reopen browser** - should still be there

### How it works

```typescript
// When you make a choice:
1. Frontend sends choice to backend
2. Backend saves session (auto-save)
3. Frontend updates local state
4. Refresh happens → frontend checks backend for saved session
5. Resume from saved position
```

### If not working

Check:
- ✅ Backend session save endpoint responding
- ✅ Session data being stored
- ✅ Frontend loading session on startup

Tell Dev 3 if sessions not persisting.

### Success Criteria
- ✅ Can play, advance scenes
- ✅ Refresh keeps you in same scene
- ✅ Close/reopen keeps position
- ✅ Session counter shows correct scene

---

## Task 5.9: Test Full Story Flow (2 hours)

**Before declaring done**

### Complete playthrough

1. **Go to http://localhost:5173**
2. **Click "The Veil of Thornreach"** or any story
3. **Read opening scene**
4. **Choose from top 2 choices** → navigate to segment_002
5. **View all choices** → see all available options
6. **Make custom choice** → (backend should generate - may not work yet)
7. **Check progress counter** → scene number, elapsed time
8. **Try report modal** → click ⚠ button
9. **Try back button** → goes back to story list
10. **Resume game** → check session loads correctly

### Checklist

- [ ] Story list shows real stories
- [ ] Can click and open story detail
- [ ] Start game button loads story
- [ ] Can see segment content with characters
- [ ] Top 2 choices visible and clickable
- [ ] View all choices works
- [ ] Custom choice input appears
- [ ] Progress counter shows correctly
- [ ] Report modal opens
- [ ] Back button works
- [ ] Refresh maintains position
- [ ] No console errors

### Success Criteria
- ✅ All items checked
- ✅ Smooth gameplay experience
- ✅ No errors in console
- ✅ Ready for user testing

---

## Daily Breakdown

### Day 1 (Waiting for Dev 1)
- [ ] Review API_CONTRACTS.md again
- [ ] Review backend route files (sessions.py, progress.py, reports.py)
- [ ] Prepare questions for Dev 1
- [ ] Stand by for "backend is running" notification

### Day 2 (When Dev 1 confirms server running)
- [ ] Task 5.5: Switch to real API (1h)
- [ ] Task 5.6: Fix integration issues (3-4h)
- [ ] Run integration tests (30m)

### Day 3
- [ ] Task 5.7: Loading & error states (2h)
- [ ] Task 5.8: Session persistence (1h)
- [ ] Task 5.9: Full flow testing (2h)
- [ ] Verify everything works end-to-end

---

## Commits

```bash
[DEV-4] switch frontend to real api - set USE_MOCK = false
[DEV-4] add error handling for api integration
[DEV-4] improve loading states and spinners
[DEV-4] verify session persistence works with real backend
[DEV-4] comprehensive integration testing
```

---

## Testing Checklist

### Before declaring "done"

```
API Integration:
  ✅ Stories loading from real backend
  ✅ Segments loading correctly
  ✅ Choices displaying and navigating
  ✅ Sessions saving and loading
  ✅ Reports submitting
  
Error Handling:
  ✅ Network errors display nicely
  ✅ Missing segments show error
  ✅ Invalid stories show error
  ✅ Retry buttons work
  
Performance:
  ✅ No console errors
  ✅ Smooth navigation
  ✅ Proper loading states
  ✅ Fast responses
  
Content:
  ✅ Real story data displays
  ✅ Characters show with avatars
  ✅ Locations display correctly
  ✅ Progress counter accurate
```

---

## Blocking Points

**What blocks you**:
1. Dev 1 finishing backend API (Days 2-3)

**What you unblock**:
1. Full end-to-end playable game
2. Dev 5 can now polish UI with real data
3. Team can test actual gameplay

---

## Success = Full Game Works

When this is complete:
1. ✅ Frontend running on :5173
2. ✅ Backend running on :8000
3. ✅ Real stories loading from backend
4. ✅ Can play stories end-to-end
5. ✅ Sessions persist
6. ✅ All major features working
7. ✅ Ready for user testing

You're the bridge between frontend and backend! 🌉

---

## Need Help?

- API not responding? → Check Dev 1's work
- Session not saving? → Check Dev 3's work
- Styling looks bad? → Dev 5 will fix in Phase 3
- Question about endpoints? → See API_CONTRACTS.md

Good luck! 🚀
