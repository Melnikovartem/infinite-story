# Project Board Template: Development Tasks

Use this as a template for your GitHub Project Board or Jira setup.

---

## 📋 Epic 0: Data Layer Foundation

**Status:** Not Started  
**Assignee:** Developer A (Lead)  
**Start Date:** Week 1, Day 1  
**End Date:** Week 1, Day 5  
**Blocked By:** None  
**Blocks:** E1, E2, E3

### Tasks

| Task | ID | Assignee | Status | Days | Priority |
|------|----|---------|-----------|----|----------|
| Enhance Segment Model | E0-1 | Dev A | Not Started | 3 | Critical |
| Create EpisodeRecap Model | E0-2 | Dev A | Not Started | 1 | Critical |
| Create StoryArc Model | E0-3 | Dev B | Not Started | 1 | Critical |
| Simplify UserSession | E0-4 | Dev B | Not Started | 1 | Critical |
| Create Migration Script | E0-5 | Dev C | Not Started | 2 | Critical |
| Test Infrastructure | E0-6 | Dev C | Not Started | 1 | Critical |

**Notes:**
- Dev A owns first 2 tasks (related to segments)
- Dev B can start in parallel on Arc/Session models
- Dev C starts migration script day 2
- Weekly sync: Friday EOD to review

---

## 📋 Epic 1: Generation Pipeline

**Status:** Blocked (waiting for E0)  
**Assignee:** Developer D (Lead)  
**Start Date:** Week 2, Day 1  
**End Date:** Week 3, Day 5  
**Blocked By:** E0  
**Blocks:** E3 (partially)

### Tasks

| Task | ID | Assignee | Status | Days | Priority |
|------|----|---------|-----------|----|----------|
| Segment Context Builder | E1-1 | Dev D | Not Started | 3 | Critical |
| Update Generation Pipeline | E1-2 | Dev D | Not Started | 3 | Critical |
| Enhanced Generator Interface | E1-3 | Dev E | Not Started | 2 | High |
| Segment Generation Implementation | E1-4 | Dev E | Not Started | 3 | Critical |
| Episode Transition Logic | E1-5 | Dev D | Not Started | 2 | Critical |

**Notes:**
- Dev D works on context and integration (interdependent)
- Dev E can start on generator updates in parallel
- Coordinate on _generate_segment() implementation (shared method)
- Daily standup on context building specifics

---

## 📋 Epic 2: Episode & Arc System

**Status:** Blocked (waiting for E0)  
**Assignee:** Developer F (Lead)  
**Start Date:** Week 2, Day 1  
**End Date:** Week 3, Day 5  
**Blocked By:** E0  
**Blocks:** E1 (episode integration)

### Tasks

| Task | ID | Assignee | Status | Days | Priority |
|------|----|---------|-----------|----|----------|
| Episode Recap Generator | E2-1 | Dev F | Not Started | 3 | Critical |
| New Episode Generation | E2-2 | Dev F | Not Started | 2 | Critical |
| Character State Reconciliation | E2-3 | Dev G | Not Started | 2 | High |
| Arc Compressor | E2-4 | Dev G | Not Started | 4 | Critical |
| Archive State Handling | E2-5 | Dev F | Not Started | 2 | High |

**Notes:**
- Dev F owns recap generation and new episode (sequential)
- Dev G owns reconciliation and compression (can overlap)
- Integrate with E1's context builder by end of Week 2
- Ensure Episode.recap fields match CharacterState

---

## 📋 Epic 3: CLI & User Interface

**Status:** Blocked (waiting for E0 + E1)  
**Assignee:** Developer H (Lead)  
**Start Date:** Week 2, Day 3  
**End Date:** Week 3, Day 5  
**Blocked By:** E0 (models), E1 (partially)  
**Blocks:** Integration tests

### Tasks

| Task | ID | Assignee | Status | Days | Priority |
|------|----|---------|-----------|----|----------|
| CLI Display Functions | E3-1 | Dev H | Not Started | 2 | High |
| CLI Choice Menus | E3-2 | Dev H | Not Started | 1 | High |
| Dev Commands | E3-3 | Dev I | Not Started | 2 | Medium |
| Update Main CLI Loop | E3-4 | Dev I | Not Started | 2 | Critical |
| Configuration System | E3-5 | Dev H | Not Started | 1 | High |

**Notes:**
- Dev H can start on display/config using mock data
- Dev I can stub out game loop structure early
- Integrate with E1's traverse_or_generate() by Week 2 Day 4
- Design system should support both modes

---

## 📋 Epic 4: Testing & Operations

**Status:** Not Started (ongoing)  
**Assignee:** Developer J (Lead)  
**Start Date:** Week 1 (E4-1 after E0 done, others concurrent)  
**End Date:** Week 5, Day 5  
**Blocked By:** Each epic provides test targets  
**Blocks:** Nothing (enabler)

### Tasks

| Task | ID | Assignee | Status | Days | Priority |
|------|----|---------|-----------|----|----------|
| Unit Test Suite | E4-1 | Dev J | Not Started | 3 | High |
| Integration Tests | E4-2 | Dev J | Not Started | 3 | Critical |
| Migration Testing | E4-3 | Dev K | Not Started | 2 | Critical |
| Performance Testing | E4-4 | Dev K | Not Started | 2 | High |
| CLI Testing | E4-5 | Dev J | Not Started | 2 | High |
| Manual Testing Checklist | E4-6 | QA | Not Started | Ongoing | High |

