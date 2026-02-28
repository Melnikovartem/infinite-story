# Frontend - Infinite Story Engine

React 18 + TypeScript frontend for the Infinite Story Engine.

## Project Structure

```
src/
├── components/           # React components
│   ├── Layout.tsx       # Main layout wrapper
│   ├── CharacterAvatar.tsx
│   ├── ChoiceDisplay.tsx
│   ├── CustomChoiceInput.tsx
│   ├── ProgressCounter.tsx
│   ├── SegmentDisplay.tsx
│   └── __tests__/       # Component tests
├── contexts/            # React Context
│   ├── StoryContext.tsx # Story state management
│   └── __tests__/
├── pages/               # Page components
│   ├── StoryListPage.tsx
│   ├── StoryDetailPage.tsx
│   ├── PlayPage.tsx
│   └── __tests__/
├── services/            # API integration
│   ├── api.ts          # Wrapper (mock/real toggle)
│   ├── mockApi.ts      # Mock API implementation
├── types/               # TypeScript type definitions
├── styles/              # Global styles
├── test/                # Test setup
├── App.tsx              # Root component
└── main.tsx             # Entry point
```

## Setup

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:3000`

## Build

```bash
npm run build
```

Output in `dist/`

## Testing

```bash
npm test
```

Run with watch mode:
```bash
npm test -- --watch
```

## API Integration

### Switching between Mock and Real API

The project uses a wrapper service (`src/services/api.ts`) that abstracts API calls.

**To use real API**:
1. Open `src/services/api.ts`
2. Change `const USE_MOCK = true` to `const USE_MOCK = false`
3. Ensure backend is running on `http://localhost:8000`

**To use mock API**:
- Keep `const USE_MOCK = true` (default)
- Mock data is in `src/services/mockApi.ts`

## Key Components

### StoryContext
Global state management for:
- Current story and segment
- Session state
- Character and location info
- Loading/error states
- Story navigation

Usage:
```typescript
import { useStory } from '../contexts/StoryContext'

export function MyComponent() {
  const { story, segment, loading, error } = useStory()
  // Use story state here
}
```

### CharacterAvatar
Renders character avatars as geometric shapes:
```typescript
<CharacterAvatar
  shape="circle"           // square, circle, triangle, diamond, star, pentagon
  color="#FF6B6B"
  size="medium"            // small, medium, large
/>
```

### ChoiceDisplay
Shows top 2 choices prominently with expandable list:
```typescript
<ChoiceDisplay
  onSelect={(choiceId) => handleChoice(choiceId)}
  loading={isLoading}
/>
```

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write tests first** (TDD style):
   ```typescript
   // src/components/__tests__/MyComponent.test.tsx
   describe('MyComponent', () => {
     it('does something', () => {
       // Test here
     })
   })
   ```

3. **Implement component**:
   ```typescript
   // src/components/MyComponent.tsx
   export default function MyComponent() {
     return <div>My component</div>
   }
   ```

4. **Run tests and build**:
   ```bash
   npm test
   npm run build
   ```

5. **Commit with proper message**:
   ```bash
   git commit -m "[DEV-4] add my feature"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/my-feature
   ```

## Code Standards

- Use TypeScript interfaces for all component props
- Write tests for all components
- Keep components small and focused
- Use React hooks (no class components)
- Style with CSS modules or plain CSS
- Follow PEP 8 naming conventions

## Useful Commands

```bash
npm run dev          # Start dev server
npm run build        # Build for production
npm test             # Run tests
npm test -- --ui     # Run tests with UI
npm run preview      # Preview production build
```

## Troubleshooting

### Port 3000 already in use
```bash
PORT=3001 npm run dev
```

### Clear cache and reinstall
```bash
rm -rf node_modules package-lock.json
npm install
```

### Type errors
```bash
npm run build       # Run TypeScript compiler
```

## Notes

- Session data stored in localStorage
- No real backend needed for development (use mocks)
- All API calls go through `src/services/api.ts`
- Easy to switch to real API when backend is ready
