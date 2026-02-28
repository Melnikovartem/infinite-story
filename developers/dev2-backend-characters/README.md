# Dev 2: Backend Characters System

**Role**: Build the character system, state management, and character-related endpoints.

**Timeline**: Week 1.5-2 (40 hours) 
**Start after**: Dev 1 completes Task 1.2 (models)

**Blocks**: AI generation quality

---

## What You're Building

- Character model enhancements
- Character state tracking system
- Character serialization/deserialization
- Character-related endpoints (if needed)
- Integration with segment generation

---

## Key Tasks

1. **Character Model Refinement** (10 hours)
   - Avatar system (shapes: square, circle, triangle, diamond, star, pentagon)
   - Color assignment
   - Status tracking (emotional state, location, action)

2. **Character State Persistence** (15 hours)
   - Track character states across segments
   - Accumulate running_status history
   - Update characters based on generation response

3. **Integration with Generation** (15 hours)
   - Extract character info for context building
   - Update character states after generation
   - Handle character appearances/disappearances

---

## Success Criteria

- [ ] Character avatars render correctly (color + shape)
- [ ] Character states persist across segments
- [ ] Running status history accumulates
- [ ] Tests for all character operations
- [ ] Integration tests with Dev 1's endpoints

---

## See Also

- `TASKS.md` - Detailed hour-by-hour breakdown
- `../TEAM_OVERVIEW.md` - Project context
- `../API_CONTRACTS.md` - Data structures
- `../dev1-backend-api/TASKS.md` - What Dev 1 completed

---

**Start**: After Dev 1 completes Day 2
**End**: By middle of Week 2
**Daily**: ~9 hours/day for 4-5 days

Good luck! 🚀
