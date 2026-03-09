# Developer Assignments: Role & Responsibility Matrix

## Overview

This document maps developers to epics with clear role definitions, expected skill sets, and success metrics.

---

## Developer Profiles & Assignments

### Epic 0: Data Layer Foundation (1 week)

#### Developer A (Lead) - Data Models
**Role:** Epic Lead + Senior Engineer  
**Experience Level:** Senior  
**Skills Required:**
- Pydantic data modeling
- Python async/await
- JSON serialization
- Database schema thinking

**Responsibilities:**
- Lead E0 epic (overall delivery)
- Execute E0-1 (Segment model)
- Execute E0-2 (EpisodeRecap model)
- Code review E0-3, E0-4
- Unblock team
- Daily standup

**Success Metrics:**
- Segment model complete with immutability locks
- EpisodeRecap model with proper serialization
- All E0-1, E0-2 tests passing
- Team ready for E1/E2/E3

**Mentor:** Tech Lead (Weekly check-in)

---

#### Developer B (Senior) - Arc & Session Models
**Role:** Senior Engineer  
**Experience Level:** Senior  
**Skills Required:**
- Pydantic
- Python OOP
- Data modeling

**Responsibilities:**
- Execute E0-3 (StoryArc model)
- Execute E0-4 (UserSession simplification)
- Coordinate with Dev A on model integration
- Write tests

**Success Metrics:**
- Arc model complete
- Session model simplified (no per-user state)
- Tests passing
- Smooth handoff to E1/E2/E3

**Mentor:** Dev A (Daily)

---

#### Developer C (Mid) - Migration & Testing
**Role:** Mid-level Engineer  
**Experience Level:** Mid  
**Skills Required:**
- Python scripting
- Data transformation
- Testing/QA mindset
- Validation logic

**Responsibilities:**
- Execute E0-5 (Migration script)
- Execute E0-6 (Test infrastructure)
- Validate data integrity
- Create rollback mechanism

**Success Metrics:**
- Migration script works on real data
- No data loss validation
- Rollback tested
- Test fixtures ready for E1/E2/E3/E4

**Mentor:** Dev A (Daily)

---

### Epic 1: Generation Pipeline (2 weeks)

#### Developer D (Lead) - Pipeline Architecture
**Role:** Epic Lead + Principal Engineer  
**Experience Level:** Senior/Principal  
**Skills Required:**
- System design
- Async Python
- Algorithm design (pacing, chaining)
- API integration
- Error handling

**Responsibilities:**
- Lead E1 epic (overall delivery)
- Execute E1-1 (Context builder)
- Execute E1-2 (Generation pipeline)
- Execute E1-5 (Episode transition logic)
- Coordinate with E2, E3 teams
- Code review all E1 tasks
- Unblock team

**Success Metrics:**
- Context builder works correctly
- Parent chain walking works
- Episode transitions happen at generation time
- All tests passing
- Ready for E2/E3 integration

**Mentor:** Tech Lead (2x/week)

---

#### Developer E (Mid-Senior) - Generator Integration
**Role:** Mid-Senior Engineer  
**Experience Level:** Mid-Senior  
**Skills Required:**
- Python async/await
- API integration
- JSON parsing
- Error handling
- Response validation

**Responsibilities:**
- Execute E1-3 (Generator interface)
- Execute E1-4 (Segment generation)
- Handle API responses
- Validate all required fields
- Implement graceful fallbacks

**Success Metrics:**
- Generator interface handles all response types
- Segment generation creates valid objects
- Fallback strategy tested
- Tests passing
- No orphaned API calls

**Mentor:** Dev D (Daily)

---

### Epic 2: Episode & Arc System (2 weeks)

#### Developer F (Lead) - Episode System
**Role:** Epic Lead + Senior Engineer  
**Experience Level:** Senior  
**Skills Required:**
- AI prompt engineering
- Data aggregation
- Character state logic
- Narrative understanding

**Responsibilities:**
- Lead E2 epic (overall delivery)
- Execute E2-1 (Recap generator)
- Execute E2-2 (New episode generation)
- Execute E2-5 (Archive handling)
- Coordinate with E1 on episode signals
- Code review E2-3, E2-4

**Success Metrics:**
- Recap generator creates coherent summaries
- New episode context generated correctly
- Character final states make sense
- Archive system working
- Tests passing

**Mentor:** Tech Lead (2x/week)

---

#### Developer G (Mid) - Arc Compression & State
**Role:** Mid-level Engineer  
**Experience Level:** Mid  
**Skills Required:**
- Data structures (graphs, trees)
- Algorithm design
- State management
- Data aggregation

