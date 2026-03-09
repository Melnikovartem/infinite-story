# CLI Modes Guide

## Overview
The Infinite Story CLI now supports 4 distinct modes for different use cases, with configurable logging levels.

## Quick Start

```bash
# Immersive (default) - beautiful narrative
python -m app.cli run-story story_name

# UI Debug - blocks one-by-one with ENTER
python -m app.cli run-story story_name --mode ui_debug

# Story Debug - see generation context
python -m app.cli run-story story_name --mode story_debug

# Dev - minimal with important info
python -m app.cli run-story story_name --mode dev

# Configure logging (error/warn/debug)
python -m app.cli run-story story_name --log-level debug
```

---

## Mode 1: IMMERSIVE (Default)

**Use Case:** Full player experience - beautiful, prose-focused narrative

**Features:**
- Clean screen display with colorful text blocks
- Character dialogue in cyan with quotes
- Scene titles in magenta panels
- Narrator thoughts in italics
- Flashbacks/dreams highlighted with colors
- Top 2 choices shown, option to view all
- No implementation details visible
- Auto-saves after each choice

**How It Works:**
1. Segment displays beautifully
2. Player sees top 2 choices + "view all" option
3. Player makes choice
4. Game advances to next segment or generates new one
5. Auto-saves state

**Output Example:**
```
[cyan bold]The Seaport[/cyan bold]

The salty breeze hits your face as you step onto the weathered dock...

[cyan bold]Captain:[/cyan bold]
  "Welcome aboard, friend. We set sail at dawn."

[dim italic]The captain's eyes gleam with secrets.[/dim italic]

[magenta bold]═══ Chapter 2: Departure ═══[/magenta bold]

1. Ask about the mysterious cargo
2. [View all choices]
```

---

## Mode 2: UI_DEBUG

**Use Case:** Testing UI/UX - blocks appear one-by-one, testing readability

**Features:**
- Clear screen between blocks
- Each text block appears individually
- Player presses ENTER to advance to next block
- Shows block numbers (1/5, 2/5, etc)
- Clean, minimal interface
- All choices shown with numbers
- Good for testing pacing and clarity

**How It Works:**
1. Segment ID shown at top
2. First block displays
3. Player presses ENTER
4. Next block appears
5. After all blocks, shows all choices
6. Player selects by number

**Output Example:**
```
[cyan bold]Segment: segment_042[/cyan bold]

[dim][Block 1/3][/dim]
The salty breeze hits your face as you step onto the weathered dock...

[dim]Press ENTER for next block[/dim]

─────────────────────────────────────
[dim][Block 2/3][/dim]
[cyan bold]Captain:[/cyan bold]
  "Welcome aboard, friend. We set sail at dawn."

[dim]Press ENTER for next block[/dim]
```

---

## Mode 3: STORY_DEBUG

**Use Case:** Debugging generation - see what context is used before generating

**Features:**
- Full segment metadata (ID, arc, parent, episode, status)
- Character table (active vs inactive)
- Arc table (active vs resolved)
- Episode table (current vs archived)
- Generation parameters (temperature, max tokens, context size)
- Strategy table: what will be included/excluded
- All choices shown with click counts and IDs
- Results shown after generation with new segment details

**How It Works:**
1. Display segment with metadata
2. Show generation context (what will be used/excluded)
3. Show all available choices with metadata
4. Player selects choice
5. If generation needed, shows "Generating..." with spinner
6. Display new segment metadata
7. Game continues

**Output Example:**
```
[cyan bold]╔═══ Segment: segment_042 ═══╗[/cyan bold]
[cyan]Status:[/cyan] completed
[cyan]Description:[/cyan] The captain greets you at the dock
[cyan]Episode:[/cyan] episode_001
[cyan]Arc:[/cyan] arc_001_journey
[cyan]Parent:[/cyan] segment_041

[yellow bold]╔═══ Generation Context ═══╗[/yellow bold]

[cyan bold]Characters:[/cyan bold]
┏━━━━━━━━━┳━━━━━┳───────────┓
┃ Name    ┃ Sts ┃ Last Seen ┃
┡━━━━━━━━━╇━━━━━╇───────────┩
│ Captain │ Acv │ This seg  │
│ Sailor  │ Ina │ Earlier   │
└─────────┴─────┴───────────┘

[cyan bold]Arcs:[/cyan bold]
┏━━━━━━━━━━━━━━┳━━━┳──────┓
┃ Arc ID       ┃ St┃ Prog ┃
┡━━━━━━━━━━━━━━╇━━━╇──────┩
│ journey      │ Ac│ 0.3  │
│ treasure_map │ Res│ 1.0  │
└──────────────┴───┴──────┘

[green]✓ Will Include:[/green]
  • Current segment prose and atmosphere
  • Active character states and relationships
  • Current arc direction and goals
  • Episode recap and pacing

[yellow]⊘ Will Exclude:[/yellow]
  • Resolved arcs (to stay focused)
  • Archived episodes (to save tokens)
  • Inactive characters (unless relevant)
```

