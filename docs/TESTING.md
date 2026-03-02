# Testing Guide - Infinite Story Engine v2

This guide covers testing strategies, setup, running tests, and best practices for ISE v2.

## Quick Start

```bash
# Install test dependencies
cd backend
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_e0_models.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run tests in watch mode
pytest-watch tests/
```

## Test Organization

The test suite is organized by epic:

```
backend/tests/
├── conftest.py                    # Shared fixtures & factories
├── test_e0_models.py              # E0: Data Layer models
├── test_e0_e1_integration.py      # E0 + E1: Integration
├── test_api_basic.py              # API endpoints
├── test_generation_pipeline.py    # E1: Generation
├── test_character_*.py            # E2: Characters
├── test_end_to_end_game_flow.py   # Full system tests
└── fixtures/
    ├── sample_story.json
    └── sample_segments.json
```

## Test Categories

### Unit Tests
Test individual functions and classes in isolation.

**Speed:** < 1ms per test  
**Characteristics:** No I/O, mocked dependencies, deterministic

**Example:**
```python
def test_story_creation():
    story = Story(
        id="test",
        title="Test",
        genre="Fantasy",
        user_id="user",
        start_segment_id="start"
    )
    assert story.title == "Test"
```

### Integration Tests
Test multiple components working together.

**Speed:** < 100ms per test  
**Characteristics:** Real I/O, component interaction, contract verification

**Example:**
```python
def test_segment_save_and_load(sample_segment):
    # Save a segment
    sample_segment.save()
    
    # Load it back
    loaded = StorySegment.load(...)
    
    # Verify it's the same
    assert loaded.id == sample_segment.id
```

### End-to-End Tests
Test complete user journeys and full system flows.

**Speed:** < 5s per test  
**Characteristics:** Real data, multiple subsystems, realistic scenarios

**Example:**
```python
@pytest.mark.asyncio
async def test_full_game_loop():
    runner = StoryRunner(story)
    runner.start()
    
    # Make choices
    choice = runner.current_segment.outgoing_choices[0]
    new_segment = await runner.execute_choice(choice.id)
    
    assert new_segment is not None
```

## Fixtures

Fixtures provide reusable test data and setup/teardown.

### Base Fixtures

**`sample_story`** - A test story with minimal data
```python
def test_something(sample_story):
    assert sample_story.id == "test_story_sample"
```

**`sample_segment`** - A test segment with text blocks and characters
```python
def test_segment(sample_segment):
    assert len(sample_segment.text_blocks) > 0
```

**`sample_character`** - A test character
**`sample_location`** - A test location
**`sample_choice`** - A test choice

### Complex Fixtures

**`three_segment_chain`** - 3 connected segments
```python
def test_chain(three_segment_chain):
    seg1, seg2, seg3 = three_segment_chain
    assert seg2.parent_segment_id == seg1.id
```

**`multi_episode_chain`** - Segments across multiple episodes
**`mock_generator`** - Mocked text generator for testing without API calls

### Using Fixtures

```python
def test_example(sample_story, sample_character, three_segment_chain):
    # Fixtures are injected as parameters
    seg1, seg2, seg3 = three_segment_chain
    
    # Use them in your test
    choice = StoryChoice(
        story=sample_story,
        id="choice_1",
        from_segment_id=seg1.id,
        to_segment_id=seg2.id
    )
    
    assert choice is not None
```

## Factories

Factories create test objects with default values that can be overridden.

```python
from conftest import factory_segment, factory_choice, factory_character

def test_custom_segment(sample_story):
    # Create with defaults
    seg = factory_segment(sample_story)
    assert seg.id == "seg_factory"
    
    # Override specific values
    custom = factory_segment(
        sample_story,
        id="custom_seg",
        episode_number=5
    )
    assert custom.episode_number == 5
```

## Mock Generator

For testing generation without API calls:

```python
def test_generation(sample_segment, mock_generator):
    # Queue responses
    mock_generator.add_response("Generated scene text")
    
    # Use in test
    text = asyncio.run(mock_generator.generate_scene("prompt"))
    assert "Generated" in text
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Test File
```bash
pytest tests/test_e0_models.py -v
```

### Specific Test Class
```bash
pytest tests/test_e0_models.py::TestStoryModel -v
```

### Specific Test Function
```bash
pytest tests/test_e0_models.py::TestStoryModel::test_story_creation -v
```

### With Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run Only Fast Tests
```bash
pytest tests/ -v -m "not slow"
```

### Run in Watch Mode
```bash
pip install pytest-watch
ptw tests/
```

This re-runs tests whenever you save a file.

### Run with Detailed Output
```bash
pytest tests/ -vv -s
```

The `-s` flag shows print statements

## Writing Tests

### Basic Test Pattern

```python
import pytest
from app.models import Story

def test_story_has_title(sample_story):
    """Test that a story has a title"""
    assert sample_story.title == "Test Story"
