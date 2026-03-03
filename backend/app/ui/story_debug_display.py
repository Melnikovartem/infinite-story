"""Story Debug mode - comprehensive generation context display."""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import json

console = Console()


def display_segment_story_debug(segment) -> None:
    """
    Display segment with full metadata and context.
    
    Shows:
    - Segment ID, status, description
    - Episode and arc information
    - Character states
    - Pacing weight and position
    - Text blocks
    """
    console.clear()
    
    # Header with segment info
    console.print(f"\n[bold cyan]╔═══ Segment: {segment.id} ═══╗[/bold cyan]")
    console.print(f"[cyan]Status:[/cyan] {getattr(segment, 'status', 'unknown')}")
    console.print(f"[cyan]Description:[/cyan] {segment.short_description if hasattr(segment, 'short_description') else 'N/A'}")
    
    # Episode and Arc info
    if hasattr(segment, 'episode_number'):
        console.print(f"[cyan]Episode #:[/cyan] {segment.episode_number}")
    if hasattr(segment, 'segment_number_in_episode'):
        console.print(f"[cyan]Segment in Episode:[/cyan] {segment.segment_number_in_episode}/20")
    if hasattr(segment, 'arc_id'):
        console.print(f"[cyan]Arc:[/cyan] {segment.arc_id}")
    if hasattr(segment, 'parent_segment_id'):
        console.print(f"[cyan]Parent:[/cyan] {segment.parent_segment_id}")
    if hasattr(segment, 'pacing_weight'):
        console.print(f"[cyan]Pacing Weight:[/cyan] {segment.pacing_weight:.2f}")
    if hasattr(segment, 'end_condition_proximity'):
        console.print(f"[cyan]End Condition Proximity:[/cyan] {segment.end_condition_proximity:.2f}")
    
    console.print()


