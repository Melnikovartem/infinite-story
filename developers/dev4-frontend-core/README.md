# Dev 4: Frontend Core Components & State

**Role**: Build React components, routing, and state management with mocked APIs.

**Timeline**: Week 1-2 (60 hours)
**Start**: Day 1 (start with mocked APIs!)
**Blocks**: Dev 5 (polish/styling)

---

## What You're Building

- Story list page
- Story detail/play page
- Segment display component
- Choice display (top 2 + expandable list)
- Custom choice input
- Session management (save/load/resume)
- Character avatar display
- Progress/scene counter
- Report modal
- Client-side routing

---

## Key Tasks

1. **Project Setup & Routing** (12 hours)
   - React Router setup
   - Page structure
   - Context API setup for state

2. **Component Library** (25 hours)
   - StoryList component
   - StoryDetail/Play component
   - SegmentDisplay component
   - ChoiceDisplay component
   - CharacterAvatar component
   - ProgressCounter component
   - ReportModal component

3. **State Management** (15 hours)
   - Story context
   - Session context
   - Player state
   - Error handling

4. **API Integration (Mocked)** (8 hours)
   - Create mock API service
   - Mock all endpoints
   - Design fetching strategy
   - Ready for real API swap

---

## Success Criteria

- [ ] All components render correctly
- [ ] Routing works end-to-end
- [ ] Can play a story with mocked data
- [ ] Session save/load works
- [ ] Components ready for real API
- [ ] 60%+ test coverage (component tests)

---

## Key Notes

**Don't wait for backend!** Use mocked API responses:

```typescript
// services/mockApi.ts
export const mockStories = [
  { id: "veil", title: "Veil of Thornreach", ... }
];

export const mockSegments = {
  segment_001: {
    id: "segment_001",
    title: "The Last Sanctuary",
    content: "...",
    choices: { top_2: [...], all: [...] }
  }
};
```

---

## See Also

- `TASKS.md` - Detailed breakdown
- `../TEAM_OVERVIEW.md` - Project context
- `../API_CONTRACTS.md` - API spec (for mocking)
- `mocking-guide.md` - How to set up mocks

---

**Start**: Day 1 (no dependencies!)
**End**: By end of Week 2
**Daily**: ~12 hours/day for 5 days

Good luck! 🚀
