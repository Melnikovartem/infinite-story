"""Unified story display - single interactive view for playing and debugging.

Shows the story text with a compact menu:
  [1-N] Pick a choice     [L] Toggle logs     [I] Segment info     [P] View prompt
"""

from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import logging

console = Console(force_terminal=True, legacy_windows=False)
logger = logging.getLogger("infinite_story.display")


# ============================================================================
# STATE
# ============================================================================

_logs_enabled = False


# ============================================================================
# HELPERS
# ============================================================================

def _pacing_bar(value: float, width: int = 16) -> str:
    """Visual bar like [████████░░░░░░░░] 40%."""
    filled = int(value * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {value:.0%}"


def _format_block(block) -> Text:
    """Format a single text block into a Rich Text object."""
    block_type = block.type.lower() if hasattr(block.type, 'lower') else str(block.type).lower()
    content = block.content if hasattr(block, 'content') else str(block)
    emotion = getattr(block, 'emotion', None)
    character = getattr(block, 'character', None)

    if block_type == "character_speech":
        name = character or "?"
        tag = f" [{emotion}]" if emotion else ""
        line = Text()
        line.append(f"{name}{tag}: ", style="bold cyan")
        line.append(f'"{content}"', style="cyan")
        return line

    if block_type == "character_thought":
        name = character or "?"
        line = Text()
        line.append(f"[{name}] ", style="dim italic yellow")
        line.append(content, style="italic yellow")
        return line

    if block_type == "narrator_commentary":
        return Text(f"  -- {content}", style="dim italic")

    if block_type == "scene_title":
        return Text(f"  === {content} ===", style="bold magenta")

    if block_type == "flashback":
        line = Text()
        line.append("[Flashback] ", style="yellow bold")
        line.append(content, style="yellow")
        return line

    if block_type == "dream_sequence":
        line = Text()
        line.append("[Dream] ", style="magenta bold")
        line.append(content, style="magenta")
        return line

    if block_type == "sfx":
        return Text(f"[{content}]", style="dim cyan italic")

    if block_type == "visual_cue":
        return Text(f"* {content}", style="green dim")

    if block_type == "location_label":
        return Text(content, style="bold green underline")

    if block_type == "poem_or_song":
        return Text(f"  ~ {content}", style="cyan italic")

    if block_type == "letter_or_note":
        return Text(f"  > {content}", style="yellow dim")

    if block_type == "system_message":
        return Text(f"[System] {content}", style="dim red")

    # narrator_describing + fallback
    return Text(content, style="white")


# ============================================================================
# MAIN SEGMENT DISPLAY
# ============================================================================

def display_segment(segment) -> None:
    """Display the current segment: header + text blocks."""
    console.clear()

    # ── Compact header ──
    ep = getattr(segment, 'episode_number', '?')
    seg_in_ep = getattr(segment, 'segment_number_in_episode', '?')
    arc = getattr(segment, 'arc_id', '')
    storyline = getattr(segment, 'storyline_type', None)
    desc = getattr(segment, 'short_description', '')

    header_parts = [f"[cyan]Ep {ep}[/cyan] [dim]|[/dim] [cyan]Seg {seg_in_ep}/20[/cyan]"]
    if arc:
        header_parts.append(f"[dim]|[/dim] [green]{arc}[/green]")
    if storyline:
        _icons = {"action": "!!!", "mystery": "???", "romance": "<3", "political": ">>>",
                  "horror": "!!!", "comedy": ":)", "drama": "...", "exploration": "->"}
        header_parts.append(f"[dim]|[/dim] [yellow]{_icons.get(storyline, '')} {storyline}[/yellow]")
    header_parts.append(f"[dim]|[/dim] [dim]{segment.id}[/dim]")

    console.print(" ".join(header_parts))
    if desc:
        console.print(f"[dim italic]{desc}[/dim italic]")
    console.print()

    # ── Text blocks ──
    for block in getattr(segment, 'text_blocks', []):
        console.print(_format_block(block))
        console.print()

    # ── Emotion summary ──
    char_emotions = getattr(segment, 'character_emotions', {})
    if char_emotions:
        parts = [f"[magenta]{name}: {emo}[/magenta]" for name, emo in char_emotions.items()]
        console.print(f"[dim]  -- [/dim]{'  '.join(parts)}")
        console.print()


# ============================================================================
# INTERACTIVE MENU
# ============================================================================

def prompt_menu(segment, choices: List, context: Optional[Dict[str, Any]] = None) -> str:
    """Show choices + debug menu. Returns a choice ID or a command string.

    Commands returned:
      "CMD_LOGS"   - toggle logs
      "CMD_INFO"   - show segment info
      "CMD_PROMPT" - show AI prompt
      choice.id    - user picked a story choice
    """
    # ── Show choices ──
    console.print("[bold]Choices:[/bold]")
    for i, choice in enumerate(choices, 1):
        text = choice.text if hasattr(choice, 'text') else str(choice)
        to_seg = choice.to_segment_id if hasattr(choice, 'to_segment_id') else None
        target = "[dim](new)[/dim]" if not to_seg else f"[dim]-> {to_seg}[/dim]"
        console.print(f"  [bold cyan]{i}[/bold cyan]  {text}  {target}")

    # ── Menu bar ──
    log_label = "[green]ON[/green]" if _logs_enabled else "[dim]OFF[/dim]"
    console.print()
    console.print(f"  [bold yellow]L[/bold yellow] Logs {log_label}    [bold yellow]I[/bold yellow] Info    [bold yellow]P[/bold yellow] Prompt")

    # ── Input ──
    valid = [str(i) for i in range(1, len(choices) + 1)] + ["l", "i", "p"]
    while True:
        raw = Prompt.ask("[bold]>").strip().lower()
        if raw == "l":
            return "CMD_LOGS"
        if raw == "i":
            return "CMD_INFO"
        if raw == "p":
            return "CMD_PROMPT"
        if raw in [str(i) for i in range(1, len(choices) + 1)]:
            selected = choices[int(raw) - 1]
            return selected.id if hasattr(selected, 'id') else str(selected)
        console.print(f"[red]Enter 1-{len(choices)}, L, I, or P[/red]")


# ============================================================================
# TOGGLE LOGS
# ============================================================================

def toggle_logs() -> bool:
    """Toggle debug logging and return new state."""
    global _logs_enabled
    _logs_enabled = not _logs_enabled

    root = logging.getLogger()
    app_logger = logging.getLogger("infinite_story")

    if _logs_enabled:
        root.setLevel(logging.DEBUG)
        app_logger.setLevel(logging.DEBUG)
        # Ensure there's at least one handler
        if not root.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
            root.addHandler(handler)
        console.print("[green]Logs enabled (DEBUG level)[/green]")
    else:
        root.setLevel(logging.ERROR)
        app_logger.setLevel(logging.ERROR)
        console.print("[yellow]Logs disabled[/yellow]")

    # Always keep noisy libs quiet
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("h11").setLevel(logging.WARNING)

    return _logs_enabled


# ============================================================================
# SEGMENT INFO PANEL
# ============================================================================

def _build_info_lines(segment, context: Optional[Dict[str, Any]] = None) -> List[str]:
    """Build the info lines for segment info panel (shared by interactive and dump)."""
    lines = []

    # ── Segment metadata ──
    lines.append(f"[bold cyan]Segment[/bold cyan]")
    lines.append(f"  ID:          {segment.id}")
    lines.append(f"  Status:      {getattr(segment, 'status', '?')}")
    lines.append(f"  Parent:      {getattr(segment, 'parent_segment_id', 'none')}")
    lines.append(f"  Description: {getattr(segment, 'short_description', 'N/A')}")
    lines.append(f"  Blocks:      {len(getattr(segment, 'text_blocks', []))}")

    # Storyline
    sl = getattr(segment, 'storyline_type', None)
    if sl:
        lines.append(f"  Storyline:   {sl}")

    # Environment
    atm = getattr(segment, 'atmosphere', None)
    tod = getattr(segment, 'time_of_day', None)
    weather = getattr(segment, 'weather', None)
    env_parts = [p for p in [
        f"Atmosphere: {atm}" if atm else None,
        f"Time: {tod}" if tod else None,
        f"Weather: {weather}" if weather else None,
    ] if p]
    if env_parts:
        lines.append(f"  Environment: {' | '.join(env_parts)}")

    # Characters / locations present
    chars = getattr(segment, 'characters_present', [])
    locs = getattr(segment, 'locations_present', [])
    if chars:
        lines.append(f"  Characters:  {', '.join(chars)}")
    if locs:
        lines.append(f"  Locations:   {', '.join(locs)}")

    # Key items
    items = getattr(segment, 'key_items', [])
    if items:
        lines.append(f"  Key items:   {', '.join(items)}")

    lines.append("")

    # ── Episode / pacing ──
    lines.append(f"[bold cyan]Episode & Pacing[/bold cyan]")
    ep = getattr(segment, 'episode_number', '?')
    seg_num = getattr(segment, 'segment_number_in_episode', '?')
    pacing = getattr(segment, 'pacing_weight', 0)
    end_prox = getattr(segment, 'end_condition_proximity', 0)

    lines.append(f"  Episode:       {ep}")
    lines.append(f"  Segment:       {seg_num}/20")
    lines.append(f"  Pacing:        {_pacing_bar(pacing)}")
    lines.append(f"  End proximity: {_pacing_bar(end_prox)}")

    if getattr(segment, 'triggers_episode_transition', False):
        lines.append(f"  [bold red]>>> TRIGGERS EPISODE TRANSITION <<<[/bold red]")

    if getattr(segment, 'protagonist_id', None):
        lines.append(f"  Protagonist:   {segment.protagonist_id}")

    # Episode tone / end condition from context
    if context:
        if context.get('episode_tone'):
            lines.append(f"  Episode tone:  {context['episode_tone']}")
        if context.get('episode_end_condition'):
            lines.append(f"  End condition: {context['episode_end_condition']}")

    lines.append("")

    # ── Arc info ──
    arc_id = getattr(segment, 'arc_id', None)
    if arc_id or (context and context.get('current_arc')):
        lines.append(f"[bold cyan]Arc[/bold cyan]")
        lines.append(f"  ID: {arc_id or 'N/A'}")
        if context:
            ca = context.get('current_arc', {})
            if ca.get('title'):
                lines.append(f"  Title:    {ca['title']}")
            if ca.get('premise'):
                lines.append(f"  Premise:  {ca['premise'][:120]}")
            if ca.get('central_conflict'):
                lines.append(f"  Conflict: {ca['central_conflict'][:120]}")
            if ca.get('themes'):
                lines.append(f"  Themes:   {', '.join(ca['themes'])}")
        lines.append("")

    # ── Momentum metrics ──
    if context:
        momentum = context.get('story_momentum')
        tension = context.get('tension_level')
        pacing_trend = context.get('pacing_trend')
        if any(v is not None for v in [momentum, tension, pacing_trend]):
            lines.append(f"[bold cyan]Momentum[/bold cyan]")
            if momentum is not None and isinstance(momentum, (int, float)):
                lines.append(f"  Momentum: {_pacing_bar(float(momentum))}")
            if tension is not None and isinstance(tension, (int, float)):
                lines.append(f"  Tension:  {_pacing_bar(float(tension))}")
            if pacing_trend is not None and isinstance(pacing_trend, (int, float)):
                sign = "+" if pacing_trend >= 0 else ""
                lines.append(f"  Trend:    {sign}{pacing_trend:.2f}")
            lines.append("")

    # ── Character emotions ──
    char_emotions = getattr(segment, 'character_emotions', {})
    if char_emotions:
        lines.append(f"[bold cyan]Character Emotions[/bold cyan]")
        for name, emo in char_emotions.items():
            lines.append(f"  {name}: {emo}")
        lines.append("")

    # ── Running changes ──
    changes = getattr(segment, 'running_changes', [])
    if changes:
        lines.append(f"[bold cyan]Running Changes ({len(changes)})[/bold cyan]")
        for rc in changes[:12]:
            entity = getattr(rc, 'entity_name', getattr(rc, 'entity_id', '?'))
            prop = getattr(rc, 'property', '?')
            frm = str(getattr(rc, 'from_value', '') or '-')[:20]
            to = str(getattr(rc, 'to_value', '') or '-')[:20]
            lines.append(f"  {entity}.{prop}: {frm} -> {to}")
        if len(changes) > 12:
            lines.append(f"  [dim]... +{len(changes) - 12} more[/dim]")
        lines.append("")

    # ── Change notes ──
    notes = getattr(segment, 'change_notes', [])
    if notes:
        lines.append(f"[bold cyan]Change Notes[/bold cyan]")
        for n in notes[:8]:
            lines.append(f"  - {n}")
        if len(notes) > 8:
            lines.append(f"  [dim]... +{len(notes) - 8} more[/dim]")
        lines.append("")

    # ── Context: characters ──
    if context:
        arc_chars = context.get('arc_characters', {})
        if arc_chars:
            lines.append(f"[bold cyan]Characters in Arc ({len(arc_chars)})[/bold cyan]")
            for cid, cinfo in list(arc_chars.items())[:10]:
                if isinstance(cinfo, dict):
                    name = cinfo.get('name', cid)
                    status = cinfo.get('status', '')
                    lines.append(f"  {name}" + (f" [{status}]" if status else ""))
                else:
                    lines.append(f"  {cid}")
            if len(arc_chars) > 10:
                lines.append(f"  [dim]... +{len(arc_chars) - 10} more[/dim]")
            lines.append("")

        # Factions
        factions = context.get('factions')
        if factions:
            faction_list = factions
            if isinstance(factions, dict) and 'factions' in factions:
                faction_list = factions['factions']
            elif isinstance(factions, dict):
                faction_list = list(factions.values())
            if isinstance(faction_list, list):
                lines.append(f"[bold cyan]Factions ({len(faction_list)})[/bold cyan]")
                for f in faction_list[:5]:
                    if isinstance(f, dict):
                        lines.append(f"  {f.get('name', '?')}: {f.get('description', '')[:60]}")
                lines.append("")

        # Magic system
        magic = context.get('magic_system')
        if magic and isinstance(magic, dict) and magic.get('name'):
            lines.append(f"[bold cyan]Magic/Tech System[/bold cyan]")
            lines.append(f"  {magic['name']}: {(magic.get('description') or magic.get('summary', ''))[:100]}")
            lines.append("")

        # Generation strategy summary
        lines.append(f"[bold cyan]Context Summary[/bold cyan]")
        arc_chars_count = len(context.get('arc_characters', {}))
        ep_chars_count = len(context.get('episode_characters', {}))
        recaps_count = len(context.get('segment_recaps', []))
        full_segs_count = len(context.get('recent_segments_full', []))
        lines.append(f"  Arc chars: {arc_chars_count}  Ep chars: {ep_chars_count}  Seg recaps: {recaps_count}  Full segs: {full_segs_count}")
        prev_arcs = len(context.get('previous_arcs', []))
        ep_recaps = len(context.get('recent_episode_recaps', []))
        hooks = len(context.get('story_hooks', []))
        lines.append(f"  Prev arcs: {prev_arcs}  Ep recaps: {ep_recaps}  Hooks: {hooks}")

    return lines


def show_segment_info(segment, context: Optional[Dict[str, Any]] = None) -> None:
    """Show a detailed info panel for the current segment, then wait for Enter."""
    lines = _build_info_lines(segment, context)
    console.print(Panel(
        "\n".join(lines),
        title="Segment Info",
        border_style="cyan",
        padding=(1, 2),
    ))
    Prompt.ask("[dim]Press Enter to go back[/dim]", default="")


# ============================================================================
# AI PROMPT VIEW
# ============================================================================

def show_prompt(context: Optional[Dict[str, Any]] = None) -> None:
    """Build and display the formatted AI prompt, then wait for Enter."""
    if not context:
        console.print("[yellow]No context available (need at least one generated segment)[/yellow]")
        Prompt.ask("[dim]Press Enter to go back[/dim]", default="")
        return

    try:
        from app.utils.prompt_formatter import PromptFormatter
        formatted = PromptFormatter.format_scene_context(dict(context))

        char_count = len(formatted)
        token_est = char_count // 4

        console.print(Panel(
            formatted,
            title=f"AI Prompt  ({char_count:,} chars  ~{token_est:,} tokens)",
            border_style="red",
            padding=(1, 2),
        ))
    except Exception as e:
        console.print(f"[red]Could not format prompt: {e}[/red]")
        console.print(f"[dim]Context keys: {', '.join(context.keys())}[/dim]")

    Prompt.ask("[dim]Press Enter to go back[/dim]", default="")


# ============================================================================
# GENERATION RESULT (shown briefly after generation completes)
# ============================================================================

def display_generation_result(segment) -> None:
    """Show a brief summary after a new segment is generated."""
    ep = getattr(segment, 'episode_number', '?')
    seg_num = getattr(segment, 'segment_number_in_episode', '?')
    blocks = len(getattr(segment, 'text_blocks', []))
    sl = getattr(segment, 'storyline_type', None)
    transition = getattr(segment, 'triggers_episode_transition', False)

    parts = [
        f"Ep {ep} Seg {seg_num}",
        f"{blocks} blocks",
    ]
    if sl:
        parts.append(sl)
    if transition:
        parts.append("[red]EPISODE TRANSITION[/red]")

    console.print(f"[green]Generated:[/green] {' | '.join(parts)}")


# ============================================================================
# NON-INTERACTIVE DUMP VARIANTS (for --dump flag)
# ============================================================================

def show_segment_info_noninteractive(segment, context: Optional[Dict[str, Any]] = None) -> None:
    """Print segment info without waiting for Enter (for --dump mode)."""
    # Reuse the same body as show_segment_info but skip the Prompt.ask
    lines = _build_info_lines(segment, context)
    console.print(Panel(
        "\n".join(lines),
        title="Segment Info",
        border_style="cyan",
        padding=(1, 2),
    ))


def show_prompt_noninteractive(context: Optional[Dict[str, Any]] = None) -> None:
    """Print AI prompt without waiting for Enter (for --dump mode)."""
    if not context:
        console.print("[yellow]No context available[/yellow]")
        return

    try:
        from app.utils.prompt_formatter import PromptFormatter
        formatted = PromptFormatter.format_scene_context(dict(context))

        char_count = len(formatted)
        token_est = char_count // 4

        console.print(Panel(
            formatted,
            title=f"AI Prompt  ({char_count:,} chars  ~{token_est:,} tokens)",
            border_style="red",
            padding=(1, 2),
        ))
    except Exception as e:
        console.print(f"[red]Could not format prompt: {e}[/red]")
        console.print(f"[dim]Context keys: {', '.join(context.keys())}[/dim]")
