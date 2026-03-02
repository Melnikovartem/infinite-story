"""Story Debug mode - comprehensive generation context display."""

from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
import json

console = Console()


def display_segment_story_debug(segment) -> None:
    """
    Display segment with full metadata and context.
    
    Shows:
    - Segment ID, status, description
    - Episode and arc information
    - Character states
    - Generation context (what was used/excluded)
    - Text blocks
    """
    console.clear()
    
    # Header with segment info
    console.print(f"\n[bold cyan]╔═══ Segment: {segment.id} ═══╗[/bold cyan]")
    console.print(f"[cyan]Status:[/cyan] {getattr(segment, 'status', 'unknown')}")
    console.print(f"[cyan]Description:[/cyan] {segment.short_description if hasattr(segment, 'short_description') else 'N/A'}")
    
    # Episode and Arc info
    if hasattr(segment, 'episode_id'):
        console.print(f"[cyan]Episode:[/cyan] {segment.episode_id}")
    if hasattr(segment, 'arc_id'):
        console.print(f"[cyan]Arc:[/cyan] {segment.arc_id}")
    if hasattr(segment, 'parent_segment_id'):
        console.print(f"[cyan]Parent:[/cyan] {segment.parent_segment_id}")
    
    console.print()


def display_generation_context_story_debug(runner, segment) -> None:
    """
    Display comprehensive generation context before generating new content.
    
    Shows:
    - Characters (active vs inactive)
    - Arcs (active vs resolved)
    - Episodes (current vs archived)
    - Generation parameters
    - What will be included/excluded
    """
    console.print("[bold yellow]╔═══ Generation Context ═══╗[/bold yellow]\n")
    
    # Get story and component data
    story = runner.story if hasattr(runner, 'story') else None
    if not story:
        console.print("[dim]Story data not available[/dim]")
        return
    
    # Characters table
    if hasattr(story, 'characters'):
        console.print("[bold cyan]Characters:[/bold cyan]")
        char_table = Table(show_header=True, header_style="bold magenta")
        char_table.add_column("Name", style="cyan")
        char_table.add_column("Status", style="green")
        char_table.add_column("Last Seen", style="yellow")
        
        for char_id, char in story.characters.items():
            name = char.name if hasattr(char, 'name') else char_id
            status = "Active" if char_id in getattr(segment, 'active_characters', []) else "Inactive"
            last_seen = "This segment" if char_id in getattr(segment, 'active_characters', []) else "Earlier"
            char_table.add_row(name, status, last_seen)
        
        console.print(char_table)
        console.print()
    
    # Arcs table
    if hasattr(story, 'arcs'):
        console.print("[bold cyan]Arcs:[/bold cyan]")
        arc_table = Table(show_header=True, header_style="bold magenta")
        arc_table.add_column("Arc ID", style="cyan")
        arc_table.add_column("Status", style="green")
        arc_table.add_column("Progress", style="yellow")
        
        for arc_id, arc in story.arcs.items():
            status = "Active" if arc_id in getattr(segment, 'active_arcs', []) else "Resolved"
            progress = getattr(arc, 'progress', 'unknown')
            arc_table.add_row(arc_id, status, str(progress))
        
        console.print(arc_table)
        console.print()
    
    # Episodes table
    if hasattr(story, 'episodes'):
        console.print("[bold cyan]Episodes:[/bold cyan]")
        ep_table = Table(show_header=True, header_style="bold magenta")
        ep_table.add_column("Episode", style="cyan")
        ep_table.add_column("Status", style="green")
        
        for ep_id, episode in story.episodes.items():
            status = "Current" if ep_id == getattr(segment, 'episode_id', None) else "Archived"
            ep_table.add_row(ep_id, status)
        
        console.print(ep_table)
        console.print()
    
    # Generation parameters
    console.print("[bold cyan]Generation Parameters:[/bold cyan]")
    gen_table = Table(show_header=False)
    gen_table.add_row("[cyan]Temperature:[/cyan]", "[yellow]0.7[/yellow]")
    gen_table.add_row("[cyan]Max Tokens:[/cyan]", "[yellow]2000[/yellow]")
    gen_table.add_row("[cyan]Context Size:[/cyan]", "[yellow]~4000 tokens[/yellow]")
    console.print(gen_table)
    console.print()
    
    # What will be included/excluded
    console.print("[bold cyan]Generation Strategy:[/bold cyan]")
    console.print("[green]✓ Will Include:[/green]")
    console.print("  • Current segment prose and atmosphere")
    console.print("  • Active character states and relationships")
    console.print("  • Current arc direction and goals")
    console.print("  • Episode recap and pacing")
    
    console.print("\n[yellow]⊘ Will Exclude:[/yellow]")
    console.print("  • Resolved arcs (to stay focused)")
    console.print("  • Archived episodes (to save tokens)")
    console.print("  • Inactive characters (unless relevant)")
    console.print()


def display_generation_result_story_debug(segment) -> None:
    """Display result of generation with what was actually used."""
    console.print("[bold green]╔═══ Generation Complete ═══╗[/bold green]\n")
    
    console.print(f"[cyan]New Segment:[/cyan] {segment.id}")
    console.print(f"[cyan]Episode:[/cyan] {getattr(segment, 'episode_id', 'N/A')}")
    console.print(f"[cyan]Arc:[/cyan] {getattr(segment, 'arc_id', 'N/A')}")
    console.print(f"[cyan]Blocks Generated:[/cyan] {len(getattr(segment, 'text_blocks', []))}")
    console.print()


def prompt_choice_story_debug(segment, choices: List) -> str:
    """
    Get user choice in story debug mode.
    Shows all choices with IDs and detailed metadata.
    
    Args:
        segment: Current story segment
        choices: List of available choices
    
    Returns:
        Choice ID selected by player
    """
    console.print("\n[bold cyan]Available Choices:[/bold cyan]")
    
    choice_table = Table(show_header=True, header_style="bold magenta")
    choice_table.add_column("Num", style="cyan")
    choice_table.add_column("Choice Text", style="white")
    choice_table.add_column("To Segment", style="yellow")
    choice_table.add_column("Clicks", style="green")
    
    for i, choice in enumerate(choices, 1):
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        to_segment = choice.to_segment_id if hasattr(choice, 'to_segment_id') else "Generate"
        clicks = getattr(choice, 'clicks', 0)
        
        choice_table.add_row(
            str(i),
            choice_text[:50],
            str(to_segment) if to_segment else "[yellow]NEW[/yellow]",
            str(clicks)
        )
    
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
            console.print("[red]Invalid selection[/red]")
