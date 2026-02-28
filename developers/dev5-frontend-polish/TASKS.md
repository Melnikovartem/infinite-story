# Dev 5: Frontend Polish - Detailed Task Breakdown

**Total Hours**: 45 (9 hours/day × 5 days)
**Timeline**: Week 1.5-2.5
**Start After**: Dev 4 completes basic component structure (Day 3-4)

---

## Task 6.1: Design System & Styling Setup (12 hours)

**Days 1-2 - Estimated 12 hours**

### What You're Building
Color system, typography, spacing, and Tailwind/CSS configuration.

### Subtasks

#### 6.1.1: Design Tokens (3 hours)
- [ ] Define color palette (primary, secondary, accent, neutrals)
- [ ] Define typography scale (headings, body, small)
- [ ] Define spacing scale (8px, 16px, 24px, etc.)
- [ ] Define border radius scales
- [ ] Define shadow system
- [ ] Create design-tokens.ts or CSS variables

**Example**:
```typescript
// src/styles/design-tokens.ts
export const colors = {
  primary: '#6366F1',
  secondary: '#06B6D4',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  neutral: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    500: '#6B7280',
    900: '#111827',
  },
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
};
```

#### 6.1.2: Tailwind CSS Configuration (3 hours)
- [ ] If using Tailwind:
  - Install tailwindcss
  - Create tailwind.config.ts
  - Import design tokens
  - Configure custom colors and spacing
  - Set up content paths
- [ ] Or set up CSS-in-JS (styled-components, emotion, etc.)
- [ ] Set up global styles

#### 6.1.3: Component Base Styles (3 hours)
- [ ] Create base button styles (primary, secondary, ghost, danger)
- [ ] Create base card/container styles
- [ ] Create base form input styles
- [ ] Create text/heading styles
- [ ] Create layout utility classes
- [ ] Test styles with existing components

#### 6.1.4: Responsive Design (3 hours)
- [ ] Define breakpoints (mobile: 0, tablet: 768px, desktop: 1024px)
- [ ] Set up media query helpers
- [ ] Test responsive layout
- [ ] Document breakpoints

---

## Task 6.2: Component Styling (15 hours)

**Days 2-3 - Estimated 15 hours**

### What You're Building
Style all components from Dev 4 to look polished and professional.

### Subtasks

#### 6.2.1: Story List Page Styling (3 hours)
- [ ] Style story cards (image placeholder, title, description)
- [ ] Create card grid layout
- [ ] Add hover effects
- [ ] Make responsive (1 col mobile, 2 col tablet, 3 col desktop)
- [ ] Style search/filter if present
- [ ] Test styling

#### 6.2.2: Story Detail Page Styling (2 hours)
- [ ] Style header with story info
- [ ] Style character grid with avatars
- [ ] Style location list
- [ ] Create nice call-to-action button
- [ ] Make responsive
- [ ] Test styling

#### 6.2.3: Play Page Styling (5 hours)
- [ ] Style scene title prominently
- [ ] Format text block content (different styles per type)
- [ ] Style character presence indicator
- [ ] Style location info
- [ ] Style progress counter (prominent, easy to read)
- [ ] Create nice layout with good readability
- [ ] Test styling

#### 6.2.4: Choice Display Styling (3 hours)
- [ ] Style top 2 choices as prominent buttons
- [ ] Create "View All" expandable section
- [ ] Style choice list with hover effects
- [ ] Add choice popularity indicators (optional)
- [ ] Make mobile-friendly
- [ ] Test styling

#### 6.2.5: Custom Choice Input Styling (1 hour)
- [ ] Style input with good focus states
- [ ] Style submit button
- [ ] Add character counter (optional)
- [ ] Make error messages visible
- [ ] Test styling

#### 6.2.6: Progress Counter Styling (1 hour)
- [ ] Make scene counter prominent but not intrusive
- [ ] Use nice typography
- [ ] Add icons if desired
- [ ] Style elapsed time nicely
- [ ] Test styling

