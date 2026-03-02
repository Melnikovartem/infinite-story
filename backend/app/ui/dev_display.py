"""Dev mode - minimal info with important details like arc/parent."""

from typing import List
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


def display_segment_dev(segment) -> None:
    """
    Display segment in dev mode with minimal but important info.
    
    Shows:
    - Segment ID
    - Arc and parent segment (important for debugging)
    - Episode
    - Brief text preview
    """
    console.clear()
    
    # Minimal header
    info_table = Table(show_header=False, show_edge=False)
    info_table.add_row("[cyan]ID:[/cyan]", f"[yellow]{segment.id}[/yellow]")
    if hasattr(segment, 'arc_id') and segment.arc_id:
        info_table.add_row("[cyan]Arc:[/cyan]", f"[green]{segment.arc_id}[/green]")
    if hasattr(segment, 'parent_segment_id') and segment.parent_segment_id:
        info_table.add_row("[cyan]Parent:[/cyan]", f"[blue]{segment.parent_segment_id}[/blue]")
    if hasattr(segment, 'episode_id') and segment.episode_id:
        info_table.add_row("[cyan]Episode:[/cyan]", f"[magenta]{segment.episode_id}[/magenta]")
    
    console.print(info_table)
    console.print()
    
    # Brief text
    if hasattr(segment, 'text_blocks') and segment.text_blocks:
        console.print("[dim]─" * 40 + "[/dim]")
        for block in segment.text_blocks[:3]:  # First 3 blocks only
            content = block.content if hasattr(block, 'content') else str(block)
            console.print(content[:100])
        if len(segment.text_blocks) > 3:
            console.print(f"[dim]... and {len(segment.text_blocks) - 3} more blocks[/dim]")
        console.print("[dim]─" * 40 + "[/dim]")
    
    console.print()


def display_generation_context_dev(runner, segment) -> None:
    """
    Display minimal generation context for dev mode.
    
    Shows only the most important info:
    - Arc being developed
    - Episode context
    - Characters in play
    """
    console.print("[yellow]─ Generation Context ─[/yellow]")
    
    story = runner.story if hasattr(runner, 'story') else None
    if not story:
        return
    
    ctx_table = Table(show_header=False, show_edge=False)
    
    if hasattr(segment, 'arc_id'):
        ctx_table.add_row("[cyan]Arc:[/cyan]", f"[green]{segment.arc_id}[/green]")
    if hasattr(segment, 'episode_id'):
        ctx_table.add_row("[cyan]Episode:[/cyan]", f"[magenta]{segment.episode_id}[/magenta]")
    
    # Character count
    active_chars = getattr(segment, 'active_characters', [])
    if active_chars:
        ctx_table.add_row("[cyan]Characters:[/cyan]", f"[yellow]{len(active_chars)}[/yellow]")
    
    console.print(ctx_table)
    console.print()


def prompt_choice_dev(segment, choices: List) -> str:
    """
    Get user choice in dev mode.
    Simple numeric selection.
    
    Args:
        segment: Current story segment
        choices: List of available choices
    
    Returns:
        Choice ID selected by player
    """
    console.print("\n[cyan]Choices:[/cyan]")
    
    for i, choice in enumerate(choices, 1):
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        to_seg = choice.to_segment_id if hasattr(choice, 'to_segment_id') else "..."
        console.print(f"  {i}. {choice_text[:60]} -> {to_seg}")
    
    while True:
        try:
            selection = Prompt.ask(
                "[bold]>",
                choices=[str(i) for i in range(1, len(choices) + 1)]
            )
            selected_choice = choices[int(selection) - 1]
            return selected_choice.id if hasattr(selected_choice, 'id') else str(selected_choice)
        except (ValueError, IndexError):
            pass
