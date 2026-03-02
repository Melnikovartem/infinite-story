"""Beautiful text formatting for immersive mode CLI - displays lines one-by-one."""

from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
import time

console = Console()


# ============================================================================
# LINE-BY-LINE DISPLAY ENGINE
# ============================================================================

def display_segment_immersive(segment, auto_advance: bool = False, delay: float = 0.05) -> None:
    """
    Display a story segment beautifully for immersive mode.
    Lines appear one-by-one with formatting based on type.
    
    Shows:
    - All text blocks with type-specific formatting
    - Character dialogue with speaker name
    - Scene titles, thoughts, sound effects, etc.
    - Each line appears individually for reading experience
    
    Args:
        segment: Story segment to display
        auto_advance: If True, automatically advance lines. If False, require ENTER
        delay: Delay between auto-advancing lines (seconds)
    """
    console.clear()
    
    # Display each text block
    for block in segment.text_blocks:
        _display_text_block_immersive(block, auto_advance=auto_advance, delay=delay)
    
    console.print()  # Spacing before choices


def _display_text_block_immersive(block, auto_advance: bool = False, delay: float = 0.05) -> None:
    """Display a single text block line-by-line with formatting based on type."""
    
    block_type = block.type.lower() if hasattr(block.type, 'lower') else str(block.type).lower()
    content = block.content if hasattr(block, 'content') else str(block)
    
    # Split content into lines for gradual display
    lines = content.split('\n')
    
    # ========================================================================
    # NARRATOR DESCRIBING - Main narrative prose
    # ========================================================================
    if block_type == "narrator_describing":
        for line in lines:
            if line.strip():
                # Fade in prose text
                text = Text(line)
                text.stylize("white")
                console.print(text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # CHARACTER SPEECH - Dialogue with speaker
    # ========================================================================
    elif block_type == "character_speech":
        char = block.character if hasattr(block, 'character') else "Unknown"
        # Speaker line in cyan, bold
        speaker_text = Text(f"{char}:", style="bold cyan")
        console.print(speaker_text)
        _advance(auto_advance, delay)
        
        # Dialogue lines in quotes, slightly indented
        for line in lines:
            if line.strip():
                dialogue_text = Text(f'  "{line}"', style="cyan")
                console.print(dialogue_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # CHARACTER THOUGHT - Internal monologue/thinking
    # ========================================================================
    elif block_type == "character_thought":
        char = block.character if hasattr(block, 'character') else "?"
        # Header in italic dim style
        thought_header = Text(f"[{char}'s thought]", style="dim italic yellow")
        console.print(thought_header)
        _advance(auto_advance, delay)
        
        # Content in italics
        for line in lines:
            if line.strip():
                thought_text = Text(f"  {line}", style="italic yellow")
                console.print(thought_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # NARRATOR COMMENTARY - Aside/observation
    # ========================================================================
    elif block_type == "narrator_commentary":
        for line in lines:
            if line.strip():
                comment_text = Text(f"  — {line}", style="dim italic")
                console.print(comment_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # SCENE TITLE - Chapter/scene headings
    # ========================================================================
    elif block_type == "scene_title":
        console.print()  # Spacing
        title_panel = Panel(
            Text(content, justify="center", style="bold magenta"),
            title="═",
            border_style="magenta",
            expand=False
        )
        console.print(title_panel)
        _advance(auto_advance, delay)
        console.print()  # Spacing
    
    # ========================================================================
    # FLASHBACK - Past events recalled
    # ========================================================================
    elif block_type == "flashback":
        flashback_header = Text("[Flashback]", style="yellow bold")
        console.print(flashback_header)
        _advance(auto_advance, delay)
        
        for line in lines:
            if line.strip():
                flashback_text = Text(f"  {line}", style="yellow")
                console.print(flashback_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # DREAM SEQUENCE - Dreams/visions
    # ========================================================================
    elif block_type == "dream_sequence":
        dream_header = Text("[Dream]", style="magenta bold")
        console.print(dream_header)
        _advance(auto_advance, delay)
        
        for line in lines:
            if line.strip():
                dream_text = Text(f"  {line}", style="magenta")
                console.print(dream_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # SOUND EFFECTS - [Sound]
    # ========================================================================
    elif block_type == "sfx":
        for line in lines:
            if line.strip():
                sfx_text = Text(f"[{line}]", style="dim cyan italic")
                console.print(sfx_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # VISUAL CUE - [Visual description]
    # ========================================================================
    elif block_type == "visual_cue":
        for line in lines:
            if line.strip():
                visual_text = Text(f"✦ {line}", style="green dim")
                console.print(visual_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # LOCATION LABEL - Location heading
    # ========================================================================
    elif block_type == "location_label":
        location_text = Text(content, style="bold green underline")
        console.print(location_text)
        _advance(auto_advance, delay)
    
    # ========================================================================
    # POEM OR SONG - Poetic content
    # ========================================================================
    elif block_type == "poem_or_song":
        poem_header = Text("[Verse]", style="cyan italic")
        console.print(poem_header)
        _advance(auto_advance, delay)
        
        for line in lines:
            if line.strip():
                # Keep indentation for poems
                poem_text = Text(f"  {line}", style="cyan italic")
                console.print(poem_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # LETTER OR NOTE - Written text
    # ========================================================================
    elif block_type == "letter_or_note":
        for line in lines:
            if line.strip():
                letter_text = Text(f"  {line}", style="yellow dim")
                console.print(letter_text)
                _advance(auto_advance, delay)
    
    # ========================================================================
    # SYSTEM MESSAGE - Meta/system messages
    # ========================================================================
    elif block_type == "system_message":
        system_text = Text(f"[System] {content}", style="dim red")
        console.print(system_text)
        _advance(auto_advance, delay)
    
    # ========================================================================
    # MEDIA OVERLAY - Media elements
    # ========================================================================
    elif block_type == "media_overlay":
        media_text = Text(f"[Media: {content}]", style="blue dim")
        console.print(media_text)
        _advance(auto_advance, delay)
    
    # ========================================================================
    # UNKNOWN TYPE - Default formatting
    # ========================================================================
    else:
        for line in lines:
            if line.strip():
                console.print(line)
                _advance(auto_advance, delay)
    
    console.print()  # Spacing between blocks


def _advance(auto_advance: bool = False, delay: float = 0.05) -> None:
    """Handle advancing to next line/block."""
    if auto_advance:
        time.sleep(delay)
    else:
        # Don't require input, just display all lines at once
        # User can scroll with space or enter at the end
        pass


# ============================================================================
# CHOICE PROMPTS
# ============================================================================

def prompt_choice_immersive(segment, choices: List) -> str:
    """
    Get user choice in immersive mode.
    
    Shows top 2 choices, option to see all or write custom.
    
    Args:
        segment: Current story segment
        choices: List of available choices
    
    Returns:
        Choice ID selected by player
    """
    from rich.table import Table
    from rich.align import Align
    
    console.print("\n[bold cyan]What will you do?[/bold cyan]")
    
    if len(choices) <= 2:
        # Show all choices if 2 or fewer
        for i, choice in enumerate(choices, 1):
            choice_text = choice.text if hasattr(choice, 'text') else str(choice)
            console.print(f"[bold cyan]{i}.[/bold cyan] {choice_text}")
    else:
        # Show top 2, then options
        for i, choice in enumerate(choices[:2], 1):
            choice_text = choice.text if hasattr(choice, 'text') else str(choice)
            console.print(f"[bold cyan]{i}.[/bold cyan] {choice_text}")
        
        console.print(f"[dim]  ... and {len(choices) - 2} more choices[/dim]")
        console.print("[bold cyan]3.[/bold cyan] [dim]View all choices[/dim]")
        console.print("[bold cyan]4.[/bold cyan] [dim]Save and exit[/dim]")
    
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
                    # Show all choices
                    _show_all_choices_and_select(choices)
                    break
                elif selection == "4":
                    # Save and exit
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
