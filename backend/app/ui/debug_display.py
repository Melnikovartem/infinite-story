"""Debug mode display for transparent story exploration."""

import json
from typing import List
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt
import typer

console = Console()


def display_segment_debug(segment) -> None:
    """
    Display segment with full internal details.
    
    Shows:
    - Segment ID, status
    - Episode/arc context
    - All text blocks
    - Character states
    - Pacing weight and episode signals
    """
    
    console.clear()
    
    # Segment metadata
    segment_id = segment.id if hasattr(segment, 'id') else "unknown"
    status = segment.status if hasattr(segment, 'status') else "unknown"
    episode_num = segment.episode_number if hasattr(segment, 'episode_number') else "?"
    segment_num = segment.segment_number_in_episode if hasattr(segment, 'segment_number_in_episode') else "?"
    arc_id = segment.arc_id if hasattr(segment, 'arc_id') else None
    parent_id = segment.parent_segment_id if hasattr(segment, 'parent_segment_id') else None
    
    console.print(f"[bold cyan]SEGMENT: {segment_id}[/bold cyan]")
    console.print(f"  Status: {status}")
    console.print(f"  Episode: {episode_num}")
    console.print(f"  Scene #{segment_num} of ~20")
    console.print(f"  Arc: {arc_id or '(unassigned)'}")
    console.print(f"  Parent: {parent_id or '(start)'}")
    console.print()
    
    # Pacing and episode signals
    pacing = segment.pacing_weight if hasattr(segment, 'pacing_weight') else 0
    end_proximity = segment.end_condition_proximity if hasattr(segment, 'end_condition_proximity') else 0
    triggers_transition = segment.triggers_episode_transition if hasattr(segment, 'triggers_episode_transition') else False
    
    console.print("[bold yellow]EPISODE SIGNALS[/bold yellow]")
    console.print(f"  Pacing Weight: {pacing:.1%}" if isinstance(pacing, (int, float)) else f"  Pacing Weight: {pacing}")
    console.print(f"  End Condition Proximity: {end_proximity:.1%}" if isinstance(end_proximity, (int, float)) else f"  End Condition Proximity: {end_proximity}")
    console.print(f"  Triggers Episode Transition: {triggers_transition}")
    console.print()
    
    # Protagonist and tone
    protagonist = segment.protagonist_id if hasattr(segment, 'protagonist_id') else None
    tone = segment.episode_tone if hasattr(segment, 'episode_tone') else None
    end_condition = segment.episode_end_condition if hasattr(segment, 'episode_end_condition') else None
    
    console.print("[bold green]CONTEXT[/bold green]")
    console.print(f"  Protagonist: {protagonist or '(unknown)'}")
    console.print(f"  Tone: {tone or '(not set)'}")
    console.print(f"  End Condition: {end_condition or '(not set)'}")
    console.print()
    
    # Text blocks
    text_blocks = segment.text_blocks if hasattr(segment, 'text_blocks') else []
    console.print("[bold magenta]TEXT BLOCKS[/bold magenta]")
    for i, block in enumerate(text_blocks):
        block_type = block.type if hasattr(block, 'type') else "unknown"
        block_content = block.content if hasattr(block, 'content') else str(block)
        block_char = block.character if hasattr(block, 'character') else None
        
        console.print(f"\n  [{i}] {block_type}")
        if block_char:
            console.print(f"      Character: {block_char}")
        console.print(f"      Content: {block_content[:100]}...")
    console.print()
    
    # Character states
    char_states = segment.character_states if hasattr(segment, 'character_states') else {}
    if char_states:
        console.print("[bold blue]CHARACTER STATES[/bold blue]")
        table = Table(show_header=True)
        table.add_column("Character")
        table.add_column("Status")
        table.add_column("Mood")
        table.add_column("Location")
        
        for char_id, state in char_states.items():
            if isinstance(state, dict):
                table.add_row(
                    state.get("name", "?"),
                    state.get("status", "?"),
                    state.get("mood", "?"),
                    state.get("location", "?"),
                )
            else:
                table.add_row(char_id, str(state), "?", "?")
        
        console.print(table)
        console.print()
    
    # Change notes
    change_notes = segment.change_notes if hasattr(segment, 'change_notes') else []
    if change_notes:
        console.print("[bold cyan]CHANGE NOTES[/bold cyan]")
        for note in change_notes:
            console.print(f"  • {note}")
        console.print()


