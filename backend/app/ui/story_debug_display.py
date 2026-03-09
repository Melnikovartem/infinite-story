"""Story Debug mode - the ultimate generation debugging view.

Shows everything the system tracks and sends to the AI:
- Navigation signals & pacing
- Arc context (premise, conflict, themes, mysteries)
- Episode context (tone, focus, hooks, recaps)
- Segment context (full text, recaps, key events)
- Character context (hierarchical: arc > episode > segment changes)
- Faction & magic system context
- Location & world state
- Story momentum metrics (momentum, tension, pacing trend)
- Running changes (EntityChange per segment)
- The actual formatted AI prompt
- Generation strategy (what's included/excluded)
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.columns import Columns
from rich.text import Text
import json

console = Console()


# ============================================================================
# SECTION HEADER HELPER
# ============================================================================

def _section(title: str, style: str = "bold cyan") -> None:
    """Print a consistent section header."""
    width = max(len(title) + 4, 44)
    bar = "═" * width
    console.print(f"[{style}]╔{bar}╗[/{style}]")
    console.print(f"[{style}]║  {title:<{width - 2}}║[/{style}]")
    console.print(f"[{style}]╚{bar}╝[/{style}]\n")


def _pacing_bar(value: float, width: int = 20) -> str:
    """Create a visual pacing bar like [████████░░░░░░░░░░░░] 40%."""
    filled = int(value * width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {value:.0%}"


# ============================================================================
# MAIN DISPLAY FUNCTIONS
# ============================================================================

def display_segment_story_debug(segment) -> None:
    """Display segment with full metadata, running changes, and text blocks."""
    console.clear()

    # Header panel with key segment info
    info_lines = []
    info_lines.append(f"[cyan]ID:[/cyan] [bold]{segment.id}[/bold]")
    info_lines.append(f"[cyan]Status:[/cyan] {getattr(segment, 'status', 'unknown')}")
    info_lines.append(f"[cyan]Description:[/cyan] {getattr(segment, 'short_description', 'N/A')}")

    if hasattr(segment, 'arc_id') and segment.arc_id:
        info_lines.append(f"[cyan]Arc:[/cyan] {segment.arc_id}")
    if hasattr(segment, 'parent_segment_id') and segment.parent_segment_id:
        info_lines.append(f"[cyan]Parent:[/cyan] {segment.parent_segment_id}")

    ep_num = getattr(segment, 'episode_number', '?')
    seg_in_ep = getattr(segment, 'segment_number_in_episode', '?')
    pacing = getattr(segment, 'pacing_weight', 0)
    end_prox = getattr(segment, 'end_condition_proximity', 0)

    info_lines.append(f"[cyan]Episode:[/cyan] {ep_num}  [cyan]Segment:[/cyan] {seg_in_ep}/20")
    info_lines.append(f"[cyan]Pacing:[/cyan] {_pacing_bar(pacing)}")
    info_lines.append(f"[cyan]End Proximity:[/cyan] {_pacing_bar(end_prox)}")

    if getattr(segment, 'protagonist_id', None):
        info_lines.append(f"[cyan]Protagonist:[/cyan] {segment.protagonist_id}")
    if getattr(segment, 'triggers_episode_transition', False):
        info_lines.append("[bold red]>>> TRIGGERS EPISODE TRANSITION <<<[/bold red]")
    
    # Storyline type
    storyline = getattr(segment, 'storyline_type', None)
    if storyline:
        _SL_ICONS = {"action": "!!!", "mystery": "???", "romance": "<3", "political": ">>>",
                      "horror": "!!!", "comedy": ":)", "drama": "...", "exploration": "->"}
        sl_icon = _SL_ICONS.get(storyline, "")
        info_lines.append(f"[cyan]Storyline:[/cyan] [bold]{sl_icon} {storyline.upper()}[/bold]")

    console.print(Panel(
        "\n".join(info_lines),
        title=f"Segment: {segment.id}",
        border_style="cyan"
    ))
    
    # Character Emotions snapshot
    char_emotions = getattr(segment, 'character_emotions', {})
    if char_emotions:
        console.print(f"\n[bold magenta]Character Emotions:[/bold magenta]")
        emo_table = Table(show_header=True, header_style="dim magenta")
        emo_table.add_column("Character", style="cyan", width=20)
        emo_table.add_column("Emotion", style="magenta", width=40)
        for char_name, emotion in char_emotions.items():
            emo_table.add_row(str(char_name), str(emotion))
        console.print(emo_table)

    # ── Running Changes (EntityChange) ──
    running_changes = getattr(segment, 'running_changes', [])
    if running_changes:
        console.print(f"\n[bold yellow]Running Changes ({len(running_changes)}):[/bold yellow]")
        change_table = Table(show_header=True, header_style="dim yellow")
        change_table.add_column("Entity", style="cyan", width=18)
        change_table.add_column("Type", style="dim", width=10)
        change_table.add_column("Property", style="white", width=12)
        change_table.add_column("From", style="red", width=15)
        change_table.add_column("To", style="green", width=15)
        change_table.add_column("Description", style="dim")

        for rc in running_changes:
            change_table.add_row(
                getattr(rc, 'entity_name', getattr(rc, 'entity_id', '?')),
                getattr(rc, 'entity_type', '?'),
                getattr(rc, 'property', '?'),
                str(getattr(rc, 'from_value', '') or '—'),
                str(getattr(rc, 'to_value', '') or '—'),
                str(getattr(rc, 'description', ''))[:50],
            )
        console.print(change_table)

    # ── Change Notes ──
    change_notes = getattr(segment, 'change_notes', [])
    if change_notes:
        console.print(f"\n[bold yellow]Change Notes ({len(change_notes)}):[/bold yellow]")
        for note in change_notes[:8]:
            console.print(f"  • {note}")
        if len(change_notes) > 8:
            console.print(f"  [dim]... and {len(change_notes) - 8} more[/dim]")

    # ── Characters & Locations Present ──
    chars_present = getattr(segment, 'characters_present', [])
    locs_present = getattr(segment, 'locations_present', [])
    if chars_present or locs_present:
        console.print()
        if chars_present:
            console.print(f"[cyan]Characters Present:[/cyan] {', '.join(chars_present)}")
        if locs_present:
            console.print(f"[cyan]Locations Present:[/cyan] {', '.join(locs_present)}")

    # ── Atmosphere & Environment ──
    atmosphere = getattr(segment, 'atmosphere', None)
    time_of_day = getattr(segment, 'time_of_day', None)
    weather = getattr(segment, 'weather', None)
    key_items = getattr(segment, 'key_items', [])
    if any([atmosphere, time_of_day, weather, key_items]):
        console.print()
        if atmosphere:
            console.print(f"[cyan]Atmosphere:[/cyan] {atmosphere}")
        if time_of_day:
            console.print(f"[cyan]Time:[/cyan] {time_of_day}")
        if weather:
            console.print(f"[cyan]Weather:[/cyan] {weather}")
        if key_items:
            console.print(f"[cyan]Key Items:[/cyan] {', '.join(key_items)}")

    # ── Text Blocks ──
    text_blocks = getattr(segment, 'text_blocks', [])
    if text_blocks:
        console.print(f"\n[bold cyan]Text Blocks ({len(text_blocks)}):[/bold cyan]")
        console.print("[dim]" + "─" * 70 + "[/dim]")
        for block in text_blocks:
            content = block.content if hasattr(block, 'content') else str(block)
            block_type = block.type if hasattr(block, 'type') else 'narrative'
            block_emotion = getattr(block, 'emotion', None)
            block_storyline = getattr(block, 'storyline', None)
            
            # Build tag line: [type] (emotion) {storyline}
            tags = f"[dim][{block_type}][/dim]"
            if block_emotion:
                tags += f" [magenta]({block_emotion})[/magenta]"
            if block_storyline:
                tags += f" [yellow]{{{block_storyline}}}[/yellow]"
            if hasattr(block, 'character') and block.character:
                tags += f" [cyan]@{block.character}[/cyan]"
            
            console.print(f"{tags} {content}")
        console.print("[dim]" + "─" * 70 + "[/dim]")

    console.print()


def display_generation_context_story_debug(
    runner, segment, context: Optional[Dict[str, Any]] = None
) -> None:
    """Display the ultimate generation context debugging view.

    Shows ALL data the system has collected for the next generation call:
    navigation, arcs, episodes, segments, characters, factions, magic,
    locations, world state, momentum metrics, running changes,
    the actual formatted AI prompt, and a generation strategy summary.
    """
    console.print(Panel(
        "[bold yellow]Generation Context (Sent to AI)[/bold yellow]",
        border_style="yellow"
    ))

    if context:
        _display_context_from_dict(context)
    else:
        _display_context_from_segment(runner, segment)


# ============================================================================
# CONTEXT FROM DICT (primary path — uses SegmentContextBuilder output)
# ============================================================================

def _display_context_from_dict(context: Dict[str, Any]) -> None:
    """Display context using the actual context dictionary from SegmentContextBuilder."""

    # 1. Navigation Signals
    _display_navigation_signals(context)

    # 2. Story Momentum Metrics
    _display_momentum_metrics(context)

    # 3. Arc Context
    _display_arc_context(context)

    # 4. Episode Context
    _display_episode_context(context)

    # 5. Segment Context
    _display_segment_context(context)

    # 6. Character Context (hierarchical)
    _display_character_context(context)

    # 7. Faction Context
    _display_faction_context(context)

    # 8. Magic / Tech System
    _display_magic_system_context(context)

    # 9. Location & World State
    _display_location_world_context(context)

    # 10. Mysteries & Theme Tracking
    _display_mysteries_themes(context)

    # 11. Storyline Type Tracking (NEW)
    _display_storyline_context(context)

    # 12. Character Emotions (NEW)
    _display_character_emotions(context)

    # 13. Generation Strategy
    _display_generation_strategy(context)

    # 14. Actual Formatted AI Prompt
    _display_actual_ai_prompt(context)


# ============================================================================
# 1. NAVIGATION SIGNALS
# ============================================================================

def _display_navigation_signals(context: Dict[str, Any]) -> None:
    _section("NAVIGATION SIGNALS", "bold magenta")

    ep_num = context.get('episode_number', 'N/A')
    seg_num = context.get('segment_number_in_episode', 'N/A')
    pacing = context.get('pacing_weight', 0)
    should_transition = context.get('should_transition_episode', False)
    user_choice = context.get('user_choice', '')

    nav_table = Table(show_header=False, box=None, padding=(0, 2))
    nav_table.add_column("Key", style="cyan", width=22)
    nav_table.add_column("Value")

    nav_table.add_row("Episode #", f"[yellow]{ep_num}[/yellow]")
    nav_table.add_row("Segment in Episode", f"[yellow]{seg_num}/20[/yellow]")
    nav_table.add_row("Pacing", _pacing_bar(pacing))

    transition_style = "[bold red]YES — TRANSITION NOW[/bold red]" if should_transition else "[green]No[/green]"
    nav_table.add_row("Should Transition?", transition_style)

    if context.get('episode_tone'):
        nav_table.add_row("Episode Tone", f"[white]{context['episode_tone']}[/white]")
    if context.get('episode_end_condition'):
        nav_table.add_row("End Condition", f"[white]{context['episode_end_condition']}[/white]")
    if context.get('protagonist_id'):
        nav_table.add_row("Protagonist", f"[green]{context['protagonist_id']}[/green]")

    nav_table.add_row("User Choice", f"[bold green]\"{user_choice}\"[/bold green]")

    console.print(nav_table)
    console.print()


# ============================================================================
# 2. STORY MOMENTUM METRICS
# ============================================================================

def _display_momentum_metrics(context: Dict[str, Any]) -> None:
    momentum = context.get('story_momentum')
    tension = context.get('tension_level')
    pacing_trend = context.get('pacing_trend')

    # Only show section if any metric exists
    if momentum is None and tension is None and pacing_trend is None:
        return

    _section("STORY MOMENTUM METRICS", "bold red")

    metrics_table = Table(show_header=True, header_style="dim red")
    metrics_table.add_column("Metric", style="cyan", width=18)
    metrics_table.add_column("Value", style="yellow", width=10)
    metrics_table.add_column("Visual", width=24)
    metrics_table.add_column("Interpretation", style="dim")

    if momentum is not None:
        if isinstance(momentum, (int, float)):
            m_val = float(momentum)
            interp = "Stagnant" if m_val < 0.3 else "Steady" if m_val < 0.6 else "High momentum" if m_val < 0.85 else "Peak action"
            metrics_table.add_row("Momentum", f"{m_val:.2f}", _pacing_bar(m_val), interp)
        else:
            metrics_table.add_row("Momentum", str(momentum)[:10], "", "")

    if tension is not None:
        if isinstance(tension, (int, float)):
            t_val = float(tension)
            interp = "Calm" if t_val < 0.3 else "Building" if t_val < 0.6 else "High tension" if t_val < 0.85 else "Critical"
            metrics_table.add_row("Tension", f"{t_val:.2f}", _pacing_bar(t_val), interp)
        else:
            metrics_table.add_row("Tension", str(tension)[:10], "", "")

    if pacing_trend is not None:
        if isinstance(pacing_trend, (int, float)):
            p_val = float(pacing_trend)
            interp = "Slowing down" if p_val < -0.1 else "Steady pace" if p_val < 0.1 else "Accelerating"
            sign = "+" if p_val >= 0 else ""
            metrics_table.add_row("Pacing Trend", f"{sign}{p_val:.2f}", "", interp)
        else:
            metrics_table.add_row("Pacing Trend", str(pacing_trend)[:10], "", "")

    console.print(metrics_table)
    console.print()


# ============================================================================
# 3. ARC CONTEXT
# ============================================================================

def _display_arc_context(context: Dict[str, Any]) -> None:
    _section("ARC CONTEXT")

    # Current arc info
    current_arc = context.get('current_arc', {})
    arc_premise = current_arc.get('premise', context.get('arc_premise', 'N/A'))
    arc_conflict = current_arc.get('central_conflict', context.get('central_conflict', 'N/A'))
    arc_tone = current_arc.get('arc_tone', context.get('arc_tone', 'N/A'))
    arc_themes = current_arc.get('themes', context.get('arc_themes', []))
    arc_title = current_arc.get('title', 'Current Arc')
    arc_direction = current_arc.get('narrative_direction', '')

    arc_table = Table(show_header=False, box=None, padding=(0, 2))
    arc_table.add_column("Key", style="cyan", width=22)
    arc_table.add_column("Value")

    if arc_title and arc_title != 'Current Arc':
        arc_table.add_row("Title", f"[bold]{arc_title}[/bold]")
    arc_table.add_row("Premise", f"[white]{arc_premise}[/white]")
    arc_table.add_row("Central Conflict", f"[white]{arc_conflict}[/white]")
    arc_table.add_row("Tone", f"[white]{arc_tone}[/white]")
    if arc_themes:
        arc_table.add_row("Themes", f"[magenta]{', '.join(arc_themes)}[/magenta]")
    if arc_direction:
        arc_table.add_row("Direction", f"[white]{arc_direction[:100]}[/white]")
    console.print(arc_table)

    # Character arc goals
    char_goals = current_arc.get('character_arc_goals', context.get('character_arc_goals', {}))
    if char_goals:
        console.print("\n[cyan]Character Arc Goals:[/cyan]")
        for char_id, goal in char_goals.items():
            console.print(f"  • [green]{char_id}[/green]: {goal}")

    # Plot hooks
    plot_hooks = current_arc.get('plot_hooks', [])
    if plot_hooks:
        console.print("\n[cyan]Active Plot Hooks:[/cyan]")
        for hook in plot_hooks[:5]:
            console.print(f"  • [yellow]{hook}[/yellow]")

    # Unresolved mysteries
    mysteries = current_arc.get('unresolved_mysteries', context.get('unresolved_mysteries', []))
    if mysteries:
        console.print("\n[cyan]Unresolved Mysteries:[/cyan]")
        for mystery in mysteries:
            console.print(f"  ? [yellow]{mystery}[/yellow]")

    # Previous arcs
    prev_arcs = context.get('previous_arcs', [])
    if prev_arcs:
        console.print(f"\n[cyan]Previous Arcs ({len(prev_arcs)}):[/cyan]")
        for arc in prev_arcs[:3]:
            name = arc.get('name', arc.get('title', arc.get('arc_id', '?')))
            recap = arc.get('recap', arc.get('resolution', ''))
            console.print(f"  • [dim]{name}[/dim]: {str(recap)[:80]}")

    # Recent arc recaps
    arc_recaps = context.get('recent_arc_recaps', [])
    if arc_recaps:
        console.print(f"\n[cyan]Recent Arc Recaps ({len(arc_recaps)}):[/cyan]")
        for recap in arc_recaps[:5]:
            if isinstance(recap, dict):
                arc_id = recap.get('arc_id', '?')
                summary = recap.get('summary', recap.get('recap', ''))
                console.print(f"  • [dim]{arc_id}[/dim]: {str(summary)[:80]}")
            else:
                console.print(f"  • {str(recap)[:80]}")

    console.print()


# ============================================================================
# 4. EPISODE CONTEXT
# ============================================================================

def _display_episode_context(context: Dict[str, Any]) -> None:
    _section("EPISODE CONTEXT")

    current_ep = context.get('current_episode', {})
    if current_ep:
        ep_table = Table(show_header=False, box=None, padding=(0, 2))
        ep_table.add_column("Key", style="cyan", width=22)
        ep_table.add_column("Value")

        ep_table.add_row("Episode #", f"[yellow]{current_ep.get('number', 'N/A')}[/yellow]")
        if current_ep.get('title'):
            ep_table.add_row("Title", f"[bold]{current_ep['title']}[/bold]")
        if current_ep.get('tone'):
            ep_table.add_row("Tone", f"[white]{current_ep['tone']}[/white]")
        if context.get('episode_focus'):
            ep_table.add_row("Focus", f"[white]{context['episode_focus']}[/white]")
        if current_ep.get('end_condition'):
            ep_table.add_row("End Condition", f"[white]{current_ep['end_condition']}[/white]")
        console.print(ep_table)

    # Episode summary
    if current_ep and current_ep.get('summary'):
        console.print(f"\n[cyan]Episode Summary:[/cyan]")
        console.print(f"[white]{current_ep['summary']}[/white]")

    # Selected themes
    themes = context.get('episode_selected_themes', [])
    if themes:
        console.print(f"\n[cyan]Selected Themes:[/cyan] [magenta]{', '.join(themes)}[/magenta]")

    # Story hooks
    hooks = context.get('story_hooks', [])
    if hooks:
        console.print("\n[cyan]Story Hooks to Explore:[/cyan]")
        for hook in hooks:
            console.print(f"  • [yellow]{hook}[/yellow]")

    # Themes explored
    themes_explored = context.get('themes_explored', [])
    if themes_explored:
        console.print(f"\n[cyan]Themes Explored So Far:[/cyan] [dim]{', '.join(themes_explored)}[/dim]")

    # Previous episode recap (bridging context)
    if context.get('previous_episode_recap'):
        prev_title = context.get('previous_episode_title', 'Last Episode')
        console.print(f"\n[cyan]Previous Episode ({prev_title}):[/cyan]")
        console.print(f"[dim]{context['previous_episode_recap'][:200]}...[/dim]")

    # Recent episode recaps
    recent_eps = context.get('recent_episode_recaps', [])
    if recent_eps:
        console.print(f"\n[cyan]Recent Episode Recaps ({len(recent_eps)}):[/cyan]")
        for ep_recap in recent_eps:
            ep_num = ep_recap.get('episode_number', ep_recap.get('episode', ep_recap.get('number', '?')))
            ep_title = ep_recap.get('title', 'N/A')
            console.print(f"  • Episode {ep_num}: [bold]{ep_title}[/bold]")
            if ep_recap.get('summary'):
                console.print(f"      [dim]{ep_recap['summary'][:150]}...[/dim]")

    # Episodes in arc
    eps_in_arc = context.get('episodes_in_arc', [])
    if eps_in_arc:
        console.print(f"\n[cyan]Episodes in Current Arc ({len(eps_in_arc)}):[/cyan]")
        for ep in eps_in_arc[:5]:
            if isinstance(ep, dict):
                console.print(f"  • Episode {ep.get('number', '?')}: {ep.get('title', ep.get('summary', ''))[:60]}")

    console.print()


# ============================================================================
# 5. SEGMENT CONTEXT
# ============================================================================

def _display_segment_context(context: Dict[str, Any]) -> None:
    _section("SEGMENT CONTEXT")

    # Recent full segment texts
    full_segments = context.get('recent_segments_full', [])
    if full_segments:
        console.print(f"[cyan]Full Text of Last {len(full_segments)} Segments:[/cyan]\n")

        for i, seg in enumerate(full_segments[-3:], 1):
            seg_id = seg.get('segment_id', 'unknown')
            seg_text = seg.get('text', '')
            seg_recap = seg.get('recap', {})

            console.print(f"[bold cyan]-- Segment {i}: {seg_id} --[/bold cyan]")

            # Segment metadata
            if seg_recap:
                meta_parts = []
                if seg_recap.get('episode_number'):
                    meta_parts.append(f"Ep:{seg_recap['episode_number']}")
                if seg_recap.get('segment_number_in_episode'):
                    meta_parts.append(f"Seg:{seg_recap['segment_number_in_episode']}")
                if seg_recap.get('short_description'):
                    meta_parts.append(seg_recap['short_description'][:50])
                if meta_parts:
                    console.print(f"  [dim]{' | '.join(meta_parts)}[/dim]")

            # Full text
            if seg_text:
                # Truncate long text
                display_text = seg_text[:500]
                if len(seg_text) > 500:
                    display_text += f"... [dim]({len(seg_text)} chars total)[/dim]"
                console.print(f"\n[white]{display_text}[/white]\n")

            # Key events
            if seg_recap and seg_recap.get('key_events'):
                console.print("[dim]Key Events:[/dim]")
                for event in seg_recap.get('key_events', []):
                    console.print(f"  • {event}")

            # Characters present
            if seg_recap and seg_recap.get('characters_present'):
                console.print(f"[dim]Characters:[/dim] {', '.join(seg_recap['characters_present'])}")

            console.print()

    # Segment recaps
    recaps = context.get('segment_recaps', [])
    if recaps:
        console.print(f"[cyan]Segment Recaps (Last {len(recaps)}):[/cyan]")
        for recap in recaps:
            seg_id = recap.get('segment_id', 'unknown')
            seg_desc = recap.get('short_description', recap.get('description', 'N/A'))
            console.print(f"  • [yellow]{seg_id}[/yellow]: {seg_desc[:80]}")

    console.print()


# ============================================================================
# 6. CHARACTER CONTEXT (hierarchical: arc > episode > segment)
# ============================================================================

def _display_character_context(context: Dict[str, Any]) -> None:
    _section("CHARACTER CONTEXT")

    # ── Arc-level characters (short summaries) ──
    arc_chars = context.get('arc_characters', {})
    if arc_chars:
        console.print(f"[cyan]Arc Characters ({len(arc_chars)}):[/cyan]")
        char_table = Table(show_header=True, header_style="dim cyan")
        char_table.add_column("ID", style="cyan", width=18)
        char_table.add_column("Name", style="white", width=18)
        char_table.add_column("Status", style="yellow", width=12)
        char_table.add_column("Description", style="dim", max_width=40)

        for char_id, char_info in arc_chars.items():
            if isinstance(char_info, dict):
                name = char_info.get('name', char_id)
                status = char_info.get('status', '—')
                desc = char_info.get('description', '')[:40]
            else:
                name, status, desc = str(char_info)[:18], '—', ''
            char_table.add_row(char_id[:18], name, status, desc)

        console.print(char_table)

    # ── Episode-level characters (updated states) ──
    ep_chars = context.get('episode_characters', {})
    if ep_chars:
        console.print(f"\n[cyan]Episode Character States ({len(ep_chars)}):[/cyan]")
        for char_id, info in ep_chars.items():
            if isinstance(info, dict):
                name = info.get('name', char_id)
                status = info.get('status', '')
                console.print(f"  • [green]{name}[/green] [{status}]" if status else f"  • [green]{name}[/green]")
                if info.get('description'):
                    console.print(f"      [dim]{info['description'][:80]}[/dim]")
            else:
                console.print(f"  • [green]{char_id}[/green]: {str(info)[:80]}")

    # ── Segment-level character changes ──
    seg_changes = context.get('segment_character_changes', {})
    if seg_changes:
        console.print(f"\n[cyan]Segment Character Changes:[/cyan]")
        for char_id, changes in seg_changes.items():
            console.print(f"  [green]{char_id}[/green]:")
            if isinstance(changes, list):
                for change in changes[:3]:
                    console.print(f"    • {change}")
            elif isinstance(changes, dict):
                for prop, val in list(changes.items())[:3]:
                    console.print(f"    • {prop}: {val}")

    # ── All characters (fallback/legacy) ──
    all_chars = context.get('all_characters', {})
    if all_chars and not arc_chars:
        console.print(f"[cyan]All Characters ({len(all_chars)}):[/cyan]")
        for char_id, char_info in all_chars.items():
            name = char_info.get('name', char_id) if isinstance(char_info, dict) else char_id
            status = char_info.get('status', '') if isinstance(char_info, dict) else ''
            console.print(f"  • {name}" + (f" ({status})" if status else ""))

    # ── Extended character info ──
    extended_chars = context.get('extended_characters', {})
    if extended_chars:
        console.print(f"\n[cyan]Extended Character Details (Last 3 Segments):[/cyan]")
        for char_id, char_info in extended_chars.items():
            console.print(f"\n  [bold green]{char_info.get('name', char_id)}[/bold green]")
            for field in ['background', 'current_goal', 'emotional_state', 'status', 'loyalty']:
                val = char_info.get(field)
                if val:
                    console.print(f"    [dim]{field}:[/dim] {val}")

    # ── Character Role Tiers ──
    role_tiers = context.get('character_role_tiers', {})
    if role_tiers:
        console.print(f"\n[cyan]Character Role Tiers:[/cyan]")
        for tier, chars in role_tiers.items():
            if chars:
                console.print(f"  [yellow]{tier}:[/yellow] {', '.join(chars[:5])}")

    # ── Relationships ──
    relationships = context.get('character_relationships', {})
    if relationships:
        console.print("\n[cyan]Character Relationships:[/cyan]")
        for char_id, rels in relationships.items():
            if rels and isinstance(rels, dict):
                console.print(f"  [green]{char_id}[/green]:")
                for other_char, rel_desc in list(rels.items())[:3]:
                    console.print(f"    → [yellow]{other_char}[/yellow]: {rel_desc}")

    # ── Relationship changes ──
    rel_changes = context.get('relationship_changes', [])
    if rel_changes:
        console.print("\n[cyan]Relationship Changes This Episode:[/cyan]")
        for change in rel_changes[:5]:
            console.print(f"  • {change}")

    # ── Accumulated changes this episode ──
    changes = context.get('character_changes_this_episode', [])
    if changes:
        console.print(f"\n[cyan]Accumulated Changes This Episode ({len(changes)}):[/cyan]")
        for i, change in enumerate(changes[:10], 1):
            console.print(f"  {i}. {change}")
        if len(changes) > 10:
            console.print(f"  [dim]... and {len(changes) - 10} more[/dim]")

    console.print()


# ============================================================================
# 7. FACTION CONTEXT
# ============================================================================

def _display_faction_context(context: Dict[str, Any]) -> None:
    factions = context.get('factions')
    faction_dynamics = context.get('faction_dynamics')
    char_alignment = context.get('character_faction_alignment')

    if not any([factions, faction_dynamics, char_alignment]):
        return

    _section("FACTION CONTEXT", "bold blue")

    # Factions list
    if factions:
        factions_list = factions
        if isinstance(factions, dict) and 'factions' in factions:
            factions_list = factions['factions']
        elif isinstance(factions, dict) and 'count' in factions:
            factions_list = factions.get('factions', list(factions.values()))

        if isinstance(factions_list, list):
            faction_table = Table(show_header=True, header_style="dim blue")
            faction_table.add_column("Faction", style="cyan", width=20)
            faction_table.add_column("Description", style="white", max_width=35)
            faction_table.add_column("Goals", style="yellow", max_width=30)

            for f in factions_list[:6]:
                if isinstance(f, dict):
                    name = f.get('name', f.get('id', '?'))
                    desc = f.get('description', f.get('status', ''))[:35]
                    goals = f.get('goals', [])
                    goals_str = ', '.join(goals[:2]) if isinstance(goals, list) else str(goals)[:30]
                    faction_table.add_row(name, desc, goals_str)

            console.print(faction_table)
        elif isinstance(factions_list, dict):
            for fid, finfo in list(factions_list.items())[:6]:
                name = finfo.get('name', fid) if isinstance(finfo, dict) else fid
                desc = finfo.get('description', '') if isinstance(finfo, dict) else str(finfo)
                console.print(f"  • [cyan]{name}[/cyan]: {desc[:60]}")

    # Faction dynamics
    if faction_dynamics:
        console.print(f"\n[cyan]Faction Dynamics:[/cyan]")
        if isinstance(faction_dynamics, list):
            for dyn in faction_dynamics[:5]:
                console.print(f"  • {dyn}")
        elif isinstance(faction_dynamics, dict):
            for key, val in list(faction_dynamics.items())[:5]:
                console.print(f"  • [yellow]{key}[/yellow]: {val}")

    # Character-faction alignment
    if char_alignment:
        console.print(f"\n[cyan]Character-Faction Alignment:[/cyan]")
        if isinstance(char_alignment, dict):
            for char_id, faction_id in list(char_alignment.items())[:8]:
                console.print(f"  • [green]{char_id}[/green] → [blue]{faction_id}[/blue]")

    console.print()


# ============================================================================
# 8. MAGIC / TECH SYSTEM
# ============================================================================

def _display_magic_system_context(context: Dict[str, Any]) -> None:
    magic = context.get('magic_system')
    if not magic:
        return

    _section("MAGIC / TECH SYSTEM", "bold magenta")

    if isinstance(magic, dict):
        ms_table = Table(show_header=False, box=None, padding=(0, 2))
        ms_table.add_column("Key", style="cyan", width=18)
        ms_table.add_column("Value")

        if magic.get('name'):
            ms_table.add_row("Name", f"[bold]{magic['name']}[/bold]")
        if magic.get('description') or magic.get('summary'):
            ms_table.add_row("Description", (magic.get('description') or magic.get('summary', ''))[:120])
        if magic.get('source'):
            ms_table.add_row("Source", magic['source'])
        if magic.get('limitations'):
            lims = magic['limitations']
            if isinstance(lims, list):
                ms_table.add_row("Limitations", ', '.join(lims[:3]))
            else:
                ms_table.add_row("Limitations", str(lims)[:80])
        if magic.get('cost'):
            ms_table.add_row("Cost", str(magic['cost'])[:60])
        console.print(ms_table)

        # Abilities / tiers
        if magic.get('abilities') or magic.get('tiers'):
            abilities = magic.get('abilities', magic.get('tiers', []))
            if isinstance(abilities, list):
                console.print(f"\n[cyan]Abilities/Tiers ({len(abilities)}):[/cyan]")
                for ab in abilities[:5]:
                    console.print(f"  • {ab}")
    elif isinstance(magic, str) and magic:
        console.print(f"[white]{magic[:200]}[/white]")

    console.print()


# ============================================================================
# 9. LOCATION & WORLD STATE
# ============================================================================

def _display_location_world_context(context: Dict[str, Any]) -> None:
    locations = context.get('location_states')
    world_changes = context.get('world_state_changes')

    if not any([locations, world_changes]):
        return

    _section("LOCATION & WORLD STATE", "bold green")

    # Location states
    if locations:
        if isinstance(locations, dict):
            loc_table = Table(show_header=True, header_style="dim green")
            loc_table.add_column("Location", style="cyan", width=20)
            loc_table.add_column("State", style="white", max_width=40)
            loc_table.add_column("Changes", style="yellow", max_width=30)

            for loc_id, loc_info in list(locations.items())[:8]:
                if isinstance(loc_info, dict):
                    name = loc_info.get('name', loc_id)
                    state = loc_info.get('state', loc_info.get('status', loc_info.get('description', '—')))
                    changes = loc_info.get('changes', '')
                    loc_table.add_row(name, str(state)[:40], str(changes)[:30])
                else:
                    loc_table.add_row(loc_id, str(loc_info)[:40], '—')
            console.print(loc_table)
        elif isinstance(locations, list):
            for loc in locations[:8]:
                if isinstance(loc, dict):
                    console.print(f"  • [cyan]{loc.get('name', loc.get('id', '?'))}[/cyan]: {loc.get('state', loc.get('status', ''))[:60]}")
                else:
                    console.print(f"  • {loc}")

    # World state changes
    if world_changes:
        console.print(f"\n[cyan]World State Changes This Episode:[/cyan]")
        if isinstance(world_changes, list):
            for change in world_changes[:5]:
                console.print(f"  • {change}")
        elif isinstance(world_changes, dict):
            for key, val in list(world_changes.items())[:5]:
                console.print(f"  • [yellow]{key}[/yellow]: {val}")

    console.print()


# ============================================================================
# 10. MYSTERIES & THEME TRACKING
# ============================================================================

def _display_mysteries_themes(context: Dict[str, Any]) -> None:
    mysteries = context.get('mysteries_tracking')
    new_mysteries = context.get('new_mysteries_introduced')
    theme_depth = context.get('theme_depth')
    themes_explored = context.get('themes_explored')

    if not any([mysteries, new_mysteries, theme_depth]):
        return

    _section("MYSTERIES & THEME TRACKING", "bold yellow")

    # Active mysteries
    if mysteries:
        console.print("[cyan]Open Mysteries:[/cyan]")
        if isinstance(mysteries, list):
            for m in mysteries[:8]:
                if isinstance(m, dict):
                    console.print(f"  ? [yellow]{m.get('mystery', m.get('name', str(m)))}[/yellow]")
                else:
                    console.print(f"  ? [yellow]{m}[/yellow]")
        elif isinstance(mysteries, dict):
            for k, v in list(mysteries.items())[:8]:
                console.print(f"  ? [yellow]{k}[/yellow]: {v}")

    # New mysteries this episode
    if new_mysteries:
        console.print(f"\n[cyan]New Mysteries Introduced:[/cyan]")
        if isinstance(new_mysteries, list):
            for m in new_mysteries[:5]:
                console.print(f"  + [bold yellow]{m}[/bold yellow]")

    # Theme depth
    if theme_depth:
        console.print(f"\n[cyan]Theme Exploration Depth:[/cyan]")
        if isinstance(theme_depth, dict):
            depth_table = Table(show_header=True, header_style="dim magenta")
            depth_table.add_column("Theme", style="magenta", width=20)
            depth_table.add_column("Depth", style="yellow")
            depth_table.add_column("Visual", width=24)
            for theme, depth in theme_depth.items():
                if isinstance(depth, (int, float)):
                    depth_table.add_row(theme, f"{depth:.2f}", _pacing_bar(min(float(depth), 1.0)))
                else:
                    depth_table.add_row(theme, str(depth), "")
            console.print(depth_table)

    console.print()


# ============================================================================
# 11. STORYLINE TYPE TRACKING (NEW)
# ============================================================================

def _display_storyline_context(context: Dict[str, Any]) -> None:
    """Display current and dominant storyline types."""
    storyline = context.get('storyline_type')
    dominants = context.get('dominant_storylines', [])
    
    if not storyline and not dominants:
        return
    
    _section("STORYLINE TYPE", "bold bright_green")
    
    _SL_COLORS = {
        "action": "bold red", "mystery": "dim cyan", "romance": "magenta",
        "political": "yellow", "horror": "red dim", "comedy": "bright_green",
        "drama": "white", "exploration": "green",
    }
    _SL_ICONS = {
        "action": "!!!", "mystery": "???", "romance": "<3", "political": ">>>",
        "horror": "!!!", "comedy": ":)", "drama": "...", "exploration": "->",
    }
    
    if storyline:
        sl_color = _SL_COLORS.get(storyline, "white")
        sl_icon = _SL_ICONS.get(storyline, "")
        console.print(f"[cyan]Current Scene Storyline:[/cyan] [{sl_color}]{sl_icon} {storyline.upper()}[/{sl_color}]")
    
    if dominants:
        console.print(f"[cyan]Dominant This Episode:[/cyan]")
        for i, sl in enumerate(dominants, 1):
            sl_color = _SL_COLORS.get(sl, "white")
            sl_icon = _SL_ICONS.get(sl, "")
            bar_len = max(1, 10 - i * 2)
            bar = "█" * bar_len
            console.print(f"  {i}. [{sl_color}]{sl_icon} {sl}[/{sl_color}] [{sl_color}]{bar}[/{sl_color}]")
    
    console.print()


# ============================================================================
# 12. CHARACTER EMOTIONS (NEW)
# ============================================================================

def _display_character_emotions(context: Dict[str, Any]) -> None:
    """Display character emotions and emotion change tracking."""
    char_emotions = context.get('character_emotions', {})
    
    if not char_emotions:
        return
    
    _section("CHARACTER EMOTIONS", "bold magenta")
    
    emo_table = Table(show_header=True, header_style="dim magenta")
    emo_table.add_column("Character", style="cyan", width=20)
    emo_table.add_column("Current Emotion", style="magenta", width=35)
    emo_table.add_column("Intensity", style="yellow", width=15)
    
    _INTENSITY_KEYWORDS = {
        "high": ["furious", "terrified", "ecstatic", "desperate", "enraged", "seething", "overwhelmed"],
        "low": ["slightly", "mildly", "somewhat", "quietly", "faintly"],
    }
    
    for char_name, emotion in char_emotions.items():
        emotion_str = str(emotion)
        # Determine intensity
        intensity = "moderate"
        for kw in _INTENSITY_KEYWORDS["high"]:
            if kw in emotion_str.lower():
                intensity = "HIGH"
                break
        for kw in _INTENSITY_KEYWORDS["low"]:
            if kw in emotion_str.lower():
                intensity = "low"
                break
        
        # Visual intensity bar
        if intensity == "HIGH":
            bar = "[red]██████████[/red]"
        elif intensity == "low":
            bar = "[dim]███░░░░░░░[/dim]"
        else:
            bar = "[yellow]██████░░░░[/yellow]"
        
        emo_table.add_row(str(char_name), emotion_str, bar)
    
    console.print(emo_table)
    
    # Show emotion changes from running_changes if available
    # (These come from EntityChange objects with property="emotion")
    # Context doesn't directly carry these, but we can hint at the flow
    console.print()


# ============================================================================
# 13. GENERATION STRATEGY
# ============================================================================

def _display_generation_strategy(context: Dict[str, Any]) -> None:
    _section("GENERATION STRATEGY")

    # Count everything included
    arc_chars = context.get('arc_characters', {})
    ep_chars = context.get('episode_characters', {})
    all_chars = context.get('all_characters', {})
    extended_chars = context.get('extended_characters', {})
    recaps = context.get('segment_recaps', [])
    full_segments = context.get('recent_segments_full', [])
    changes = context.get('character_changes_this_episode', [])
    hooks = context.get('story_hooks', [])
    mysteries = context.get('unresolved_mysteries', context.get('mysteries_tracking', []))
    factions = context.get('factions')
    magic = context.get('magic_system')
    locations = context.get('location_states')
    prev_arcs = context.get('previous_arcs', [])
    ep_recaps = context.get('recent_episode_recaps', [])
    arc_recaps = context.get('recent_arc_recaps', [])

    char_count = len(arc_chars or all_chars or {})
    faction_count = len(factions.get('factions', factions) if isinstance(factions, dict) else factions or []) if factions else 0
    loc_count = len(locations) if isinstance(locations, dict) else (len(locations) if isinstance(locations, list) else 0)

    console.print("[green]Included in Context:[/green]")
    include_table = Table(show_header=False, box=None, padding=(0, 2))
    include_table.add_column("Item", style="green", width=35)
    include_table.add_column("Count", style="yellow")

    include_table.add_row("Arc characters (short)", str(char_count))
    include_table.add_row("Episode character states", str(len(ep_chars)))
    include_table.add_row("Extended character details", str(len(extended_chars)))
    include_table.add_row("Segment recaps", str(len(recaps)))
    include_table.add_row("Full segment texts", str(len(full_segments)))
    include_table.add_row("Character changes this episode", str(len(changes)))
    include_table.add_row("Factions", str(faction_count))
    include_table.add_row("Locations", str(loc_count))
    include_table.add_row("Magic/tech system", "Yes" if magic else "No")
    include_table.add_row("Story hooks", str(len(hooks)))
    include_table.add_row("Previous arcs", str(len(prev_arcs)))
    include_table.add_row("Episode recaps", str(len(ep_recaps)))
    include_table.add_row("Arc recaps", str(len(arc_recaps)))
    include_table.add_row("Mysteries", str(len(mysteries) if isinstance(mysteries, (list, dict)) else 0))

    console.print(include_table)

    console.print("\n[yellow]Excluded (to save tokens):[/yellow]")
    console.print("  • Inactive character details")
    console.print("  • Episodes older than recent 3")
    console.print("  • Segments older than recent 10")
    console.print("  • Resolved/archived arcs")
    console.print("  • Full location descriptions (summaries only)")

    console.print()


# ============================================================================
# 12. ACTUAL FORMATTED AI PROMPT
# ============================================================================

def _display_actual_ai_prompt(context: Dict[str, Any]) -> None:
    """Format and display the exact prompt that will be sent to the AI."""
    _section("ACTUAL AI PROMPT (what LLM receives)", "bold red")

    try:
        from app.utils.prompt_formatter import PromptFormatter
        formatted_prompt = PromptFormatter.format_scene_context(dict(context))  # copy to avoid mutation
        
        # Show the prompt with syntax highlighting
        console.print(Panel(
            formatted_prompt,
            title="Formatted Prompt",
            border_style="red",
            padding=(1, 2),
        ))

        # Token estimate (rough: ~4 chars per token)
        char_count = len(formatted_prompt)
        token_estimate = char_count // 4
        console.print(f"[dim]Prompt length: {char_count:,} chars (~{token_estimate:,} tokens)[/dim]")
    except Exception as e:
        console.print(f"[red]Could not format prompt: {e}[/red]")
        console.print("[dim]Falling back to raw context keys[/dim]")
        console.print(f"[dim]Context keys: {', '.join(context.keys())}[/dim]")

    console.print()


# ============================================================================
# FALLBACK: Context from segment only
# ============================================================================

def _display_context_from_segment(runner, segment) -> None:
    """Fallback display using only segment info when context dict not available."""
    story = runner.story if hasattr(runner, 'story') else None
    if not story:
        console.print("[dim]Story data not available[/dim]")
        return

    # Characters table
    if hasattr(story, '_characters') and story._characters:
        _section("CHARACTERS (from story)")
        char_table = Table(show_header=True, header_style="bold magenta")
        char_table.add_column("Name", style="cyan")
        char_table.add_column("Status", style="green")

        for char_id, char in list(story._characters.items())[:10]:
            name = char.name if hasattr(char, 'name') else char_id
            is_present = char_id in getattr(segment, 'characters_present', [])
            status = "[green]Present[/green]" if is_present else "[dim]Not present[/dim]"
            char_table.add_row(name, status)

        console.print(char_table)
        console.print()

    # Pacing info
    _section("PACING")
    pacing_table = Table(show_header=False, box=None)
    pacing_table.add_row("[cyan]Episode:[/cyan]", f"{getattr(segment, 'episode_number', 'N/A')}")
    pacing_table.add_row("[cyan]Segment in Episode:[/cyan]", f"{getattr(segment, 'segment_number_in_episode', 'N/A')}/20")
    pacing_table.add_row("[cyan]Pacing:[/cyan]", _pacing_bar(getattr(segment, 'pacing_weight', 0)))
    pacing_table.add_row("[cyan]End Proximity:[/cyan]", _pacing_bar(getattr(segment, 'end_condition_proximity', 0)))
    console.print(pacing_table)
    console.print()

    # Running changes on current segment
    running_changes = getattr(segment, 'running_changes', [])
    if running_changes:
        _section("RUNNING CHANGES")
        for rc in running_changes[:10]:
            entity = getattr(rc, 'entity_name', getattr(rc, 'entity_id', '?'))
            prop = getattr(rc, 'property', '?')
            from_val = getattr(rc, 'from_value', '—')
            to_val = getattr(rc, 'to_value', '—')
            console.print(f"  • [cyan]{entity}[/cyan].{prop}: {from_val} → {to_val}")

    # Generation strategy
    _section("GENERATION STRATEGY")
    console.print("[green]Will Include:[/green]")
    console.print("  • Current segment prose and atmosphere")
    console.print("  • Active character states and relationships")
    console.print("  • Current arc direction and goals")
    console.print("  • Recent segment history (last 10)")
    console.print("  • Full text of last 3 segments (for continuity)")
    console.print("  • Changes accumulated this episode")
    console.print("  • Factions, magic system, locations")
    console.print("  • Pacing signals and episode metadata")

    console.print("\n[yellow]Will Exclude:[/yellow]")
    console.print("  • Resolved arcs (to stay focused)")
    console.print("  • Archived episodes (to save tokens)")
    console.print("  • Inactive characters (unless relevant)")
    console.print()


# ============================================================================
# GENERATION RESULT DISPLAY
# ============================================================================

def display_generation_result_story_debug(
    segment, context: Optional[Dict[str, Any]] = None
) -> None:
    """Display result of generation with running changes, characters, and full metadata."""

    result_lines = []
    result_lines.append(f"[cyan]Segment ID:[/cyan] [bold]{segment.id}[/bold]")
    result_lines.append(f"[cyan]Episode:[/cyan] {getattr(segment, 'episode_number', 'N/A')}")
    result_lines.append(f"[cyan]Segment #:[/cyan] {getattr(segment, 'segment_number_in_episode', 'N/A')}")
    result_lines.append(f"[cyan]Arc:[/cyan] {getattr(segment, 'arc_id', 'N/A')}")
    result_lines.append(f"[cyan]Parent:[/cyan] {getattr(segment, 'parent_segment_id', 'N/A')}")
    result_lines.append(f"[cyan]Status:[/cyan] {getattr(segment, 'status', 'N/A')}")
    result_lines.append(f"[cyan]Blocks:[/cyan] {len(getattr(segment, 'text_blocks', []))}")

    # Storyline type
    storyline = getattr(segment, 'storyline_type', None)
    if storyline:
        result_lines.append(f"[cyan]Storyline:[/cyan] [bold]{storyline.upper()}[/bold]")

    # Pacing
    pacing = getattr(segment, 'pacing_weight', 0)
    end_prox = getattr(segment, 'end_condition_proximity', 0)
    result_lines.append(f"[cyan]Pacing:[/cyan] {_pacing_bar(pacing)}")
    result_lines.append(f"[cyan]End Proximity:[/cyan] {_pacing_bar(end_prox)}")

    if getattr(segment, 'triggers_episode_transition', False):
        result_lines.append("[bold red]>>> TRIGGERS EPISODE TRANSITION <<<[/bold red]")

    console.print(Panel(
        "\n".join(result_lines),
        title="Generation Complete",
        border_style="green"
    ))

    # Atmosphere & environment
    atmosphere = getattr(segment, 'atmosphere', None)
    time_of_day = getattr(segment, 'time_of_day', None)
    weather = getattr(segment, 'weather', None)
    if any([atmosphere, time_of_day, weather]):
        env_parts = []
        if atmosphere:
            env_parts.append(f"Atmosphere: {atmosphere}")
        if time_of_day:
            env_parts.append(f"Time: {time_of_day}")
        if weather:
            env_parts.append(f"Weather: {weather}")
        console.print(f"[dim]{' | '.join(env_parts)}[/dim]")

    # Characters present
    chars_present = getattr(segment, 'characters_present', [])
    if chars_present:
        console.print(f"\n[cyan]Characters Present:[/cyan] {', '.join(chars_present)}")

    # Locations present
    locs_present = getattr(segment, 'locations_present', [])
    if locs_present:
        console.print(f"[cyan]Locations Present:[/cyan] {', '.join(locs_present)}")

    # Key items
    key_items = getattr(segment, 'key_items', [])
    if key_items:
        console.print(f"[cyan]Key Items:[/cyan] {', '.join(key_items)}")

    # Running changes
    running_changes = getattr(segment, 'running_changes', [])
    if running_changes:
        console.print(f"\n[bold yellow]Running Changes ({len(running_changes)}):[/bold yellow]")
        change_table = Table(show_header=True, header_style="dim yellow")
        change_table.add_column("Entity", style="cyan", width=16)
        change_table.add_column("Property", style="white", width=12)
        change_table.add_column("From", style="red", width=14)
        change_table.add_column("To", style="green", width=14)

        for rc in running_changes[:10]:
            change_table.add_row(
                getattr(rc, 'entity_name', '?'),
                getattr(rc, 'property', '?'),
                str(getattr(rc, 'from_value', '') or '—')[:14],
                str(getattr(rc, 'to_value', '') or '—')[:14],
            )
        console.print(change_table)

    # Change notes
    change_notes = getattr(segment, 'change_notes', [])
    if change_notes:
        console.print(f"\n[cyan]Change Notes ({len(change_notes)}):[/cyan]")
        for note in change_notes[:8]:
            console.print(f"  • {note}")
        if len(change_notes) > 8:
            console.print(f"  [dim]... and {len(change_notes) - 8} more[/dim]")

    # Character emotions in generation result
    char_emotions = getattr(segment, 'character_emotions', {})
    if char_emotions:
        console.print(f"\n[bold magenta]Character Emotions:[/bold magenta]")
        for char_name, emotion in char_emotions.items():
            console.print(f"  [cyan]{char_name}:[/cyan] [magenta]{emotion}[/magenta]")
    
    # Emotion changes in running_changes
    emotion_changes = [rc for rc in getattr(segment, 'running_changes', []) if getattr(rc, 'property', '') == 'emotion']
    if emotion_changes:
        console.print(f"\n[bold magenta]Emotion Shifts ({len(emotion_changes)}):[/bold magenta]")
        for ec in emotion_changes:
            from_val = getattr(ec, 'from_value', None)
            to_val = getattr(ec, 'to_value', None)
            name = getattr(ec, 'entity_name', '?')
            if from_val:
                console.print(f"  [cyan]{name}:[/cyan] [red]{from_val}[/red] -> [green]{to_val}[/green]")
            else:
                console.print(f"  [cyan]{name}:[/cyan] [green]{to_val}[/green]")

    console.print()


# ============================================================================
# CHOICE PROMPT
# ============================================================================

def prompt_choice_story_debug(segment, choices: List) -> str:
    """Get user choice in story debug mode with detailed metadata."""

    console.print("\n[bold cyan]Available Choices:[/bold cyan]")

    choice_table = Table(show_header=True, header_style="bold magenta")
    choice_table.add_column("#", style="cyan", width=3)
    choice_table.add_column("Choice Text", style="white", max_width=55)
    choice_table.add_column("Target", style="yellow", width=14)
    choice_table.add_column("Clicks", style="green", width=6)

    for i, choice in enumerate(choices, 1):
        choice_text = choice.text if hasattr(choice, 'text') else str(choice)
        to_segment = choice.to_segment_id if hasattr(choice, 'to_segment_id') else None
        clicks = getattr(choice, 'click_count', getattr(choice, 'clicks', 0))

        target = str(to_segment)[:14] if to_segment else "[yellow]GENERATE[/yellow]"

        choice_table.add_row(str(i), choice_text[:55], target, str(clicks))

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
