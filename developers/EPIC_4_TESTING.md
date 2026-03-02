# Epic 4: Testing & Operations

**For Developers J, K**  
**Duration:** 4+ weeks (runs throughout all epics)  
**Blocker:** None (work in parallel with E0-E3)  
**Deliverable:** Test suite, CI/CD pipeline, performance testing, documentation

---

## What You're Building

Testing is continuous. Your job is to:

1. **Write comprehensive tests** for all other epics as they complete
2. **Set up CI/CD pipeline** (GitHub Actions) to run tests on every PR
3. **Performance testing** to ensure v2 doesn't regress
4. **Documentation** of testing patterns and procedures
5. **Ops scripts** for deployment, rollback, monitoring
6. **QA checklists** for each epic's deliverables

This prevents bugs from reaching production and ensures all epics integrate smoothly.

---

## Files You'll Touch

### Test Infrastructure (Create/Enhance)
- `backend/tests/` → Comprehensive test suite
- `backend/tests/conftest.py` → Fixtures and factories (started by E0)
- `.github/workflows/` → **NEW** (CI/CD pipelines)

### Ops & Documentation
- `backend/scripts/` → Deployment and utility scripts
- `docs/TESTING.md` → **NEW** (testing guide)
- `docs/CI_CD.md` → **NEW** (pipeline documentation)

---

## Task Breakdown

### E4-1: Comprehensive Test Suite (Dev-J, 2 weeks ongoing)

**What:** Write unit & integration tests for all features as E0-E3 complete.

**File:** `backend/tests/` (CREATE & ENHANCE)

**Strategy:**
- **Unit tests**: Individual components (models, functions)
- **Integration tests**: Full flows (context building → generation → recap)
- **Edge case tests**: Error handling, missing data, contradictions
- **Fixtures**: Reusable test data and factories

**Test Structure:**

```
backend/tests/
├── conftest.py                    # Shared fixtures
├── test_story_models.py           # Model validation (E0)
├── test_segment_context.py        # Context building (E1)
├── test_generation_pipeline.py    # Generation flow (E1)
├── test_episode_system.py         # Episodes & recaps (E2)
├── test_arc_compression.py        # Arc compression (E2)
├── test_cli_modes.py              # CLI modes (E3)
├── test_integration_e0_e1.py      # E0 + E1 together
├── test_integration_e1_e2.py      # E1 + E2 together
├── test_integration_full.py       # Full system end-to-end
└── fixtures/
    ├── sample_story.json          # Reusable test data
    └── sample_segments.json       # Pre-generated test segments
```

**Test Examples:**

```python
# test_segment_context.py
import pytest
from app.engine.segment_context_builder import SegmentContextBuilder

@pytest.fixture
def three_segment_chain(sample_story):
    """Create 3 connected segments in same episode"""
    seg1 = StorySegment(
        story=sample_story,
        id="seg_1",
        episode_number=1,
        change_notes=["Alice learns truth"]
    )
    seg2 = StorySegment(
        story=sample_story,
        id="seg_2",
        episode_number=1,
        parent_segment_id="seg_1",
        change_notes=["Alice becomes angry"]
    )
    seg3 = StorySegment(
        story=sample_story,
        id="seg_3",
        episode_number=1,
        parent_segment_id="seg_2",
        change_notes=["Alice confronts Bob"]
    )
    return [seg1, seg2, seg3]

class TestSegmentContextBuilder:
    def test_walk_episode_chain(self, three_segment_chain):
        """Walking backward collects all segments"""
        builder = SegmentContextBuilder(three_segment_chain[0].story)
        chain = builder._walk_episode_chain("seg_3")
        
        assert chain == ["seg_1", "seg_2", "seg_3"]
    
    def test_accumulate_changes(self, three_segment_chain):
        """All changes from chain are collected"""
        story = three_segment_chain[0].story
        builder = SegmentContextBuilder(story)
        
        changes = builder._accumulate_changes(
            ["seg_1", "seg_2", "seg_3"]
        )
        
        assert "Alice learns truth" in changes
        assert "Alice becomes angry" in changes
        assert "Alice confronts Bob" in changes
    
    def test_pacing_weight_progression(self, sample_story):
        """Pacing increases nonlinearly"""
        builder = SegmentContextBuilder(sample_story)
        
        weights = []
        for seg_num in [1, 5, 10, 15, 18]:
            seg = StorySegment(
                story=sample_story,
                id=f"seg_{seg_num}",
                segment_number_in_episode=seg_num
            )
            w = builder._calculate_pacing_weight(seg, False)
            weights.append(w)
        
        # Should increase, and increasingly so
        for i in range(len(weights) - 1):
            assert weights[i] < weights[i+1]
    
    def test_episode_transition_on_proximity(self, sample_story):
        """Episode transitions when proximity >= 0.8"""
        builder = SegmentContextBuilder(sample_story)
        
        seg_low = StorySegment(
            story=sample_story,
            id="seg_low",
            end_condition_proximity=0.5
        )
        seg_high = StorySegment(
            story=sample_story,
            id="seg_high",
            end_condition_proximity=0.85
        )
        
        assert builder._should_transition_episode(seg_low, []) is False
        assert builder._should_transition_episode(seg_high, []) is True

# test_integration_full.py (example of end-to-end)
@pytest.mark.asyncio
async def test_full_game_loop(sample_story, mock_generator):
    """
    Full flow: start story → display scene → make choice →
    generate new segment → display → repeat
    """
    runner = StoryRunner(sample_story)
    runner.generator = mock_generator
    runner.start()
    
    # First segment should be loaded
    assert runner.current_segment is not None
    assert runner.current_segment_id == sample_story.start_segment_id
    
    # Get available choices
    choices = runner.current_segment.outgoing_choices
    assert len(choices) >= 1
    
    # Pick a choice and execute
    first_choice = list(choices.values())[0]
    
    if first_choice.to_segment_id is None:
        # Will trigger generation
        new_seg = await runner.execute_choice(first_choice.id)
        
        # New segment should be created and saved
        assert new_seg.status == SegmentStatus.GENERATED
        assert new_seg.episode_number >= 1
        assert new_seg.parent_segment_id == runner.current_segment_id
    else:
        # Traverse to existing
        new_seg = await runner.execute_choice(first_choice.id)
        assert new_seg.id == first_choice.to_segment_id
    
    # State should be updated
    assert runner.current_segment_id == new_seg.id
    assert new_seg.id in runner.visited_segments
```

