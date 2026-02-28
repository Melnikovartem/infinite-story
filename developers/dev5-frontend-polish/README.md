# Dev 5: Frontend Polish & Accessibility

**Role**: Style, animate, and polish the UI for MVP release.

**Timeline**: Week 1.5-2.5 (45 hours)
**Start after**: Dev 4 completes basic components (Day 3-4)
**Blocks**: Nothing (final polish)

---

## What You're Building

- Tailwind CSS setup / custom CSS
- Responsive design (mobile, tablet, desktop)
- Color system and design tokens
- Animations and micro-interactions
- Accessibility (WCAG 2.1 AA)
- Loading states and skeletons
- Dark mode (optional, if time)
- Performance optimization

---

## Key Tasks

1. **Styling System** (15 hours)
   - Design tokens (colors, spacing, fonts)
   - Tailwind/CSS-in-JS setup
   - Component styling
   - Responsive breakpoints
   - Theme variables

2. **Accessibility** (12 hours)
   - WCAG 2.1 AA compliance
   - Keyboard navigation
   - Screen reader support
   - ARIA labels
   - Color contrast
   - Testing with accessibility tools

3. **Animations & UX Polish** (12 hours)
   - Smooth transitions
   - Loading states
   - Error animations
   - Skeleton screens
   - Micro-interactions

4. **Performance & Testing** (6 hours)
   - Lighthouse audit
   - Bundle size optimization
   - Performance budget
   - Final QA

---

## Success Criteria

- [ ] Fully styled and responsive UI
- [ ] WCAG 2.1 AA accessibility score
- [ ] Lighthouse score 90+
- [ ] Smooth animations throughout
- [ ] Works on mobile/tablet/desktop
- [ ] Zero console errors

---

## Character Avatar System

MVP: Simple colored shapes (no images)

```typescript
const shapes = ['square', 'circle', 'triangle', 'diamond', 'star', 'pentagon'];
const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA502', '#6C5CE7', '#00B894'];

<CharacterAvatar shape="circle" color="#FF6B6B" name="Eira" />
```

---

## See Also

- `TASKS.md` - Detailed breakdown
- `styling-guide.md` - CSS/Tailwind patterns
- `accessibility-guide.md` - WCAG checklist
- `../TEAM_OVERVIEW.md` - Project context

---

**Start**: Day 3-4 (after Dev 4 foundation)
**End**: By end of Week 2.5
**Daily**: ~9 hours/day for 5 days

Good luck! 🚀