---

## Task 6.3: Accessibility & WCAG Compliance (12 hours)

**Days 3-4 - Estimated 12 hours**

### What You're Building
Ensure UI is accessible to all users (WCAG 2.1 AA standard).

### Subtasks

#### 6.3.1: Semantic HTML (2 hours)
- [ ] Review all components for semantic tags
- [ ] Use proper heading hierarchy (h1, h2, h3, etc.)
- [ ] Use `<button>` for buttons, `<a>` for links
- [ ] Use `<nav>`, `<main>`, `<article>`, etc.
- [ ] Fix non-semantic elements
- [ ] Test with accessibility checker

#### 6.3.2: Keyboard Navigation (3 hours)
- [ ] Test tab order (should be logical)
- [ ] Ensure all interactive elements are keyboard accessible
- [ ] Set focus styles (visible outlines)
- [ ] Test with keyboard only (no mouse)
- [ ] Fix focus trap if needed
- [ ] Test with screen reader

#### 6.3.3: Color Contrast & Readability (3 hours)
- [ ] Check all text/background contrast (WCAG AA minimum 4.5:1)
- [ ] Use WebAIM contrast checker
- [ ] Fix low contrast areas
- [ ] Don't rely on color alone (use icons/text)
- [ ] Test with color blindness simulator
- [ ] Document color choices

#### 6.3.4: ARIA Labels (2 hours)
- [ ] Add aria-label to icon buttons
- [ ] Add aria-describedby for help text
- [ ] Add aria-live for dynamic content
- [ ] Add role attributes where needed
- [ ] Remove redundant ARIA
- [ ] Test with screen reader (NVDA, JAWS, or VoiceOver)

#### 6.3.5: Accessibility Testing (2 hours)
- [ ] Run Lighthouse accessibility audit
- [ ] Fix all critical issues
- [ ] Use axe DevTools browser extension
- [ ] Test with real screen reader
- [ ] Document accessibility features

---

## Task 6.4: Animations & Micro-interactions (12 hours)

**Days 4-5 - Estimated 12 hours**

### What You're Building
Smooth animations, loading states, and delightful micro-interactions.

### Subtasks

#### 6.4.1: Page Transitions (2 hours)
- [ ] Add fade-in on page load
- [ ] Add slide/fade between segments
- [ ] Add smooth route transitions
- [ ] Keep animations fast (< 300ms)
- [ ] Test on slow devices

#### 6.4.2: Loading States (3 hours)
- [ ] Create skeleton screens for content
- [ ] Add loading spinners
- [ ] Fade in content when loaded
- [ ] Show loading state on buttons
- [ ] Disable buttons during loading
- [ ] Test loading UX

#### 6.4.3: Interactive Feedback (3 hours)
- [ ] Add hover effects to buttons/cards
- [ ] Add active/pressed state
- [ ] Add transition effects (200-300ms)
- [ ] Add hover tooltip effects
- [ ] Test on mobile (no hover, use active state)
- [ ] Ensure feedback is clear

#### 6.4.4: Error States & Animations (2 hours)
- [ ] Style error messages with animation
- [ ] Add shake/bounce effect on errors
- [ ] Fade in error alerts
- [ ] Slide in notification bars
- [ ] Test error flow

#### 6.4.5: Celebration/Success Animations (2 hours)
- [ ] Add subtle success animation when choice selected
- [ ] Add animation when scene loads
- [ ] Add fade effect for text blocks
- [ ] Keep animations tasteful (not distracting)
- [ ] Test on various devices

---

## Task 6.5: Performance & Final Polish (4 hours)

**Day 5 - Estimated 4 hours**

### What You're Building
Fast, polished, production-ready UI.

### Subtasks

