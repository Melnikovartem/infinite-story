# Welcome, Developer A!

**Epic Lead:** Data Layer Foundation  
**Duration:** 1 week  
**Your Role:** Senior Engineer, team lead for E0

---

## Your Mission

You're leading Epic 0, the foundation everything else depends on. Your team (A, B, C) will:

1. Enhance the `StorySegment` model with 20+ new fields for episodes/arcs
2. Create the `EpisodeRecap` model for episode summaries
3. Create the `StoryArc` model for arc metadata
4. Simplify the `UserSession` model (remove bloat)
5. Write a migration script to convert v1 data to v2
6. Set up test infrastructure for all other teams

**Why You?** You're the data modeling expert. You understand Pydantic, immutability, and persistence. E1, E2, E3, E4 all depend on your work being rock-solid.

---

## First Steps (Today)

1. **Read ONBOARDING.md** (in `/developers/`)
   - Setup guide, codebase map, git workflow
2. **Read ARCHITECTURE_V2.md** (in project root)
   - Understand the full system design
3. **Read EPIC_0_DATA_LAYER.md** (in `/developers/`)
   - Your detailed task breakdown with code examples
4. **Skim QUICK_REFERENCE.md** (in project root)
   - Diagrams and checklists

---

## Your Epic Tasks

See `EPIC_0_DATA_LAYER.md` for full details. Quick summary:

- **E0-1** (Dev-A, 3 days): Enhance `StorySegment` model
  - Add 20+ fields (episode context, character state, signals)
  - Implement immutability lock
  - Write unit tests

- **E0-2** (Dev-A, 1 day): Create `EpisodeRecap` model
  - Model for episode summaries with character states
  - Serialization/deserialization
  - Tests

- **E0-3** (Dev-B, 1 day): Create `StoryArc` model
- **E0-4** (Dev-B, 1 day): Simplify `UserSession`
- **E0-5** (Dev-C, 2 days): Migration script
- **E0-6** (Dev-C, 1 day): Test infrastructure

**You lead, code review, and unblock the team.**

---

## Key Files to Know

```
backend/app/models/
  ├── story_base.py       ← Base class (read, don't modify)
  ├── story_segment.py    ← YOU ENHANCE (E0-1)
  ├── session_state.py    ← YOU SIMPLIFY (E0-4)
  └── (others: story.py, story_character.py, etc.)

backend/tests/
  ├── conftest.py         ← YOU ENHANCE with fixtures (E0-6)
  └── test_story_models.py ← YOU WRITE tests

backend/scripts/
  └── migrate_v1_to_v2.py ← Dev-C creates (E0-5)
```

---

## Definition of Done

- [ ] All E0-1 & E0-2 code written and tested (by you)
- [ ] E0-3 & E0-4 code reviewed and approved (by you)
- [ ] E0-5 migration tested on real data (by Dev-C, reviewed by you)
- [ ] E0-6 fixtures ready (by Dev-C, reviewed by you)
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code review completed
- [ ] PR merged to main
- [ ] E1/E2/E3/E4 teams unblocked and ready to start

---

## Collaboration

- **Daily standup** with Dev-B and Dev-C (15 min)
- **Code reviews** for all team members' PRs
- **Unblocking** your team if they hit issues
- **Tech lead check-in** once per week (mentorship)

---

## Resources

- **Code patterns** → See EPIC_0_DATA_LAYER.md (full Pydantic examples)
- **Git workflow** → See ONBOARDING.md (commits, branches, PRs)
- **Architecture** → See ARCHITECTURE_V2.md (data model hierarchy)
- **Questions?** → Ask in team Slack or tag your tech lead

---

## Commit Style

```bash
# Good ✅
git commit -m "E0-1: add episode context fields to segment model"
git commit -m "E0-2: implement episoderecap serialization"

# Bad ❌
git commit -m "update models"
git commit -m "WIP: data layer"
```

---

## Next Action

→ Open `developers/EPIC_0_DATA_LAYER.md` and start on E0-1.

You've got this! 🚀
