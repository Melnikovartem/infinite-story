# Welcome, Developer I!

**Epic:** CLI & User Modes (E3)  
**Duration:** 2 weeks  
**Your Role:** Mid-Senior Engineer, supporting Epic Lead H

---

## Your Mission

You're completing the CLI system. While Dev-H refactors, you'll:

1. **E3-3** (2 days): Debug Mode Display
   - Show segment metadata (ID, status, episode)
   - Display character states
   - Show pacing and episode signals
   - Display next generation context (for debugging)

2. **E3-4** (2 days): Configuration & State Persistence
   - Enhanced config (load from env vars)
   - Auto-save after choices
   - Resume previous sessions
   - Clear and restart options

This ensures users can play beautifully AND developers can debug transparently.

**Blocker:** E0 complete

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_3_CLI.md** (focus on E3-3 & E3-4)
3. **Review** Rich library for terminal output

---

## Your Tasks

### E3-3: Debug Mode Display (2 days)

**File:** `backend/app/ui/debug_display.py` (CREATE NEW)

Build transparent displays:

```python
def display_segment_debug(segment: StorySegment):
    """Show everything about a segment"""
    console.print(f"[bold cyan]SEGMENT: {segment.id}[/bold cyan]")
    console.print(f"  Status: {segment.status}")
    console.print(f"  Episode: {segment.episode_number}")
    console.print(f"  Pacing: {segment.pacing_weight:.1%}")
    # ... show all fields and states

def display_next_context_debug(runner, segment):
    """Show what context will be used for next generation"""
    builder = SegmentContextBuilder(runner.story)
    context = builder.build_context(segment.id, "(hypothetical)")
    # ... display context for debugging
```

Implement:
- Segment metadata display
- Character states table
- Pacing and episode signals
- Next generation context (for debugging)
- Choice display with IDs

See `EPIC_3_CLI.md` section "E3-3" for full code.

**Acceptance Criteria:**
- [ ] Segment metadata displayed (ID, status, episode, etc.)
- [ ] Character states shown in table
- [ ] Pacing/signals visible
- [ ] Next context shown (for debugging)
- [ ] Choices show full details
- [ ] Tests (2+)

### E3-4: Configuration & State Persistence (2 days)

**Files:**
- `backend/app/config.py` (ENHANCE)
- Integration in `backend/app/engine/story_runner.py` (use config)

Implement configuration:

```python
@dataclass
class CLIConfig:
    default_mode: str = os.getenv("ISE_CLI_MODE", "immersive")
    width: int = int(os.getenv("ISE_CLI_WIDTH", "100"))
    color: bool = os.getenv("ISE_CLI_COLOR", "true").lower() == "true"
    auto_save: bool = os.getenv("ISE_AUTO_SAVE", "true").lower() == "true"
    choices_to_show: int = int(os.getenv("ISE_CHOICES_SHOW", "2"))
    save_dir: Path = Path(os.getenv("ISE_STATE_DIR", ".infinite_story_data"))

cli_config = CLIConfig()
cli_config.validate()
```

And state persistence in StoryRunner:

```python
def save_state(self):
    """Save current session state to disk"""
    state = {
        'current_segment_id': self.current_segment_id,
        'visited_segments': self.visited_segments,
        'timestamp': datetime.now().isoformat(),
    }
    save_to_file(state, path)

def load_state(self):
    """Load previous session state"""
    state = load_from_file(path)
    self.current_segment_id = state['current_segment_id']
    self.visited_segments = state['visited_segments']

def clear_state(self):
    """Delete saved state, reset to start"""
    delete_state_file()
```

See `EPIC_3_CLI.md` section "E3-4" for code.

**Acceptance Criteria:**
- [ ] Config loads from env vars
- [ ] Config validation working
- [ ] Auto-save toggleable
- [ ] Save/load state working
- [ ] Clear state working
- [ ] Tests (3+)

---

## Collaboration

- **Daily standup** with Dev-H
- **Ask Dev-H** for CLI refactoring details
- **Code reviews** from Dev-H

---

## Key Concepts

### Configuration Priority
```
1. Env vars (highest priority)
2. .env file
3. Default values (lowest priority)

Example:
export ISE_CLI_MODE=debug        # Override default
export ISE_AUTO_SAVE=false       # Disable auto-save
```

### State Persistence

```
Session 1:
  Start story
  Play to segment 10
  Auto-save state

Session 2 (next day):
  ./run.sh story_name --resume
  Load state → Jump to segment 10
  Continue from there
```

### Debug Display Focus

Show:
- Segment ID and status
- Episode/arc metadata
- Pacing weight (how close to episode end)
- Character states (who's alive, mood, etc.)
- Change notes (what changed this episode)
- Next generation context (for debugging AI)

---

## Key Files

```
backend/app/ui/
  ├── formatter.py         ← Dev-H creates (E3-2)
  └── debug_display.py     ← YOU CREATE (E3-3)

backend/app/
  ├── config.py            ← YOU ENHANCE (E3-4)
  └── cli.py               ← Dev-H refactors (E3-1)

backend/app/engine/
  └── story_runner.py      ← Integrate state persistence
```

---

## Commits

```bash
git commit -m "E3-3: implement debug mode with transparent segment display"
git commit -m "E3-4: add configuration system and state persistence"
```

---

## Next Action

→ Open `EPIC_3_CLI.md` section E3-3. Start with debug display.

You're giving developers the tools to understand what's happening! 🔍