**Notes:**
- Dev J starts E4-1 once E0 models are stable (Week 1 Day 3)
- Dev K starts E4-3 once migration script done (Week 1 Day 4)
- Stagger integration tests as features complete (E4-2 starts Week 2)
- Performance testing Week 3 (all features ready)

---

## 📋 Integration & Finalization

**Status:** Planning  
**Assignee:** Tech Lead  
**Start Date:** Week 4, Day 1  
**End Date:** Week 5, Day 5

### Tasks

| Task | ID | Assignee | Status | Days | Priority |
|------|----|---------|-----------|----|----------|
| Merge All Branches | I-1 | All Leads | Not Started | 1 | Critical |
| End-to-End Testing | I-2 | Test Lead | Not Started | 2 | Critical |
| Documentation Update | I-3 | Tech Writer | Not Started | 1 | High |
| Production Readiness | I-4 | DevOps | Not Started | 1 | High |

---

## 🎯 Kanban Board Status

### Not Started
- E0-1 through E4-6 (all tasks)

### In Progress
- (None until Week 1 Day 1)

### Review
- (Code reviews as tasks complete)

### Done
- (Completed tasks)

---

## 📊 Burndown Chart Template

```
Week 1:
  Mon: 25 tasks remaining
  Tue: 23 tasks remaining
  Wed: 20 tasks remaining (E0-1 in progress)
  Thu: 18 tasks remaining (E0-1 complete, E0-2 in progress)
  Fri: 15 tasks remaining (E0-2,3,4 done, migration started)

Week 2:
  Mon: 12 tasks remaining (E0 complete, E1-E3 start)
  Tue: 10 tasks remaining
  ...

Week 3:
  Complete E1, E2, E3 (9 tasks)

Week 4:
  Integration & final testing

Week 5:
  Done!
```

---

## 🔄 Pull Request Template

```markdown
## PR Title
[Epic ID] Task Title - Brief Description

## Related Issue
Closes #[GitHub Issue]
Epic: E[0-4]-[number]

## Description
What does this PR do?
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added
- [ ] Integration tests passing
- [ ] Manual testing done
- [ ] No regressions

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Ready for merge

## Assignee
[Epic Lead]

## Label
e0-data-layer / e1-pipeline / e2-episodes / e3-cli / e4-testing
```

---

## 📅 Weekly Sync Agenda

### Every Friday, 4 PM

**Duration:** 1 hour

**Agenda:**
1. **Epic Status Reports** (45 min)
   - E0 Lead: Progress, blockers, next week
   - E1 Lead: Progress, blockers, next week
   - E2 Lead: Progress, blockers, next week
   - E3 Lead: Progress, blockers, next week
   - E4 Lead: Progress, blockers, next week
   
2. **Cross-Epic Issues** (10 min)
   - Integration points
   - Dependencies
   - Risks

3. **Action Items** (5 min)
   - Tasks for next week
   - Who's responsible

---

## 🚨 Escalation Path

**Blocker Found:**
1. Report in standup (daily)
2. Escalate to epic lead (same day)
3. If blocking multiple epics, escalate to tech lead (immediately)
4. Tech lead decides: accept delay, replan, or parachute

---

## 📞 Communication Channels

- **Daily Standup:** Slack thread (9 AM)
- **Weekly Sync:** Video call (Friday 4 PM)
- **Urgent Issues:** @tech-lead in Slack
- **Code Review:** GitHub PR comments
- **Questions:** #dev-infinite-story channel

---

## ✅ Definition of Done (Task)

A task is done when:

- [ ] Code written and compiles
- [ ] Unit tests written (>80% coverage for unit)
- [ ] Code reviewed by epic lead
- [ ] All review comments addressed
- [ ] Tests passing locally
- [ ] PR merged to feature branch
- [ ] Documented in PR description
- [ ] No known bugs

---

## ✅ Definition of Done (Epic)

An epic is done when:

- [ ] All tasks marked complete
- [ ] All tests passing (unit + integration)
- [ ] Code merged to main feature branch
- [ ] No blocking issues
- [ ] Integration testing scheduled
- [ ] Documentation updated

---

## 📍 Current Status (Update Daily)

**Last Updated:** [Date]

| Epic | Lead | Status | Progress | Est. Complete |
|------|------|--------|----------|----------------|
| E0 | Dev A | Not Started | 0% | Week 1 Fri |
| E1 | Dev D | Blocked | 0% | Week 3 Fri |
| E2 | Dev F | Blocked | 0% | Week 3 Fri |
| E3 | Dev H | Blocked | 0% | Week 3 Fri |
| E4 | Dev J | Not Started | 0% | Week 5 Fri |
| Integration | Tech Lead | Planning | 0% | Week 5 Fri |

---

## 🎯 Metrics to Track

- **Velocity:** Tasks completed per week
- **Burndown:** Tasks remaining vs. ideal
- **Test Coverage:** % of code covered by tests
- **Code Review Time:** Days in review before merge
- **Blocker Resolution Time:** Hours from reporting to resolution
- **Regression Count:** Bugs found in testing vs. fixed before release

---

## 📝 Notes

- **Time Zone:** [Your timezone]
- **Holidays:** [Any holidays to account for]
- **Vacation:** [Any team member vacations]
- **Office Days:** [If applicable]

---

**Board Owner:** Tech Lead  
**Last Updated:** [Date]  
**Next Review:** Weekly sync
