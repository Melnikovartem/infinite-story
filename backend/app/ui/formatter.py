"""Beautiful text formatting for immersive mode CLI - displays lines one-by-one.

Supports storyline-aware rollout (different timing/style per storyline type)
and character emotion indicators.
"""

from typing import List, Optional, Dict
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
import time
import random

from app.models.text_types import StorylineType, STORYLINE_DISPLAY_CONFIG

console = Console()


# ============================================================================
# STORYLINE-AWARE ROLLOUT ENGINE
# ============================================================================

# Emotion color mapping for subtle emotion indicators
_EMOTION_COLORS = {
    # Negative
    "angry": "red", "furious": "bold red", "enraged": "bold red",
    "fearful": "red dim", "afraid": "red dim", "terrified": "bold red",
    "sad": "blue dim", "grieving": "blue", "heartbroken": "magenta dim",
    "anxious": "yellow dim", "nervous": "yellow dim", "worried": "yellow",
    "desperate": "red", "hopeless": "dim", "defeated": "dim red",
    "suspicious": "yellow", "distrustful": "yellow dim",
    "betrayed": "bold red", "vengeful": "red",
    # Positive
    "happy": "bright_green", "joyful": "bold green", "elated": "bold bright_green",
    "hopeful": "green", "optimistic": "green",
    "calm": "cyan dim", "serene": "cyan", "peaceful": "cyan dim",
    "determined": "bold white", "resolute": "bold white",
    "curious": "cyan", "intrigued": "cyan",
    "confident": "bold cyan", "brave": "bold cyan",
    "loving": "magenta", "affectionate": "magenta", "tender": "magenta dim",
    # Neutral / complex
    "conflicted": "yellow", "torn": "yellow dim",
    "stoic": "white dim", "neutral": "white dim",
    "mysterious": "dim cyan", "enigmatic": "dim cyan",
    "amused": "bright_green dim", "sardonic": "yellow dim",
}


def _get_emotion_color(emotion: Optional[str]) -> str:
    """Get Rich color string for an emotion, with fuzzy matching."""
    if not emotion:
        return "white"
    emotion_lower = emotion.lower().strip()
    # Direct match
    if emotion_lower in _EMOTION_COLORS:
        return _EMOTION_COLORS[emotion_lower]
    # Fuzzy: check if any keyword appears in the emotion string
    for keyword, color in _EMOTION_COLORS.items():
        if keyword in emotion_lower:
            return color
    return "white"


def _get_storyline_config(storyline: Optional[str]) -> Dict:
    """Get display config for a storyline type."""
    if not storyline:
        return {"color": "white", "delay": 0.05, "icon": "", "rollout": "steady"}
    try:
        st = StorylineType(storyline)
        return STORYLINE_DISPLAY_CONFIG.get(st, {"color": "white", "delay": 0.05, "icon": "", "rollout": "steady"})
    except ValueError:
        return {"color": "white", "delay": 0.05, "icon": "", "rollout": "steady"}


def _rollout_line(text_obj: Text, rollout: str, delay: float, auto_advance: bool) -> None:
    """Display a line with storyline-specific rollout effect.
    
    Rollout styles:
    - burst:    Instant display with brief flash (action)
    - fade:     Slow character-by-character reveal (mystery)
    - gentle:   Smooth line display with soft pause (romance)
    - measured: Standard display with deliberate pause (political)
    - crawl:    Very slow, ominous reveal (horror)
    - bounce:   Quick with tiny random pauses (comedy)
    - steady:   Normal display (drama)
    - sweep:    Left-to-right sweep feel (exploration)
    """
    if not auto_advance:
        # Non-auto: just print immediately
        console.print(text_obj)
        return
    
    if rollout == "burst":
        # Action: instant print, very short pause
        console.print(text_obj)
        time.sleep(delay * 0.4)
    
    elif rollout == "fade":
        # Mystery: character-by-character with cursor effect
        plain = text_obj.plain
        style = text_obj.style or "white"
        for i in range(0, len(plain), 3):
            chunk = Text(plain[:i+3])
            chunk.stylize(str(style))
            console.print(chunk, end="\r")
            time.sleep(delay * 0.3)
        console.print(text_obj)  # Final clean print
    
    elif rollout == "crawl":
        # Horror: slow reveal with longer pauses
        console.print(text_obj)
        time.sleep(delay * 2.5)
    
    elif rollout == "bounce":
        # Comedy: quick print with random micro-pauses
        console.print(text_obj)
        time.sleep(delay * random.uniform(0.2, 0.8))
    
    elif rollout == "gentle":
        # Romance: smooth with soft pause
        console.print(text_obj)
        time.sleep(delay * 1.2)
    
    elif rollout == "sweep":
        # Exploration: moderate paced
        console.print(text_obj)
        time.sleep(delay * 0.8)
    
    elif rollout == "measured":
        # Political: deliberate, even pacing
        console.print(text_obj)
        time.sleep(delay * 1.0)
    
    else:
        # steady / default
        console.print(text_obj)
        time.sleep(delay)


