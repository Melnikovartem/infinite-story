# Test Suite - Infinite Story Engine v2

Comprehensive testing infrastructure for ISE v2 across all epics (E0-E3) and integration scenarios.

## Quick Start

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_e0_models.py -v

# Run specific test
pytest tests/test_e0_models.py::TestStoryModel::test_story_creation -v
```

## Test Files

### E0 - Data Layer

**`test_e0_models.py`** - Story models and data structures
- Story creation and management
- StorySegment model validation
- Character and Location models
- StoryChoice model
- Text block types
- Serialization/deserialization
- Edge cases and error handling

**Coverage:**
- ✅ Story CRUD operations
- ✅ Segment parent-child relationships
- ✅ Character and Location management
- ✅ Choice creation and status tracking
- ✅ Text block formatting
- ✅ Model serialization to JSON
- ✅ Long descriptions and special characters

### E0+E1 Integration

**`test_e0_e1_integration.py`** - Data layer + Generation pipeline
- Segment chain traversal
- Multi-episode progression
- Context building from segments
- Choice creation and handling
- Generated segment creation
- Data persistence across operations
- Branching scenarios
- Episode transitions

**Coverage:**
- ✅ Segment connectivity
- ✅ Context accumulation from chains
- ✅ Choice pointing to targets
- ✅ Generation triggers
- ✅ Pacing and proximity tracking
- ✅ Long segment chains (50+ segments)

### API Tests

**`test_api_*.py`** - REST API endpoints
- Story API (`test_api_stories.py`)
- Session management (`test_api_sessions.py`)
- Progress tracking (`test_api_progress.py`)
- Reports and analytics (`test_api_reports.py`)

### Generation & Characters

**`test_generation_pipeline.py`** - E1: Generation engine
**`test_character_*.py`** - E2: Character management
**`test_end_to_end_game_flow.py`** - Full system integration

## Fixtures

Available in `conftest.py`:

### Base Fixtures

- `sample_story` - Basic test story
- `sample_segment` - Test segment with content
- `sample_character` - Test character
- `sample_location` - Test location
- `sample_choice` - Test choice

### Complex Fixtures

- `three_segment_chain` - 3 connected segments
- `multi_episode_chain` - Segments across episodes
- `mock_generator` - Mocked AI generator
- `fixtures_dir` - Test data directory
- `clear_test_data` - Auto cleanup

### Factories

```python
from conftest import (
    factory_segment,
    factory_choice,
    factory_character,
    factory_location
)

# Create with defaults
seg = factory_segment(story)

# Create with custom values
seg = factory_segment(
    story,
    id="custom",
    episode_number=5,
    segment_number=3
)
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### By Category
```bash
# E0 tests only
pytest tests/test_e0_models.py -v

# Integration tests
pytest tests/test_e0_e1_integration.py -v

# API tests
pytest tests/test_api*.py -v

# End-to-end tests
pytest tests/test_end_to_end_game_flow.py -v
```

### By Pattern
```bash
# Tests matching pattern
pytest tests/ -k "segment" -v

# Tests containing "save"
pytest tests/ -k "save" -v

# Exclude slow tests
pytest tests/ -m "not slow" -v
```

### With Coverage
```bash
# Generate HTML report
pytest tests/ --cov=app --cov-report=html

# Open report
open htmlcov/index.html

# Show missing lines
pytest tests/ --cov=app --cov-report=term-missing
```

### Watch Mode
```bash
# Install pytest-watch
pip install pytest-watch

# Watch and re-run
ptw tests/
```

## Test Structure

Each test file follows this pattern:

```python
class TestFeature:
    """Test feature/component"""
    
    def test_basic_operation(self, fixture):
        """Test basic functionality"""
        # Arrange - set up data
        # Act - perform action
        # Assert - verify result
        assert result == expected
    
    def test_edge_case(self):
        """Test edge case"""
        # Handle unusual input/state
        pass
```

## Writing Tests

### Simple Test
```python
def test_story_has_title(sample_story):
    assert sample_story.title == "Test Story"
```

### Test with Fixtures
```python
def test_segment_in_chain(three_segment_chain):
    seg1, seg2, seg3 = three_segment_chain
    assert seg2.parent_segment_id == seg1.id
```

### Test with Setup/Teardown
```python
@pytest.fixture
def custom_story():
    story = Story(...)
    yield story
    story.delete()

def test_with_cleanup(custom_story):
    assert custom_story.title == "Test"
```