---

## Mode 4: DEV

**Use Case:** Fast development iteration - minimal interface with key debugging info

**Features:**
- Segment ID prominently shown
- Arc ID (in green) - key for debugging flow
- Parent segment ID (in blue) - tracing navigation
- Episode ID (in magenta) - tracking episodes
- First 3 text blocks only (preview)
- Shows "... and N more blocks" if there are more
- Character count shown
- Simple numeric choice selection
- Minimal noise, maximum signal

**How It Works:**
1. Display segment with essential metadata
2. Show generation context (arc, episode, characters)
3. Show choices with arrow to destination
4. Player selects by number
5. Game advances quickly

**Output Example:**
```
┌─────────────────────────────┐
│ ID:      segment_042        │
│ Arc:     arc_001_journey    │
│ Parent:  segment_041        │
│ Episode: episode_001        │
└─────────────────────────────┘

─────────────────────────────────────
The salty breeze hits your face...
The captain nods knowingly.
  "Welcome aboard, friend..."
... and 2 more blocks
─────────────────────────────────────

[yellow]─ Generation Context ─[/yellow]
Arc:       arc_001_journey
Episode:   episode_001
Characters: 4

[cyan]Choices:[/cyan]
  1. Ask about cargo -> None (will generate)
  2. Board the ship -> segment_043
  3. Return to shore -> segment_040

>
```

---

## Logging Levels

Configure logging with `--log-level`:

### Error (Default)
```bash
python -m app.cli run-story story_name --log-level error
```
- Only errors displayed
- Clean output, no noise
- Best for immersive mode

### Warn
```bash
python -m app.cli run-story story_name --log-level warn
```
- Errors and warnings shown
- Good for design/testing
- Alerts about potential issues

### Debug
```bash
python -m app.cli run-story story_name --log-level debug
```
- Full debug output
- All internal operations logged
- Best for story_debug and dev modes
- Useful for investigating generation

**Example Debug Output:**
```
infinite_story.cli - DEBUG - [EXEC_CHOICE_START] Executing choice: choice_042
infinite_story.cli - DEBUG - [EXEC_CHOICE_GEN_START] Starting generation for choice: Ask about cargo
infinite_story.cli - DEBUG - [EXEC_CHOICE_GEN_CALL] Calling generate_next_scene()
infinite_story.cli - DEBUG - [EXEC_CHOICE_GEN_RECEIVED] Received new segment: segment_043
infinite_story.cli - DEBUG - [EXEC_CHOICE_GEN_DONE] New segment set as current: segment_043
```

---

## Mode Selection Guide

| Mode | Use Case | Player | Developer |
|------|----------|--------|-----------|
| **IMMERSIVE** | Full game experience | ✅ Primary | 🔍 Testing |
| **UI_DEBUG** | Test block pacing | ✅ Alternative | 🔍 UX testing |
| **STORY_DEBUG** | Understand generation | ❌ Too verbose | ✅ Context debugging |
| **DEV** | Fast iteration | ❌ Minimal info | ✅ Quick loops |

---

## Examples

### Play a story immersively
```bash
python -m app.cli run-story veil_of_thornreach
```

### Debug UI pacing issues
```bash
python -m app.cli run-story veil_of_thornreach --mode ui_debug
```

### Investigate why generation is including wrong characters
```bash
python -m app.cli run-story veil_of_thornreach --mode story_debug --log-level debug
```

### Quick development iteration with arc tracking
```bash
python -m app.cli run-story veil_of_thornreach --mode dev --log-level warn
```

### Resume from last position in dev mode
```bash
python -m app.cli run-story veil_of_thornreach --mode dev --resume
```

---

## Architecture

Each mode has its own display module:

- `backend/app/ui/formatter.py` - IMMERSIVE mode
- `backend/app/ui/ui_debug_display.py` - UI_DEBUG mode
- `backend/app/ui/story_debug_display.py` - STORY_DEBUG mode
- `backend/app/ui/dev_display.py` - DEV mode

All modes route through:
- `backend/app/cli.py` - Mode selection and logging setup
- Shared: `_execute_choice()`, `runner.get_available_choices()`, `runner.save_state()`

Logging controlled by `setup_logging()` function in `cli.py`.

---

## Future Enhancements

- [ ] Mode-specific color schemes (high contrast for accessibility)
- [ ] Export mode to save transcripts
- [ ] Replay mode to step through saved games
- [ ] Compare mode to see two branches side-by-side
- [ ] Performance mode with timing statistics