# ============================================================================
# LINE-BY-LINE DISPLAY ENGINE
# ============================================================================

def display_segment_immersive(segment, auto_advance: bool = False, delay: float = 0.05) -> None:
    """Display a story segment with storyline-aware rollout and emotion indicators.
    
    Features:
    - Storyline type determines rollout speed and overall color accent
    - Per-block emotions shown as subtle color shifts
    - Character emotions summary shown after scene
    - Different text types get type-specific formatting
    
    Args:
        segment: Story segment to display
        auto_advance: If True, automatically advance lines with delays
        delay: Base delay between auto-advancing lines (seconds)
    """
    console.clear()
    
    # Get segment-level storyline config
    seg_storyline = getattr(segment, 'storyline_type', None)
    seg_config = _get_storyline_config(seg_storyline)
    
    # Show storyline indicator if present
    if seg_storyline and seg_config.get("icon"):
        icon = seg_config["icon"]
        sl_color = seg_config["color"]
        console.print(Text(f" {icon} {seg_storyline.upper()} ", style=f"{sl_color}"))
        console.print()
    
    # Display each text block with storyline-aware rollout
    for block in segment.text_blocks:
        # Determine rollout: per-block storyline overrides segment-level
        block_storyline = getattr(block, 'storyline', None) or seg_storyline
        block_config = _get_storyline_config(block_storyline) if block_storyline != seg_storyline else seg_config
        
        _display_text_block_immersive(
            block,
            auto_advance=auto_advance,
            delay=block_config.get("delay", delay),
            rollout=block_config.get("rollout", "steady"),
            storyline_color=block_config.get("color", "white"),
        )
    
    # Show character emotion summary after the scene
    char_emotions = getattr(segment, 'character_emotions', {})
    if char_emotions:
        console.print()
        _display_emotion_summary(char_emotions)
    
    console.print()  # Spacing before choices


def _display_emotion_summary(character_emotions: Dict[str, str]) -> None:
    """Display a subtle character emotion summary bar after a scene."""
    parts = []
    for char_name, emotion in character_emotions.items():
        color = _get_emotion_color(emotion)
        parts.append(f"[{color}]{char_name}: {emotion}[/{color}]")
    
    if parts:
        emotion_line = "  ".join(parts)
        console.print(f"[dim]  -- [/dim]{emotion_line}")