**Acceptance Criteria:**
- [ ] Unit tests for all models (story, segment, choice, etc.)
- [ ] Unit tests for all engine components (context, generation, recap, compression)
- [ ] Unit tests for CLI modes
- [ ] Integration tests for E0+E1, E1+E2, E0+E1+E2+E3
- [ ] Edge case tests (missing parent, archived segments, contradictions)
- [ ] Async tests working properly
- [ ] Fixtures and factories complete
- [ ] Test coverage > 80%
- [ ] All tests passing (pytest -v)

---

### E4-2: CI/CD Pipeline Setup (Dev-K, 1 week)

**What:** Automated testing & deployment via GitHub Actions.

**File:** `.github/workflows/` (CREATE NEW)

**Create `.github/workflows/test.yml`:**

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Lint with flake8
        run: |
          cd backend
          flake8 app tests --count --select=E9,F63,F7,F82 \
            --show-source --statistics
      
      - name: Format check with black
        run: |
          cd backend
          black --check app tests
      
      - name: Run tests with pytest
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          fail_ci_if_error: false
      
      - name: Type check with mypy
        run: |
          cd backend
          mypy app --ignore-missing-imports
        continue-on-error: true

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t infinite-story:latest \
            -f backend/Dockerfile .
      
      - name: Push to registry (if needed)
        run: echo "Docker image built successfully"
```

**Create `.github/workflows/lint.yml`:**

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.13"
      
      - name: Install linting tools
        run: |
          pip install flake8 black isort mypy
      
      - name: Run black
        run: black backend/app backend/tests
      
      - name: Run isort
        run: isort backend/app backend/tests
      
      - name: Run flake8
        run: flake8 backend/app backend/tests
      
      - name: Commit changes (if any)
        run: |
          git config user.email "actions@github.com"
          git config user.name "GitHub Actions"
          git add -A
          git commit -m "chore: auto-format code" || true
          git push || true
```

**Acceptance Criteria:**
- [ ] GitHub Actions workflows created and working
- [ ] Tests run on every push and PR
- [ ] Code coverage tracked
- [ ] Linting enforced (flake8, black)
- [ ] Type checking configured (mypy)
- [ ] PR cannot merge if tests fail
- [ ] Badge added to README

---

### E4-3: Performance Testing (Dev-K, 1 week)

**What:** Ensure v2 doesn't regress in speed or memory usage.

**File:** `backend/tests/test_performance.py` (CREATE NEW)

**Code:**

