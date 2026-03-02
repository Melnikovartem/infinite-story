"""Beautiful text formatting for immersive mode CLI."""

from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import typer

console = Console()


def display_segment_immersive(segment) -> None:
    """
    Display a story segment beautifully for immersive mode.
    
    Shows:
    - Segment prose (text blocks)
    - Character dialogue
    - Location/setting info (if any)
    
    Hides:
    - Segment ID, pacing_weight, internal state
    """
    
    # Clear screen for fresh display
    console.clear()
    
    # Display text blocks in order
    for block in segment.text_blocks:
        _display_text_block(block)
    
    console.print()  # Spacing before choices


def _display_text_block(block) -> None:
    """Display a single text block with appropriate formatting."""
    
    block_type = block.type.lower() if hasattr(block.type, 'lower') else str(block.type).lower()
    content = block.content if hasattr(block, 'content') else str(block)
    
    if block_type in ["narrator_describing", "narrator_describing"]:
        console.print(content)
    
    elif block_type == "character_speech":
        # Dialogue in quotes
        char = block.character if hasattr(block, 'character') else "Unknown"
        console.print(f"[bold cyan]{char}:[/bold cyan]")
        console.print(f'  "{content}"')
    
    elif block_type == "character_thought":
        # Inner monologue
        char = block.character if hasattr(block, 'character') else "?"
        console.print(f"[italic]{char} thought: {content}[/italic]")
    
    elif block_type == "narrator_commentary":
        # Narrator aside
        console.print(f"[dim italic]{content}[/dim italic]")
    
    elif block_type == "scene_title":
        # Episode/scene title
        title_panel = Panel(
            content,
            title="═",
            style="bold magenta"
        )
        console.print(title_panel)
    
    elif block_type == "flashback":
        console.print(f"[yellow italic]*Flashback*[/yellow italic]")
        console.print(f"  {content}")
    
    elif block_type == "dream_sequence":
        console.print(f"[magenta italic]*Dream*[/magenta italic]")
        console.print(f"  {content}")
    
    elif block_type == "sfx":
        # Sound effects
        console.print(f"[italic][{content}][/italic]")
    
    else:
        # Default formatting for unknown types
        console.print(content)
    
    console.print()  # Spacing between blocks


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
    
    if not choices:
        console.print("[red]❌ No choices available[/red]")
        return None
    
    # Show top 2 choices
    console.print("[bold]What do you do?[/bold]\n")
    
    top_choices = choices[:2]
    
    for i, choice in enumerate(top_choices, 1):
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        console.print(f"  {i}. {choice_text}")
    
    # Show additional options
    console.print(f"\n  [dim]v) View all choices[/dim]")
    console.print(f"  [dim]s) Save and exit[/dim]")
    console.print(f"  [dim]q) Quit without saving[/dim]")
    
    # Get input
    selection = Prompt.ask("\nYour choice").strip().lower()
    
    if selection == "1" and len(top_choices) > 0:
        return top_choices[0].id
    
    elif selection == "2" and len(top_choices) > 1:
        return top_choices[1].id
    
    elif selection == "v":
        return _show_all_choices_and_select(choices)
    
    elif selection == "s":
        console.print("[green]Progress saved![/green]")
        console.print("[yellow]Thanks for playing![/yellow]")
        raise typer.Exit(0)
    
    elif selection == "q":
        console.print("[yellow]Thanks for playing![/yellow]")
        raise typer.Exit(0)
    
    else:
        console.print("[red]Invalid choice, please try again[/red]")
        return prompt_choice_immersive(segment, choices)


def _show_all_choices_and_select(choices: List) -> str:
    """Show all available choices and let player select."""
    console.print("\n[bold]All Available Choices:[/bold]\n")
    
    for i, choice in enumerate(choices, 1):
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        console.print(f"  {i}. {choice_text}")
    
    selection = Prompt.ask("\nSelect choice (number)").strip()
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(choices):
            return choices[idx].id
        else:
            console.print("[red]Invalid selection[/red]")
            return _show_all_choices_and_select(choices)
    except (ValueError, IndexError):
        console.print("[red]Invalid selection[/red]")
        return _show_all_choices_and_select(choices)
