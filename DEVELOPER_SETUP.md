# Developer Setup & Workflow Guide

Welcome to the Infinite Story Engine team! This guide covers everything you need to know about setting up your development environment, writing code, and collaborating with the team. Updated with real implementation knowledge from the team.

## Table of Contents

0. [Phase 2 Status Update](#phase-2-status-update)
1. [Quick Start](#quick-start)
2. [Development Environment Setup](#development-environment-setup)
3. [Testing Requirements](#testing-requirements)
4. [Phase 2: Integration & Real API](#phase-2-integration--real-api)
5. [Branching & PR Workflow](#branching--pr-workflow)
6. [Commit Message Format](#commit-message-format)
7. [Code Standards](#code-standards)
8. [Daily Development Workflow](#daily-development-workflow)
9. [Using GitHub CLI (gh)](#using-github-cli-gh)
10. [Troubleshooting](#troubleshooting)

---

## Phase 2 Status Update

### Backend API ✅ COMPLETE
**Status**: All core endpoints are now functional!

**What Changed**:
- ✅ Fixed main.py merge conflict
- ✅ Integrated all routes (sessions, progress, reports, stories, characters)
- ✅ Created story/segment API endpoints
- ✅ All 33 API tests passing

**Available API Endpoints**:
```
GET  /api/stories                      - List all stories
GET  /api/stories/{story_id}           - Get story details
GET  /api/segments/{segment_id}        - Get segment with choices
GET  /api/characters/{character_id}    - Get character info
POST /api/sessions/save                - Save session
GET  /api/progress/{story_id}          - Get progress
POST /api/reports                      - Submit content report
```

**Access API Docs**:
```bash
# Start backend
cd backend && source venv/bin/activate
python -m uvicorn app.main:app --reload

# Visit: http://localhost:8000/api/docs
```

**Frontend Next Steps**:
- Update `USE_MOCK = false` in frontend API config
- Test with real backend endpoints
- All endpoints return consistent response format with success/error fields

---

## Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone and navigate
git clone https://github.com/Melnikovartem/infinite-story.git
cd infinite-story

# 2. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/ -v  # Verify setup

# 3. Frontend setup (new terminal/tab)
cd frontend
npm install
npm test  # Verify setup

# 4. Start developing
# Backend server: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload
# Backend tests: cd backend && source venv/bin/activate && python -m pytest tests/ -v
# Frontend dev: cd frontend && npm run dev
# Frontend tests: cd frontend && npm test -- --watch
```

---

## Development Environment Setup

### Backend Setup

#### Prerequisites
- Python 3.13+ (tested with Python 3.13.7)
- Git with GitHub CLI (`gh`) installed
- Virtual environment tool (built-in `venv`)
- OpenRouter API key (for AI generation features)

#### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Melnikovartem/infinite-story.git
   cd infinite-story
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
   # Edit .env with your API keys:
   # - OPENROUTER_API_KEY: Your OpenRouter API key for AI generation
   # - Any other required configuration
   ```

5. **Verify setup by running tests**
   ```bash
   python -m pytest tests/test_character_*.py -v  # Quick character tests
   python -m pytest tests/ -v  # All tests
   ```

**Testing specific components:**
- Character system: `python -m pytest tests/test_character_avatar.py tests/test_character_state_manager.py tests/test_character_context_builder.py -v`
- Session/progress: `python -m pytest tests/test_api_sessions.py tests/test_api_progress.py -v`
- Content reports: `python -m pytest tests/test_api_reports.py -v`
- Story endpoints (Phase 2): `python -m pytest tests/test_api_stories.py -v`

#### Running the API Server (Phase 2+)

**Start the FastAPI server** (with auto-reload):
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Access the API**:
- Server base URL: http://localhost:8000
- Interactive API docs: http://localhost:8000/api/docs
- ReDoc documentation: http://localhost:8000/api/redoc
- Health check: http://localhost:8000/api/health

**API Endpoints Available** (Phase 2):
```
Story Management:
GET  /api/stories                    - List all available stories
GET  /api/stories/{story_id}         - Get story details with characters/locations

Segment Navigation:
GET  /api/segments/{segment_id}      - Get segment content and choices
POST /api/segments/{segment_id}/next - Generate next scene (AI - Phase 2.5)

Character Management:
GET  /api/characters/{char_id}       - Get character details
GET  /api/characters                 - List story characters

Session Management:
POST /api/sessions/save              - Save current session state
GET  /api/sessions/{story_id}        - Load saved session
DELETE /api/sessions/{story_id}      - Delete session

Progress & Reports:
GET  /api/progress/{story_id}        - Get player progress
POST /api/reports                    - Submit content report
GET  /api/reports                    - List reports (admin)
```

### Frontend Setup

#### Prerequisites
- Node.js 18+ and npm (tested with npm recent versions)
- Git with GitHub CLI (`gh`) installed
- Backend running (for API integration)

#### Steps

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment variables** (if needed)
   ```bash
   cp .env.example .env
   # Configure API endpoint to match your backend:
   # VITE_API_URL=http://localhost:8000/api  (for local development)
   # VITE_API_URL=http://your-server/api     (for remote backend)
   ```

3. **Verify setup by running tests**
   ```bash
   npm test                    # Run all tests
   npm test -- --coverage      # Run with coverage
   npm test -- --watch         # Watch mode for development
   ```

4. **Start development server**
   ```bash
   npm start         # Starts on http://localhost:3000
   npm run dev       # Alternative (Vite dev server)
   ```

**Component structure:**
- Components: `src/components/`
- Pages: `src/pages/`
- Context/State: `src/contexts/`
- API services: `src/services/`
- Tests: `src/components/__tests__/` and `src/pages/__tests__/`

---

## Testing Requirements

### Rule: Always Write Tests

**Every piece of code you write must have corresponding tests.** Tests are checked before merging PRs.

### Backend Testing

**Location**: `backend/tests/`

**Test Framework**: pytest (with fixtures and parametrization)

**Activate venv before testing:**
```bash
cd backend
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

**Running tests:**
```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_story_models.py

# Run specific test class
python -m pytest tests/test_character_avatar.py::TestAvatarSystem

# Run specific test
python -m pytest tests/test_character_avatar.py::TestAvatarSystem::test_avatar_shape_enum -v

# Run with coverage
python -m pytest --cov=app tests/

# Run tests for specific component
python -m pytest tests/test_character_*.py -v   # Character system tests
python -m pytest tests/test_api_*.py -v         # API endpoint tests
python -m pytest tests/test_auto_save.py -v     # Auto-save tests
```

**Writing tests:**
- Test files: `test_*.py` in `tests/` directory
- Use descriptive test names: `test_<function>_<scenario>`
- Use pytest fixtures for setup/teardown (see test data cleanup patterns)
- Use `@pytest.fixture` with cleanup for database/file operations
- Test both success and error cases
- Use mocks for external dependencies (AI API, file I/O, etc.)

**Example with fixture cleanup:**
```python
import pytest
import shutil
from pathlib import Path
from app.models.story import Story
from app.models.story_base import LOCAL_DATA_DIR

@pytest.fixture
def test_story():
    """Fixture to create and clean up test story."""
    test_story_id = "test_story_1"
    test_data_dir = LOCAL_DATA_DIR / test_story_id
    
    # Cleanup before
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # Create test story
    story = Story(
        id=test_story_id,
        title="Test Story",
        description="A test story",
        genre="Test",
        user_id="test_user_1",
        start_segment_id="start_segment_1"
    )
    
    yield story  # Test runs here
    
    # Cleanup after
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)

def test_story_creation(test_story):
    """Test that a story can be created with valid data."""
    assert test_story.id == "test_story_1"
    assert test_story.title == "Test Story"
```

**Test organization:**
- Model tests: `test_story_models.py`, `test_character_avatar.py`
- API tests: `test_api_sessions.py`, `test_api_progress.py`, `test_api_reports.py`
- Utility tests: `test_character_state_manager.py`, `test_character_context_builder.py`
- Integration tests: `test_auto_save.py`, `test_generation_pipeline.py`

### Frontend Testing

**Location**: `frontend/src/components/__tests__/` and `frontend/src/pages/__tests__/`

**Test Framework**: Vitest with React Testing Library

**Running tests:**
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode (recommended during development)
npm test -- --watch

# Run specific test file
npm test CharacterAvatar.test.tsx

# Run tests matching a pattern
npm test -- --grep "character"

# Run with coverage
npm test -- --coverage

# Run single test and exit
npm test -- --run
```

**Writing tests:**
- Test files: `*.test.tsx` or `*.test.ts` in `__tests__` directories
- Use descriptive test names: `test('<component> <behavior>')`
- Test component rendering, user interactions, and state
- Mock API calls and external dependencies
- Use React Testing Library for user-centric testing

**Example component test:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { CharacterAvatar } from '../CharacterAvatar';

describe('CharacterAvatar', () => {
  it('renders character with correct avatar shape and color', () => {
    render(
      <CharacterAvatar
        name="Eira"
        shape="circle"
        color="#FF6B6B"
      />
    );
    
    const avatar = screen.getByText('Eira');
    expect(avatar).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(
      <CharacterAvatar
        name="Hero"
        shape="square"
        color="#4ECDC4"
        onClick={handleClick}
      />
    );
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

**Test locations:**
- Component tests: `src/components/__tests__/`
- Page tests: `src/pages/__tests__/`
- Context tests: `src/contexts/__tests__/`
- Service tests: `src/services/__tests__/`

### Merge Requirement

**Your PR will not be merged until:**
- ✅ All tests pass
- ✅ New code has test coverage
- ✅ No test failures introduced

---

## Phase 2: Integration & Real API

**Phase 2** focuses on integrating all components with the real backend API and polishing the user experience.

### What's Changed

1. **Backend API Integration**
   - Main API now running on `http://localhost:8000`
   - Real endpoints for stories, segments, characters, sessions, progress, reports
   - Swagger docs available at `http://localhost:8000/api/docs`

2. **Frontend API Connection**
   - Frontend connected to real backend (no more mock data)
   - Toggle in `frontend/src/services/api.ts`: `USE_MOCK = false`
   - All API calls now go to real backend

3. **Frontend Polish** (Dev 5 focus)
   - Responsive design for mobile (320px), tablet (768px), desktop (1200px+)
   - Smooth animations and transitions
   - WCAG 2.1 AA accessibility compliance
   - Performance optimizations with GPU acceleration
   - Touch-friendly UI (44px+ min touch targets)

### Dev 5 Phase 2 Deliverables

**CSS/Styling Improvements**:
- `frontend/src/accessibility.css` - WCAG 2.1 AA compliance (302 lines)
- `frontend/src/performance.css` - GPU-accelerated animations (270 lines)
- Enhanced component CSS files for responsive design
- Global styles with proper focus-visible states

**Key Features Added**:
- ✅ Task 6.2: Real data styling (word-wrap, overflow handling)
- ✅ Task 6.3: Smooth animations (0.3-0.4s fade-ins, hover effects)
- ✅ Task 6.4: Responsive design (mobile-first approach)
- ✅ Task 6.6: Accessibility (WCAG 2.1 AA, keyboard navigation, ARIA)
- ✅ Task 6.7: Performance (GPU acceleration, CSS containment)

### New Frontend Files

```
frontend/src/
├── accessibility.css          # WCAG 2.1 AA compliance rules
├── performance.css            # GPU acceleration & rendering optimization
└── components/
    ├── ChoiceDisplay.tsx      # Updated with ARIA labels
    └── *.css                  # Enhanced with animations & responsive design
```

### Testing Phase 2

**Frontend Tests**:
```bash
cd frontend
npm test                        # Run all tests (74 passing)
npm test -- --watch           # Watch mode for development
npm test -- --coverage        # Coverage report
```

**Backend Tests**:
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v    # All backend tests
python -m pytest tests/test_integration_phase2.py -v  # Integration tests
```

### Phase 2 Workflow

1. **Create feature branch**: `git checkout -b feature/phase2-task-name`
2. **Make changes** with proper commits: `[DEV-5] task description`
3. **Test locally**: Run full test suite
4. **Push and create PR**: `gh pr create --title "..." --body "..."`
5. **Merge when ready**: `gh pr merge --merge` (no review needed)
6. **Clean up**: `git branch -d feature/...`

### Phase 2 Branch Examples

```bash
feature/phase2-real-data-styling
feature/phase2-animations
feature/phase2-responsive-design
feature/phase2-accessibility
feature/phase2-performance
```

### API Integration Updates

**Switching Frontend to Real API**:
```typescript
// frontend/src/services/api.ts
const USE_MOCK = false  // Set to false for real API
const api = USE_MOCK ? mockApi : realApi
```

**Backend Running**:
```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_integration_phase2.py -v
# Or start the server:
uvicorn app.main:app --reload
```

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

5. **Create a Pull Request using `gh`**
   ```bash
   gh pr create --title "Feature: your feature description" \
     --body "## Description
   Clear summary of what this PR does.
   
   ## Changes
   - Change 1
   - Change 2
   
   ## Tests
   - Test coverage details
   - All tests passing: ✅"
   ```

6. **Merge using `gh`** (when ready)
   ```bash
   gh pr merge <PR_NUMBER> --merge
   ```

7. **Cleanup**
   ```bash
   # After merge, delete local and remote branches
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   
   # Pull latest master
   git checkout master
   git pull origin master
   ```

**Pro Tip**: Use GitHub CLI for faster workflow:
```bash
gh pr create --title "Your title" --body "Your description"  # Create PR
gh pr view                                                    # View current PR
gh pr merge                                                   # Merge current PR
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

- **Imports**: Group by standard library, third-party, local (with blank lines between groups)
- **Type Hints**: Always use type hints (100% coverage expected)
- **Async**: Use `async/await` for I/O operations
- **Data Models**: Use Pydantic `BaseModel` for validation and Enums for fixed choices
- **Error Handling**: Use specific exceptions, don't catch `Exception`
- **Docstrings**: Use triple quotes for all classes and methods
- **Field Validation**: Use Pydantic `Field` and `@field_validator` for validation

**Example with real patterns from codebase:**
```python
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class AvatarShape(str, Enum):
    """Available avatar shapes for characters."""
    SQUARE = "square"
    CIRCLE = "circle"
    TRIANGLE = "triangle"

class StoryCharacter(BaseModel):
    """Represents a character in the story with avatar and state tracking."""
    
    id: str = Field(..., description="Unique character identifier")
    name: str
    description: str
    avatar_shape: AvatarShape = Field(default=AvatarShape.CIRCLE)
    avatar_color: str = Field(default="#FF6B6B")
    running_status: List[Dict[str, Any]] = Field(default_factory=list)
    
    @field_validator('avatar_color')
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate that avatar_color is a valid hex color."""
        if not isinstance(v, str):
            raise ValueError("avatar_color must be a string")
        color = v.lstrip('#')
        if len(color) not in (3, 6):
            raise ValueError(f"Invalid hex color: {v}")
        try:
            int(color, 16)
        except ValueError:
            raise ValueError(f"Invalid hex color: {v}")
        return f"#{color}"
    
    def add_state(self, segment_id: str, emotion: Optional[str] = None,
                  status: str = "present", notes: str = "") -> None:
        """Add or update character state at a segment.
        
        Args:
            segment_id: The segment ID where this state applies
            emotion: The character's emotional state
            status: Whether character is present, absent, or mentioned
            notes: Additional notes about the character
        """
        state_dict = {
            "segment_id": segment_id,
            "emotion": emotion,
            "status": status,
            "notes": notes
        }
        # Update or append logic
        for existing_state in self.running_status:
            if existing_state["segment_id"] == segment_id:
                existing_state.update(state_dict)
                return
        self.running_status.append(state_dict)
    
    def get_state_at_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        """Get character's state at a specific segment.
        
        Args:
            segment_id: The segment ID to look up
            
        Returns:
            The character state dict at that segment, or None if not found
        """
        for state in self.running_status:
            if state["segment_id"] == segment_id:
                return state
        return None
```

**Project structure:**
```
backend/
├── app/
│   ├── models/               # Data models (Pydantic BaseModel)
│   ├── utils/                # Utility functions and managers
│   ├── engine/               # Core business logic (generators, etc.)
│   ├── routes/               # API endpoints (FastAPI)
│   ├── services/             # Services (auto-save, etc.)
│   └── main.py              # FastAPI app initialization
├── tests/                     # All test files
├── requirements.txt           # Python dependencies
└── venv/                      # Virtual environment
```

**Requirements & Dependencies:**
- FastAPI: Web framework
- Pydantic: Data validation
- pytest: Testing framework
- OpenRouter: AI generation API client

**Run linting before committing:**
```bash
# Type checking
python -m mypy app/

# Note: flake8 optional, rely on PEP 8 compliance
```

### TypeScript/React (Frontend)

**Style Guide**:

- **Props**: Use interfaces for component props
- **State**: Use React hooks (`useState`, `useContext`)
- **Typing**: Always provide explicit types (no `any` unless absolutely necessary)
- **Components**: Functional components with hooks (no class components)
- **File Structure**: One component per file with colocated tests
- **Context**: Use React Context for global state (StoryContext pattern)
- **Styling**: CSS modules or colocated CSS files

**Example with real patterns:**
```typescript
import React, { useState, useContext } from 'react';
import { StoryContext } from '../contexts/StoryContext';
import './CharacterAvatar.css';

interface CharacterAvatarProps {
  characterId: string;
  name: string;
  avatarShape: 'square' | 'circle' | 'triangle' | 'diamond' | 'star' | 'pentagon';
  avatarColor: string;
  emotion?: string;
  status?: 'present' | 'absent' | 'mentioned';
}

export const CharacterAvatar: React.FC<CharacterAvatarProps> = ({
  characterId,
  name,
  avatarShape,
  avatarColor,
  emotion,
  status = 'present',
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const { currentSegment } = useContext(StoryContext);

  const handleMouseEnter = () => setIsHovered(true);
  const handleMouseLeave = () => setIsHovered(false);

  const avatarClassName = `character-avatar avatar-${avatarShape} status-${status}`;

  return (
    <div
      className={avatarClassName}
      style={{ backgroundColor: avatarColor }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      aria-label={`${name} - ${emotion || 'neutral'}`}
    >
      <span className="character-name">{name}</span>
      {isHovered && emotion && (
        <span className="emotion-indicator">{emotion}</span>
      )}
    </div>
  );
};
```

**Project structure:**
```
frontend/
├── src/
│   ├── components/           # Reusable React components
│   │   ├── CharacterAvatar.tsx
│   │   ├── CharacterAvatar.css
│   │   ├── __tests__/       # Component tests
│   │   └── ...
│   ├── pages/               # Full page components
│   │   ├── PlayPage.tsx
│   │   ├── StoryListPage.tsx
│   │   ├── __tests__/
│   │   └── ...
│   ├── contexts/            # React Context (global state)
│   │   ├── StoryContext.tsx
│   │   └── __tests__/
│   ├── services/            # API and utility services
│   │   ├── api.ts          # Real API calls
│   │   ├── mockApi.ts      # Mock API for testing
│   │   └── __tests__/
│   ├── types/               # TypeScript interfaces
│   │   └── index.ts
│   ├── styles/              # Global styles
│   └── App.tsx             # Main app component
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vitest.config.ts
```

**Context pattern (StoryContext):**
```typescript
interface Story {
  id: string;
  title: string;
  description: string;
  characters: Character[];
}

interface StoryContextType {
  currentSegment: Segment | null;
  currentStory: Story | null;
  characters: Character[];
  loadStory: (storyId: string) => Promise<void>;
  makeChoice: (choiceId: string) => Promise<void>;
  saveSession: () => Promise<void>;
}

export const StoryContext = React.createContext<StoryContextType | undefined>(undefined);

export const useStory = () => {
  const context = useContext(StoryContext);
  if (!context) {
    throw new Error('useStory must be used within StoryProvider');
  }
  return context;
};
```

**API service pattern:**
```typescript
// src/services/api.ts
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = {
  getStories: async () => {
    const response = await fetch(`${API_BASE}/stories`);
    return response.json();
  },
  
  getSegment: async (segmentId: string) => {
    const response = await fetch(`${API_BASE}/segments/${segmentId}`);
    return response.json();
  },
  
  generateNextScene: async (segmentId: string, choiceText: string) => {
    const response = await fetch(
      `${API_BASE}/segments/${segmentId}/next`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ choice_text: choiceText }),
      }
    );
    return response.json();
  },
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

# Check for test data cleanup issues
python -m pytest tests/test_character_avatar.py -v --tb=short
```

#### Import Errors / ModuleNotFoundError
```bash
# Make sure venv is activated
source venv/bin/activate

# Ensure PYTHONPATH is set correctly
cd backend
PYTHONPATH=. python -m pytest tests/

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

#### pytest: Unknown config option: asyncio_default_fixture_loop_scope
This is a warning, not an error. It occurs with pytest-asyncio plugins. Can be safely ignored.

#### Tests fail due to test data not cleaning up
```bash
# The character tests use fixtures with cleanup
# Make sure fixtures properly remove test data:
import shutil
from pathlib import Path

@pytest.fixture
def test_story():
    test_data_dir = LOCAL_DATA_DIR / "test_story_id"
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)  # Cleanup before
    
    yield story  # Test runs here
    
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)  # Cleanup after
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

# Check what's using port 3000
lsof -i :3000        # macOS/Linux
netstat -ano | grep :3000  # Windows
```

#### npm install fails or node_modules is corrupted
```bash
# Clear everything and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# On Windows:
rmdir /s /q node_modules
del package-lock.json
npm cache clean --force
npm install
```

#### API not connecting from frontend
```bash
# Check that backend is running
cd backend && source venv/bin/activate && python -m pytest tests/test_api_basic.py -v

# Check VITE_API_URL environment variable
# Default: http://localhost:8000/api

# In frontend/.env:
VITE_API_URL=http://localhost:8000/api

# Or check frontend logs for errors
npm start  # Look at browser console
```

#### Character tests fail with serialization errors
```bash
# Character state must be serializable to JSON
# If you add new fields, ensure they're JSON-compatible

# Test character save/load:
python -m pytest tests/test_character_avatar.py::TestCharacterSerialization -v
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

## Using GitHub CLI (gh)

The team uses GitHub CLI for efficient PR management. Install it and authenticate:

```bash
# Install gh (macOS with Homebrew)
brew install gh

# Or download from https://github.com/cli/cli#installation

# Authenticate with GitHub
gh auth login
```

### Common gh Commands

```bash
# Create a PR from current branch
gh pr create --title "Your title" \
  --body "## Description
Your description here"

# List open PRs
gh pr list

# View specific PR
gh pr view 4

# Merge current PR (auto-detects)
gh pr merge                    # Interactive selection
gh pr merge 4 --merge          # Merge specific PR with merge commit
gh pr merge 4 --squash         # Squash commits before merge
gh pr merge 4 --rebase         # Rebase before merge

# Close a PR without merging
gh pr close 4

# Check PR status
gh pr status

# Checkout a PR branch locally
gh pr checkout 4
```

### Workflow with gh

1. **Work on feature branch**
   ```bash
   git checkout -b feature/your-feature
   # ... make changes and commit ...
   git push origin feature/your-feature
   ```

2. **Create PR**
   ```bash
   gh pr create --title "Feature: description" --body "PR description"
   ```

3. **Merge PR**
   ```bash
   gh pr merge  # Current PR in current branch
   ```

**Example:**
```bash
$ gh pr create --title "DEV-2: Add character avatar system" \
  --body "## Summary
Implements avatar system with 6 shapes and color validation.

## Changes
- Add AvatarShape enum
- Add hex color validation
- 51 tests added

## Tests
All tests passing: ✅ 51/51"

# Returns: Created pull request #4

$ gh pr merge 4 --merge
# Returns: Pull request #4 merged
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