**Responsibilities:**
- Execute E2-3 (Character state reconciliation)
- Execute E2-4 (Arc compression)
- Implement mainline selection
- Archive non-mainline segments

**Success Metrics:**
- State reconciliation algorithm correct
- Compression picks reasonable branches
- Archiving works cleanly
- Tests passing
- Performance acceptable (<5 min per arc)

**Mentor:** Dev F (Daily)

---

### Epic 3: CLI & User Interface (2 weeks)

#### Developer H (Lead) - CLI Architecture & Display
**Role:** Epic Lead + Mid-Senior Engineer  
**Experience Level:** Mid-Senior  
**Skills Required:**
- Rich library expertise
- CLI design
- User experience
- Configuration management
- Async CLI handling

**Responsibilities:**
- Lead E3 epic (overall delivery)
- Execute E3-1 (Display functions)
- Execute E3-2 (Choice menus)
- Execute E3-5 (Configuration system)
- Coordinate with E1 on integration points
- Code review E3-3, E3-4

**Success Metrics:**
- Both CLI modes display correctly
- Menus are intuitive
- Configuration system flexible
- Rich output professional
- Tests passing

**Mentor:** Dev D (coordinate generation integration)

---

#### Developer I (Mid) - Game Loop & Dev Tools
**Role:** Mid-level Engineer  
**Experience Level:** Mid  
**Skills Required:**
- Game loop architecture
- Async programming
- Event handling
- Debugging/inspection tools

**Responsibilities:**
- Execute E3-3 (Dev commands)
- Execute E3-4 (Main CLI loop update)
- Integrate with E1's traverse_or_generate()
- Create dev debugging commands

**Success Metrics:**
- Game loop works smoothly
- Dev commands functional
- Choice handling correct
- Mode switching seamless
- Tests passing

**Mentor:** Dev H (Daily)

---

### Epic 4: Testing & Operations (ongoing + 4+ weeks)

#### Developer J (Lead) - Test Architecture & Coverage
**Role:** Testing Lead + QA Engineer  
**Experience Level:** Mid-Senior  
**Skills Required:**
- pytest expertise
- Test design
- Coverage analysis
- Integration testing
- Manual QA

**Responsibilities:**
- Lead E4 epic (overall testing delivery)
- Execute E4-1 (Unit test suite)
- Execute E4-2 (Integration tests)
- Execute E4-5 (CLI tests)
- Coordinate testing with all epics
- Maintain test coverage >90%

**Success Metrics:**
- All unit tests passing
- All integration tests passing
- Coverage >90%
- No regressions
- Performance baselines established

**Mentor:** Tech Lead (2x/week)

---

#### Developer K (Mid) - Migration & Performance
**Role:** Mid-level Engineer + DevOps  
**Experience Level:** Mid  
**Skills Required:**
- Data migration
- Performance profiling
- Scripting
- Benchmarking

**Responsibilities:**
- Execute E4-3 (Migration testing)
- Execute E4-4 (Performance testing)
- Test on real data
- Establish performance baselines
- Document issues found

**Success Metrics:**
- Migration tested on real story
- No data loss confirmed
- Performance targets met
- Benchmarks documented
- Rollback tested

**Mentor:** Dev C (migration guidance)

---

### QA/Manual Testing

#### QA Team
**Responsibilities:**
- Execute E4-6 (Manual testing checklist)
- Test both CLI modes
- Find edge cases
- User acceptance testing
- Report bugs clearly

**Success Metrics:**
- Checklist 100% complete
- No critical bugs remain
- User experience is smooth
- Both modes work well

---

## Role Distribution Summary

| Role | Developer | Epic | Days | Skill Level |
|------|-----------|------|------|-------------|
| Epic Lead | A | E0 | 5 | Senior |
| Senior Dev | B | E0 | 5 | Senior |
| Mid Dev | C | E0 | 5 | Mid |
| Epic Lead | D | E1 | 10 | Principal |
| Mid-Senior Dev | E | E1 | 10 | Mid-Senior |
| Epic Lead | F | E2 | 10 | Senior |
| Mid Dev | G | E2 | 10 | Mid |
| Epic Lead | H | E3 | 10 | Mid-Senior |
| Mid Dev | I | E3 | 10 | Mid |
| Testing Lead | J | E4 | 20+ | Mid-Senior |
| Mid Dev | K | E4 | 20+ | Mid |

**Total:** 11 developers (but many can overlap roles)

---

## Skill Matrix

### Skills Needed

| Skill | Required For | Experts |
|-------|--------------|---------|
| Pydantic | E0 | A, B |
| Async Python | E0, E1, E3 | D, H |
| API Integration | E1 | D, E |
| Character State Logic | E2 | F, G |
| Rich CLI | E3 | H, I |
| pytest | E4 | J |
| Performance Profiling | E4 | K |

