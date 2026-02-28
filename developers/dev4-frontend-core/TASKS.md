# Dev 4: Frontend Core - Detailed Task Breakdown

**Total Hours**: 60 (12 hours/day × 5 days)
**Timeline**: Week 1-2
**Start**: Day 1 (use mocked APIs!)

---

## Task 5.1: Project Setup & Routing (12 hours)

**Days 1-2 - Estimated 12 hours**

### What You're Building
React project structure, routing, and context setup with mocked API service.

### Subtasks

#### 5.1.1: React Project Initialization (3 hours)
- [ ] Set up Vite + React 18 + TypeScript (or use existing create-react-app)
- [ ] Install dependencies (react-router-dom, axios/fetch)
- [ ] Set up project structure:
  ```
  src/
  ├── pages/
  ├── components/
  ├── services/
  ├── contexts/
  ├── hooks/
  ├── types/
  ├── styles/
  └── App.tsx
  ```
- [ ] Verify build works: `npm run build`

#### 5.1.2: Create Mock API Service (4 hours)
- [ ] Create `src/services/mockApi.ts`
- [ ] Mock all endpoints from API_CONTRACTS.md
- [ ] Use realistic data (from existing stories if available)
- [ ] Add small delays (simulate network latency)
- [ ] Export mock data for easy testing

**Example**:
```typescript
// src/services/mockApi.ts
export const mockStories = [
  {
    id: "veil_of_thornreach",
    title: "The Veil of Thornreach",
    description: "A tale of mystery...",
    author: "Story Creator"
  }
];

export const mockSegments: Record<string, SegmentData> = {
  segment_001: {
    id: "segment_001",
    title: "The Last Sanctuary",
    content: "The ancient trees sway...",
    text_blocks: [...],
    choices: {
      top_2: [...],
      all: [...]
    }
  }
};

export async function fetchStories(): Promise<Story[]> {
  await new Promise(r => setTimeout(r, 300)); // Simulate latency
  return mockStories;
}
```

#### 5.1.3: Set Up React Router (3 hours)
- [ ] Install react-router-dom
- [ ] Create router configuration
- [ ] Define routes:
  - `/` - Story list
  - `/story/:storyId` - Story detail
  - `/play/:storyId` - Play game
  - `/about` - About page
- [ ] Create layout component with navigation
- [ ] Test routing

**Example**:
```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

export function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<StoryListPage />} />
          <Route path="/story/:storyId" element={<StoryDetailPage />} />
          <Route path="/play/:storyId" element={<PlayPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
```

#### 5.1.4: Set Up Context API (2 hours)
- [ ] Create `src/contexts/StoryContext.tsx`
- [ ] Define context for:
  - Current story data
  - Current segment
  - Session state
  - Loading states
  - Errors
- [ ] Create provider component
- [ ] Create custom hook: `useStory()`
- [ ] Test context

**Example**:
```typescript
// src/contexts/StoryContext.tsx
interface StoryContextType {
  story: Story | null;
  segment: Segment | null;
  sessionState: SessionState | null;
  loading: boolean;
  error: string | null;
  loadStory: (storyId: string) => Promise<void>;
  goToSegment: (segmentId: string) => Promise<void>;
  makeChoice: (choiceId: string) => Promise<void>;
  customChoice: (text: string) => Promise<void>;
}

export const StoryContext = createContext<StoryContextType | null>(null);

export function StoryProvider({ children }: PropsWithChildren) {
  // Implementation here
}
```

---

## Task 5.2: Component Library (25 hours)

**Days 2-4 - Estimated 25 hours**

### What You're Building
Core React components for displaying story content and UI.

### Subtasks

#### 5.2.1: StoryListPage Component (4 hours)
- [ ] Fetch and display all stories
- [ ] Show story card with title, description, author
- [ ] Make clickable (navigate to detail page)
- [ ] Handle loading and error states
- [ ] Add search/filter (optional)
- [ ] Test component

