# Dev 1: Backend API Core

**Role**: Build the core FastAPI backend infrastructure, data models, and API endpoints.

**Timeline**: Week 1 (Critical Path) - 80 hours
**Estimated Daily**: 16 hours/day for 5 days

**Blocked by**: Nothing (you're first!)
**Blocks**: Dev 2 (characters), Dev 3 (features), Dev 4 (frontend integration)

---

## What You're Building

- FastAPI server with proper structure
- Pydantic data models (Story, Segment, Choice, etc.)
- Core API endpoints (GET stories, GET segment, POST next scene)
- AI generation integration (context building, LLM calls)
- File-based persistence (JSON storage)
- CORS setup for frontend

---

## Success Criteria

### By End of Day 1
- [ ] FastAPI project structure created
- [ ] Pydantic models defined
- [ ] Basic endpoints returning mock data
- [ ] Can run `uvicorn app.main:app --reload`

### By End of Day 2
- [ ] File-based persistence working (save/load segments)
- [ ] All core models serializable to JSON
- [ ] Story listing and retrieval endpoints working

### By End of Day 3
- [ ] Segment retrieval with choices implemented
- [ ] Custom choice endpoint structure (no AI yet)
- [ ] Session save/load endpoints working

### By End of Day 4
- [ ] AI generation integration (context building)
- [ ] Full choice→segment flow working
- [ ] Tests for all endpoints

### By End of Day 5
- [ ] Bug fixes and optimization
- [ ] Dev 3 can integrate state persistence
- [ ] Dev 2 can start character work
- [ ] Dev 4 can connect frontend to real APIs

---

## Key Files to Modify/Create

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app setup
│   ├── config.py               # Configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # All API endpoints
│   │   └── models.py           # Pydantic request/response models
│   ├── models/
│   │   ├── story.py            # (already exists, extend)
│   │   ├── story_segment.py    # (already exists, extend)
│   │   ├── story_choice.py     # (already exists, extend)
│   │   └── story_character.py  # (already exists, extend)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── story_service.py    # Story business logic
│   │   ├── segment_service.py  # Segment operations
│   │   └── generation_service.py # AI generation
│   └── utils/
│       └── response_formatter.py # Consistent response format
├── tests/
│   ├── test_api_endpoints.py   # API tests
│   └── test_services.py        # Service tests
├── requirements.txt            # Add: fastapi, uvicorn, pydantic
└── main.py                     # Entry point
```

---

## Dependencies to Add

Update `backend/requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2  # For async HTTP calls to AI API
```

---

## Detailed Tasks

See `TASKS.md` for hour-by-hour breakdown and detailed subtasks.

---

## Testing

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run API tests only
python -m pytest tests/test_api_endpoints.py -v

# Run with coverage
python -m pytest --cov=app tests/ -v
```

All new code must have tests!

---

## API Endpoints You're Building

See `../API_CONTRACTS.md` for full spec. Quick summary:

```
GET    /api/stories              # List all stories
GET    /api/stories/{id}         # Get story + start segment
GET    /api/segments/{id}        # Get segment + choices
POST   /api/segments/{id}/next   # Generate next scene
POST   /api/sessions/save        # Save session
GET    /api/sessions/{id}        # Load session
DELETE /api/sessions/{id}        # Delete session
POST   /api/reports              # Report content
```

---

## Key Architecture Notes

### File Persistence

Stories are stored in `.infinite_story_data/`:

```
.infinite_story_data/
└── veil_of_thornreach/
    ├── story/
    │   └── veil_of_thornreach.json
    ├── storysegment/
    │   └── segment_001.json
    ├── storychoice/
    │   └── choice_001.json
    ├── storycharacter/
    │   └── eira.json
    └── storylocation/
```

Use existing `StoryBase.save()` and `StoryBase.load()` methods from `app/models/story_base.py`.

### Context Building for AI

When generating next scene:

1. Get previous 5-10 segments
2. Get character states from those segments
3. Get location state from current segment
4. Get story worldbuilding (StoryContext)
5. Combine with current choice text
6. Pass to TextGenerator

Example context:

```python
context = {
    "story_context": story_context.get_full_overview(),
    "previous_segments": [seg.get_full_overview() for seg in previous_segs],
    "current_characters": character_states,
    "current_location": location_state,
    "player_choice": choice_text
}
```

### Response Format

All responses should follow this pattern:

```python
@router.get("/stories")
async def list_stories():
    try:
        stories = StoryService.list_all_stories()
        return {
            "success": True,
            "data": stories,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }, 500
```

---

## Blockers & Dependencies

**You're not blocked by anyone!** You're the foundation.

**However**:
- Dev 2 waits for your StoryCharacter model
- Dev 3 waits for your session endpoints
- Dev 4 uses your API once it's ready

---

## Communication

- Daily standup: Report progress on tasks
- If stuck: Check API_CONTRACTS.md for spec clarity
- Before merging: Ensure Dev 3 can integrate easily

---

## Getting Started

1. Read `API_CONTRACTS.md` (30 min)
2. Review existing code in `backend/app/models/` (30 min)
3. Start with Task 1.1: FastAPI setup (see `TASKS.md`)
4. Follow the timeline for each day

**Questions?** Check `TEAM_OVERVIEW.md` or ask in standup.

Good luck! 🚀
