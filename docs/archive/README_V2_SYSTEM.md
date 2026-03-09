# Infinite Story Engine v2: Shared Graph with Narrative Overlays

## 📚 Documentation Index

You're looking at a complete redesign of the story engine. Here's where to start:

### For Everyone

**[VISION.md](./VISION.md)** (18 KB) — **START HERE**
- What is the new system?
- Why design it this way?
- How does it feel to use?
- Comparison to other systems
- Philosophy and principles

### For Developers

**[ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md)** (30 KB) — **Technical Details**
- System overview with diagrams
- Data models (Segment, Choice, Episode, Arc, etc.)
- Generation pipeline (step-by-step)
- Episode recap system
- Arc compression system
- CLI implementation (both modes)
- Storage structure
- Performance considerations
- Testing strategy

**[REIMPLEMENTATION_PLAN.md](./REIMPLEMENTATION_PLAN.md)** (32 KB) — **Build Plan**
- 7 phases of implementation (4-5 weeks total)
- Specific files to create/modify
- Code examples for each phase
- Testing requirements
- Risk analysis
- Success criteria
- Rollout strategy

### Quick Reference

**[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** (25 KB) — **Diagrams & Checklists**
- Data model diagram
- Generation flow (detailed)
- Episode recap process
- Arc compression process
- Character state tracking
- CLI modes comparison
- File changes summary
- Common mistakes to avoid
- Performance targets
- Debugging checklist
- Database growth estimates

**[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** (9 KB) — **One-Page Overview**
- Document overview
- Quick concept reference
- Implementation phases summary
- Migration path
- Rollout checklist
- Key files to create/modify
- Success criteria
- Glossary

---

## 🎯 Quick Navigation

### "I want to understand the vision"
→ Read [VISION.md](./VISION.md)

### "I want to implement this"
→ Read [REIMPLEMENTATION_PLAN.md](./REIMPLEMENTATION_PLAN.md) then [ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md)

### "I need a quick diagram"
→ Check [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

### "What changed from the old system?"
→ See Comparison section in [VISION.md](./VISION.md)

### "How do I handle X?"
→ Use Glossary in [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) to find relevant doc

### "What files do I need to create?"
→ Check "File Changes Summary" in [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

### "How long will this take?"
→ See "Implementation Phases" in [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

---

## 🔑 Key Concepts (TL;DR)

### The Problem We're Solving

**Old system**: Infinite branching tree. No structure. Exponential growth. Per-user state duplication.

**New system**: Shared immutable segment graph. Episodes + arcs provide narrative shape. Compression stabilizes timeline.

### The Core Insight

```
Users explore the same world
  ↓
Make different choices
  ↓
Generate shared segments
  ↓
Experience unique journeys
  ↓
(Compression picks mainline)
  ↓
Next arc continues together
```

### Core Data Structure

**Segment** (immutable node)
- Generated once
- Shared by all users who reach it
- Contains episode context (baked)
- Contains character snapshot + changes

**Choice** (edge)
- Points to segment or null (unexplored)
- First pick triggers generation
- Subsequent picks reuse existing segment

**Episode** (metadata overlay)
- ~20 segments with shared tone
- Context baked into segments
- Recap generated when ends
- Next segments start new episode

**Arc** (compression point)
- ~15 episodes
- Compressed to pick mainline
- Non-mainline archived
- Next arc continues from mainline

**User Session** (minimal state)
- Just a cursor: current_segment + visited
- No per-user episode tracking
- No per-user character states

---

## 📋 Implementation Checklist

### Phase 1: Models (Week 1)
- [ ] Enhance Segment model (add episode context, character states)
- [ ] Enhance Choice model (add status field)
- [ ] Create EpisodeRecap model
- [ ] Create StoryArc model
- [ ] Simplify UserSession model
- [ ] Create migration script

### Phase 2: Generation (Week 1)
- [ ] Create SegmentContextBuilder
- [ ] Update generation pipeline
- [ ] Implement episode transition logic
- [ ] Handle pacing weight calculation

### Phase 3: Episodes (Week 1)
- [ ] Create EpisodeRecapGenerator
- [ ] Implement recap generation
- [ ] Implement character state reconciliation
- [ ] Generate new episode context

### Phase 4: Compression (Week 1)
- [ ] Create ArcCompressor
- [ ] Implement branch finding
- [ ] Implement mainline selection
- [ ] Implement archiving

### Phase 5: CLI (Week 1)
- [ ] Implement gameplay mode
- [ ] Implement exploration mode
- [ ] Create display functions
- [ ] Create dev commands

### Phase 6: Testing (Weeks 1-2)
- [ ] Unit tests for all components
- [ ] Integration tests for full flow
- [ ] Simulation tests for multi-user
- [ ] Migration tests

### Phase 7: Finalization
- [ ] Update documentation
- [ ] Performance tuning
- [ ] Final testing
- [ ] Deploy

---

## 🚀 Getting Started

### For New Team Members

1. Read **[VISION.md](./VISION.md)** (30 min)
   - Get the big picture
   - Understand philosophy
   - See example UX

2. Read **[ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md)** Sections 1-3 (1 hour)
   - Data models
   - Generation pipeline
   - Episode system

3. Browse **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** (20 min)
   - Diagrams help understanding
   - Use as reference while reading code

### For Implementation

1. Follow **[REIMPLEMENTATION_PLAN.md](./REIMPLEMENTATION_PLAN.md)** phases in order
2. Reference **[ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md)** for details
3. Use **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** for quick lookups
4. Check **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** for checklists

---

## 📊 Document Sizes & Reading Time

| Document | Size | Reading Time | Best For |
|----------|------|--------------|----------|
| VISION.md | 18 KB | 30 min | Understanding vision |
| ARCHITECTURE_V2.md | 30 KB | 1.5 hours | Implementation details |
| REIMPLEMENTATION_PLAN.md | 32 KB | 1 hour | Planning work |
| QUICK_REFERENCE.md | 25 KB | Reference | Diagrams, checklists |
| IMPLEMENTATION_SUMMARY.md | 9 KB | 15 min | Quick overview |
| **TOTAL** | **114 KB** | **3 hours** | Full understanding |

---

## 🎮 Example: How It Works End-to-End

### User 1 Session

```
1. Start: Load world, pick protagonist Eira, start at Segment 1
2. Segment 1: "You arrive in Thornreach"
   - Episode 1, tone: "mystery"
   - Choice A (unexplored)
   
3. Choose A: AI generates Segment 2
   - Episode 1, Eira learns about curse
   - Choice A, B (unexplored)
   
4. Choose B: AI generates Segment 3
   - Episode 1, meets rebel leader
   - Change notes: "encountered Thorne"
   - ...continues...
   
5. Segment 20: end_condition_proximity ≈ 1.0
   - Triggers episode recap
   - AI generates: title, summary, character final states
   
6. Segment 21 (from choice): Episode 2 starts
   - New tone: "betrayal"
   - New end_condition
   - Character states from recap
```

### User 2 Session (later)

```
1. Start: Load world, pick protagonist Thorne, start at Segment 1
2. Segment 1: "You arrive in Thornreach" (SAME as User 1)
   - Episode 1, tone: "mystery"
   - Same choices
   
3. Choose A: AI ALREADY GENERATED Segment 2
   - User 2 gets EXACT same segment (shared!)
   - Same change notes: Eira learned about curse
   
4. Choose A: different choice path
   - AI generates different Segment (4)
   - But still Episode 1
   - New branch formed
```

### After Arc 1 (15 episodes)

```
Arc compression:
- User 1's branch: 1→2→5→12→... (popular)
- User 2's branch: 1→2→3→7→... (popular)
- User 3's branch: 1→4→6→... (random)
- User 4's branch: 1→3→8→... (random)

AI reviews & picks: User 1's branch as mainline
- Other branches archived (hidden)
- All segments in other branches marked ARCHIVED
- Users with other branches can still read archived content
  but can't explore forward from them

Arc 2 starts:
- All users continue from mainline frontier (Segment at position of User 1)
- New arc, new episodes, new tone
```

---

## 🔧 Technology Stack

### Backend (Unchanged)
- Python 3.13+
- Pydantic for models
- Typer for CLI
- Rich for terminal UI
- Asyncio for async operations

### New Libraries (May Add)
- Redis (for distributed locking if scaling)
- PostgreSQL (if moving from JSON to DB)

### Existing Integration Points
- OpenAI / OpenRouter (AI generation) — unchanged API
- JSON file storage — new schema
- CLI interface — dual mode

---

## 🐛 Common Issues & Troubleshooting

### Segment Not Showing Change Notes
- Check: Is segment.change_notes populated?
- Check: Are you reading from the right segment?
- Note: Change notes only visible in exploration mode

### Episode Not Transitioning
- Check: Is end_condition_proximity >= 0.8?
- Check: Is segment.segment_number_in_episode >= 18?
- Debug: Use exploration mode to see proximity value

### Character State Inconsistent
- Check: Is recap being generated?
- Check: Is AI reconciling changes correctly?
- Debug: Review recap character_states_final

### Archive Not Working
- Check: Are non-mainline segments marked ARCHIVED?
- Check: Is Story.get_segment() excluding archived?
- Note: Can recover archived segments with include_archived=True

---

## 📞 Questions?

### Design Questions
→ See [VISION.md](./VISION.md) sections "Key Design Decisions" and "Known Limitations"

### Implementation Questions
→ See [ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md) relevant section

### Timeline Questions
→ See [REIMPLEMENTATION_PLAN.md](./REIMPLEMENTATION_PLAN.md) "Timeline" section

### Code Examples
→ See [ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md) and [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)

### Performance Questions
→ See [ARCHITECTURE_V2.md](./ARCHITECTURE_V2.md) "Performance Considerations" and [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) "Performance Targets"

---

## 📝 Change Summary from v1

| Aspect | v1 | v2 |
|--------|----|----|
| **Segments** | Per-user generation | Shared immutable nodes |
| **Graph** | Infinite tree | Bounded by compression |
| **State** | Per-user episode tracking | Minimal cursor only |
| **Episodes** | Not implemented | Narrative structure |
| **Arcs** | Not implemented | Compression + mainline |
| **Character State** | Basic | Snapshot + running log |
| **CLI** | Single mode | Two modes (gameplay/exploration) |
| **Scaling** | Unbounded growth | Stable after compression |

---

## 🎯 Success Metrics

After implementation, the system should:

✅ Handle 100+ concurrent users
✅ Generate segments in <10 seconds (AI call)
✅ Load segments in <100ms
✅ Compress arcs in <5 minutes
✅ Provide immersive gameplay experience (mode 1)
✅ Provide full debugging capability (mode 2)
✅ Migrate existing stories without data loss
✅ All tests passing
✅ Documentation complete

---

## 📦 What's Next?

1. **Review VISION.md** with stakeholders
2. **Review ARCHITECTURE_V2.md** with engineering team
3. **Plan resources** using REIMPLEMENTATION_PLAN.md
4. **Create development branch** (v2-segment-graph)
5. **Start Phase 1** (models and data structure)
6. **Weekly check-ins** against plan
7. **Deploy when all phases complete**

---

## 📄 Document Versions

- **VISION.md** v1.0 — Final design
- **ARCHITECTURE_V2.md** v1.0 — Technical specs
- **REIMPLEMENTATION_PLAN.md** v1.0 — Build plan
- **QUICK_REFERENCE.md** v1.0 — Reference guide
- **IMPLEMENTATION_SUMMARY.md** v1.0 — Overview
- **README_V2_SYSTEM.md** v1.0 — This document

Last updated: March 2, 2026

---

**Ready to build? Start with [VISION.md](./VISION.md) →**
