# CI/CD Pipeline Documentation - ISE v2

This document describes the automated testing and deployment pipeline for Infinite Story Engine v2.

## Overview

The CI/CD pipeline runs on every push and pull request, ensuring code quality and preventing regressions.

**Pipeline Goals:**
- Automated testing on every change
- Code quality enforcement
- Coverage tracking
- Fast feedback to developers
- Reliable deployments

## Pipeline Workflow

```
Push/PR → Lint → Type Check → Tests → Coverage → Results
                ↓
           All pass? → Can merge
           Any fail? → Block merge, notify developer
```

## GitHub Actions Workflows

### Test Suite (`test.yml`)

Runs on every push and PR to `main` and `develop` branches.

**Triggers:**
- Push to main/develop
- Pull request to main/develop
- Manual trigger

**Steps:**
1. Checkout code
2. Set up Python (3.12, 3.13)
3. Install dependencies
4. Lint with flake8
5. Format check with black
6. Run pytest
7. Upload coverage
8. Type check with mypy

**Matrix:** Tests run on Python 3.12 and 3.13

**Time:** ~5 minutes

```yaml
# .github/workflows/test.yml
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
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Lint
        run: |
          cd backend
          flake8 app tests
      
      - name: Format check
        run: |
          cd backend
          black --check app tests
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Code Quality (`lint.yml`)

Runs code formatting and linting checks.

**Triggers:**
- Push to any branch
- Pull request

**Steps:**
1. Set up Python
2. Run black (formatting)
3. Run isort (import sorting)
4. Run flake8 (linting)
5. Commit changes (auto-fix)

```yaml
# .github/workflows/lint.yml
name: Code Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.13"
      
      - name: Install tools
        run: |
          pip install black isort flake8
      
      - name: Format code
        run: |
          black backend/app backend/tests
          isort backend/app backend/tests
      
      - name: Lint
        run: |
          flake8 backend/app backend/tests
      
      - name: Commit changes
        run: |
          git config user.email "ci@github.com"
          git config user.name "CI Bot"
          git add -A
          git commit -m "chore: auto-format code" || true
          git push || true
```

## Local Testing Before Push

Run these locally before pushing:

```bash
# Install dev requirements
pip install -r requirements-dev.txt

# Run all checks
pytest tests/ -v --cov=app
black --check app tests
isort --check-only app tests
flake8 app tests
mypy app --ignore-missing-imports
```

Or use the pre-commit hook:

```bash
# Create .git/hooks/pre-commit
#!/bin/bash
set -e
cd backend

echo "Running linting..."
black --check app tests || exit 1
isort --check-only app tests || exit 1
flake8 app tests || exit 1

echo "Running tests..."
pytest tests/ -q || exit 1

echo "✅ All checks passed"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Pull Request Checks

### Required Checks

Before merging, these must pass:
- ✅ All tests pass
- ✅ Code coverage maintained (>80%)
- ✅ No linting errors
- ✅ Type checks pass
- ✅ Code review approved

### PR Workflow

1. **Create PR** → Triggers test suite
2. **Review feedback** → Address comments
3. **Passing checks** → Shows ✅ green checkmark
4. **Approval** → Code owner approves
5. **Merge** → PR merges to main

### Status Checks

GitHub shows status on PR:

```
✅ All checks have passed
  └─ Lint / lint (3.13)          ✅ passed
  └─ Test Suite / test (3.12)    ✅ passed
  └─ Test Suite / test (3.13)    ✅ passed
  └─ Code Quality               ✅ passed
```

If any fail:

```
❌ Some checks didn't pass
  └─ Test Suite / test (3.12)    ❌ failed
       View details
```

## Coverage Tracking

### Coverage Goals

- **Overall:** >80%
- **New code:** 100%
- **Critical paths:** >90%

### View Coverage

After tests run, coverage report is generated:

```bash
# Local coverage
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Upload to Codecov
codecov --token=<token>
```

## Performance Baselines

Performance tests establish baselines to prevent regressions:

```bash
pytest tests/test_performance.py -v --benchmark-only
```

Tracked metrics:
- Segment creation time
- Context building time
- Generation latency
- Memory usage
- Query performance

## Branch Strategy

### Main Branch
- Always deployable
- All checks must pass
- Code review required
- No direct pushes

### Develop Branch
- Integration branch
- All checks must pass
- Staging tests required

### Feature Branches
- `feature/description`
- Local testing only
- PR to develop first

## Deployment Pipeline

### Staging Deployment

Triggered manually or on:
- Merge to develop
- After tests pass
- Requires approval

