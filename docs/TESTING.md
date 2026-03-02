# Testing Guide - Infinite Story Engine v2

## Overview

The Infinite Story Engine v2 uses a comprehensive testing approach across multiple levels:

- **Unit Tests**: Individual components (models, functions, methods)
- **Integration Tests**: Multiple components working together
- **End-to-End Tests**: Full game loop and system flows
- **Performance Tests**: Benchmarks to prevent regressions
- **API Tests**: HTTP endpoint validation

Current test coverage: **335+ passing tests** covering all major system components.

## Quick Start

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_story_models.py -v
```

### Run with Coverage Report

```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Only Performance Tests

```bash
pytest tests/test_performance.py -v --benchmark-only
```

### Watch Mode (Re-run on File Changes)

```bash
pip install pytest-watch
cd backend
ptw tests/
```

## Test Structure

### Directory Layout

```
backend/
├── tests/
│   ├── conftest.py                    # Shared fixtures and configuration
│   ├── fixtures/                      # Sample data and factories
│   ├── test_e0_models.py              # E0: Data models
│   ├── test_e0_e1_integration.py      # E0 + E1 integration
│   ├── test_story_models.py           # Story model tests
│   ├── test_story_segment.py          # Segment tests
│   ├── test_story_arc.py              # Arc system tests
│   ├── test_episode_recap.py          # Episode recap tests
│   ├── test_generation_pipeline.py    # Generation flow
│   ├── test_api_*.py                  # API endpoint tests
│   ├── test_character_*.py            # Character system tests
│   ├── test_auto_save*.py             # Auto-save functionality
│   ├── test_performance.py            # Performance benchmarks
│   └── test_end_to_end_game_flow.py   # Full game loop
├── app/
│   ├── models/                        # Data models
│   ├── engine/                        # Core generation engine
│   ├── api/                           # FastAPI routes
│   ├── services/                      # Business logic
│   └── utils/                         # Utility functions
└── scripts/
    ├── deploy.sh                      # Deployment automation
    ├── rollback.sh                    # Rollback script
    └── health-check.py                # System health monitoring
```

## Writing Tests

### Using Fixtures

Fixtures provide reusable test data and setup:

```python
import pytest

# Use a fixture from conftest.py
def test_story_creation(sample_story):
    assert sample_story.id == "test_story"
    assert sample_story.title == "Test Story"
```

### Common Fixtures

- `sample_story`: A basic Story instance
- `sample_segment`: A basic StorySegment
- `sample_character`: A basic StoryCharacter
- `sample_location`: A basic StoryLocation
- `sample_choice`: A basic StoryChoice
- `three_segment_chain`: A chain of 3 connected segments
- `mock_generator`: Mocked AI text generator

### Async Tests

Tests for async functions use the `@pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_async_generation(sample_story, mock_generator):
    result = await mock_generator.generate("test prompt")
    assert result is not None
```

### Mocking External Calls

Mock the AI generator to avoid API calls in tests:

```python
from unittest.mock import AsyncMock, MagicMock

def test_generation_with_mock(sample_story):
    mock_gen = AsyncMock()
    mock_gen.generate.return_value = "Generated text"
    
    # Use mock_gen in your test
```

### Testing Models

```python
def test_segment_creation(sample_story):
    """Test basic segment creation"""
    from app.models.story_segment import StorySegment
    
    segment = StorySegment(
        story=sample_story,
        id="test_seg",
        short_description="Test",
    )
    
    assert segment.id == "test_seg"
    assert segment.story == sample_story
```

### Testing API Endpoints

```python
from fastapi.testclient import TestClient

def test_api_endpoint(client):
    response = client.get("/api/stories")
    assert response.status_code == 200
    data = response.json()
    assert "stories" in data
```

## Markers and Categories

### Run Tests by Category

```bash
# Integration tests only
pytest tests/ -m integration -v

# Performance tests only
pytest tests/ -m performance -v

# Slow tests only
pytest tests/ -m slow -v

# Exclude slow tests
pytest tests/ -m "not slow" -v
```

### Available Markers

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.slow` - Slow-running tests

## Performance Testing

### Run Performance Benchmarks

```bash
cd backend
pytest tests/test_performance.py -v --benchmark-only
```

### Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Story creation | < 10ms | ✓ |
| Segment creation | < 10ms | ✓ |
| Context building | < 50ms | ✓ |
| Save/load cycle | < 100ms | ✓ |
| Full generation | < 5s | ✓ |
| Memory per story | < 100MB | ✓ |

## Coverage Reports

### Generate Coverage Report

```bash
cd backend
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

This creates an HTML report in `htmlcov/index.html` showing:
- Line-by-line coverage
- Missing lines
- Coverage percentage by file

### Coverage Goals

- Overall coverage: > 80%
- Models coverage: > 90%
- Engine coverage: > 85%
- Critical paths: > 95%

## CI/CD Integration

### Automated Testing

Tests run automatically on:
- Every push to `main`, `master`, `develop`
- Every pull request
- Nightly scheduled runs

See `.github/workflows/test.yml` for configuration.

### PR Requirements

Before merging a PR:
- ✅ All unit tests must pass
- ✅ All integration tests must pass
- ✅ Coverage must be > 80%
- ✅ No linting errors (flake8, black)
- ✅ Type checks pass (mypy, optional)
- ✅ Performance not regressed

## Debugging Tests

### Verbose Output

```bash
pytest tests/test_story_models.py::TestStoryModel::test_creation -vv
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Drop into Debugger

```python
def test_something():
    breakpoint()  # Debug here
    assert False
```

### Print Output

```python
def test_with_print(sample_story):
    print(f"Story: {sample_story}")
    print(f"ID: {sample_story.id}")
    # Run with: pytest -s tests/test_file.py
```

### Show Locals on Failure

```bash
pytest tests/ -l
```

## Common Issues

### Import Errors

If you get `ModuleNotFoundError`, ensure:
1. You're in the `backend/` directory
2. Run: `export PYTHONPATH=$(pwd):$PYTHONPATH`
3. Or ensure `conftest.py` adds the path (it should)

### Async Test Issues

Use `@pytest.mark.asyncio` and ensure:
- Event loop is running
- No blocking calls in async code
- Await async functions

### Fixture Dependencies

If a fixture depends on another:

```python
@pytest.fixture
def sample_segment(sample_story):  # Depends on sample_story
    return StorySegment(story=sample_story, ...)
```

Pytest handles dependency injection automatically.

### Database/File Issues

Tests use `.infinite_story_data/` directory:
- It's created automatically
- Can safely delete it to reset state
- CI tests run in isolation

## Continuous Development

### Before Committing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Check code style
black --check app tests
flake8 app tests

# Type check
mypy app --ignore-missing-imports
```

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd backend
pytest tests/ -q || exit 1
black app tests || exit 1
```

## Next Steps

- Read `EPIC_4_TESTING.md` for test specifications
- Check `backend/tests/conftest.py` for available fixtures
- See individual test files for patterns
- Review `.github/workflows/` for CI/CD setup

## Questions?

Refer to:
- **Test files**: `backend/tests/*.py` for examples
- **Fixtures**: `backend/tests/conftest.py` for available fixtures
- **CI/CD**: `.github/workflows/test.yml` for automation
- **Scripts**: `backend/scripts/` for deployment tools
