# Developer Setup & Workflow Guide

Welcome to the Infinite Story Engine team! This guide covers everything you need to know about setting up your development environment, writing code, and collaborating with the team.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Testing Requirements](#testing-requirements)
3. [Branching & PR Workflow](#branching--pr-workflow)
4. [Commit Message Format](#commit-message-format)
5. [Code Standards](#code-standards)
6. [Daily Development Workflow](#daily-development-workflow)
7. [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Backend Setup

#### Prerequisites
- Python 3.13+
- Git
- Virtual environment tool (built-in `venv`)

#### Steps

1. **Clone the repository** (if you haven't already)
   ```bash
   git clone <repo-url>
   cd infinite_story
   ```

2. **Create and activate virtual environment**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Verify setup by running tests**
   ```bash
   python -m pytest tests/ -v
   ```

### Frontend Setup

#### Prerequisites
- Node.js 18+ and npm/yarn
- Git

#### Steps

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment variables** (if needed)
   ```bash
   cp .env.example .env
   # Edit .env if API endpoints or other config is needed
   ```

3. **Verify setup by running tests** (when available)
   ```bash
   npm test
   ```

4. **Start development server**
   ```bash
   npm start
   ```

---

## Testing Requirements

### Rule: Always Write Tests

**Every piece of code you write must have corresponding tests.** Tests are checked before merging PRs.

### Backend Testing

**Location**: `backend/tests/`

**Test Framework**: pytest

**Running tests:**
```bash
cd backend

# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_story_models.py

# Run specific test
python -m pytest tests/test_story_models.py::test_story_creation -v

# Run with coverage
python -m pytest --cov=app tests/
```

**Writing tests:**
- Test files: `test_*.py` in `tests/` directory
- Use descriptive test names: `test_<function>_<scenario>`
- Use pytest fixtures for setup/teardown
- Test both success and error cases
- Use mocks for external dependencies (AI API, file I/O, etc.)

**Example:**
```python
import pytest
from app.models.story import Story

def test_story_creation():
    """Test that a story can be created with valid data."""
    story = Story(id="test_story", title="Test Story")
    assert story.id == "test_story"
    assert story.title == "Test Story"

def test_story_requires_id():
    """Test that story creation fails without an ID."""
    with pytest.raises(ValueError):
        Story(title="Test Story")  # Missing required 'id'
```

### Frontend Testing

**Location**: `frontend/src/__tests__/`

**Test Framework**: Jest/Vitest (when configured)

**Running tests:**
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test PerformanceCounter.test.tsx

# Run with coverage
npm test -- --coverage
```

**Writing tests:**
- Test files: `*.test.tsx` or `*.test.ts`
- Use descriptive test names: `test('<component> <behavior>')`
- Test component rendering, user interactions, and state
- Mock API calls and external dependencies

### Merge Requirement

**Your PR will not be merged until:**
- ✅ All tests pass
- ✅ New code has test coverage
- ✅ No test failures introduced

---

## Branching & PR Workflow

### Branch Naming Convention

Create feature branches with clear, descriptive names:

```
feature/<task-description>      # New features
fix/<issue-description>          # Bug fixes
refactor/<area-description>      # Code refactoring
docs/<documentation-change>      # Documentation updates
```

**Examples:**
- `feature/add-character-selection`
- `fix/story-segment-loading-bug`
- `refactor/simplify-api-endpoint`
- `docs/update-deployment-guide`

### Workflow

1. **Pull latest changes**
   ```bash
   git checkout master
   git pull origin master
   ```

2. **Create and switch to feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** (see [Commit Message Format](#commit-message-format))

4. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to GitHub and create a PR from your branch to `master`
   - Write a clear PR description (see below)
   - No review needed—you can merge after CI checks pass

6. **Merge and cleanup**
   ```bash
   # After PR is approved/CI passes, merge it
   # (Can do via GitHub UI)
   
   # Delete local branch
   git branch -d feature/your-feature-name
   
   # Delete remote branch
   git push origin --delete feature/your-feature-name
   ```

### Pull Request Description Template

```markdown
## Description
Brief summary of what this PR does.

## Changes
- Change 1
- Change 2
- Change 3

## Tests
- Added test for X
- Added test for Y
- All tests passing: ✅

## Related Issues
Closes #123 (if applicable)
```

**Example:**
```markdown
## Description
Add character selection UI to story entry screen, allowing players to choose from pre-defined colored shape avatars.

## Changes
- Add CharacterSelector component
- Add character avatar display with colors
- Add character state management in StoryContext
- Update story entry to show character selection

## Tests
- Added CharacterSelector.test.tsx with 5 test cases
- Added integration test for character selection flow
- All backend tests passing: ✅

## Related Issues
Closes #45
```

---

## Commit Message Format

### Format

```
[TASK_ID] description
```

Where:
- **TASK_ID**: Your developer/feature identifier (e.g., `DEV-1`, `FEATURE-AUTH`, `FIX-BUG-123`)
- **description**: Brief, lowercase description of what changed (no punctuation at end)

### Examples

```
[DEV-1] add user authentication endpoint
[DEV-2] fix story segment loading race condition
[FIX-BUG-45] resolve character state not persisting
[FEATURE-AUTH] implement jwt token refresh logic
[REFACTOR] simplify api response handling
[TEST] add comprehensive test coverage for choice generation
```

### Rules

- ✅ Lowercase (unless referencing code/class names)
- ✅ Use imperative mood: "add", "fix", "update", "refactor" (not "added", "fixed")
- ✅ Concise but descriptive
- ✅ No period at end
- ✅ Start with task/feature ID in brackets
- ✅ Commit frequently—one logical change per commit (not one giant commit per day)

### Example Workflow

```bash
# Make a change to file
git add app/models/story.py

# Commit with proper format
git commit -m "[DEV-1] add validation to story creation"

# Make another change
git add backend/tests/test_story.py

# Commit again
git commit -m "[DEV-1] add tests for story validation"

# Push all commits at once
git push origin feature/add-story-validation
```

---

## Code Standards

### Python (Backend)

**Style Guide**: Follow PEP 8 with these conventions:

- **Imports**: Group by standard library, third-party, local
- **Type Hints**: Always use type hints
- **Async**: Use `async/await` for I/O operations
- **Data Models**: Use Pydantic `BaseModel` for data validation
- **Error Handling**: Use specific exceptions, don't catch `Exception`

**Example:**
```python
from typing import Optional
from pydantic import BaseModel, Field
from app.engine.generator import TextGenerator

class StorySegment(BaseModel):
    """Represents a scene in the story."""
    
    id: str = Field(..., description="Unique segment identifier")
    title: str = Field(..., min_length=1)
    content: str
    is_generated: bool = False
    
    async def generate_next_scene(self, choice_text: str) -> "StorySegment":
        """Generate the next story scene based on player choice."""
        generator = TextGenerator()
        response = await generator.generate(context=self.build_context())
        return self._create_segment_from_response(response)
    
    def build_context(self) -> str:
        """Build context for AI generation."""
        return f"Current segment: {self.title}\n{self.content}"
```

**Linting**: Run before committing:
```bash
# Check style (if flake8 installed)
python -m flake8 app/

# Type checking
python -m mypy app/
```

### TypeScript/React (Frontend)

**Style Guide**:

- **Props**: Use interfaces for component props
- **State**: Use React hooks (`useState`, `useContext`)
- **Typing**: Always provide explicit types
- **Components**: Functional components with hooks (no class components)
- **File Structure**: One component per file, colocate tests

**Example:**
```typescript
import React, { useState } from 'react';

interface StorySegmentProps {
  segmentId: string;
  content: string;
  onChoiceSelect: (choiceId: string) => void;
}

export const StorySegment: React.FC<StorySegmentProps> = ({
  segmentId,
  content,
  onChoiceSelect,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleChoice = async (choiceId: string) => {
    setIsLoading(true);
    try {
      onChoiceSelect(choiceId);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="story-segment">
      <p>{content}</p>
      {isLoading && <p>Loading...</p>}
    </div>
  );
};
```

### Shared Standards

- **Comments**: Write comments for "why", not "what" (code should be self-documenting)
- **Naming**: Use clear, descriptive names for functions/variables/classes
- **DRY Principle**: Don't repeat code—extract common patterns
- **Testing**: Test edge cases, errors, and normal flows

---

## Daily Development Workflow

### Morning

1. **Sync with latest changes**
   ```bash
   git checkout master
   git pull origin master
   ```

2. **Check for any blockers** from team standups

3. **Create feature branch** (if starting new task)
   ```bash
   git checkout -b feature/your-task
   ```

### During Development

1. **Write code & tests together**
   - Write a failing test first (TDD approach is optional but recommended)
   - Implement the feature
   - Ensure test passes

2. **Commit frequently**
   ```bash
   git add <files>
   git commit -m "[TASK_ID] description of change"
   ```

3. **Run tests before pushing**
   ```bash
   # Backend
   cd backend && python -m pytest
   
   # Frontend
   cd frontend && npm test
   ```

4. **Push when ready**
   ```bash
   git push origin feature/your-task
   ```

### Afternoon/Before End of Day

1. **Create Pull Request** (if you haven't)
   - Descriptive title and description
   - Reference any related issues

2. **Run full test suite**
   ```bash
   # Backend
   cd backend && python -m pytest -v
   
   # Frontend
   cd frontend && npm test -- --coverage
   ```

3. **Address any test failures immediately**

4. **Merge PR** when tests pass
   - Via GitHub UI (no review required)
   - Delete branch

5. **Pull master and start next task**
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feature/next-task
   ```

---

## Troubleshooting

### Backend Issues

#### Virtual Environment Not Activated
```bash
# Check if venv is activated (you should see (venv) in prompt)
# If not:
source backend/venv/bin/activate  # macOS/Linux
# OR
backend\venv\Scripts\activate     # Windows
```

#### Dependency Issues
```bash
# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt
```

#### Tests Failing Locally but Passing in CI
```bash
# Ensure you're using the latest dependencies
pip install --upgrade -r requirements.txt

# Run full test suite to check for timing issues
python -m pytest -v --tb=short
```

#### Import Errors
```bash
# Ensure PYTHONPATH is set correctly
cd backend
PYTHONPATH=. python -m pytest tests/
```

### Frontend Issues

#### Node Modules Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Tests Failing
```bash
# Clear Jest cache
npm test -- --clearCache

# Run tests with verbose output
npm test -- --verbose
```

#### Port Already in Use
```bash
# Default port is 3000, but you can specify a different one:
PORT=3001 npm start
```

### Git Issues

#### Need to Switch Branches Without Committing
```bash
# Stash changes
git stash

# Switch branch
git checkout master

# Switch back and restore changes
git checkout feature/your-branch
git stash pop
```

#### Accidentally Committed to Wrong Branch
```bash
# Reset last commit (keep changes)
git reset --soft HEAD~1

# Switch to correct branch
git checkout -b feature/correct-branch

# Commit again
git commit -m "[TASK_ID] your message"
```

#### Need to Update Your Branch with Latest Master
```bash
# Fetch latest
git fetch origin

# Rebase (preferred for clean history)
git rebase origin/master

# OR merge (if rebase causes conflicts)
git merge origin/master
```

---

## Getting Help

- **Documentation**: See README.md in backend/ and frontend/
- **Architecture**: Check ARCHITECTURE.md for system design
- **Code Questions**: Review existing code patterns
- **Blockers**: Report immediately in team chat/standup

---

## Summary Checklist

When starting each day:

- [ ] Virtual environment activated (backend)
- [ ] Dependencies installed (`pip install` / `npm install`)
- [ ] Latest master pulled
- [ ] Feature branch created
- [ ] `.env` configured with API keys

When committing:

- [ ] Tests written and passing
- [ ] Code follows style guide
- [ ] Commit message formatted: `[TASK_ID] description`
- [ ] Frequency: multiple small commits, not one big commit

Before merging:

- [ ] All tests passing locally
- [ ] PR created with clear description
- [ ] No CI failures
- [ ] Ready to merge (no review needed)

Happy coding! 🚀
