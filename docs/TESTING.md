# Testing Guide

## Overview

ISE v2 uses comprehensive testing across units, integration, and end-to-end. This guide covers how to run tests, write new tests, and maintain code quality.

## Quick Start

### Running All Tests

```bash
cd backend
pytest tests/ -v
```

### Running Specific Test File

```bash
pytest tests/test_story_models.py -v
```

### Running Specific Test

```bash
pytest tests/test_story_models.py::test_segment_creation -v
```

### With Coverage Report

```bash
pytest tests/ --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Performance Tests Only

```bash
pytest tests/test_performance.py -v --benchmark-only
```

## Test Structure

The test suite is organized by functionality:

```
backend/tests/
├── conftest.py                    # Shared fixtures
├── test_story_models.py           # Story, segment, choice models
├── test_segment_context.py        # Context building
├── test_generation_pipeline.py    # Generation flow
├── test_episode_system.py         # Episodes & recaps
├── test_arc_compression.py        # Arc compression
├── test_cli_modes.py              # CLI modes
├── test_performance.py            # Performance benchmarks
├── test_api_*.py                  # API endpoint tests
├── test_integration_*.py          # Integration tests
├── test_end_to_end_*.py           # End-to-end tests
└── fixtures/
    ├── sample_story.json          # Reusable test data
    └── sample_segments.json       # Pre-generated segments
```

### Test Categories

#### Unit Tests
- Test individual functions/methods
- Fast (< 1ms each)
- No I/O, no async
- Use mocks for dependencies
- Examples: `test_story_models.py`, `test_generation_pipeline.py`

#### Integration Tests
- Test multiple components together
- Moderate speed (< 100ms each)
- Can use real I/O
- Test contracts between components
- Examples: `test_integration_*.py`

#### End-to-End Tests
- Test full system flows
- Slower (< 5s each)
- Real data, mocked AI
- Test complete user journeys
- Examples: `test_end_to_end_game_flow.py`

#### Performance Tests
- Benchmark critical operations
- Verify no regressions
- Run with `--benchmark-only`
- Examples: `test_performance.py`

## Writing Tests

### Basic Test Pattern

```python
import pytest
from app.models import Story, StorySegment

class TestSegmentCreation:
    def test_segment_basic_creation(self, sample_story):
        """Segment is created with correct attributes."""
        seg = StorySegment(
            story=sample_story,
            id="test_seg",
            text_blocks=[]
        )
        
        assert seg.id == "test_seg"
        assert seg.story == sample_story
        assert len(seg.text_blocks) == 0
```

### Using Fixtures

Fixtures provide reusable test setup:

```python
@pytest.fixture
def sample_segment(sample_story):
    """Create a sample segment for testing."""
    return StorySegment(
        story=sample_story,
        id="test",
        text_blocks=[],
        episode_number=1
    )

def test_segment_episode(sample_segment):
    """Segment tracks episode number correctly."""
    assert sample_segment.episode_number == 1
```

#### Available Fixtures

- `sample_story` - Pre-configured Story instance
- `sample_segment` - Pre-configured StorySegment
- `three_segment_chain` - Three connected segments
- `mock_generator` - Mocked AI text generator

See `conftest.py` for all available fixtures.

### Factory Pattern for Complex Objects

```python
def factory_segment(story, id="test", episode=1, **kwargs):
    """Factory for creating segments with defaults."""
    return StorySegment(
        story=story,
        id=id,
        episode_number=episode,
        text_blocks=[],
        **kwargs
    )

def test_different_episodes():
    """Test segments in different episodes."""
    seg1 = factory_segment(sample_story, episode=1)
    seg2 = factory_segment(sample_story, episode=2)
    
    assert seg1.episode_number != seg2.episode_number
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_generation_async(mock_generator):
    """Test async generation."""
    result = await mock_generator.generate("test prompt")
    assert result is not None
    assert len(result) > 0
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock(mock_generator):
    """Test with mocked dependencies."""
    mock_generator.generate.return_value = "Generated text"
    
    result = mock_generator.generate("prompt")
    assert result == "Generated text"

def test_with_patch():
    """Test with patch decorator."""
    with patch('app.engine.generator.TextGenerator') as mock_gen:
        mock_gen.return_value.generate.return_value = "text"
        # Your test code here
```

### Parametrized Tests

```python
@pytest.mark.parametrize("episode,expected", [
    (1, "Act 1"),
    (2, "Act 2"),
    (3, "Act 3"),
])
def test_episode_names(sample_story, episode, expected):
    """Test episode naming for different numbers."""
    seg = StorySegment(
        story=sample_story,
        id="test",
        episode_number=episode
    )
    assert seg.get_episode_name() == expected
```

## Performance Testing

### Running Performance Benchmarks

```bash
cd backend
pytest tests/test_performance.py -v --benchmark-only
```

This runs all performance tests and prints comparison data:

```
test_performance.py::TestPerformance::test_segment_creation_speed PASSED [  5%]
  0.0023 sec per iteration (+-0.0001 sec)
```

### Performance Baselines

Target performance metrics:

| Operation | Target |
|-----------|--------|
| Segment creation | < 10ms |
| Story creation | < 5ms |
| Choice creation | < 5ms |
| Save/load cycle | < 100ms |
| Memory per 100 segments | < 10MB |

### Writing Performance Tests

```python
def test_operation_speed(benchmark, sample_story):
    """Operation should complete in X time."""
    def operation():
        return expensive_operation(sample_story)
    
    result = benchmark(operation)
    # Benchmark automatically verifies timing