def _display_text_block_immersive(
    block,
    auto_advance: bool = False,
    delay: float = 0.05,
    rollout: str = "steady",
    storyline_color: str = "white",
) -> None:
    """Display a single text block with type-specific formatting and storyline rollout."""
    
    block_type = block.type.lower() if hasattr(block.type, 'lower') else str(block.type).lower()
    content = block.content if hasattr(block, 'content') else str(block)
    block_emotion = getattr(block, 'emotion', None)
    
    # Emotion can tint the text subtly
    emotion_color = _get_emotion_color(block_emotion)
    
    # Split content into lines for gradual display
    lines = content.split('\n')
    
    # ========================================================================
    # NARRATOR DESCRIBING - Main narrative prose
    # ========================================================================
    if block_type == "narrator_describing":
        # Use storyline color for narration tinting
        style = storyline_color if storyline_color != "white" else emotion_color
        for line in lines:
            if line.strip():
                text = Text(line, style=style)
                _rollout_line(text, rollout, delay, auto_advance)
    
    # ========================================================================
    # CHARACTER SPEECH - Dialogue with speaker + emotion indicator
    # ========================================================================
    elif block_type == "character_speech":
        char = block.character if hasattr(block, 'character') else "Unknown"
        # Speaker line with emotion color hint
        speaker_style = f"bold {emotion_color}" if block_emotion else "bold cyan"
        emotion_tag = f" [{block_emotion}]" if block_emotion else ""
        speaker_text = Text(f"{char}{emotion_tag}:", style=speaker_style)
        _rollout_line(speaker_text, rollout, delay, auto_advance)
        
        # Dialogue lines
        dialogue_style = emotion_color if block_emotion else "cyan"
        for line in lines:
            if line.strip():
                dialogue_text = Text(f'  "{line}"', style=dialogue_style)
                _rollout_line(dialogue_text, rollout, delay, auto_advance)
    
    # ========================================================================
    # CHARACTER THOUGHT - Internal monologue with emotion
    # ========================================================================
    elif block_type == "character_thought":
        char = block.character if hasattr(block, 'character') else "?"
        emotion_tag = f" ({block_emotion})" if block_emotion else ""
        thought_header = Text(f"[{char}'s thought{emotion_tag}]", style=f"dim italic {emotion_color}")
        _rollout_line(thought_header, rollout, delay, auto_advance)
        
        thought_style = f"italic {emotion_color}" if block_emotion else "italic yellow"
        for line in lines:
            if line.strip():
                thought_text = Text(f"  {line}", style=thought_style)
                _rollout_line(thought_text, rollout, delay, auto_advance)
    
    # ========================================================================
    # NARRATOR COMMENTARY - Aside/observation
    # ========================================================================
    elif block_type == "narrator_commentary":
        for line in lines:
            if line.strip():
                comment_text = Text(f"  -- {line}", style="dim italic")
                _rollout_line(comment_text, rollout, delay, auto_advance)
    
    # ========================================================================
    # SCENE TITLE - Chapter/scene headings
    # ========================================================================
    elif block_type == "scene_title":
        console.print()
        # Use storyline color for title border
        border_color = storyline_color.replace("bold ", "").replace("dim ", "").replace("italic ", "")
        if border_color in ("white",):
            border_color = "magenta"
        title_panel = Panel(
            Text(content, justify="center", style=f"bold {border_color}"),
            title="=",
            border_style=border_color,
            expand=False
        )
        console.print(title_panel)
        _rollout_line(Text(""), rollout, delay * 2, auto_advance)
        console.print()
    
    # ========================================================================
    # FLASHBACK - Past events recalled
    # ========================================================================
    elif block_type == "flashback":
        flashback_header = Text("[Flashback]", style="yellow bold")
        _rollout_line(flashback_header, "fade", delay, auto_advance)
        
        for line in lines:
            if line.strip():
                flashback_text = Text(f"  {line}", style="yellow")
                _rollout_line(flashback_text, "fade", delay, auto_advance)
    
    # ========================================================================
    # DREAM SEQUENCE - Dreams/visions
    # ========================================================================
    elif block_type == "dream_sequence":
        dream_header = Text("[Dream]", style="magenta bold")
        _rollout_line(dream_header, "crawl", delay, auto_advance)
        
        for line in lines:
            if line.strip():
                dream_text = Text(f"  {line}", style="magenta")
                _rollout_line(dream_text, "crawl", delay, auto_advance)
    
    # ========================================================================
    # SOUND EFFECTS - [Sound]
    # ========================================================================
    elif block_type == "sfx":
        for line in lines:
            if line.strip():
                sfx_text = Text(f"[{line}]", style="dim cyan italic")
                _rollout_line(sfx_text, "burst", delay, auto_advance)
    
    # ========================================================================
    # VISUAL CUE - [Visual description]
    # ========================================================================
    elif block_type == "visual_cue":
        for line in lines:
            if line.strip():
                visual_text = Text(f"* {line}", style="green dim")
                _rollout_line(visual_text, rollout, delay, auto_advance)
    
    # ========================================================================
    # LOCATION LABEL - Location heading
    # ========================================================================
    elif block_type == "location_label":
        location_text = Text(content, style="bold green underline")
        _rollout_line(location_text, "sweep", delay, auto_advance)
    
    # ========================================================================
    # POEM OR SONG - Poetic content
    # ========================================================================
    elif block_type == "poem_or_song":
        poem_header = Text("[Verse]", style="cyan italic")
        _rollout_line(poem_header, "gentle", delay, auto_advance)
        
        for line in lines:
            if line.strip():
                poem_text = Text(f"  {line}", style="cyan italic")
                _rollout_line(poem_text, "gentle", delay, auto_advance)
    
    # ========================================================================
    # LETTER OR NOTE - Written text
    # ========================================================================
    elif block_type == "letter_or_note":
        for line in lines:
            if line.strip():
                letter_text = Text(f"  {line}", style="yellow dim")
                _rollout_line(letter_text, "measured", delay, auto_advance)
    
    # ========================================================================
    # SYSTEM MESSAGE - Meta/system messages
    # ========================================================================
    elif block_type == "system_message":
        system_text = Text(f"[System] {content}", style="dim red")
        _rollout_line(system_text, "burst", delay, auto_advance)
    
    # ========================================================================
    # MEDIA OVERLAY - Media elements
    # ========================================================================
    elif block_type == "media_overlay":
        media_text = Text(f"[Media: {content}]", style="blue dim")
        _rollout_line(media_text, rollout, delay, auto_advance)
    
    # ========================================================================
    # UNKNOWN TYPE - Default formatting
    # ========================================================================
    else:
        for line in lines:
            if line.strip():
                text = Text(line)
                _rollout_line(text, rollout, delay, auto_advance)
    
    console.print()  # Spacing between blocks