### Developer Skill Map

| Developer | Skills | Gaps |
|-----------|--------|------|
| A | Pydantic, Senior design, leadership | CLI, Performance |
| B | Pydantic, OOP, Testing | API, Async heavy |
| C | Scripting, QA, Testing | Backend architecture |
| D | System design, Async, API | Testing, UI/UX |
| E | Async, API, Error handling | Testing, Leadership |
| F | Narrative logic, Data aggregation | Low-level coding |
| G | Algorithms, State machines | Leadership, UI |
| H | CLI, UX, Configuration | Low-level APIs |
| I | Event handling, Debugging | Architecture |
| J | Testing, Coverage | Development |
| K | Performance, Scripting | Architecture |

---

## Onboarding Checklist per Developer

### Before Day 1

- [ ] Read VISION.md (30 min)
- [ ] Read DEVELOPMENT_TASKS.md (your epic section)
- [ ] Read relevant technical docs (30 min)
- [ ] Setup dev environment
- [ ] Access to repo & project board
- [ ] Slack added to #dev-infinite-story

### Day 1

- [ ] Kickoff meeting with tech lead
- [ ] Assigned epic lead reviews scope
- [ ] First task assigned
- [ ] Pair programming session if needed
- [ ] Standup added to calendar

### Week 1

- [ ] Complete first task
- [ ] Code review cycle done
- [ ] Weekly sync attended
- [ ] Comfortable with codebase

---

## Mentorship Pairings

| Mentee | Mentor | Focus |
|--------|--------|-------|
| C | A | Data modeling, migration |
| E | D | API integration, async |
| G | F | Character logic, data |
| I | H | CLI, UX, integration |
| K | C | Testing, data validation |

---

## Communication Expectations

### Daily
- Standup (10 min, Slack thread)
- Slack messages to epic lead if blocked
- PR updates if in review

### Weekly
- Friday sync (1 hour, full team)
- Code reviews on PRs

### As Needed
- Pair programming sessions
- Design discussions
- Problem solving

---

## Success Criteria by Epic (Developer Perspective)

### Epic 0 Success (Devs A, B, C)
✅ All model changes backward compatible  
✅ Migration script works on real data  
✅ >90% test coverage  
✅ Zero data loss  
✅ E1/E2/E3 can start on Monday  

### Epic 1 Success (Devs D, E)
✅ Context builder produces correct prompts  
✅ Segments generate with episode context  
✅ Episode transitions at generation time  
✅ Character states tracked  
✅ >90% test coverage  

### Epic 2 Success (Devs F, G)
✅ Recaps are coherent and correct  
✅ Arc compression picks reasonable mainlines  
✅ Character state reconciliation works  
✅ Archiving hides non-mainline branches  
✅ >90% test coverage  

### Epic 3 Success (Devs H, I)
✅ Gameplay mode is immersive  
✅ Exploration mode shows all context  
✅ Mode switching seamless  
✅ Dev commands functional  
✅ >90% test coverage  

### Epic 4 Success (Devs J, K)
✅ >90% overall code coverage  
✅ All integration tests passing  
✅ Migration validated on real data  
✅ Performance targets met  
✅ Zero regressions  

---

## Performance Reviews Criteria

Each developer will be evaluated on:

1. **Task Completion** (40%)
   - Tasks done on time
   - Quality of code
   - Tests passing

2. **Collaboration** (30%)
   - Communication effectiveness
   - Responsiveness to PR reviews
   - Helping teammates

3. **Ownership** (20%)
   - Takes responsibility for blockers
   - Proactive problem solving
   - Goes beyond just assigned tasks

4. **Learning** (10%)
   - Asks good questions
   - Improves skills
   - Shares knowledge

---

## Time Tracking

**Use format:** [Epic ID] [Task ID] - [Hours]

Example: `E0-1: 4h model implementation`

This helps track:
- Estimation accuracy
- Time per task type
- Bottlenecks

---

## Escalation Path

**Blocked?**
1. → Epic lead (same day)
2. → Tech lead if epic lead can't unblock (next day)
3. → Project manager if tech lead needs help (within 24h)

**Off Track?**
1. → Epic lead (daily standup)
2. → Tech lead (weekly sync)
3. → Project manager (if >1 day behind)

---

## Questions?

Contact your epic lead directly for:
- Task clarification
- Technical questions
- Blockers
- Timeline adjustments

Contact tech lead for:
- Cross-epic issues
- Architecture questions
- Major blockers
- Career development

---

**Last Updated:** [Date]  
**Next Review:** End of Week 1  
**Project Manager:** [Name]  
**Tech Lead:** [Name]