```

### Test with Setup and Teardown

```python
@pytest.fixture
def custom_story():
    # Setup
    story = Story(...)
    yield story
    # Teardown
    story.delete()

def test_with_cleanup(custom_story):
    assert custom_story.title == "Test"
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_generation():
    result = await generator.generate_scene("prompt")
    assert result is not None
```

### Testing Exceptions

```python
def test_invalid_story_fails():
    with pytest.raises(ValueError):
        Story(id="", title="", genre="")
```

### Parametrized Tests

```python
@pytest.mark.parametrize("genre", ["Fantasy", "SciFi", "Horror"])
def test_story_genres(genre):
    story = Story(
        id="test",
        title="Test",
        genre=genre,
        user_id="user",
        start_segment_id="start"
    )
    assert story.genre == genre
```

## Performance Testing

Establish and track performance baselines:

```bash
pytest tests/test_performance.py -v --benchmark-only
```

Performance targets:
- **Segment creation:** < 10ms
- **Context building:** < 50ms
- **Save/load:** < 100ms
- **Generation:** < 5 seconds
- **Memory:** < 100MB typical

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop`
- All pull requests
- Scheduled nightly runs

See `.github/workflows/test.yml` for details.

### Pre-Commit Checks

Before committing, run:
```bash
# Run tests
pytest tests/ -v

# Check code formatting
black --check app tests

# Check linting
flake8 app tests

# Check types
mypy app --ignore-missing-imports
```

Or create a git hook:
```bash
#!/bin/bash
pytest tests/ || exit 1
black --check app tests || exit 1
flake8 app tests || exit 1
```

## Common Issues

### Tests Fail: "No module named 'app'"
**Solution:** Make sure you're running pytest from the `backend/` directory:
```bash
cd backend
pytest tests/ -v
```

### Tests Hang on Async
**Solution:** Ensure pytest-asyncio is installed and tests use `@pytest.mark.asyncio`:
```bash
pip install pytest-asyncio
```

### Fixture Not Found
**Solution:** Check that `conftest.py` is in the tests directory and has the fixture defined:
```bash
# Should see fixture name in:
pytest tests/ --fixtures | grep fixture_name
```

### Test Data Not Cleaning Up
**Solution:** Use the `clear_test_data` fixture:
```python
def test_cleanup(clear_test_data):
    # Test runs with clean data
    # Auto-cleans up afterward
    pass
```

## Best Practices

1. **One assertion per test** - Easier to debug failures
   ```python
   # Good
   def test_story_title(sample_story):
       assert sample_story.title == "Test Story"
   
   # Avoid
   def test_story_properties(sample_story):
       assert sample_story.title == "Test Story"
       assert sample_story.genre == "Fantasy"  # Separate test
   ```

2. **Use descriptive names** - Test name should describe what's tested
   ```python
   # Good
   def test_segment_cannot_reference_itself_as_parent()
   
   # Avoid
   def test_segment1()
   ```

3. **Test behavior, not implementation** - Don't tie tests to internal details
   ```python
   # Good
   assert segment.parent_segment_id == parent.id
   
   # Avoid (testing internals)
   assert segment._parent_ref[0] == parent._id_internal
   ```

4. **Use fixtures for common setup** - Don't repeat initialization
   ```python
   # Good - use fixture
   def test_example(sample_story):
       pass
   
   # Avoid - manual setup
   def test_example():
       story = Story(...)
   ```

5. **Mock external dependencies** - Don't call real APIs
   ```python
   # Good - use mock
   def test_generation(mock_generator):
       result = mock_generator.generate_scene("prompt")
   
   # Avoid - calls real API
   def test_generation():
       result = TextGenerator().generate_scene("prompt")
   ```

## Coverage Goals

Aim for >80% code coverage:

```bash
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

Check `htmlcov/index.html` for coverage details by file.

## Continuous Testing

Set up continuous testing during development:

```bash
# Terminal 1: Watch for test changes
ptw tests/

# Terminal 2: Watch for code changes and run affected tests
pytest tests/ -v --lf  # Last failed

# Terminal 3: Your editor
# Make changes, save, tests run automatically
```

## Documentation Tests

Document examples in code:

```python
def example_story_creation():
    """
    Example of creating a story:
    
    >>> story = Story(
    ...     id="example",
    ...     title="My Story",
    ...     genre="Fantasy",
    ...     user_id="user1",
    ...     start_segment_id="start"
    ... )
    >>> story.title
    'My Story'
    """
```

Run doctests:
```bash
pytest --doctest-modules app/
```

## Contributing Tests

When adding features:

1. Write tests first (TDD style)
2. Make tests pass with implementation
3. Ensure >80% coverage of new code
4. Run full test suite before PR
5. Include test updates in PR

---

**For questions or issues with tests, check the test output carefully - pytest provides detailed failure messages.**