def _advance(auto_advance: bool = False, delay: float = 0.05) -> None:
    """Handle advancing to next line/block (legacy helper)."""
    if auto_advance:
        time.sleep(delay)


# ============================================================================
# CHOICE PROMPTS
# ============================================================================

def prompt_choice_immersive(segment, choices: List) -> str:
    """Get user choice in immersive mode.
    
    Shows top 2 choices, option to see all or write custom.
    Choices are tinted by segment storyline color.
    
    Args:
        segment: Current story segment
        choices: List of available choices
    
    Returns:
        Choice ID selected by player
    """
    from rich.table import Table
    from rich.align import Align
    
    # Get storyline accent color
    seg_storyline = getattr(segment, 'storyline_type', None)
    accent = _get_storyline_config(seg_storyline).get("color", "cyan")
    # Strip modifiers for prompt styling
    accent_clean = accent.replace("bold ", "").replace("dim ", "").replace("italic ", "").replace("bright_", "")
    if accent_clean in ("white", "white dim"):
        accent_clean = "cyan"
    
    console.print(f"\n[bold {accent_clean}]What will you do?[/bold {accent_clean}]")
    
    if len(choices) <= 2:
        for i, choice in enumerate(choices, 1):
            choice_text = choice.text if hasattr(choice, 'text') else str(choice)
            console.print(f"[bold {accent_clean}]{i}.[/bold {accent_clean}] {choice_text}")
    else:
        for i, choice in enumerate(choices[:2], 1):
            choice_text = choice.text if hasattr(choice, 'text') else str(choice)
            console.print(f"[bold {accent_clean}]{i}.[/bold {accent_clean}] {choice_text}")
        
        console.print(f"[dim]  ... and {len(choices) - 2} more choices[/dim]")
        console.print(f"[bold {accent_clean}]3.[/bold {accent_clean}] [dim]View all choices[/dim]")
        console.print(f"[bold {accent_clean}]4.[/bold {accent_clean}] [dim]Save and exit[/dim]")
    
    while True:
        try:
            if len(choices) <= 2:
                selection = Prompt.ask(
                    "[bold]Choose",
                    choices=[str(i) for i in range(1, len(choices) + 1)]
                )
                selected_choice = choices[int(selection) - 1]
            else:
                selection = Prompt.ask(
                    "[bold]Choose",
                    choices=["1", "2", "3", "4"]
                )
                
                if selection == "3":
                    return _show_all_choices_and_select(choices)
                elif selection == "4":
                    console.print("[yellow]Game saved. Thanks for playing![/yellow]")
                    return None
                else:
                    selected_choice = choices[int(selection) - 1]
            
            return selected_choice.id if hasattr(selected_choice, 'id') else str(selected_choice)
        except (ValueError, IndexError):
            console.print("[red]Invalid choice[/red]")


def _show_all_choices_and_select(choices: List) -> str:
    """Show all available choices in a menu."""
    from rich.table import Table
    
    console.print("\n[bold cyan]All Choices:[/bold cyan]\n")
    
    choice_table = Table(show_header=True, header_style="bold cyan")
    choice_table.add_column("No.", style="cyan")
    choice_table.add_column("Choice", style="white")
    
    for i, choice in enumerate(choices, 1):
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        choice_table.add_row(str(i), choice_text)
    
    console.print(choice_table)
    
    while True:
        try:
            selection = Prompt.ask(
                "[bold]Select choice by number",
                choices=[str(i) for i in range(1, len(choices) + 1)]
            )
            selected_choice = choices[int(selection) - 1]
            return selected_choice.id if hasattr(selected_choice, 'id') else str(selected_choice)
        except (ValueError, IndexError):
            console.print("[red]Invalid choice[/red]")
