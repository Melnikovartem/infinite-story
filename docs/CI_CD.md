# CI/CD Pipeline Documentation

## Overview

The Infinite Story Engine uses GitHub Actions for continuous integration and continuous deployment (CI/CD). This ensures code quality, test coverage, and reliable deployments.

## Pipeline Architecture

```
Developer Pushes Code
    ↓
GitHub Actions Triggered
    ├─ Test (pytest with coverage)
    ├─ Lint (black, flake8, isort)
    ├─ Type Check (mypy)
    └─ Security (basic checks)
    ↓
All Checks Pass?
    ├─ Yes → PR can merge to master
    └─ No → PR blocked, developer fixes
    ↓
Merge to Master
    ↓
Deployment (Manual or Automatic)
```

## Workflows

### 1. Test Workflow (`.github/workflows/test.yml`)

Runs on every push and pull request.

**Matrix Testing:**
- Python 3.12
- Python 3.13

**Steps:**
1. Checkout code
2. Set up Python environment
3. Install dependencies
4. Run linting (flake8) - non-blocking
5. Format check (black) - non-blocking
6. Run tests with coverage (pytest)
7. Upload coverage to Codecov
8. Type check with mypy - non-blocking

**Requirements:**
- ✅ All tests must pass
- ⚠️ Linting warnings non-blocking (but visible)
- ⚠️ Type check warnings non-blocking

**Build Step:**
- Triggered only on `main`/`master` branches
- Requires test job to pass
- Runs basic import checks

### 2. Code Quality Workflow (`.github/workflows/lint.yml`)

Runs on every push and pull request for code quality checks.

**Steps:**
1. Code formatting (black)
2. Import sorting (isort)
3. Linting (flake8)
4. Type checking (mypy)

**Result:**
- Non-blocking warnings
- Helps maintain consistency
- Automated fixes possible (future)

## Running Tests Locally

Before pushing, test locally:

```bash
cd backend

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Lint check
black --check app tests
flake8 app tests
isort --check-only app tests

# Type check
mypy app --ignore-missing-imports
```

## Deployment

### Manual Deployment

```bash
# 1. Deploy to staging
cd backend/scripts
./deploy.sh staging

# 2. Test in staging
# ... run tests/smoke tests ...

# 3. Deploy to production
./deploy.sh production

# 4. Monitor health
python health-check.py
```

### Rollback

If deployment fails:

```bash
cd backend/scripts

# List available backups
ls -d .infinite_story_data_backup_*

# Rollback to specific backup
./rollback.sh .infinite_story_data_backup_20260302_140000
```

## Health Checks

### Automated Health Checks

Run after deployment:

```bash
cd backend
python3 scripts/health-check.py -v
```

### Manual Health Checks

**Check imports:**
```bash
python3 -c "from app.models.story import Story; print('OK')"
```

**Check data access:**
```bash
python3 -c "
from app.models.story import Story
s = Story(id='test', title='Test', genre='Test', user_id='test', start_segment_id='s1')
print(f'Story created: {s.id}')
"
```

**Check API:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Performance Baselines

### Establishing Baselines

Performance benchmarks are recorded in CI:

```
Test Name                          Min      Max      Mean     Median
test_story_creation_speed          1.2ms    2.5ms    1.5ms    1.4ms
test_segment_creation_speed        0.8ms    1.5ms    1.0ms    0.9ms
test_context_building_speed        20ms     45ms     30ms     28ms
test_segment_save_load_speed       50ms     110ms    70ms     65ms
```

### Detecting Regressions

Performance test failures trigger alerts:
- If segment creation > 10ms
- If context building > 50ms
- If save/load > 100ms
- If generation > 5s

## Debugging CI Failures

### View Workflow Logs

1. Go to GitHub repository
2. Click "Actions" tab
3. Select failed workflow
4. Click job for details
5. Expand logs

### Common Failures

**Tests fail:**
- Check test output in logs
- Run locally: `pytest tests/ -v`
- Fix and push again

**Coverage low:**
- Add missing tests
- Check `coverage.xml` report
- Target > 80% coverage

**Lint warnings:**
- Run black: `black app tests`
- Run isort: `isort app tests`
- Fix manually if needed

**Type check fails:**
- Add type hints to functions
- Check mypy output
- May be non-blocking depending on config

## Configuration

### Environment Variables (if needed)

Create `.env.local` for local development:
```
OPENROUTER_API_KEY=your_key
```

CI uses GitHub Secrets:
- Set in repository settings
- Available as environment variables
- Not logged or displayed

### Test Configuration

`backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = strict
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    asyncio
    integration
    performance
    slow
```

## Integration with Version Control

### Branch Strategy

- `develop`: Development branch, all tests must pass
- `master`/`main`: Production branch, only releases
- Feature branches: `feature/*`, all tests before PR

### PR Requirements

Before merging to master:
- ✅ All tests pass
- ✅ Coverage maintained
- ✅ No lint errors
- ✅ Code review approval

### Auto-merge (if enabled)

Can configure GitHub to auto-merge if:
- All checks pass
- Dismisses stale reviews
- Requires at least 1 approval

## Monitoring

### Build Status Badge

Add to README:

```markdown
[![Test Suite](https://github.com/your-repo/workflows/Test%20Suite/badge.svg)](https://github.com/your-repo/actions)
[![Code Quality](https://github.com/your-repo/workflows/Code%20Quality/badge.svg)](https://github.com/your-repo/actions)
```

### Coverage Badge

Add to README:

```markdown
[![Coverage](https://codecov.io/gh/your-repo/branch/master/graph/badge.svg)](https://codecov.io/gh/your-repo)
```

## Customization

### Adding New Workflows

Create `.github/workflows/custom.yml`:

```yaml
name: Custom Workflow
on: [push, pull_request]
jobs:
  custom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: echo "Custom job"
```

### Modifying Test Matrix

Edit `.github/workflows/test.yml`:

```yaml
strategy:
  matrix:
    python-version: ["3.12", "3.13", "3.14"]
```

### Conditional Steps

```yaml
- name: Deploy to Production
  if: github.ref == 'refs/heads/master'
  run: ./deploy.sh production
```

## Troubleshooting

### Workflow Won't Start

- Check `.github/workflows/` exists
- Ensure YAML syntax is valid
- Check branch name matches `on.push.branches`

### Timeout Issues

Increase timeout in workflow:
```yaml
timeout-minutes: 30
```

### Cache Issues

Clear GitHub Actions cache in repository settings.

### Credential Issues

- Use GitHub Secrets for sensitive data
- Set in repository Settings → Secrets
- Reference as `${{ secrets.NAME }}`

## Best Practices

1. **Test Locally First**
   - Run tests before pushing
   - Check linting before PR

2. **Keep Tests Fast**
   - Unit tests: < 1s
   - Integration: < 5s
   - Total: < 2 minutes

3. **Meaningful Commits**
   - Reference issue in commit message
   - Describe what and why
   - Keep commits atomic

4. **Review Before Merge**
   - At least one approval
   - Run tests one final time
   - Verify performance metrics

5. **Monitor Deployments**
   - Check health after deploy
   - Have rollback plan ready
   - Monitor in production

## Next Steps

- Review `.github/workflows/` files
- Test locally with provided scripts
- Set up GitHub Secrets if needed
- Monitor first deployment

## References

- [GitHub Actions Docs](https://docs.github.com/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
