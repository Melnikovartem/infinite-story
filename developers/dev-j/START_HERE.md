# Welcome, Developer J!

**Epic:** Testing & Operations (E4)  
**Duration:** 4+ weeks (runs throughout all epics)  
**Your Role:** Senior Engineer, Epic Lead

---

## Your Mission

Testing is continuous. As E0-E3 develop, you'll ensure quality:

1. **E4-1** (2 weeks, ongoing): Comprehensive Test Suite
   - Unit tests for all models (E0)
   - Unit tests for all engine components (E1/E2)
   - Unit tests for CLI (E3)
   - Integration tests (E0+E1, E1+E2, full stack)
   - Edge case and error handling tests

2. **E4-4** (1 week): Ops Scripts & Monitoring
   - Deploy script with backup/migration
   - Rollback script
   - Health checks
   - Monitoring utilities

You work alongside other epics as they develop. Coordinate with leads.

**Blocker:** None (start in parallel with E0)

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_4_TESTING.md** (your blueprint)
3. **Look at existing tests** (`backend/tests/`) to understand patterns

---

## Your Epic Tasks

### E4-1: Comprehensive Test Suite (ongoing, 2+ weeks)

**File:** `backend/tests/` (CREATE & ENHANCE)

As each epic develops, write tests:

**Week 1: E0 Tests**
- `test_story_models.py` → Pydantic model validation
- Model serialization/deserialization
- Immutability locks
- Fixture + factory creation

**Week 2: E1 Tests**
- `test_segment_context.py` → Context builder (walk, accumulate, pacing)
- `test_generation_pipeline.py` → Traverse vs. generate, locking
- `test_generator_interface.py` → Validation, fallbacks

**Week 3: E2 Tests**
- `test_episode_system.py` → Recap generation
- `test_arc_compression.py` → Branch finding, mainline selection

**Week 4: E3 Tests**
- `test_cli_modes.py` → Both modes, state persistence

**Week 5+: Integration Tests**
- `test_integration_e0_e1.py` → Models + generation
- `test_integration_full.py` → Full game loop end-to-end

See `EPIC_4_TESTING.md` section "E4-1" for code examples and fixtures.

**Acceptance Criteria:**
- [ ] Unit tests for all components (>80% coverage)
- [ ] Integration tests for all epic combinations
- [ ] Edge case tests (errors, missing data, contradictions)
- [ ] Async tests working
- [ ] Fixtures and factories complete
- [ ] Performance baselines established

### E4-4: Ops Scripts & Monitoring (1 week)

**Files:** `backend/scripts/`

Create deployment utilities:

1. **deploy.sh** → Deploy to production
   - Run tests first
   - Backup existing data
   - Run migrations
   - Health checks
   - Rollback on failure

2. **rollback.sh** → Revert to previous version
   - Stop services
   - Restore backup
   - Restart

3. **health-check.py** → Monitor system health
   - Data access working
   - Generator ready
   - Archive system OK

See `EPIC_4_TESTING.md` section "E4-4" for full scripts.

**Acceptance Criteria:**
- [ ] Deploy script working
- [ ] Rollback tested
- [ ] Health checks passing
- [ ] Backup/restore working

---

## Dev-K's Work (Parallel)

While you lead E4-1/4, Dev-K will:
- E4-2: CI/CD Pipeline (GitHub Actions)
- E4-3: Performance Testing (benchmarks)
- E4-5: Testing Documentation

You coordinate. Keep testing holistic.

---

## Collaboration

- **Daily standup** with Dev-K
- **Coordinate with E0-E3 leads** on test timing
- **Code reviews** for all test PRs

---

## Test Structure

```
backend/tests/
├── conftest.py                  # Shared fixtures
├── test_story_models.py         # E0
├── test_segment_context.py      # E1
├── test_generation_pipeline.py  # E1
├── test_episode_system.py       # E2
├── test_arc_compression.py      # E2
├── test_cli_modes.py            # E3
├── test_integration_e0_e1.py    # E0 + E1
├── test_integration_full.py     # All together
├── test_performance.py          # Performance benchmarks (Dev-K)
└── fixtures/
    ├── sample_story.json
    └── sample_segments.json
```

---

## Commits

```bash
git commit -m "E4-1: add comprehensive unit tests for E0 data models"
git commit -m "E4-1: add integration tests for E0 + E1 generation pipeline"
git commit -m "E4-4: create deploy and rollback scripts with health checks"
```

---

## Testing Metrics to Track

- Code coverage (aim for > 80%)
- Test count (should grow each week)
- Pass/fail rate (100% passing always)
- Performance baselines (track regressions)

---

## Next Action

→ Open `EPIC_4_TESTING.md` section E4-1. Start with E0 test planning.

You're ensuring quality for everything else! ✅