```

## Code Quality

### Running Linters and Formatters

```bash
cd backend

# Format code with black
black app tests

# Sort imports
isort app tests

# Check code quality
flake8 app tests

# Type check
mypy app --ignore-missing-imports
```

### Checking Code Coverage

```bash
pytest tests/ --cov=app --cov-report=term-missing

# Generates HTML report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

Coverage targets:
- Overall: > 80%
- Critical paths: > 95%
- Utils: > 70%

## CI/CD Pipeline

Tests run automatically on:
- **Push to master/main**: Full test suite + linting
- **Pull requests**: Full test suite + linting
- **Performance regressions**: Tracked and reported
- **Coverage**: Reported and enforced

### GitHub Actions Workflows

#### Test Workflow (`.github/workflows/test.yml`)
Runs on every push and PR:
1. Setup Python environment
2. Install dependencies
3. Run linters (flake8, black)
4. Run tests with pytest
5. Generate coverage report
6. Type check with mypy
7. Build Docker image (on master only)

#### Lint Workflow (`.github/workflows/lint.yml`)
Auto-fixes code formatting:
1. Run black formatter
2. Run isort import sorter
3. Run flake8 linter
4. Commit fixes back to PR

### PR Requirements

A PR cannot merge until:
- ✅ All tests pass
- ✅ Code coverage maintained
- ✅ Linting passes
- ✅ Type checking passes
- ✅ Performance doesn't regress

## Common Testing Patterns

### Testing Error Cases

```python
def test_missing_required_field(sample_story):
    """Creating segment without required field raises error."""
    with pytest.raises(ValueError):
        StorySegment(story=sample_story)  # Missing id
```

### Testing State Changes

```python
def test_segment_status_transition(sample_segment):
    """Segment status changes correctly."""
    assert sample_segment.status == "draft"
    
    sample_segment.publish()
    assert sample_segment.status == "published"
```

### Testing Data Relationships

```python
def test_parent_child_relationship(three_segment_chain):
    """Segments maintain correct parent-child relationships."""
    seg1, seg2, seg3 = three_segment_chain
    
    assert seg2.parent_segment_id == seg1.id
    assert seg3.parent_segment_id == seg2.id
```

### Testing Collections

```python
def test_choice_list_filtering(sample_segment):
    """Choice lists filter correctly."""
    choices = sample_segment.get_available_choices()
    
    assert len(choices) > 0
    assert all(isinstance(c, StoryChoice) for c in choices)
```

## Debugging Tests

### Run Single Test with Output

```bash
pytest tests/test_story_models.py::test_segment_creation -v -s
```

The `-s` flag shows print statements.

### Run with Detailed Failure Info

```bash
pytest tests/ -v --tb=long
```

### Run with Debug Breakpoints

```python
def test_with_breakpoint(sample_segment):
    """Test with debugging."""
    breakpoint()  # Test will pause here when run
    assert sample_segment.id is not None
```

Then run:
```bash
pytest tests/ -s -v
```

### Run Slower Tests Only

```bash
pytest tests/ -v --durations=10  # Shows 10 slowest tests
```

## Fixture and Conftest Guide

### Common Fixtures in conftest.py

```python
@pytest.fixture
def sample_story():
    """Create a test story."""
    return Story(
        id="test_story",
        title="Test Story",
        summary="Test",
        characters={},
        custom_instructions=""
    )

@pytest.fixture
def mock_generator():
    """Mock text generator."""
    mock = Mock()
    mock.generate = AsyncMock(return_value="Generated text")
    return mock
```

### Fixture Scope

```python
@pytest.fixture(scope="session")  # Created once per test session
def expensive_setup():
    ...

@pytest.fixture(scope="function")  # Default - created for each test
def per_test_setup():
    ...
```

## Best Practices

### ✅ Do

- Write descriptive test names (`test_segment_creation_sets_id_correctly`)
- Test one thing per test function
- Use fixtures for common setup
- Test error cases and edge cases
- Keep tests fast (< 100ms for unit tests)
- Isolate tests (no dependencies between tests)
- Use meaningful assertions with messages

### ❌ Don't

- Write tests that depend on execution order
- Use global state in tests
- Make tests too complex
- Test implementation details instead of behavior
- Skip tests instead of fixing them
- Mix test categories (unit + integration)
- Leave debugging code in tests

## Troubleshooting

### Issue: "ModuleNotFoundError" in tests

**Solution**: Make sure you're in the backend directory:
```bash
cd backend
pytest tests/
```

### Issue: Async tests timeout

**Solution**: Increase timeout in pytest config:
```ini
[pytest]
asyncio_mode = auto
timeout = 30
```

### Issue: Tests pass locally but fail in CI

**Solution**: 
- Check Python version (CI uses 3.12 and 3.13)
- Verify all dependencies in requirements.txt
- Check for hardcoded paths or OS-specific code

### Issue: Flaky tests (sometimes pass, sometimes fail)

**Solution**:
- Avoid time-dependent assertions
- Mock external services
- Use proper fixtures for setup/teardown
- Increase timeouts if needed

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov coverage](https://pytest-cov.readthedocs.io/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Questions?

Contact Dev-J for test infrastructure questions or Dev-K for CI/CD questions.
