# Welcome, Developer H!

**Epic:** CLI & User Modes (E3)  
**Duration:** 2 weeks  
**Your Role:** Senior Engineer, Epic Lead

---

## Your Mission

You're building the user-facing interface. Your team (H, I) will create two CLI modes:

1. **Immersive Mode** (default) → Beautiful, prose-focused gameplay
   - Pretty formatting, narrative focus
   - Hide implementation details
   - Quick choices, flow state

2. **Debug Mode** → Transparent, developer exploration
   - Show everything: segment ID, status, context
   - Display generation details
   - Show pacing, character states

You'll also lead architecture, configuration, and state management.

**Blocker:** E0 complete; E1/E2 helpful but not required

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_3_CLI.md** (your detailed blueprint)
3. **Look at existing** `backend/app/cli.py` (understand current structure)
4. **Review** Rich library docs for beautiful formatting

---

## Your Epic Tasks

### E3-1: Refactor CLI into Two Modes (3 days)

**File:** `backend/app/cli.py` (REFACTOR)

Refactor the existing CLI to support:

```python
class RunMode(str, Enum):
    IMMERSIVE = "immersive"
    DEBUG = "debug"

@app.command()
def run_story(
    story_id: str,
    mode: RunMode = RunMode.IMMERSIVE,
    resume: bool = False,
):
    """Run story in immersive or debug mode"""
    
    runner = StoryRunner(story)
    if resume:
        runner.load_state()
    else:
        runner.start()
    
    if mode == RunMode.IMMERSIVE:
        _run_immersive_mode(runner)
    else:
        _run_debug_mode(runner)
```

Implement:
- `_run_immersive_mode()` → Beautiful narrative flow
- `_run_debug_mode()` → Full transparency
- Supporting commands: `list-stories`, `delete-story`, `clear-state`

See `EPIC_3_CLI.md` section "E3-1" for full code.

**Acceptance Criteria:**
- [ ] CLI supports `--mode immersive/debug`
- [ ] `--resume` flag loads previous state
- [ ] Both modes working end-to-end
- [ ] Supporting commands complete
- [ ] Unit tests (4+)

### E3-2: Immersive Mode Formatting (2 days)

**File:** `backend/app/ui/formatter.py` (CREATE NEW)

Build beautiful text rendering:

```python
def display_segment_immersive(segment: StorySegment):
    """Pretty display for immersive mode"""
    for block in segment.text_blocks:
        _display_text_block(block)

def _display_text_block(block):
    if block.type == "CHARACTER_SPEECH":
        console.print(f"[bold cyan]{char}:[/bold cyan]")
        console.print(f"  \"{block.content}\"")
```

Implement:
- Pretty rendering for all text block types
- Choice prompting (top 2 + view all + custom)
- No debug info shown

See `EPIC_3_CLI.md` section "E3-2" for code and examples.

**Acceptance Criteria:**
- [ ] Beautiful formatting with Rich
- [ ] All block types rendered nicely
- [ ] Choice prompting working
- [ ] Tests (3+)

---

## Dev-I's Work (Parallel)

While you lead E3-1/2, Dev-I will:
- E3-3: Debug Mode Display
- E3-4: Configuration & State Persistence

You code review their work. Coordinate daily.

---

## Collaboration

- **Daily standup** with Dev-I
- **Code reviews** for Dev-I's PRs

---

## Key Libraries

- **Rich** → Beautiful terminal output (already in requirements)
- **Typer** → CLI framework (already in requirements)
- **asyncio** → Async support

---

## Design Principles

### Immersive Mode
- Focus on story, not mechanics
- Hide segment IDs, status, pacing weight
- Quick feedback loop
- Two visible choices (not all)
- Beautiful prose formatting

### Debug Mode
- Show everything
- Display internal state
- Show generation context before generation
- Useful for testing and learning

---

## Commits

```bash
git commit -m "E3-1: refactor cli into immersive and debug modes"
git commit -m "E3-2: implement immersive mode with beautiful formatting"
```

---

## Next Action

→ Open `EPIC_3_CLI.md` section E3-1. Start refactoring cli.py.

You're building the gateway to the story engine! 🎨