```bash
cd backend
./scripts/deploy.sh staging
```

### Production Deployment

Only from main branch:
- Manual trigger
- Requires 2 approvals
- Tests must pass
- Staging must be verified

```bash
cd backend
./scripts/deploy.sh production
```

## Notification Settings

### Slack Integration

Configure Slack notifications:

```yaml
# Add to workflow
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "❌ Build failed for ${{ github.ref }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Build Failed*\nRepo: ${{ github.repository }}\nBranch: ${{ github.ref }}"
            }
          }
        ]
      }
```

### Email Notifications

GitHub settings → Notifications → Email

Default: On push failures and pull request reviews

## Troubleshooting CI/CD

### Tests Fail in CI but Pass Locally

**Causes:**
- Different Python version
- Environment variables not set
- Missing test data

**Solutions:**
```bash
# Test with same Python version
pyenv install 3.12
pyenv shell 3.12
pytest tests/ -v

# Check environment variables
echo $PYTHONPATH

# Verify test data
ls -la backend/tests/fixtures/
```

### Coverage Drop Detected

**Causes:**
- New code not tested
- Test removal
- Coverage threshold lowered

**Solutions:**
```bash
# View coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Add tests for uncovered code
# Focus on critical paths first

# Check current coverage
pytest tests/ --cov=app --cov-report=term-missing | grep -E "^TOTAL|missing"
```

### Linting Fails

**Causes:**
- Code style issues
- Import ordering
- Naming conventions

**Solutions:**
```bash
# Auto-fix formatting
black backend/app backend/tests

# Auto-fix imports
isort backend/app backend/tests

# Fix remaining issues
flake8 backend/app backend/tests --show-source
```

### Type Checking Fails

**Causes:**
- Missing type hints
- Incompatible types
- Generic types

**Solutions:**
```bash
# Run mypy locally
mypy backend/app --ignore-missing-imports

# Add type hints
# def process(data: str) -> dict:

# Suppress warnings if needed
# type: ignore
```

## Dashboard and Monitoring

### GitHub Actions Dashboard

View all workflows:
1. Go to Actions tab
2. Select workflow
3. View run details
4. Check logs for failures

### Coverage Dashboard

Codecov dashboard shows:
- Coverage trends over time
- File-by-file coverage
- Diff coverage for PRs
- Historical data

### Performance Dashboard

Track performance benchmarks:
```bash
# View benchmark results
pytest tests/test_performance.py --benchmark-only --benchmark-json=results.json

# Compare to baseline
pytest-benchmark compare
```

## Security Scanning

### Dependency Scanning

Automated checks for vulnerable dependencies:

```bash
# Local check
pip install safety
safety check

# Or with pip-audit
pip install pip-audit
pip-audit
```

### Code Scanning

Configure GitHub code scanning:
1. Settings → Code security → Code scanning
2. Enable with CodeQL
3. Review alerts

## Best Practices

1. **Keep CI fast** - Optimize slow tests
2. **Fail fast** - Run lint before tests
3. **Parallel execution** - Use matrix for multiple versions
4. **Cache dependencies** - Speed up installs
5. **Clear logs** - Remove debug output
6. **Document changes** - Update CI docs with config changes
7. **Monitor alerts** - Review failed runs promptly
8. **Automate everything** - No manual steps in merge process

## Performance Optimization

### Speed Up CI

```yaml
# Cache dependencies
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

# Run tests in parallel
pytest tests/ -n auto

# Only run affected tests
pytest tests/ --lf  # Last failed
pytest tests/ --ff  # First failed
```

### Matrix Strategy

Test multiple configurations efficiently:

```yaml
strategy:
  matrix:
    python-version: ["3.12", "3.13"]
    os: [ubuntu-latest, macos-latest]
```

## Maintenance

### Update Dependencies

Monthly:
```bash
pip install --upgrade pip setuptools
pip list --outdated
pip install --upgrade -r requirements.txt
```

### Review Workflows

Quarterly:
- Check for deprecated actions
- Update action versions
- Review coverage thresholds
- Optimize execution time

### Archive Old Artifacts

GitHub Actions artifacts have storage limits:
```bash
# Delete old artifacts
gh run list --status completed --limit 100 | \
  awk '{print $1}' | \
  xargs -I {} gh run delete {}
```

## Documentation

- [GitHub Actions docs](https://docs.github.com/en/actions)
- [Codecov documentation](https://docs.codecov.io/)
- [pytest documentation](https://docs.pytest.org/)
- [Black code formatter](https://black.readthedocs.io/)

---

**Need help? Check workflow logs in Actions tab → select failed run → view logs**