### Async Test
```python
@pytest.mark.asyncio
async def test_generation():
    result = await generator.generate_scene(prompt)
    assert result is not None
```

### Parametrized Test
```python
@pytest.mark.parametrize("episode", [1, 2, 3, 4, 5])
def test_episode_numbers(episode):
    seg = StorySegment(story=story, episode_number=episode)
    assert seg.episode_number == episode
```

### Test with Exception
```python
def test_invalid_story_fails():
    with pytest.raises(ValueError):
        Story(id="", title="", genre="")
```

## Coverage Goals

- **Overall:** >80%
- **New code:** 100%
- **Critical paths:** >90%

Check coverage:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Performance Testing

Performance tests establish baselines:

```bash
# Run performance tests
pytest tests/test_performance.py -v --benchmark-only

# Compare to baseline
pytest tests/test_performance.py --benchmark-compare
```

Targets:
- Segment creation: < 10ms
- Context building: < 50ms
- Save/load: < 100ms
- Generation: < 5 seconds
- Memory: < 100MB

## Mocking

### Mock Generator

```python
def test_generation(mock_generator):
    # Queue response
    mock_generator.add_response("Generated text")
    
    # Use in test
    text = asyncio.run(mock_generator.generate_scene("prompt"))
    assert "Generated" in text
```

### Mock External Calls

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_api():
    mock = AsyncMock()
    mock.get_data.return_value = {"data": "test"}
    return mock
```

## Debugging Tests

### Run with Verbose Output
```bash
pytest tests/ -vv -s
```

The `-s` flag shows print statements.

### Run Single Test
```bash
pytest tests/test_file.py::TestClass::test_method -vv
```

### Debug with pdb
```python
def test_debug():
    import pdb; pdb.set_trace()  # Breakpoint
    result = function()
```

### Show Local Variables
```bash
pytest tests/ -l  # Show local vars on failure
```

## CI/CD Integration

Tests run automatically:
- On every push
- On pull requests
- On schedule (nightly)

View results:
1. Go to Actions tab
2. Select workflow run
3. View test summary and logs

## Test Data

Test fixtures are stored in `fixtures/`:
- `sample_story.json` - Sample story data
- `sample_segments.json` - Sample segments

Add more:
```python
@pytest.fixture
def custom_fixture_json(fixtures_dir):
    data = {"key": "value"}
    file_path = fixtures_dir / "custom.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    yield file_path
    
    file_path.unlink()  # Cleanup
```

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
cd backend
pytest tests/
```

### Fixture Not Found

**Problem:** `fixture 'sample_story' not found`

**Solution:**
1. Check `conftest.py` has the fixture
2. Ensure file is named `conftest.py`
3. Verify fixture is in tests directory

### Tests Timeout

**Problem:** Test hangs indefinitely

**Solution:**
```bash
# Run with timeout
pytest tests/ --timeout=10  # 10 second timeout

# Debug async issues
# Check for missing @pytest.mark.asyncio
```

### Flaky Tests

**Problem:** Test passes sometimes, fails others

**Solution:**
1. Identify timing dependencies
2. Use proper async/await
3. Mock time-dependent code
4. Add retries if needed:
   ```python
   @pytest.mark.flaky(reruns=3)
   def test_flaky():
       pass
   ```

## Best Practices

1. **Descriptive names** - Test name explains what's tested
2. **One assertion** - Test one thing per test
3. **Use fixtures** - Don't repeat setup code
4. **Mock externals** - Don't call real APIs
5. **Test behavior** - Not implementation details
6. **Arrange-Act-Assert** - Clear test structure
7. **Fast feedback** - Keep tests under 100ms
8. **Deterministic** - Same result every time

## Documentation

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Testing Guide](../docs/TESTING.md)
- [EPIC_4_TESTING.md](../../developers/EPIC_4_TESTING.md)

## Contributing

When adding tests:

1. Follow naming conventions (`test_*.py`, `Test*`, `test_*`)
2. Use descriptive names
3. Add docstrings
4. Use fixtures from `conftest.py`
5. Aim for >80% coverage
6. Run full suite before submitting PR

```bash
# Before PR
pytest tests/ -v --cov=app --cov-report=term-missing
black --check tests/
flake8 tests/
```

## Contact

For testing questions, check:
- This README
- [TESTING.md](../docs/TESTING.md)
- Test file docstrings
- pytest docs

---

**Keep tests fast, clear, and comprehensive!**