```python
import pytest
import asyncio
import time
from memory_profiler import profile
from app.models import Story, StorySegment
from app.engine.story_runner import StoryRunner
from app.engine.segment_context_builder import SegmentContextBuilder

class TestPerformance:
    """Performance benchmarks to prevent regressions"""
    
    def test_segment_creation_speed(self, benchmark, sample_story):
        """Creating a segment should be fast (<10ms)"""
        def create_segment():
            return StorySegment(
                story=sample_story,
                id="test",
                text_blocks=[],
                episode_number=1
            )
        
        result = benchmark(create_segment)
        # benchmark automatically measures time
    
    def test_context_building_speed(self, benchmark, three_segment_chain):
        """Building context for generation should be fast (<50ms)"""
        story = three_segment_chain[0].story
        builder = SegmentContextBuilder(story)
        
        def build_context():
            return builder.build_context("seg_3", "test choice")
        
        result = benchmark(build_context)
    
    def test_segment_save_load_speed(self, benchmark, sample_story):
        """Save/load cycle should be fast (<100ms)"""
        seg = StorySegment(
            story=sample_story,
            id="perf_test",
            text_blocks=[]
        )
        
        def save_and_load():
            seg.save()
            loaded = StorySegment.load(sample_story.id, "perf_test")
            return loaded
        
        result = benchmark(save_and_load)
    
    @pytest.mark.asyncio
    async def test_generation_latency(self, benchmark, sample_story, mock_generator):
        """Generation should complete in reasonable time (<5 seconds)"""
        runner = StoryRunner(sample_story)
        runner.generator = mock_generator
        runner.start()
        
        async def generate():
            choice = list(runner.current_segment.outgoing_choices.values())[0]
            await runner.execute_choice(choice.id)
        
        # Benchmark async function
        start = time.time()
        await generate()
        elapsed = time.time() - start
        
        assert elapsed < 5.0, f"Generation took {elapsed:.2f}s, expected < 5s"
    
    def test_memory_usage(self, sample_story):
        """Ensure story loading doesn't blow up memory"""
        import tracemalloc
        
        tracemalloc.start()
        
        # Load story multiple times
        for i in range(100):
            seg = StorySegment.load(
                sample_story.id,
                f"seg_{i}"
            )
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory should be reasonable (< 100MB)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Peak memory {peak_mb:.1f}MB exceeds limit"
    
    def test_query_performance(self, benchmark, sample_story):
        """Querying segments should be fast"""
        def list_segments():
            return StorySegment.list_all(sample_story.id)
        
        result = benchmark(list_segments)
```

**Run Performance Tests:**

```bash
cd backend
pytest tests/test_performance.py -v --benchmark-only
```

**Acceptance Criteria:**
- [ ] Performance baseline established
- [ ] Segment creation < 10ms
- [ ] Context building < 50ms
- [ ] Save/load < 100ms
- [ ] Generation < 5 seconds
- [ ] Memory usage < 100MB for typical story
- [ ] Benchmarks tracked over time
- [ ] Regressions detected on CI

---

### E4-4: Ops Scripts & Monitoring (Dev-J, 1 week)

**What:** Tools for deployment, rollback, health checks.

**Files:** `backend/scripts/` (CREATE NEW)

**Script: `deploy.sh`**

```bash
#!/bin/bash
# Deploy story engine to production

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "Deploying ISE v2 to $ENVIRONMENT..."

# 1. Run tests
echo "Running tests..."
cd backend
pytest tests/ -v || exit 1

# 2. Build
echo "Building..."
python -m pip install -r requirements.txt

# 3. Backup current data
echo "Backing up data..."
BACKUP_DIR=".infinite_story_data_backup_$(date +%s)"
cp -r .infinite_story_data "$BACKUP_DIR" || true

# 4. Run migrations if needed
echo "Running migrations..."
PYTHONPATH=. python scripts/migrate_v1_to_v2.py --all || {
    echo "Migration failed, restoring backup..."
    rm -rf .infinite_story_data
    cp -r "$BACKUP_DIR" .infinite_story_data
    exit 1
}

# 5. Start services
echo "Starting services..."
# (Docker/systemd/etc depending on setup)

# 6. Health check
echo "Running health checks..."
sleep 2
for i in {1..10}; do
    PYTHONPATH=. python -c \
        "from app.models import Story; \
         s = Story.load('test', 'test'); \
         print('✓ Health check passed')" && break || \
    { echo "Attempt $i failed..."; sleep 1; }
done

echo "✅ Deployment successful"
```

**Script: `rollback.sh`**

```bash
#!/bin/bash
# Rollback to previous deployment

set -e

BACKUP_DIR=${1:-.infinite_story_data_backup}

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "Rolling back from $BACKUP_DIR..."

# Stop services
echo "Stopping services..."
# systemctl stop infinite-story || true

# Restore data
echo "Restoring data..."
rm -rf .infinite_story_data
cp -r "$BACKUP_DIR" .infinite_story_data

# Start services
echo "Starting services..."
# systemctl start infinite-story

echo "✅ Rollback complete"
```

**Script: `health-check.py`**

