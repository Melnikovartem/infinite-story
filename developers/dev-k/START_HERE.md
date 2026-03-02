# Welcome, Developer K!

**Epic:** Testing & Operations (E4)  
**Duration:** 4+ weeks (runs throughout all epics)  
**Your Role:** Mid-Senior Engineer, supporting Epic Lead J

---

## Your Mission

You're completing the testing & ops infrastructure:

1. **E4-2** (1 week): CI/CD Pipeline
   - GitHub Actions workflows
   - Automated testing on every PR
   - Code coverage tracking
   - Linting & type checking

2. **E4-3** (1 week): Performance Testing
   - Segment creation, context building, save/load benchmarks
   - Memory usage tests
   - Generation latency tests
   - Regression detection

3. **E4-5** (ongoing): Testing Documentation
   - How to run tests
   - Testing patterns and fixtures
   - Performance baselines
   - CI/CD explanation

You work alongside Dev-J. Coordinate daily.

**Blocker:** None (start in parallel with E0)

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_4_TESTING.md** (focus on E4-2, E4-3, E4-5)
3. **Review GitHub Actions documentation** (CI/CD concepts)

---

## Your Epic Tasks

### E4-2: CI/CD Pipeline (1 week)

**Files:** `.github/workflows/` (CREATE NEW)

Create two main workflows:

**test.yml** → Test suite runs on every PR
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - checkout
      - setup Python
      - install dependencies
      - run pytest
      - upload coverage
      - type check
      - build Docker image (if main)
```

**lint.yml** → Code quality checks
```yaml
on: [push, pull_request]
jobs:
  lint:
    steps:
      - run black (formatting)
      - run isort (import sorting)
      - run flake8 (linting)
      - commit fixes if needed
```

See `EPIC_4_TESTING.md` section "E4-2" for complete workflows.

**Acceptance Criteria:**
- [ ] test.yml created and working
- [ ] lint.yml created and working
- [ ] Tests run on every push/PR
- [ ] Code coverage tracked
- [ ] Linting enforced
- [ ] Type checking configured
- [ ] PR cannot merge if tests fail
- [ ] README has badges (build status, coverage)

### E4-3: Performance Testing (1 week)

**File:** `backend/tests/test_performance.py` (CREATE NEW)

Write performance benchmarks:

```python
def test_segment_creation_speed(benchmark):
    """Creating segment should be fast (<10ms)"""
    def create():
        return StorySegment(...)
    result = benchmark(create)

def test_context_building_speed(benchmark):
    """Building context should be fast (<50ms)"""
    ...

def test_generation_latency(benchmark):
    """Full generation should complete (<5 seconds)"""
    ...

def test_memory_usage():
    """Peak memory should be reasonable (<100MB)"""
    ...
```

Baselines:
- Segment creation: < 10ms
- Context building: < 50ms
- Save/load cycle: < 100ms
- Full generation: < 5 seconds
- Memory: < 100MB typical

See `EPIC_4_TESTING.md` section "E4-3" for full code.

**Acceptance Criteria:**
- [ ] Performance baselines established
- [ ] Segment creation < 10ms ✓
- [ ] Context building < 50ms ✓
- [ ] Save/load < 100ms ✓
- [ ] Generation < 5s ✓
- [ ] Memory < 100MB ✓
- [ ] Benchmarks tracked
- [ ] Regressions detected on CI

### E4-5: Testing Documentation (ongoing)

**File:** `docs/TESTING.md` (CREATE NEW)

Document:

1. How to run tests
   ```bash
   pytest tests/ -v
   pytest tests/test_story_models.py -v
   pytest --cov=app --cov-report=html
   ```

2. Test structure (units, integration, E2E)

3. Writing tests (fixtures, mocking, async)

4. Performance testing (`--benchmark-only`)

5. CI/CD explanation (what runs where)

See `EPIC_4_TESTING.md` section "E4-5" for full documentation.

**Acceptance Criteria:**
- [ ] Testing guide comprehensive
- [ ] Setup instructions clear
- [ ] Examples provided
- [ ] Common patterns documented
- [ ] Performance testing explained

---

## Collaboration

- **Daily standup** with Dev-J
- **Coordinate** test timing with E0-E3 leads
- **Code reviews** for all CI/CD PRs

---

## Key Files

```
.github/workflows/
  ├── test.yml     ← YOU CREATE
  └── lint.yml     ← YOU CREATE

backend/tests/
  └── test_performance.py ← YOU CREATE

docs/
  └── TESTING.md   ← YOU CREATE
```

---

## Performance Baselines

Track these metrics:

| Operation | Target | Actual |
|-----------|--------|--------|
| Segment creation | < 10ms | ? |
| Context building | < 50ms | ? |
| Save/load cycle | < 100ms | ? |
| Full generation | < 5s | ? |
| Memory usage | < 100MB | ? |

Run benchmarks regularly to catch regressions.

---

## CI/CD Flow

```
Developer pushes:
  ↓
GitHub Actions triggered:
  ├─ Test (pytest)
  ├─ Lint (black, flake8)
  ├─ Type check (mypy)
  ├─ Coverage report
  └─ Performance baseline
  ↓
All checks pass?
  ├─ Yes → PR can merge
  └─ No → PR blocked, developer fixes
```

---

## Commits

```bash
git commit -m "E4-2: setup github actions for testing and linting"
git commit -m "E4-3: add performance benchmarks and regression detection"
git commit -m "E4-5: create comprehensive testing documentation"
```

---

## Next Action

→ Open `EPIC_4_TESTING.md` section E4-2. Start with GitHub Actions setup.

You're automating quality assurance! 🤖