#### 5.2.2: StoryDetailPage Component (3 hours)
- [ ] Display story information
- [ ] Show "Start Playing" button
- [ ] Check for existing session
- [ ] Offer resume or start fresh
- [ ] Show character list with avatars
- [ ] Test component

#### 5.2.3: PlayPage Component (6 hours)
- [ ] Load current segment
- [ ] Display segment content
- [ ] Show scene counter
- [ ] Handle multiple text blocks
- [ ] Manage state transitions
- [ ] Handle errors
- [ ] Test component

#### 5.2.4: SegmentDisplay Component (3 hours)
- [ ] Display segment title
- [ ] Render text blocks with proper formatting
- [ ] Handle different text block types (narrative, dialogue, etc.)
- [ ] Display character presence
- [ ] Display location information
- [ ] Test component

#### 5.2.5: ChoiceDisplay Component (4 hours)
- [ ] Display top 2 choices prominently
- [ ] Show expandable "All Choices" section
- [ ] Make choices clickable
- [ ] Show choice preview on hover
- [ ] Handle selection state
- [ ] Test component

**Example**:
```typescript
// src/components/ChoiceDisplay.tsx
interface Props {
  top2: Choice[];
  allChoices: Choice[];
  onSelect: (choiceId: string) => void;
  loading?: boolean;
}

export function ChoiceDisplay({ top2, allChoices, onSelect, loading }: Props) {
  const [showAll, setShowAll] = useState(false);
  
  return (
    <div className="choices">
      <div className="top-choices">
        {top2.map(choice => (
          <button 
            key={choice.id}
            onClick={() => onSelect(choice.id)}
            disabled={loading}
          >
            {choice.choice_text}
          </button>
        ))}
      </div>
      
      {!showAll && allChoices.length > 2 && (
        <button onClick={() => setShowAll(true)}>
          View All Choices ({allChoices.length})
        </button>
      )}
      
      {showAll && (
        <div className="all-choices">
          {allChoices.map(choice => (
            <button key={choice.id} onClick={() => onSelect(choice.id)}>
              {choice.choice_text}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 5.2.6: CustomChoiceInput Component (3 hours)
- [ ] Text input for custom choice
- [ ] Validation (min/max length)
- [ ] Submit button
- [ ] Show loading state during generation
- [ ] Handle errors
- [ ] Test component

#### 5.2.7: ProgressCounter Component (2 hours)
- [ ] Display current scene number
- [ ] Show elapsed time
- [ ] Show start date
- [ ] Format nicely (Scene 5 • 2h 15m • Started Feb 28)
- [ ] Test component

---

## Task 5.3: State Management & API Integration (15 hours)

**Days 3-5 - Estimated 15 hours**

### What You're Building
Wire up components to context, handle state transitions, and prepare for real API.

### Subtasks

#### 5.3.1: Session Management (4 hours)
- [ ] Implement session load on app start
- [ ] Check localStorage for session data
- [ ] Load saved session if available
- [ ] Offer resume vs. new game
- [ ] Implement save session to localStorage
- [ ] Test session flow

#### 5.3.2: Story Navigation Flow (4 hours)
- [ ] Load story on page load
- [ ] Load initial segment
- [ ] Load segment on navigation
- [ ] Update context with current state
- [ ] Handle loading/error states
- [ ] Test navigation

#### 5.3.3: Choice Handling (4 hours)
- [ ] Handle existing choice selection
- [ ] Call mock API to get next segment
- [ ] Handle custom choice submission
- [ ] Show generation progress
- [ ] Update scene counter
- [ ] Test choice flow

#### 5.3.4: Error Handling (2 hours)
- [ ] Catch all errors from mock API
- [ ] Display user-friendly error messages
- [ ] Provide retry buttons
- [ ] Log errors to console for debugging
- [ ] Test error scenarios

#### 5.3.5: API Service Layer (1 hour)
- [ ] Create `src/services/api.ts` wrapper
- [ ] Export all API methods
- [ ] Make swappable (mock vs. real)
- [ ] Document API for real backend

**Example**:
```typescript
// src/services/api.ts
let USE_MOCK = true;  // Toggle this for real API

