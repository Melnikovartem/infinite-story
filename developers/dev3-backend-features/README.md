# Dev 3: Backend Features & State Persistence

**Role**: Build session state persistence, progress tracking, reporting, and auto-save system.

**Timeline**: Week 1-2 (85 hours)
**Start**: Day 1 (no blockers!)
**Blocks**: None (independent work)

---

## What You're Building

- Session state persistence (save/load/resume)
- Auto-save system (triggers after AI generation)
- Progress tracking (scene counters, elapsed time)
- Content reporting system
- State migration/recovery

---

## Key Tasks

1. **Session Management** (30 hours)
   - Save session to `runner_state.json`
   - Load session from disk
   - Resume from any segment
   - Clear/delete sessions
   - Handle session expiry

2. **Progress Tracking** (20 hours)
   - Scene counter (X out of estimated total)
   - Elapsed time tracking
   - Start date/time
   - Visited segments list
   - Progress persistence

3. **Content Reporting** (20 hours)
   - Report modal UI support (backend)
   - Store reports in JSON
   - Report types (inappropriate content, bugs, etc.)
   - Report retrieval for moderation

4. **Auto-Save System** (15 hours)
   - Trigger after AI generation
   - Handle failures gracefully
   - Clean up old saves
   - Performance optimization

---

## Success Criteria

- [ ] Can save/load session state
- [ ] Auto-save works after generation
- [ ] Progress tracking accurate
- [ ] Reports stored and retrievable
- [ ] 75%+ test coverage
- [ ] Integration with Dev 1's endpoints working

---

## See Also

- `TASKS.md` - Detailed breakdown
- `../TEAM_OVERVIEW.md` - Project context
- `../API_CONTRACTS.md` - Session endpoints
- `../dev1-backend-api/` - Endpoint patterns

---

**Start**: Day 1 (no waiting!)
**End**: By end of Week 2
**Daily**: ~17 hours/day for 5 days

Good luck! 🚀
