# Infinite Story Engine - Team Developer Overview

## Project Vision

Build an **AI-powered interactive storytelling platform** where users can explore infinite branching narratives. Players navigate through dynamically generated scenes, make choices, and watch the story unfold with AI-generated content that responds to their decisions.

**Key Goal**: MVP ready for users to play existing stories with dynamic AI generation in 2-2.5 weeks.

---

## MVP Scope

### What Users Can Do

1. **Play existing stories** (no story creation UI)
2. **Choose from top 2 popular choices** or view all available choices
3. **Write custom choices** (AI generates the next scene)
4. **See character avatars** (colored shapes: square, circle, triangle, diamond, star, pentagon)
5. **Track progress** (Scene X • elapsed time • start date)
6. **Auto-save/resume** stories (continue from where you left off)
7. **Report inappropriate content** (basic modal)

### What's NOT in MVP

- Story creation UI
- User accounts/authentication
- Advanced UI (branch visualization, character relationships)
- Multi-language support
- AI-generated character images
- Advanced monetization features

---

## Team Structure (5 Developers)

### Developer Roles & Responsibilities

| Developer | Role | Focus | Hours | Timeline |
|-----------|------|-------|-------|----------|
| **Dev 1** | Backend API Core | FastAPI setup, endpoints, database models | 80h | Week 1 (Critical Path) |
| **Dev 2** | Backend Characters | Character system, states, serialization | 40h | Week 1.5-2 |
| **Dev 3** | Backend Features | Progress tracking, reporting, auto-save | 85h | Week 1-2 |
| **Dev 4** | Frontend Core | Components, routing, state management | 60h | Week 1-2 |
| **Dev 5** | Frontend Polish | Styling, animations, accessibility | 45h | Week 1.5-2.5 |

**Total**: 310 hours over 2-2.5 weeks

---

## Architecture Overview

### Tech Stack

```
Frontend: React 18 + TypeScript
├── State: React Context API
├── HTTP: Fetch API
└── Styling: Tailwind CSS (or custom CSS)

Backend: Python 3.13+ FastAPI
├── Server: Uvicorn
├── Data: JSON files (.infinite_story_data/)
├── AI: OpenRouter (Deepseek-V3 or similar)
└── Models: Pydantic

AI Generation:
├── Input: Story context + player choice
├── Processing: LLM generates next scene
└── Output: Scene text, character states, next choices
```

### Data Model

```
Story (top-level container)
├── StorySegment (scenes)
│   ├── id, title, content, created_at
│   ├── character_states (who's present, emotions)
│   ├── location_state (where we are)
│   └── text_blocks (narrative, dialogue, etc.)
│
├── StoryChoice (connections between segments)
│   ├── id, from_segment_id, to_segment_id
│   ├── choice_text, popularity_score
│   └── is_custom (user-written)
│
├── StoryCharacter (character definitions)
│   ├── id, name, description, avatar_shape, avatar_color
│   └── running_status (state changes through story)
│
├── StoryLocation (location definitions)
│   ├── id, name, description
│   └── running_status (state changes through story)
│
└── StoryContext (worldbuilding)
    ├── id, rules, fundamental_truths
    └── world_description
```

### API Endpoints (Summary)

```
GET    /api/stories              # List all stories
GET    /api/stories/{id}         # Get story details + start segment
GET    /api/segments/{id}        # Get segment content + choices
POST   /api/segments/{id}/next   # Generate next scene from choice
POST   /api/sessions/save        # Save session state
GET    /api/sessions/{id}        # Load session state
POST   /api/reports              # Report inappropriate content
```

**Full spec**: See `API_CONTRACTS.md`

---

## Workflow & Communication

### Daily Standups

**Time**: Start of day
**Duration**: 15 minutes
**Format**: 
- What did you accomplish yesterday?
- What are you working on today?
- Any blockers?

### Branching & PRs

**Never blocked by reviews** - once tests pass, you merge immediately:

1. Create feature branch: `feature/task-description`
2. Commit frequently: `[DEV-N] task description`
3. Push and create PR (no review needed)
4. Tests pass → Merge → Delete branch → Move to next task

### Parallel Work Strategy

**Key Insight**: Frontend doesn't need backend to exist!

- **Dev 4** (Frontend) uses **mocked APIs** from Day 1
- **Dev 1** (Backend) implements real endpoints to match API spec
- **Week 2.5**: Integration happens when both sides are done
- **Result**: No waiting, maximum parallelization

### Blockers

