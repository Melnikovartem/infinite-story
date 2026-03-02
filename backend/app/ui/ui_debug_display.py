"""UI Debug mode - blocks appear one-by-one with space, clean interface."""

from typing import List
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()


def display_segment_ui_debug(segment) -> None:
    """
    Display segment with blocks appearing one-by-one.
    User presses space to continue to next block.
    
    Features:
    - Clean, colored interface
    - Pause between blocks for readability
    - Shows block type subtly
    """
    console.clear()
    console.print(f"[bold cyan]Segment: {segment.id}[/bold cyan]\n")
    
    for i, block in enumerate(segment.text_blocks, 1):
        _display_text_block_interactive(block, i, len(segment.text_blocks))
        
        # Pause before next block (except last one)
        if i < len(segment.text_blocks):
            Prompt.ask("\n[dim]Press ENTER for next block[/dim]", default="")
    
    console.print()  # Spacing before choices


def _display_text_block_interactive(block, block_num: int, total_blocks: int) -> None:
    """Display a single text block with type indicator and formatting."""
    
    block_type = block.type.lower() if hasattr(block.type, 'lower') else str(block.type).lower()
    content = block.content if hasattr(block, 'content') else str(block)
    
    # Show block indicator
    console.print(f"[dim][Block {block_num}/{total_blocks}][/dim]")
    
    if block_type in ["narrator_describing", "narrator_describing"]:
        console.print(content)
    
    elif block_type == "character_speech":
        char = block.character if hasattr(block, 'character') else "Unknown"
        console.print(f"[bold cyan]{char}:[/bold cyan]")
        console.print(f'  "{content}"')
    
    elif block_type == "character_thought":
        char = block.character if hasattr(block, 'character') else "?"
        console.print(f"[italic]{char} thought: {content}[/italic]")
    
    elif block_type == "narrator_commentary":
        console.print(f"[dim italic]{content}[/dim italic]")
    
    elif block_type == "scene_title":
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
        console.print(f"[italic][{content}][/italic]")
    
    else:
        console.print(content)


def prompt_choice_ui_debug(segment, choices: List) -> str:
    """
    Get user choice in UI debug mode.
    Shows all choices with numeric selection.
    
    Args:
        segment: Current story segment
        choices: List of available choices
    
    Returns:
        Choice ID selected by player
    """
    console.print("\n[bold cyan]Available Choices:[/bold cyan]")
    
    for i, choice in enumerate(choices, 1):
        choice_id = choice.id if hasattr(choice, 'id') else str(choice)
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        console.print(f"  {i}. {choice_text}")
    
    while True:
        try:
            selection = Prompt.ask(
                "[bold]Select choice",
                choices=[str(i) for i in range(1, len(choices) + 1)]
            )
            selected_choice = choices[int(selection) - 1]
            return selected_choice.id if hasattr(selected_choice, 'id') else str(selected_choice)
        except (ValueError, IndexError):
            console.print("[red]Invalid selection[/red]")
