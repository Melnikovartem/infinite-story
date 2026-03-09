# Epic 3: CLI & User Modes

**For Developers H, I**  
**Duration:** 2 weeks (parallel to E1 & E2)  
**Blocker:** Epic 0 complete; E1 helpful but not required  
**Deliverable:** Two CLI modes - immersive (player) and debug (transparent), config system, state persistence

---

## What You're Building

The v2 system has **two distinct CLI interfaces**:

1. **Immersive Mode** → Beautiful prose-focused gameplay (default)
   - Pretty formatting, narrative focus
   - Hide implementation details
   - Focus on story experience

2. **Debug Mode** → Transparent, developer-friendly exploration
   - Show segment details, choice metadata
   - Display generation context, AI reasoning
   - Expose internal state for testing

This epic refactors `cli.py` to support both modes, adds configuration, and ensures state persistence.

---

## Files You'll Touch

### Core Files (Read to Understand)
- `backend/app/cli.py` → **REFACTOR** (existing CLI)
- `backend/app/config.py` → **ENHANCE** (add CLI settings)
- `backend/app/engine/story_runner.py` → Game loop (you'll integrate with)

### Files You'll Create
- `backend/app/ui/formatter.py` → **NEW** (text formatting helpers)
- `backend/app/ui/debug_display.py` → **NEW** (debug mode rendering)

---

## Task Breakdown

### E3-1: Refactor CLI into Two Modes (Dev-H, 3 days)

**What:** Split v1's single CLI into immersive and debug modes.

**File:** `backend/app/cli.py` (REFACTOR)

**Current v1 structure** probably has:
```python
@app.command()
def run_story(story_id: str):
    """Run a story"""
    # ... hard-coded user experience
```

**New v2 structure:**

```python
from typer import Typer
from enum import Enum

class RunMode(str, Enum):
    IMMERSIVE = "immersive"  # Default: beautiful prose
    DEBUG = "debug"          # Transparent: all details shown

app = Typer()

@app.command()
def run_story(
    story_id: str = typer.Option(..., help="Story to play"),
    mode: RunMode = typer.Option(
        RunMode.IMMERSIVE,
        "--mode",
        help="CLI mode: immersive (default) or debug"
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume previous session"
    ),
):
    """
    Run a story with two modes:
    
    Immersive (default):
      ./run.sh story_name
      Beautiful narrative experience, focus on prose.
    
    Debug:
      ./run.sh story_name --mode debug
      Transparent view of segments, choices, context.
    """
    
    # Validate story exists
    story = Story.load(story_id, story_id)
    if not story:
        typer.echo(f"❌ Story '{story_id}' not found")
        raise typer.Exit(1)
    
    # Create runner
    runner = StoryRunner(story)
    
    # Load previous state if resuming
    if resume:
        runner.load_state()
    else:
        runner.start()
    
    # Run appropriate mode
    if mode == RunMode.IMMERSIVE:
        _run_immersive_mode(runner)
    else:
        _run_debug_mode(runner)

def _run_immersive_mode(runner: StoryRunner):
    """Beautiful, prose-focused gameplay"""
    
    while runner.is_running:
        # Get current segment
        current = runner.current_segment
        
        # Display segment with beautiful formatting
        display_segment_immersive(current)
        
        # Get user choice
        choice_id = prompt_choice_immersive(current)
        
        # Execute choice
        try:
            asyncio.run(runner.execute_choice(choice_id))
        except Exception as e:
            typer.echo(f"❌ Error: {e}")
            continue
        
        # Save state
        runner.save_state()

def _run_debug_mode(runner: StoryRunner):
    """Transparent, developer-friendly exploration"""
    
    while runner.is_running:
        current = runner.current_segment
        
        # Display with full context
        display_segment_debug(current)
        
        # Show generation context for next choice
        display_next_context_debug(runner, current)
        
        # Get choice
        choice_id = prompt_choice_debug(current)
        
        # Execute and show AI reasoning
        try:
            context = runner.get_context_for_choice(choice_id)
            typer.echo(f"\n[DEBUG] Generation context:")
            typer.echo(json.dumps(context, indent=2))
            
            asyncio.run(runner.execute_choice(choice_id))
            
            typer.echo(f"\n[DEBUG] New segment created:")
            new_seg = runner.current_segment
            typer.echo(f"  ID: {new_seg.id}")
            typer.echo(f"  Status: {new_seg.status}")
            typer.echo(f"  Pacing: {new_seg.pacing_weight:.1%}")
        
        except Exception as e:
            typer.echo(f"❌ Error: {e}")
            continue
        
        runner.save_state()

@app.command()
def list_stories():
    """List all available stories"""
    stories = Story.list_all()
    
    if not stories:
        typer.echo("No stories found.")
        return
    
    typer.echo("Available Stories:")
    for story in stories:
        typer.echo(f"  • {story.id}: {story.title}")

@app.command()
def delete_story(story_id: str):
    """Delete a story and all associated data"""
    story = Story.load(story_id, story_id)
    if not story:
        typer.echo(f"❌ Story '{story_id}' not found")
        return
    
    confirm = typer.confirm(
        f"Delete '{story.title}' and all segments?"
    )
    if confirm:
        story.delete()
        typer.echo(f"✅ Story deleted")

@app.command()
def clear_state(story_id: str):
    """Reset a story to start (keep segments, clear session)"""
    story = Story.load(story_id, story_id)
    if not story:
        typer.echo(f"❌ Story '{story_id}' not found")
        return
    
    runner = StoryRunner(story)
    runner.clear_state()
    typer.echo(f"✅ Session cleared")
```

**Key Differences:**
- **Immersive**: Minimal metadata, focus on prose, two visible choices
- **Debug**: Show everything—segment ID, status, generation context, pacing weight, character state

**Acceptance Criteria:**
- [ ] `run_story` supports `--mode immersive/debug`
- [ ] `--resume` flag loads previous state
- [ ] `_run_immersive_mode()` focuses on narrative
- [ ] `_run_debug_mode()` shows all details
- [ ] Supporting commands (list, delete, clear) working
- [ ] Unit tests (4+ tests)

---

### E3-2: Immersive Mode Formatting (Dev-H, 2 days)

**What:** Beautiful text rendering for player experience.

**File:** `backend/app/ui/formatter.py` (CREATE NEW)

**Code:**

```python
from typing import List, Optional
from app.models import StorySegment, StoryChoice
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

console = Console()

def display_segment_immersive(segment: StorySegment):
    """
    Display a segment beautifully for immersive mode.
    
    Shows:
    - Segment prose (text blocks)
    - Location/setting info (if any)
    - Character dialogue
    - But NOT: segment ID, pacing_weight, etc.
    """
    
    # Clear screen
    console.clear()
    
    # Display text blocks in order
    for block in segment.text_blocks:
        _display_text_block(block)
    
    # Show location label if present
    if any(b.type == "LOCATION_LABEL" for b in segment.text_blocks):
        location_block = next(
            b for b in segment.text_blocks 
            if b.type == "LOCATION_LABEL"
        )
        console.print(f"\n[dim]{location_block.content}[/dim]")
    
    console.print()  # Spacing

def _display_text_block(block):
    """Display a single text block with appropriate formatting"""
    
    if block.type == "NARRATOR_DESCRIBING":
        console.print(block.content)
    
    elif block.type == "CHARACTER_SPEECH":
        # Quote dialogue
        char = block.character or "Unknown"
        console.print(f"[bold cyan]{char}:[/bold cyan]")
        console.print(f"  "{block.content}"")
    
    elif block.type == "CHARACTER_THOUGHT":
        # Inner monologue
        char = block.character or "?"
        console.print(f"[italic]{char} thought: {block.content}[/italic]")
    
    elif block.type == "NARRATOR_COMMENTARY":
        console.print(f"[dim italic]{block.content}[/dim italic]")
    
    elif block.type == "SCENE_TITLE":
        # Episode/scene title
        title = Panel(
            block.content,
            title="═",
            style="bold magenta"
        )
        console.print(title)
    
    elif block.type == "FLASHBACK":
        console.print(f"[yellow italic]*Flashback*[/yellow italic]")
        console.print(f"  {block.content}")
    
    elif block.type == "DREAM_SEQUENCE":
        console.print(f"[magenta italic]*Dream*[/magenta italic]")
        console.print(f"  {block.content}")
    
    console.print()

def prompt_choice_immersive(segment: StorySegment) -> str:
    """
    Get user choice in immersive mode.
    
    Shows top 2 choices, option to see all or write custom.
    """
    
    choices = segment.outgoing_choices
    
    if not choices:
        console.print("[red]❌ No choices available[/red]")
        return None
    
    # Show top 2 choices
    console.print("[bold]What do you do?[/bold]\n")
    
    top_choices = list(choices.values())[:2]
    
    for i, choice in enumerate(top_choices, 1):
        console.print(f"  {i}. {choice.text}")
    
    console.print(f"\n  [dim]v) View all choices[/dim]")
    console.print(f"  [dim]c) Custom choice[/dim]")
    
    # Get input
    selection = typer.prompt("\nYour choice")
    
    if selection == "1" or selection == "2":
        return top_choices[int(selection) - 1].id
    
    elif selection.lower() == "v":
        return _show_all_choices_and_select(choices)
    
    elif selection.lower() == "c":
        custom_text = typer.prompt("Enter your action")
        return _create_custom_choice(segment, custom_text)
    
    else:
        console.print("[red]Invalid choice[/red]")
        return prompt_choice_immersive(segment)

def _show_all_choices_and_select(choices: dict) -> str:
    """Show all available choices"""
    console.print("\n[bold]All Available Choices:[/bold]\n")
    
    for i, (cid, choice) in enumerate(choices.items(), 1):
        console.print(f"  {i}. {choice.text}")
    
    selection = typer.prompt("\nSelect choice (number)")
    
    try:
        idx = int(selection) - 1
        return list(choices.items())[idx][0]
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")
        return _show_all_choices_and_select(choices)

def _create_custom_choice(segment: StorySegment, text: str) -> str:
    """Create custom choice (will trigger generation)"""
    console.print(f"\n[yellow]You say: {text}[/yellow]")
    console.print("[dim]Generating next scene...[/dim]")
    
    # Create choice, trigger generation
    # (Handled by CLI, just return special ID)
    return f"__custom__{text}"
```

**Acceptance Criteria:**
- [ ] Beautiful text rendering with Rich
- [ ] Text blocks displayed appropriately (dialogue in quotes, etc.)
- [ ] Choice prompting with top 2 options
- [ ] "View all" and "Custom" options working
- [ ] Unit tests (3+ tests)

---

### E3-3: Debug Mode Display (Dev-I, 2 days)

**What:** Transparent, data-rich display for debugging.

**File:** `backend/app/ui/debug_display.py` (CREATE NEW)

**Code:**

```python
import json
from app.models import StorySegment
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

console = Console()

def display_segment_debug(segment: StorySegment):
    """
    Display segment with full internal details.
    
    Shows:
    - Segment ID, status
    - Episode/arc context
    - All text blocks
    - Character states
    - Pacing weight
    """
    
    console.clear()
    
    # Segment metadata
    console.print(f"[bold cyan]SEGMENT: {segment.id}[/bold cyan]")
    console.print(f"  Status: {segment.status}")
    console.print(f"  Episode: {segment.episode_number}")
    console.print(f"  Scene #{segment.segment_number_in_episode} of ~20")
    console.print(f"  Arc: {segment.arc_id or '(unassigned)'}")
    console.print(f"  Parent: {segment.parent_segment_id or '(start)'}")
    console.print()
    
    # Pacing and episode signals
    console.print("[bold yellow]EPISODE SIGNALS[/bold yellow]")
    console.print(f"  Pacing Weight: {segment.pacing_weight:.1%}")
    console.print(f"  End Condition Proximity: {segment.end_condition_proximity:.1%}")
    console.print(f"  Triggers Episode Transition: {segment.triggers_episode_transition}")
    console.print()
    
    # Protagonist and tone
    console.print("[bold green]CONTEXT[/bold green]")
    console.print(f"  Protagonist: {segment.protagonist_id or '(unknown)'}")
    console.print(f"  Tone: {segment.episode_tone or '(not set)'}")
    console.print(f"  End Condition: {segment.episode_end_condition or '(not set)'}")
    console.print()
    
    # Text blocks
    console.print("[bold magenta]TEXT BLOCKS[/bold magenta]")
    for i, block in enumerate(segment.text_blocks):
        console.print(f"\n  [{i}] {block.type}")
        if block.character:
            console.print(f"      Character: {block.character}")
        console.print(f"      Content: {block.content[:100]}...")
    console.print()
    
    # Character states
    if segment.character_states:
        console.print("[bold blue]CHARACTER STATES[/bold blue]")
        table = Table(show_header=True)
        table.add_column("Character")
        table.add_column("Status")
        table.add_column("Mood")
        table.add_column("Location")
        
        for char_id, state in segment.character_states.items():
            table.add_row(
                state.get("name", "?"),
                state.get("status", "?"),
                state.get("mood", "?"),
                state.get("location", "?"),
            )
        
        console.print(table)
        console.print()
    
    # Changes
    if segment.change_notes:
        console.print("[bold cyan]CHANGE NOTES[/bold cyan]")
        for note in segment.change_notes:
            console.print(f"  • {note}")
        console.print()

def display_next_context_debug(runner, segment: StorySegment):
    """
    Show what context will be used for next generation.
    
    Useful for debugging generation logic.
    """
    from app.engine.segment_context_builder import SegmentContextBuilder
    
    console.print("[bold yellow]NEXT GENERATION CONTEXT[/bold yellow]")
    
    builder = SegmentContextBuilder(runner.story)
    
    try:
        # Build context for a hypothetical next choice
        context = builder.build_context(
            segment.id,
            "(hypothetical choice)"
        )
        
        # Show condensed view
        console.print(f"  Episode: {context['episode_number']}")
        console.print(f"  Tone: {context['episode_tone']}")
        console.print(f"  Pacing: {context['pacing_weight']:.1%}")
        console.print(f"  Should Transition: {context['should_transition_episode']}")
        console.print(f"  Accumulated Changes: {len(context['accumulated_changes'])} items")
        
        console.print("\n  [dim]Full context (for copy-paste debugging):[/dim]")
        syntax = Syntax(
            json.dumps(context, indent=2),
            "json",
            theme="monokai"
        )
        console.print(syntax)
    
    except Exception as e:
        console.print(f"  [red]Error building context: {e}[/red]")
    
    console.print()

def prompt_choice_debug(segment: StorySegment) -> str:
    """
    Get user choice in debug mode.
    
    Shows all choices with IDs.
    """
    console.print("[bold]Available Choices:[/bold]\n")
    
    choices = list(segment.outgoing_choices.items())
    
    for i, (cid, choice) in enumerate(choices, 1):
        dest = " → (generated)" if choice.to_segment_id is None else f" → {choice.to_segment_id}"
        console.print(f"  {i}. [{cid}] {choice.text}{dest}")
    
    console.print(f"\n  [dim]Enter choice number or ID[/dim]")
    
    selection = typer.prompt("Choice")
    
    if selection.isdigit():
        idx = int(selection) - 1
        try:
            return choices[idx][0]
        except IndexError:
            console.print("[red]Invalid choice[/red]")
            return prompt_choice_debug(segment)
    else:
        # Treat as ID
        if selection in dict(choices).keys():
            return selection
        else:
            console.print("[red]Choice not found[/red]")
            return prompt_choice_debug(segment)
```

**Acceptance Criteria:**
- [ ] Segment metadata displayed (ID, status, episode, etc.)
- [ ] Character states shown in table
- [ ] Pacing and episode signals visible
- [ ] Next generation context shown (for debugging)
- [ ] Unit tests (2+ tests)

---

### E3-4: Configuration & State Persistence (Dev-I, 2 days)

**What:** Enhanced config and auto-save/resume functionality.

**File:** `backend/app/config.py` (ENHANCE)

**Changes:**

```python
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class CLIConfig:
    """CLI-specific configuration"""
    
    # Display settings
    default_mode: str = os.getenv("ISE_CLI_MODE", "immersive")  # immersive or debug
    width: int = int(os.getenv("ISE_CLI_WIDTH", "100"))
    color: bool = os.getenv("ISE_CLI_COLOR", "true").lower() == "true"
    
    # Gameplay settings
    auto_save: bool = os.getenv("ISE_AUTO_SAVE", "true").lower() == "true"
    show_debug_info: bool = os.getenv("ISE_DEBUG", "false").lower() == "true"
    choices_to_show: int = int(os.getenv("ISE_CHOICES_SHOW", "2"))  # Top N
    
    # State persistence
    save_dir: Path = Path(os.getenv(
        "ISE_STATE_DIR",
        ".infinite_story_data"
    ))
    
    def validate(self):
        """Validate configuration"""
        if self.default_mode not in ["immersive", "debug"]:
            raise ValueError(f"Invalid default_mode: {self.default_mode}")
        
        if self.choices_to_show < 1:
            raise ValueError("choices_to_show must be >= 1")

# Global config instance
cli_config = CLIConfig()
cli_config.validate()
```

**Acceptance Criteria:**
- [ ] Configuration loads from env vars
- [ ] Config validation working
- [ ] Auto-save toggleable
- [ ] Save/load state working (in StoryRunner)
- [ ] Unit tests (3+ tests)

---

## Definition of Done for Epic 3

- [ ] E3-1: CLI refactored into two modes (immersive & debug)
- [ ] E3-2: Immersive mode formatting (beautiful prose display)
- [ ] E3-3: Debug mode display (full transparency)
- [ ] E3-4: Config and state persistence
- [ ] All tests passing (pytest -v)
- [ ] Manual testing: both modes work end-to-end
- [ ] Code review completed
- [ ] PR merged to main

---

## Key Concepts for E3

### Immersive Mode Philosophy
- **Focus on story**: Beautiful prose, minimal metadata
- **Hide complexity**: Segment IDs, pacing weights, etc. not shown
- **Two choices always**: Top 2 suggestions + "View all" option
- **Flow state**: Quick choices, no information paralysis

### Debug Mode Philosophy
- **Full transparency**: Everything shown
- **Developer focus**: IDs, status, context, AI reasoning
- **Learning tool**: See how generation works
- **Testing aid**: Verify pacing, episode transitions, etc.

### State Persistence
```
Session starts:
  StoryRunner.start() → Current segment = start_segment_id

User makes choice:
  StoryRunner.execute_choice() → Generate/traverse → New segment

Auto-save after each choice:
  StoryRunner.save_state() → Write to runner_state.json

Resume previous:
  ./run.sh story_name --resume
  StoryRunner.load_state() → Load current segment and visited

Clear and restart:
  ./run.sh story_name (no --resume flag) → Start fresh
```

---

## Common Pitfalls

1. **Mixed modes** → Don't show debug info in immersive, or vice versa
2. **State corruption** → Validate state before loading
3. **Lost progress** → Always save before starting new generation
4. **Config conflicts** → Env vars should override defaults
5. **Terminal escapes** → Use Rich for all formatting, not raw ANSI codes

---

## Next: Integration with All Epics

Once E3 is merged:
- Users can play with beautiful immersive interface
- Developers can debug with transparent mode
- State persists between sessions
- Config is flexible for different environments