```python
#!/usr/bin/env python3
"""Monitor story engine health"""

import asyncio
import time
from app.models import Story
from app.engine.story_runner import StoryRunner

async def check_health():
    """Run health checks"""
    checks = {
        'data_access': check_data_access,
        'generation': check_generation_ready,
        'archive': check_archive_system,
    }
    
    results = {}
    
    for name, check in checks.items():
        try:
            result = await check()
            results[name] = {'status': 'ok', 'message': result}
        except Exception as e:
            results[name] = {'status': 'error', 'message': str(e)}
    
    # Report
    for name, result in results.items():
        status = "✓" if result['status'] == 'ok' else "✗"
        print(f"{status} {name}: {result['message']}")
    
    all_ok = all(r['status'] == 'ok' for r in results.values())
    return all_ok

async def check_data_access():
    """Can we load a story?"""
    try:
        story = Story.load("test", "test")
        return "Story data accessible"
    except Exception as e:
        raise Exception(f"Data access failed: {e}")

async def check_generation_ready():
    """Is AI generator configured?"""
    from app.engine.generator import TextGenerator
    # Check if API keys are set
    return "Generator ready"

async def check_archive_system():
    """Archive queries working?"""
    # Test archive/non-archive queries
    return "Archive system OK"

if __name__ == "__main__":
    all_ok = asyncio.run(check_health())
    exit(0 if all_ok else 1)
```

**Acceptance Criteria:**
- [ ] Deploy script working
- [ ] Rollback script tested
- [ ] Health checks passing
- [ ] Backup created before deploy
- [ ] Migrations run safely
- [ ] Services restart correctly

---

### E4-5: Testing Documentation (Dev-J, ongoing)

**What:** Document testing patterns, setup, and procedures.

**File:** `docs/TESTING.md` (CREATE NEW)

**Content:**

```markdown
# Testing Guide

## Overview

ISE v2 uses comprehensive testing across units, integration, and end-to-end.

## Running Tests

### All tests
```bash
cd backend
pytest tests/ -v
```

### Specific test file
```bash
pytest tests/test_story_models.py -v
```

### Specific test
```bash
pytest tests/test_story_models.py::test_segment_creation -v
```

### With coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Structure

### Unit Tests
- One file per module
- Test individual functions/methods
- Use fixtures for setup
- Mock external dependencies

### Integration Tests
- Test multiple components together
- Use real data where possible
- Test error paths

### End-to-End Tests
- Full game loop
- Multiple epics together
- Real AI generator (or mock)

## Writing Tests

### Fixture Pattern
```python
@pytest.fixture
def sample_segment(sample_story):
    return StorySegment(
        story=sample_story,
        id="test",
        ...
    )
```

### Factory Pattern
```python
def factory_segment(story, id="test", **kwargs):
    return StorySegment(story=story, id=id, **kwargs)
```

### Async Tests
```python
@pytest.mark.asyncio
async def test_generation():
    result = await generate_scene(...)
    assert result is not None
```

## Performance Testing

Benchmark critical paths:
```bash
pytest tests/test_performance.py -v --benchmark-only
```

## CI/CD

Tests run automatically on:
- Push to main/develop
- Every pull request
- Scheduled nightly runs

See `.github/workflows/` for details.
```

**Acceptance Criteria:**
- [ ] Testing guide comprehensive
- [ ] Setup instructions clear
- [ ] Examples provided
- [ ] Common patterns documented
- [ ] Performance testing explained

---

## Definition of Done for Epic 4

- [ ] E4-1: Comprehensive test suite (>80% coverage)
- [ ] E4-2: CI/CD pipeline fully functional
- [ ] E4-3: Performance baseline established
- [ ] E4-4: Ops scripts created and tested
- [ ] E4-5: Testing documentation complete
- [ ] All tests passing
- [ ] No regressions introduced
- [ ] Code review completed
- [ ] Ready for production

---

## Key Concepts for E4

### Test Categories

1. **Unit Tests**: Individual functions
   - Fast (< 1ms)
   - No I/O, no async
   - Isolated with mocks

2. **Integration Tests**: Multiple components
   - Moderate speed (< 100ms)
   - Can use real I/O
   - Test contract between components

3. **End-to-End Tests**: Full system
   - Slower (< 5s)
   - Real data, real AI (mocked)
   - Test complete user journeys

### Fixture Hierarchy

```
conftest.py
  ├── sample_story (base fixture)
  ├── sample_segment (depends on sample_story)
  ├── three_segment_chain (depends on sample_story)
  └── mock_generator (independent)
```

### Performance Expectations

- Segment creation: < 10ms
- Context building: < 50ms
- Save/load cycle: < 100ms
- Full generation: < 5 seconds
- Memory: < 100MB typical

---

## Running Tests Continuously

### Local development
```bash
# Watch mode (re-run on file changes)
pytest-watch tests/

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Before committing
```bash
# Full test suite + linting
make test
make lint
```

### CI checks everything automatically
```
On push to PR:
  → Lint (black, flake8)
  → Type check (mypy)
  → Unit tests
  → Integration tests
  → Coverage report
  → Performance baseline
```

If any check fails, PR cannot merge. ✨