const api = USE_MOCK ? mockApi : realApi;

export async function getStories() {
  return api.fetchStories();
}

export async function getSegment(storyId: string, segmentId: string) {
  return api.fetchSegment(storyId, segmentId);
}

export async function generateNextScene(
  storyId: string,
  segmentId: string,
  choiceText: string
) {
  return api.generateNextScene(storyId, segmentId, choiceText);
}
```

---

## Task 5.4: Testing & Polish (8 hours)

**Days 4-5 - Estimated 8 hours**

### What You're Building
Component tests and final polish before Dev 5 styling.

### Subtasks

#### 5.4.1: Component Tests (5 hours)
- [ ] Test each component with different props
- [ ] Test user interactions (clicks, input)
- [ ] Test loading/error states
- [ ] Test with mocked API
- [ ] Aim for 60% coverage minimum

**Test example**:
```typescript
// src/components/__tests__/ChoiceDisplay.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChoiceDisplay } from '../ChoiceDisplay';

test('displays top 2 choices', () => {
  const choices = [
    { id: '1', choice_text: 'Choice 1', ... },
    { id: '2', choice_text: 'Choice 2', ... },
  ];
  
  render(
    <ChoiceDisplay 
      top2={choices} 
      allChoices={choices}
      onSelect={jest.fn()}
    />
  );
  
  expect(screen.getByText('Choice 1')).toBeInTheDocument();
});
```

#### 5.4.2: Integration Tests (2 hours)
- [ ] Test full story flow (list → detail → play)
- [ ] Test choice selection and scene generation
- [ ] Test session save/load
- [ ] Test error recovery

#### 5.4.3: Cleanup & Documentation (1 hour)
- [ ] Remove console errors/warnings
- [ ] Document component API
- [ ] Add README to src/
- [ ] Leave code clean for Dev 5

---

## Daily Progress

### Day 1
- [ ] Task 5.1.1-5.1.4: Setup & routing (12h)
- [ ] Total: ~12 hours

### Day 2
- [ ] Task 5.2.1-5.2.2: Story list & detail (7h)
- [ ] Task 5.1.4 continued: Context polish (1h)
- [ ] Total: ~8 hours (cumulative 20)

### Day 3
- [ ] Task 5.2.3-5.2.5: Play & display components (13h)
- [ ] Total: ~13 hours (cumulative 33)

### Day 4
- [ ] Task 5.2.6-5.2.7: Custom input & counter (5h)
- [ ] Task 5.3.1-5.3.2: Session & navigation (8h)
- [ ] Total: ~13 hours (cumulative 46)

### Day 5
- [ ] Task 5.3.3-5.3.5: Choice handling & API layer (7h)
- [ ] Task 5.4: Testing & polish (6h)
- [ ] Total: ~13 hours (cumulative 59)

**Note**: Total is 59-60 hours depending on pace.

---

## Commit Strategy

```bash
[DEV-4] init react project with routing
[DEV-4] create mock api service
[DEV-4] set up context api for story state
[DEV-4] build story list and detail pages
[DEV-4] build play page and segment display
[DEV-4] add choice display and custom input
[DEV-4] implement session management
[DEV-4] wire up story navigation flow
[DEV-4] implement choice handling and generation
[DEV-4] add component tests and integration tests
```

---

## Success Checklist

- [ ] All components render correctly
- [ ] Routing works end-to-end
- [ ] Mock API integration works
- [ ] Can play a full story flow with mock data
- [ ] Session save/load works
- [ ] No console errors
- [ ] 60%+ test coverage
- [ ] Code ready for Dev 5 styling

---

## Important Notes

**START WITH MOCKS!** Don't wait for Dev 1:
- Use `mockApi.ts` for all API calls
- Frontend is completely independent
- Switch to real API in Week 2.5 (post-Dev-1 completion)

**For Easy API Swap**:
- Create wrapper functions in `src/services/api.ts`
- All components use wrapper, not raw fetch
- Change one file to swap mock ↔ real

---

Good luck! 🚀