- Report **immediately** (don't wait for standup)
- Blockers are rare due to API contracts + mock APIs
- If blocked, pick up parallel work from another task area

---

## Development Phases

### Phase 1: Foundation (Days 1-5)

**Dev 1**: Backend API structure, models, endpoints
**Dev 3**: Progress/state persistence, auto-save system
**Dev 4**: Frontend layout, routing, component structure
**Dev 5**: CSS setup, color system, typography

**Output**: 
- Working backend server responding to requests
- Working frontend shell with mocked data
- Auto-save working (with mock data)

### Phase 2: Integration (Days 6-10)

**Dev 2**: Character system implementation
**Dev 1**: AI generation endpoint, context building
**Dev 4**: Connect frontend to real backend APIs
**Dev 5**: Refine UI based on real data

**Output**:
- Real API responses flowing to frontend
- AI-generated scenes working
- Character avatars rendering correctly
- Auto-save/resume working with real backend

### Phase 3: Polish & Testing (Days 11-14)

**All devs**: Bug fixes, performance optimization, final testing

**Output**:
- MVP ready for user testing
- All tests passing
- Known issues documented
- Ready to deploy

---

## Critical Path Dependencies

```
Dev 1 Task 1.1 (API Setup)
    ↓
Dev 1 Task 1.2 (Models)
    ↓
Dev 1 Task 1.3 (Endpoints) ← Dev 3 waits for this
Dev 3 Task 3.1 (State)      ← depends on Dev 1
    ↓
Dev 3 Task 3.2 (Auto-save)
    ↓
Dev 2 Task 2.1 (Characters) ← depends on Dev 1 models
    ↓
Dev 2 Task 2.2 (States)
    ↓
Dev 1 Task 1.4 (AI Generation) ← depends on Dev 2, Dev 3

Dev 4 Task 5.1-5.3: Runs in PARALLEL (mocked APIs)
Dev 5 Task 6.1+: Starts after Dev 4 foundation done (Phase 1.5)
```

**Key Point**: Most dependencies are one-way; devs can work in parallel for Days 1-5.

---

## Testing Requirements

### Minimum Test Coverage

- **Backend**: 70% code coverage minimum
- **Frontend**: Component tests for all major UI
- **All code must have tests before PR merge**

### Test Commands

```bash
# Backend
cd backend
python -m pytest -v --cov=app

# Frontend
cd frontend
npm test -- --coverage
```

---

## File Storage

Stories live in `.infinite_story_data/`:

```
.infinite_story_data/
└── veil_of_thornreach/         # Story ID
    ├── story/
    │   └── veil_of_thornreach.json
    ├── storysegment/
    │   ├── opening_scene.json
    │   ├── segment_2.json
    │   └── ...
    ├── storychoice/
    │   ├── choice_1.json
    │   └── ...
    ├── storycharacter/
    │   ├── eira.json
    │   └── ...
    ├── storylocation/
    │   ├── thornreach_grove.json
    │   └── ...
    └── storycontext/
        └── world_rules.json
```

---

## Success Criteria

### Week 1 End
- [ ] Backend API running and responding
- [ ] Frontend renders story content (mocked data)
- [ ] Auto-save system working
- [ ] Character system defined and modeled

### Week 2 End
- [ ] AI generation producing valid scenes
- [ ] Frontend connected to real backend
- [ ] All tests passing
- [ ] Can play a full story with AI choices

### Week 2.5 End (MVP Ready)
- [ ] All features working end-to-end
- [ ] UI polished and accessible
- [ ] No critical bugs
- [ ] Documentation complete
- [ ] Ready for user testing

---

## Resources & Documentation

### Key Files

- `API_CONTRACTS.md` - Full API specification (start here!)
- Backend: `backend/README.md`, `AGENTS.md`
- Frontend: `frontend/README.md`
- Developer Setup: `DEVELOPER_SETUP.md`

### Individual Task Details

- `developers/dev1-backend-api/TASKS.md` - Dev 1 detailed tasks
- `developers/dev2-backend-characters/TASKS.md` - Dev 2 detailed tasks
- `developers/dev3-backend-features/TASKS.md` - Dev 3 detailed tasks
- `developers/dev4-frontend-core/TASKS.md` - Dev 4 detailed tasks
- `developers/dev5-frontend-polish/TASKS.md` - Dev 5 detailed tasks

---

## Questions?

- **General project questions**: Check this document
- **Technical architecture**: See `AGENTS.md` and code comments
- **API details**: See `API_CONTRACTS.md`
- **Your specific tasks**: See your role's `TASKS.md`
- **Development workflow**: See `DEVELOPER_SETUP.md`

---

## Quick Links

```
📁 Root
├── 📄 DEVELOPER_SETUP.md        (← Start here for dev setup)
├── 📄 TEAM_OVERVIEW.md          (← You are here)
├── 📄 API_CONTRACTS.md          (← API spec for all devs)
├── 📁 backend/                  (Python + FastAPI)
├── 📁 frontend/                 (React + TypeScript)
└── 📁 developers/               (Your task breakdown)
    ├── dev1-backend-api/
    ├── dev2-backend-characters/
    ├── dev3-backend-features/
    ├── dev4-frontend-core/
    └── dev5-frontend-polish/
```

Good luck! 🚀