def display_next_context_debug(runner, segment) -> None:
    """
    Show what context will be used for next generation.
    
    Useful for debugging generation logic and understanding
    how the next segment will be created.
    """
    
    console.print("[bold yellow]NEXT GENERATION CONTEXT[/bold yellow]")
    
    try:
        # Try to build context if available
        from app.engine.segment_context_builder import SegmentContextBuilder
        
        builder = SegmentContextBuilder(runner.story)
        context = builder.build_context(
            segment.id,
            "(hypothetical choice)"
        )
        
        # Show condensed view
        episode = context.get('episode_number', '?')
        tone = context.get('episode_tone', '(not set)')
        pacing = context.get('pacing_weight', 0)
        should_transition = context.get('should_transition_episode', False)
        changes = len(context.get('accumulated_changes', []))
        
        console.print(f"  Episode: {episode}")
        console.print(f"  Tone: {tone}")
        console.print(f"  Pacing: {pacing:.1%}" if isinstance(pacing, (int, float)) else f"  Pacing: {pacing}")
        console.print(f"  Should Transition: {should_transition}")
        console.print(f"  Accumulated Changes: {changes} items")
        
        console.print("\n  [dim]Full context (for copy-paste debugging):[/dim]")
        syntax = Syntax(
            json.dumps(context, indent=2, default=str),
            "json",
            theme="monokai"
        )
        console.print(syntax)
    
    except Exception as e:
        console.print(f"  [dim]Context builder not available: {e}[/dim]")
    
    console.print()


def prompt_choice_debug(segment, choices: List) -> str:
    """
    Get user choice in debug mode.
    
    Shows all choices with IDs and destination segments.
    
    Args:
        segment: Current story segment
        choices: List of available choices
    
    Returns:
        Choice ID selected by player
    """
    console.print("[bold]Available Choices:[/bold]\n")
    
    choice_list = list(choices) if not isinstance(choices, list) else choices
    
    for i, choice in enumerate(choice_list, 1):
        choice_id = choice.id if hasattr(choice, 'id') else str(choice)
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        to_segment = choice.to_segment_id if hasattr(choice, 'to_segment_id') else None
        
        dest = " → (generated)" if to_segment is None else f" → {to_segment}"
        console.print(f"  {i}. [{choice_id}] {choice_text}{dest}")
    
    console.print(f"\n  [dim]Enter choice number or ID (or 's' to save, 'q' to quit)[/dim]")
    
    selection = Prompt.ask("Choice").strip().lower()
    
    if selection == "s":
        console.print("[green]Progress saved![/green]")
        console.print("[yellow]Thanks for playing![/yellow]")
        raise typer.Exit(0)
    
    elif selection == "q":
        console.print("[yellow]Thanks for playing![/yellow]")
        raise typer.Exit(0)
    
    elif selection.isdigit():
        idx = int(selection) - 1
        try:
            return choice_list[idx].id if hasattr(choice_list[idx], 'id') else str(choice_list[idx])
        except IndexError:
            console.print("[red]Invalid choice[/red]")
            return prompt_choice_debug(segment, choices)
    else:
        # Treat as ID
        for choice in choice_list:
            choice_id = choice.id if hasattr(choice, 'id') else None
            if choice_id == selection:
                return choice_id
        
        console.print("[red]Choice not found[/red]")
        return prompt_choice_debug(segment, choices)