#### 6.5.1: Lighthouse Audit (2 hours)
- [ ] Run Lighthouse (DevTools)
- [ ] Fix critical performance issues
- [ ] Target score: 90+ overall
- [ ] Performance: 85+
- [ ] Accessibility: 95+
- [ ] Best Practices: 90+
- [ ] SEO: 90+

#### 6.5.2: Bundle Size Optimization (1 hour)
- [ ] Check bundle size: `npm run build`
- [ ] Use dynamic imports for heavy components
- [ ] Remove unused dependencies
- [ ] Check for duplicate packages
- [ ] Lazy load routes if needed

#### 6.5.3: Final QA & Polish (1 hour)
- [ ] Check all pages on different screen sizes
- [ ] Test on real mobile device
- [ ] Check for typos
- [ ] Verify all links work
- [ ] Test all interactive elements
- [ ] No console errors/warnings
- [ ] Run accessibility checker one more time

---

## Daily Progress

### Day 1
- [ ] Task 6.1.1-6.1.4: Design system (12h)
- [ ] Total: ~12 hours

### Day 2
- [ ] Task 6.2.1-6.2.3: Component styling (10h)
- [ ] Task 6.3.1: Semantic HTML (2h)
- [ ] Total: ~12 hours (cumulative 24)

### Day 3
- [ ] Task 6.2.4-6.2.6: Remaining component styling (5h)
- [ ] Task 6.3.2-6.3.3: Keyboard & contrast (6h)
- [ ] Total: ~11 hours (cumulative 35)

### Day 4
- [ ] Task 6.3.4-6.3.5: ARIA labels & testing (4h)
- [ ] Task 6.4.1-6.4.3: Animations (8h)
- [ ] Total: ~12 hours (cumulative 47)

### Day 5
- [ ] Task 6.4.4-6.4.5: Error/success animations (4h)
- [ ] Task 6.5: Performance & polish (4h)
- [ ] Total: ~8 hours (cumulative 55)

**Note**: Adjust daily amounts as needed to hit 45 total.

---

## Commit Strategy

```bash
[DEV-5] add design tokens and tailwind setup
[DEV-5] style story list and detail pages
[DEV-5] style play page and choice display
[DEV-5] add focus states and keyboard navigation
[DEV-5] improve color contrast for wcag compliance
[DEV-5] add aria labels and semantic html
[DEV-5] add smooth page transitions and loading states
[DEV-5] add button hover and interactive feedback
[DEV-5] add error and success animations
[DEV-5] optimize performance and final polish
```

---

## Success Checklist

- [ ] All components styled consistently
- [ ] Responsive design working (mobile, tablet, desktop)
- [ ] WCAG 2.1 AA accessibility level
- [ ] All animations smooth and performant
- [ ] Lighthouse score 90+
- [ ] No console errors
- [ ] Keyboard navigation working
- [ ] Screen reader compatible
- [ ] Ready for production MVP

---

## Testing & QA

Before considering complete, test:

- [ ] Desktop browsers (Chrome, Firefox, Safari, Edge)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)
- [ ] Tablet (iPad, Android tablet)
- [ ] Keyboard navigation (no mouse)
- [ ] Screen reader (NVDA, JAWS, VoiceOver)
- [ ] Color blindness simulator
- [ ] Lighthouse audit
- [ ] Bundle size
- [ ] Performance on slow device (throttle CPU)

---

## Notes for Dev 5

**Start timing**: Days 3-4 of Dev 4
- Dev 4 will have basic components without styling
- You'll add styling, animations, and polish
- Dev 4 will ensure no console errors before you start
- Focus on making it look amazing while keeping it accessible

**Avoid**:
- Overly complex animations (keep under 300ms)
- Animations that interfere with accessibility
- Colors that don't have sufficient contrast
- Keyboard traps
- Removing focus outlines

**Embrace**:
- Smooth, purposeful animations
- Clear visual feedback for all interactions
- High color contrast
- Semantic HTML
- Keyboard accessibility

---

Good luck! 🚀