def display_generation_context_story_debug(runner, segment, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Display comprehensive generation context before generating new content.
    
    Shows the exact data that will be sent to the AI:
    - All characters (short summaries + extended for active ones)
    - Episode data (current + recent)
    - Arc data (current + premises/conflicts)
    - Segment history (recaps + full text)
    - Change notes accumulated this episode
    - Pacing and navigation signals
    - Themes and hooks
    - What's included/excluded
    """
    console.print("[bold yellow]╔═══ Generation Context (Sent to AI) ═══╗[/bold yellow]\n")
    
    # If context dict is provided, use it; otherwise build basic info
    if context:
        _display_context_from_dict(context)
    else:
        _display_context_from_segment(runner, segment)


def _display_context_from_dict(context: Dict[str, Any]) -> None:
    """Display context using the actual context dictionary from SegmentContextBuilder."""
    
    # ========================================================================
    # NAVIGATION SIGNALS (Brief Overview)
    # ========================================================================
    console.print("[bold magenta]═══ NAVIGATION SIGNALS ═══[/bold magenta]")
    nav_table = Table(show_header=False)
    nav_table.add_row("[cyan]Episode #:[/cyan]", f"[yellow]{context.get('episode_number', 'N/A')}[/yellow]")
    nav_table.add_row("[cyan]Segment in Episode:[/cyan]", f"[yellow]{context.get('segment_number_in_episode', 'N/A')}/20[/yellow]")
    nav_table.add_row("[cyan]Pacing Weight:[/cyan]", f"[yellow]{context.get('pacing_weight', 0):.2f}[/yellow]")
    nav_table.add_row("[cyan]Should Transition:[/cyan]", f"[yellow]{'YES' if context.get('should_transition_episode') else 'NO'}[/yellow]")
    nav_table.add_row("[cyan]User Chose:[/cyan]", f"[green]\"{context.get('user_choice', '')}\"[/green]")
    console.print(nav_table)
    console.print()
    
    # ========================================================================
    # ARC CONTEXT - Complete Arc Information
    # ========================================================================
    _display_arc_context(context)
    
    # ========================================================================
    # EPISODE CONTEXT - Complete Episode Information
    # ========================================================================
    _display_episode_context(context)
    
    # ========================================================================
    # SEGMENT CONTEXT - Complete Segment Information
    # ========================================================================
    _display_segment_context(context)
    
    # ========================================================================
    # CHARACTER CONTEXT - All character info
    # ========================================================================
    _display_character_context(context)
    
    # ========================================================================
    # GENERATION STRATEGY
    # ========================================================================
    _display_generation_strategy(context)


def _display_arc_context(context: Dict[str, Any]) -> None:
    """Display complete arc information with all available fields."""
    console.print("[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  ARC CONTEXT                           ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")
    
    # Arc definitions
    arc_premise = context.get('arc_premise', 'N/A')
    arc_conflict = context.get('central_conflict', 'N/A')
    arc_tone = context.get('arc_tone', 'N/A')
    arc_themes = context.get('arc_themes', [])
    
    arc_table = Table(show_header=False, padding=(0, 1))
    arc_table.add_row("[cyan]Premise:[/cyan]", f"[white]{arc_premise}[/white]")
    arc_table.add_row("[cyan]Central Conflict:[/cyan]", f"[white]{arc_conflict}[/white]")
    arc_table.add_row("[cyan]Tone:[/cyan]", f"[white]{arc_tone}[/white]")
    if arc_themes:
        arc_table.add_row("[cyan]Themes:[/cyan]", f"[white]{', '.join(arc_themes)}[/white]")
    console.print(arc_table)
    
    # Character arc goals and resolutions
    char_goals = context.get('character_arc_goals', {})
    if char_goals:
        console.print("\n[cyan]Character Arc Goals:[/cyan]")
        for char_id, goal in char_goals.items():
            console.print(f"  • [green]{char_id}[/green]: {goal}")
    
    # Mysteries tracking
    mysteries = context.get('unresolved_mysteries', [])
    if mysteries:
        console.print("\n[cyan]Unresolved Mysteries:[/cyan]")
        for mystery in mysteries:
            console.print(f"  ? [yellow]{mystery}[/yellow]")
    
    # Theme depth
    theme_depth = context.get('theme_depth', {})
    if theme_depth:
        console.print("\n[cyan]Theme Exploration Depth:[/cyan]")
        for theme, depth in theme_depth.items():
            console.print(f"  • [magenta]{theme}[/magenta]: {depth}")
    
    console.print()


def _display_episode_context(context: Dict[str, Any]) -> None:
    """Display complete episode information with all available fields."""
    console.print("[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  EPISODE CONTEXT                       ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")
    
    current_ep = context.get('current_episode', {})
    if current_ep:
        ep_table = Table(show_header=False, padding=(0, 1))
        ep_table.add_row("[cyan]Episode #:[/cyan]", f"[yellow]{current_ep.get('number', 'N/A')}[/yellow]")
        ep_table.add_row("[cyan]Title:[/cyan]", f"[yellow]{current_ep.get('title', 'N/A')}[/yellow]")
        ep_table.add_row("[cyan]Tone:[/cyan]", f"[white]{current_ep.get('tone', 'N/A')}[/white]")
        ep_table.add_row("[cyan]Focus:[/cyan]", f"[white]{context.get('episode_focus', 'N/A')}[/white]")
        ep_table.add_row("[cyan]End Condition:[/cyan]", f"[white]{current_ep.get('end_condition', 'N/A')}[/white]")
        console.print(ep_table)
    
    # Episode summary
    if current_ep and current_ep.get('summary'):
        console.print("\n[cyan]Episode Summary:[/cyan]")
        console.print(f"[white]{current_ep.get('summary', '')}[/white]")
    
    # Selected themes
    themes = context.get('episode_selected_themes', [])
    if themes:
        console.print(f"\n[cyan]Selected Themes:[/cyan] [white]{', '.join(themes)}[/white]")
    
    # Story hooks
    hooks = context.get('story_hooks', [])
    if hooks:
        console.print("\n[cyan]Story Hooks to Explore:[/cyan]")
        for hook in hooks:
            console.print(f"  • [yellow]{hook}[/yellow]")
    
    # Themes explored
    themes_explored = context.get('themes_explored', [])
    if themes_explored:
        console.print(f"\n[cyan]Themes Explored So Far:[/cyan] [white]{', '.join(themes_explored)}[/white]")
    
    # Recent episode recaps
    recent_eps = context.get('recent_episode_recaps', [])
    if recent_eps:
        console.print("\n[cyan]Recent Episode Recaps:[/cyan]")
        for ep_recap in recent_eps:
            ep_num = ep_recap.get('episode_number', ep_recap.get('number', '?'))
            ep_title = ep_recap.get('title', 'N/A')
            console.print(f"  • Episode {ep_num}: [bold]{ep_title}[/bold]")
            if ep_recap.get('summary'):
                console.print(f"      [dim]{ep_recap.get('summary', '')[:150]}...[/dim]")
    
    console.print()


def _display_segment_context(context: Dict[str, Any]) -> None:
    """Display complete segment information with text and all fields."""
    console.print("[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  SEGMENT CONTEXT                       ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")
    
    # Recent full segment texts with complete context
    full_segments = context.get('recent_segments_full', [])
    if full_segments:
        console.print(f"[cyan]Full Text of Last {len(full_segments)} Segments:[/cyan]\n")
        
        for i, seg in enumerate(full_segments[-3:], 1):  # Show last 3
            seg_id = seg.get('segment_id', 'unknown')
            seg_text = seg.get('text', '')
            seg_recap = seg.get('recap', {})
            
            console.print(f"[bold cyan]-- Segment {i}: {seg_id} --[/bold cyan]")
            
            # Segment metadata
            if seg_recap:
                meta_table = Table(show_header=False, padding=(0, 1))
                if seg_recap.get('episode_number'):
                    meta_table.add_row("[dim]Episode:[/dim]", f"{seg_recap.get('episode_number')}")
                if seg_recap.get('segment_number_in_episode'):
                    meta_table.add_row("[dim]Segment #:[/dim]", f"{seg_recap.get('segment_number_in_episode')}")
                if seg_recap.get('short_description'):
                    meta_table.add_row("[dim]Description:[/dim]", f"{seg_recap.get('short_description')}")
                console.print(meta_table)
            
            # Full text
            if seg_text:
                console.print(f"\n[white]{seg_text}[/white]\n")
            
            # Key events
            if seg_recap and seg_recap.get('key_events'):
                console.print("[dim]Key Events:[/dim]")
                for event in seg_recap.get('key_events', []):
                    console.print(f"  • {event}")
            
            # Characters present
            if seg_recap and seg_recap.get('characters_present'):
                console.print(f"[dim]Characters:[/dim] {', '.join(seg_recap.get('characters_present', []))}")
            
            console.print()
    
    # Segment recaps
    recaps = context.get('segment_recaps', [])
    if recaps:
        console.print(f"[cyan]Recent Segment Recaps (Last 10):[/cyan]")
        for recap in recaps:
            seg_id = recap.get('segment_id', 'unknown')
            seg_desc = recap.get('short_description', recap.get('description', 'N/A'))
            console.print(f"  • [yellow]{seg_id}[/yellow]: {seg_desc[:80]}")
    
    console.print()


def _display_character_context(context: Dict[str, Any]) -> None:
    """Display comprehensive character information and state changes."""
    console.print("[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  CHARACTER CONTEXT                     ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")
    
    # All characters summary
    all_chars = context.get('all_characters', {})
    if all_chars:
        console.print("[cyan]All Characters (Summary):[/cyan]")
        char_table = Table(show_header=True, header_style="dim cyan")
        char_table.add_column("ID", style="cyan", width=15)
        char_table.add_column("Name", style="white", width=20)
        char_table.add_column("Status", style="yellow", width=15)
        
        for char_id, char_info in all_chars.items():
            name = char_info.get('name', char_id)
            status = char_info.get('status', 'unknown')
            char_table.add_row(char_id, name, status)
        
        console.print(char_table)
    
    # Extended character info for active ones
    extended_chars = context.get('extended_characters', {})
    if extended_chars:
        console.print("\n[cyan]Extended Character Details (Last 3 Segments):[/cyan]")
        for char_id, char_info in extended_chars.items():
            console.print(f"\n  [bold green]{char_info.get('name', char_id)}[/bold green]")
            console.print(f"    [dim]Background:[/dim] {char_info.get('background', 'N/A')}")
            console.print(f"    [dim]Goal:[/dim] {char_info.get('current_goal', 'N/A')}")
            console.print(f"    [dim]Emotion:[/dim] {char_info.get('emotional_state', 'N/A')}")
            console.print(f"    [dim]Status:[/dim] {char_info.get('status', 'N/A')}")
            console.print(f"    [dim]Loyalty:[/dim] {char_info.get('loyalty', 'N/A')}")
    
    # Character relationships
    relationships = context.get('character_relationships', {})
    if relationships:
        console.print("\n[cyan]Character Relationships:[/cyan]")
        for char_id, rels in relationships.items():
            if rels:
                console.print(f"  [green]{char_id}[/green]:")
                for other_char, rel_desc in rels.items():
                    console.print(f"    → [yellow]{other_char}[/yellow]: {rel_desc}")
    
    # Changes this episode
    changes = context.get('character_changes_this_episode', [])
    if changes:
        console.print("\n[cyan]Character Changes This Episode:[/cyan]")
        for i, change in enumerate(changes, 1):
            console.print(f"  {i}. {change}")
    
    console.print()


def _display_generation_strategy(context: Dict[str, Any]) -> None:
    """Display what will be included/excluded in the generation."""
    console.print("[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║  GENERATION STRATEGY                   ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")
    
    all_chars = context.get('all_characters', {})
    extended_chars = context.get('extended_characters', {})
    recaps = context.get('segment_recaps', [])
    full_segments = context.get('recent_segments_full', [])
    changes = context.get('character_changes_this_episode', [])
    hooks = context.get('story_hooks', [])
    mysteries = context.get('unresolved_mysteries', [])
    
    console.print("[green]✓ Will Include in Context:[/green]")
    console.print(f"  • {len(all_chars) if all_chars else 0} character summaries")
    console.print(f"  • {len(extended_chars) if extended_chars else 0} extended character details")
    console.print(f"  • Current episode (#{context.get('episode_number', '?')})")
    console.print(f"  • {len(recaps) if recaps else 0} recent segment recaps")
    console.print(f"  • {len(full_segments) if full_segments else 0} full segment texts (for continuity)")
    console.print(f"  • {len(changes) if changes else 0} character changes this episode")
    console.print(f"  • Arc premise, conflict, themes, goals, and mysteries")
    console.print(f"  • {len(hooks) if hooks else 0} story hooks to explore")
    console.print(f"  • Episode focus, tone, and selected themes")
    
    console.print("\n[yellow]⊘ Will Not Include (to save tokens):[/yellow]")
    console.print("  • Inactive character details")
    console.print("  • Episodes older than recent")
    console.print("  • Segments older than recent")
    console.print("  • Resolved arcs (archived)")
    console.print("  • Complete location/world details (summaries only)")
    
    console.print()


def _display_context_from_segment(runner, segment) -> None:
    """Fallback display using only segment information when context dict not available."""
    
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
        
        for char_id, char in list(story.characters.items())[:10]:
            name = char.name if hasattr(char, 'name') else char_id
            status = "Active" if char_id in getattr(segment, 'active_characters', []) else "Inactive"
            char_table.add_row(name, status)
        
        console.print(char_table)
        console.print()
    
    # Pacing info
    console.print("[bold cyan]Pacing:[/bold cyan]")
    pacing_table = Table(show_header=False)
    pacing_table.add_row("[cyan]Episode:[/cyan]", f"{getattr(segment, 'episode_number', 'N/A')}")
    pacing_table.add_row("[cyan]Segment in Episode:[/cyan]", f"{getattr(segment, 'segment_number_in_episode', 'N/A')}/20")
    pacing_table.add_row("[cyan]Pacing Weight:[/cyan]", f"{getattr(segment, 'pacing_weight', 0):.2f}")
    console.print(pacing_table)
    console.print()
    
    # Generation strategy
    console.print("[bold cyan]Generation Strategy:[/bold cyan]")
    console.print("[green]✓ Will Include:[/green]")
    console.print("  • Current segment prose and atmosphere")
    console.print("  • Active character states and relationships")
    console.print("  • Current arc direction and goals")
    console.print("  • Recent segment history (last 10)")
    console.print("  • Full text of last 3 segments (for continuity)")
    console.print("  • Changes accumulated this episode")
    console.print("  • Pacing signals and episode metadata")
    
    console.print("\n[yellow]⊘ Will Exclude:[/yellow]")
    console.print("  • Resolved arcs (to stay focused)")
    console.print("  • Archived episodes (to save tokens)")
    console.print("  • Inactive characters (unless relevant)")
    console.print()


def display_generation_result_story_debug(segment, context: Optional[Dict[str, Any]] = None) -> None:
    """Display result of generation with what was actually created."""
    console.print("[bold green]╔═══ Generation Complete ═══╗[/bold green]\n")
    
    console.print(f"[cyan]New Segment:[/cyan] {segment.id}")
    console.print(f"[cyan]Episode:[/cyan] {getattr(segment, 'episode_number', 'N/A')}")
    console.print(f"[cyan]Segment #:[/cyan] {getattr(segment, 'segment_number_in_episode', 'N/A')}")
    console.print(f"[cyan]Arc:[/cyan] {getattr(segment, 'arc_id', 'N/A')}")
    console.print(f"[cyan]Parent:[/cyan] {getattr(segment, 'parent_segment_id', 'N/A')}")
    console.print(f"[cyan]Blocks Generated:[/cyan] {len(getattr(segment, 'text_blocks', []))}")
    
    # Show change notes if available
    if hasattr(segment, 'change_notes') and segment.change_notes:
        console.print("\n[cyan]Change Notes (for next context):[/cyan]")
        for note in segment.change_notes[:5]:
            console.print(f"  • {note}")
        if len(segment.change_notes) > 5:
            console.print(f"  ... and {len(segment.change_notes) - 5} more")
    
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
