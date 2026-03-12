import json
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

from app.models.story_base import LOCAL_DATA_DIR
from app.models.story import Story
from app.models.story_choice import StoryChoice
from app.engine.story_runner import StoryRunner
from app.engine.openai_generator import OpenAIGenerator
from app.engine.openrouter_generator import OpenRouterGenerator
from app.config import Config
from app.utils.error_handler import ErrorHandler, ErrorType, handle_api_error
from app.utils.model_info import (
    get_models_by_provider,
    get_recommended_models,
    format_model_list,
    get_model_recommendations
)

app = typer.Typer()
# Force console to use proper terminal without buffering
console = Console(force_terminal=True, legacy_windows=False)
logger = logging.getLogger("infinite_story.cli")

def setup_logging(log_level: str):
    """Configure logging level for the app."""
    level_map = {
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "debug": logging.DEBUG,
    }
    level = level_map.get(log_level.lower(), logging.ERROR)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    
    # Set level for infinite_story logger
    app_logger = logging.getLogger("infinite_story")
    app_logger.setLevel(level)

def display_stories(stories: List[dict]) -> None:
    """Display stories in a rich table."""
    table = Table(title="Available Stories")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Genre", style="yellow")
    table.add_column("Description", style="white")

    for story in stories:
        table.add_row(
            str(story.get("id", "N/A")),
            story.get("title", "Untitled"),
            story.get("genre", "Unspecified"),
            story.get("description", "No description")[:100] + "..."
        )

    console.print(table)

def select_story(stories: List[dict]) -> Optional[dict]:
    """Let user select a story using arrow keys."""
    if not stories:
        console.print("[red]No stories available![/red]")
        console.print("[yellow]Create one with:[/yellow]")
        console.print("  ./run.sh create-story-ai my_story --title \"Title\" --description \"...\" --genre \"Genre\"")
        return None

    story_ids = [str(story.get("id", "")) for story in stories]
    selected_id = Prompt.ask(
        "Select a story ID",
        choices=story_ids,
        default=story_ids[0]
    )

    return next((s for s in stories if str(s.get("id", "")) == selected_id), None)

@app.command()
def create_story(
    story_id: str = typer.Argument(..., help="Unique identifier for the story (e.g., my_story)"),
    title: str = typer.Option(..., "--title", help="Display title of the story"),
    description: str = typer.Option(..., "--description", help="Long description of the story"),
    genre: str = typer.Option("Unknown", "--genre", help="Genre (e.g., Fantasy, Sci-Fi, Mystery)"),
):
    """Create a new story interactively.
    
    This guides you through creating a new story with worldbuilding, characters, locations, and opening scene.
    
    Example:
        python -m app.cli create-story my_story --title "My Story" --description "A tale..." --genre Fantasy
    """
    from app.utils.story_builder import StoryBuilder
    
    # Check if story already exists
    existing = Story.load(story_id, story_id)
    if existing:
        console.print(f"[red]Story '{story_id}' already exists![/red]")
        if not typer.confirm("Do you want to overwrite it?"):
            console.print("[yellow]Cancelled[/yellow]")
            return
        # Delete existing story
        existing.delete()
        console.print(f"[yellow]Deleted existing story '{story_id}'[/yellow]")
    
    console.print(Panel(
        f"[bold cyan]Creating new story: {title}[/bold cyan]\n[yellow]Genre: {genre}[/yellow]",
        title="Story Creator",
        border_style="cyan"
    ))
    
    try:
        builder = StoryBuilder(story_id, title, description, genre)
        
        # Worldbuilding
        console.print("\n[bold cyan]Step 1: Worldbuilding[/bold cyan]")
        console.print("Enter 3-5 fundamental truths about your world (enter empty line when done):")
        fundamental_truths = []
        for i in range(5):
            truth = Prompt.ask(f"Truth {i+1}", default="")
            if not truth:
                break
            fundamental_truths.append(truth)
        
        if fundamental_truths:
            worldbuilding_desc = Prompt.ask("Brief worldbuilding description")
            builder.add_worldbuilding(
                fundamental_truths=fundamental_truths,
                worldbuilding={"description": worldbuilding_desc}
            )
            console.print(f"[green]✓ Added {len(fundamental_truths)} world truths[/green]")
        
        # Characters
        console.print("\n[bold cyan]Step 2: Characters[/bold cyan]")
        console.print("Create 2-4 main characters (enter empty name to finish):")
        for i in range(4):
            char_name = Prompt.ask(f"Character {i+1} name", default="")
            if not char_name:
                break
            
            char_id = f"char_{i+1}"
            char_desc = Prompt.ask("Brief description")
            char_bg = Prompt.ask("Background/motivation")
            
            builder.add_character(
                char_id=char_id,
                name=char_name,
                description=char_desc,
                background=char_bg
            )
            console.print(f"[green]✓ Added character '{char_name}'[/green]")
        
        # Locations
        console.print("\n[bold cyan]Step 3: Locations[/bold cyan]")
        console.print("Create 2-3 main locations (enter empty name to finish):")
        for i in range(3):
            loc_name = Prompt.ask(f"Location {i+1} name", default="")
            if not loc_name:
                break
            
            loc_id = f"loc_{i+1}"
            loc_desc = Prompt.ask("Description")
            
            builder.add_location(
                loc_id=loc_id,
                name=loc_name,
                description=loc_desc
            )
            console.print(f"[green]✓ Added location '{loc_name}'[/green]")
        
        # Opening Scene
        console.print("\n[bold cyan]Step 4: Opening Scene[/bold cyan]")
        opening_title = Prompt.ask("Scene title", default="The Story Begins")
        console.print("Enter the opening narrative (press Enter twice to finish):")
        
        lines = []
        empty_count = 0
        while empty_count < 2:
            line = Prompt.ask("", default="")
            if not line:
                empty_count += 1
            else:
                empty_count = 0
                lines.append(line)
        
        opening_content = "\n".join(lines)
        if opening_content.strip():
            builder.add_opening_segment(
                segment_id="opening",
                title=opening_title,
                content=opening_content,
                atmosphere="mysterious",
                episode_number=1
            )
            console.print("[green]✓ Added opening scene[/green]")
        
        # Opening Choices
        console.print("\n[bold cyan]Step 5: Opening Choices[/bold cyan]")
        console.print("Create 2-3 choices for the opening scene (enter empty text to finish):")
        for i in range(3):
            choice_text = Prompt.ask(f"Choice {i+1}", default="")
            if not choice_text:
                break
            
            choice_id = f"choice_{i+1}"
            builder.add_choice(
                choice_id=choice_id,
                from_segment_id="opening",
                text=choice_text,
                to_segment_id=None  # Will be AI-generated
            )
            console.print(f"[green]✓ Added choice '{choice_text}'[/green]")
        
        # Validate at least one choice exists
        opening_seg = builder.segments.get("opening")
        if not opening_seg or not opening_seg.outgoing_choices:
            console.print("[red]Error: Opening scene must have at least one choice![/red]")
            return
        
        # Save
        console.print("\n[bold cyan]Saving story...[/bold cyan]")
        with console.status("[bold yellow]Writing to disk...[/bold yellow]", spinner="dots"):
            story_id = builder.save()
        
        console.print(Panel(
            f"[green]✅ Story '{title}' created successfully![/green]\n\n[cyan]Story ID: {story_id}[/cyan]\n\nPlay it with:[/cyan]\n[bold]python -m app.cli run-story {story_id}[/bold]",
            title="Success",
            border_style="green"
        ))
        logger.info(f"Story created: {story_id}")
    
    except Exception as e:
        console.print(f"[red]Error creating story: {e}[/red]")
        logger.error(f"Story creation failed: {e}", exc_info=True)

async def create_story_ai_async(
    story_id: str,
    title: str,
    description: str,
    genre: str,
    world_input: str = "",
    first_scene_input: str = ""
):
    """Create a story with AI-powered world, arcs, characters, and opening scene generation."""
    from app.engine.generators.story_planner import StoryPlanner
    from app.engine.generators.world_description_generator import WorldDescriptionGenerator
    from app.engine.generators.faction_generator import FactionGenerator
    from app.engine.generators.magic_system_generator import MagicSystemGenerator
    from app.engine.generators.arc_generator import ArcGenerator
    from app.engine.generators.character_generator import CharacterGenerator
    from app.engine.generators.protagonist_selector import ProtagonistSelector
    from app.engine.generators.location_generator import LocationGenerator
    from app.models.text_types import TextBlock
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for story creation"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return

    # Initialize generator
    if config.generator.provider == "openrouter":
        generator = OpenRouterGenerator(
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens,
            site_url=config.generator.site_url,
            site_name=config.generator.site_name,
            auto_fallback=True
        )
    else:
        generator = OpenAIGenerator(
            api_base=config.generator.base_url,
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens
        )

    console.print(Panel(
        f"[bold cyan]Creating AI-Powered Story: {title}[/bold cyan]\n[yellow]Genre: {genre}[/yellow]",
        title="🤖 AI Story Creator",
        border_style="cyan"
    ))

    try:
        # Check if story already exists
        existing = Story.load(story_id, story_id)
        if existing:
            console.print(f"[red]Story '{story_id}' already exists![/red]")
            return
        
        # Create basic story object
        story = Story(
            id=story_id,
            story_id=story_id,
            title=title,
            description=description,
            genre=genre,
            start_segment_id="opening"
        )
        
        console.print("\n[bold yellow]⏳ Step 0: Planning story scope...[/bold yellow]")
        
        # Plan story scope before generation
        planner = StoryPlanner(generator)
        story_plan = await planner.plan_story_scope(title, description, genre)
        
        console.print(f"[green]✅ Story scope planned![/green]")
        console.print(f"[cyan]  • {story_plan['total_factions']} factions[/cyan]")
        console.print(f"[cyan]  • {story_plan['total_locations']} locations[/cyan]")
        console.print(f"[cyan]  • {story_plan['total_factions'] * ((story_plan['chars_per_faction_min'] + story_plan['chars_per_faction_max']) // 2)} characters (pool)[/cyan]")
        console.print(f"[cyan]  • {len(story_plan['major_tensions'])} major tensions[/cyan]")
        
        console.print("\n[bold yellow]⏳ Step 1: Generating living world...[/bold yellow]")
        
        # Generate world context using structured generator
        world_gen = WorldDescriptionGenerator(generator)
        world_context = await world_gen.generate_world_description(story=story, user_input=world_input)
        console.print("[green]✅ World generated![/green]")
        console.print(f"[cyan]Fundamental Truths: {len(world_context.fundamental_truths)}[/cyan]")
        
        # Build full world description string for downstream generators
        world_desc_full = ""
        if isinstance(world_context.worldbuilding, dict):
            world_desc_full = world_context.worldbuilding.get('world_description', '')
        if not world_desc_full:
            world_desc_full = '. '.join(world_context.fundamental_truths[:3])
        
        import asyncio
        
        console.print("\n[bold yellow]⏳ Steps 2-4: Generating factions, magic system, and locations (parallel)...[/bold yellow]")
        
        # Run factions, magic system, and locations in parallel
        faction_gen = FactionGenerator(story, generator)
        magic_gen = MagicSystemGenerator(story, generator)
        loc_gen = LocationGenerator(story, generator)
        
        factions_task = faction_gen.generate_factions(
            count=story_plan['total_factions'],
            world_description=world_desc_full,
            major_tensions=story_plan['major_tensions'],
            user_input=world_input
        )
        magic_task = magic_gen.generate_magic_system(
            world_description=world_desc_full,
            genre=genre,
            user_input=world_input
        )
        loc_task = loc_gen.generate_world_locations(
            world_description=world_desc_full,
            fundamental_truths=world_context.fundamental_truths,
            user_input=world_input
        )
        
        factions_result, magic_result, loc_result = await asyncio.gather(
            factions_task, magic_task, loc_task,
            return_exceptions=True
        )
        
        # Process faction results
        if isinstance(factions_result, Exception):
            console.print(f"[yellow]⚠️  Faction generation failed: {str(factions_result)[:50]}[/yellow]")
            factions = []
        else:
            factions = factions_result
            console.print(f"[green]✅ Generated {len(factions)} factions![/green]")
            for faction in factions:
                console.print(f"  • {faction.name}: {faction.description[:50]}...")
        
        # Process magic system results
        if isinstance(magic_result, Exception):
            console.print(f"[yellow]⚠️  Magic system generation failed: {str(magic_result)[:50]}[/yellow]")
            magic_system = None
        else:
            magic_system = magic_result
            if magic_system:
                console.print(f"[green]✅ Generated power system: {magic_system.name}![/green]")
                console.print(f"  [yellow]Limitations:[/yellow] {', '.join(magic_system.limitations[:2])}")
                console.print(f"  [yellow]Costs:[/yellow] {', '.join(magic_system.costs[:2])}")
            else:
                console.print(f"[green]✅ World uses no magic/tech system — mundane rules apply[/green]")
        
        # Process location results
        if isinstance(loc_result, Exception):
            console.print(f"[yellow]⚠️  Location generation failed: {str(loc_result)[:50]}[/yellow]")
            locations = []
        else:
            locations = loc_result
            console.print(f"[green]✅ Generated {len(locations)} world locations![/green]")
        
        console.print("\n[bold yellow]⏳ Steps 5-6: Generating arcs and characters (parallel)...[/bold yellow]")
        
        # Run arcs and character generation in parallel
        arc_gen = ArcGenerator(story, generator)
        arcs_task = arc_gen.generate_future_arcs(count=3, user_input=world_input)
        
        char_gen = CharacterGenerator(story, generator)
        chars_task = char_gen.generate_faction_characters(factions, story_plan)
        
        arcs_result, chars_result = await asyncio.gather(
            arcs_task, chars_task,
            return_exceptions=True
        )
        
        # Process arc results
        if isinstance(arcs_result, Exception):
            console.print(f"[yellow]⚠️  Arc generation failed: {str(arcs_result)[:50]}[/yellow]")
            arcs = []
        else:
            arcs = arcs_result
            console.print(f"[green]✅ Generated {len(arcs)} story arcs![/green]")
        
        # Process character results
        if isinstance(chars_result, Exception):
            console.print(f"[yellow]⚠️  Character generation skipped: {str(chars_result)[:50]}[/yellow]")
            characters = []
        else:
            characters = chars_result
            console.print(f"[green]✅ Generated {len(characters)} faction-aligned characters![/green]")
        
        console.print("\n[bold yellow]⏳ Step 7: Selecting protagonist...[/bold yellow]")
        
        # Select protagonist
        proto_sel = ProtagonistSelector(story, generator)
        try:
            protagonist = await proto_sel.select_or_develop_protagonist(user_choice=None)
            console.print(f"[green]✅ Protagonist selected: {protagonist.name if hasattr(protagonist, 'name') else 'Unknown'}![/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Protagonist selection skipped: {str(e)[:50]}[/yellow]")
            protagonist = None
        
        console.print("\n[bold yellow]⏳ Step 8: Creating opening scene + choices (single generation)...[/bold yellow]")
        
        # If user provided scene input, use it; otherwise AI creates something
        if first_scene_input.strip():
            scene_direction = f"User's direction: {first_scene_input}"
        else:
            scene_direction = "Create something that brings this world to life - an atmospheric, engaging scene that hooks the reader and establishes the mood of this living, breathing world."
        
        # Build rich context for opening scene
        factions_summary = '\n'.join([f"- {f.name}: {f.description[:80]}" for f in factions[:3]]) if factions else 'None yet'
        locations_summary = '\n'.join([f"- {loc.name}: {loc.description[:80]}" for loc in locations[:3]]) if locations else 'None yet'
        protagonist_name = protagonist.name if protagonist and hasattr(protagonist, 'name') else 'Unknown'
        
        # Use context_type="scene" — same pipeline as gameplay scene generation.
        # This returns a SceneTextGeneratorResponse with text_blocks, choice_1,
        # choice_2, atmosphere, etc. in one structured call.
        opening_prompt = f"""Create a CAPTIVATING opening scene for this story:

Title: {title}
Genre: {genre}
World Description: {world_desc_full}

Key Factions:
{factions_summary}

Key Locations:
{locations_summary}

Protagonist: {protagonist_name}

Scene Direction: {scene_direction}

Write an opening scene that:
- Immediately draws the reader into this LIVING world
- Establishes the atmosphere and mood
- Shows the world as a character - alive, breathing, with personality
- Hints at the story's core conflicts or mysteries
- Creates compelling story hooks that make readers want to know more
- Is vivid, atmospheric, and 2-3 paragraphs of narrative text
- Ends with two meaningful choices for the player"""
        
        from app.models.story_segment import _SCENE_SCHEMA, _SCENE_FALLBACK, _parse_text_blocks
        import asyncio as _asyncio
        
        MAX_CLI_RETRIES = 3
        scene_data = None
        
        for attempt in range(1, MAX_CLI_RETRIES + 1):
            scene_data = await generator.generate_structured(
                system_prompt="""You are a master storyteller creating immersive opening scenes.
Write with vivid sensory details that make the reader feel present in this living world.
Your opening scenes hook readers immediately and establish mood, setting, and possibility.
Always provide two compelling, distinct choices for the player at the end.""",
                user_prompt=opening_prompt,
                schema=_SCENE_SCHEMA,
                fallback_defaults=[_SCENE_FALLBACK],
            )
            
            # Detect fallback
            is_fallback = (
                scene_data.get("short_description") == _SCENE_FALLBACK["short_description"]
                or scene_data.get("text_blocks") == _SCENE_FALLBACK["text_blocks"]
            )
            
            text_blocks_raw = scene_data.get("text_blocks", [])
            has_real_content = False
            if isinstance(text_blocks_raw, list):
                for tb in text_blocks_raw:
                    content = tb.get("content", "") if isinstance(tb, dict) else str(tb)
                    if content and content not in ("The story continues...", "The story begins...", "The scene continues"):
                        has_real_content = True
                        break
            
            if not is_fallback and has_real_content:
                break
            
            raw = getattr(generator, 'last_raw_response', None) or ''
            console.print(f"[yellow]⚠️  Attempt {attempt}/{MAX_CLI_RETRIES} returned empty scene, retrying...[/yellow]")
            if raw:
                console.print(f"[dim]Raw AI response ({len(raw)} chars): {raw[:500]}...[/dim]")
            if attempt < MAX_CLI_RETRIES:
                await _asyncio.sleep(1.0)
        
        console.print("[green]✅ Opening scene generated![/green]")
        
        # Create opening segment from parsed data
        from app.models.story_segment import StorySegment
        from app.models.story_choice import StoryChoice
        import uuid
        
        first_arc_id = arcs[0].id if arcs else "arc_1"
        
        scene_text_blocks = _parse_text_blocks(scene_data.get("text_blocks", []))
        if not scene_text_blocks:
            scene_text_blocks = [TextBlock(type="narrator_describing", content="The story begins...", emotion="mysterious")]
        
        opening_segment = StorySegment(
            id="opening",
            story_id=story_id,
            story=story,
            short_description=scene_data.get("short_description") or "The Story Begins",
            atmosphere=scene_data.get("atmosphere") or "atmospheric",
            time_of_day=scene_data.get("time_of_day"),
            weather=scene_data.get("weather"),
            key_items=scene_data.get("key_items") or [],
            text_blocks=scene_text_blocks,
            characters_present=scene_data.get("characters_present") or [],
            locations_present=scene_data.get("locations_present") or [],
            episode_number=1,
            arc_id=first_arc_id,
            protagonist_id=protagonist.id if protagonist and hasattr(protagonist, 'id') else None
        )
        
        story.add_segment(opening_segment)
        
        # Create choices from structured response (new format: choices array, or fallback to choice_1/choice_2)
        choices_list = []
        choice_count = 0
        
        # Get choices from either new format (choices array) or old format (choice_1, choice_2)
        choices_data = scene_data.get("choices")
        if not choices_data:
            # Fallback to old format for compatibility
            choices_data = []
            for choice_key in ["choice_1", "choice_2"]:
                choice_text = scene_data.get(choice_key)
                if choice_text:
                    choices_data.append({"text": choice_text})
        
        # Create up to 4 choices
        for choice_item in choices_data[:4]:
            choice_text = None
            choice_tone = None
            choice_consequence = None
            
            if isinstance(choice_item, dict):
                choice_text = choice_item.get("text")
                choice_tone = choice_item.get("tone")
                choice_consequence = choice_item.get("consequence_hint")
            elif isinstance(choice_item, str):
                choice_text = choice_item
            
            if choice_text and len(str(choice_text).strip()) > 5:
                choice_count += 1
                choice_id = f"choice_{choice_count}_{uuid.uuid4().hex[:8]}"
                choice = StoryChoice(
                    story=story,
                    id=choice_id,
                    from_segment_id="opening",
                    to_segment_id=None,
                    text=str(choice_text).strip(),
                    tone=choice_tone,
                    consequence_hint=choice_consequence,
                )
                opening_segment.add_outgoing_choice(choice)
                story.add_choice(choice)
                choices_list.append(choice)
        
        console.print(f"[green]✅ Generated {len(choices_list)} choices for opening scene![/green]")
        
        # Set start segment
        story.start_segment_id = "opening"
        
        # Update first arc to point to opening segment
        if arcs:
            arcs[0].start_segment_id = "opening"
            arcs[0].current_segment_id = "opening"
        
        # Save everything
        console.print("\n[bold yellow]💾 Saving story to disk...[/bold yellow]")
        
        story.save()
        world_context.save()
        for faction in factions:
            faction.save()
        if magic_system:
            magic_system.save()
        for location in locations:
            location.save()
        for arc in arcs:
            arc.save()
        for char in characters:
            char.save()
        if protagonist:
            protagonist.save()
        opening_segment.save()
        for choice in choices_list:
            choice.save()
        
        # Build faction list safely
        faction_list = "\n".join([f"  • {f.name}" for f in factions[:3]]) if factions else "  • Unknown"
        
        # Build success message
        success_msg = f"""[green]✅ AI-Powered Story Created Successfully![/green]

Story: {title}
ID: {story_id}
Genre: {genre}

[green]Generated:[/green]
• {len(world_context.fundamental_truths)} World Truths
• {len(factions)} Factions
• {len(locations)} Locations
• {len(arcs)} Story Arcs
• {len(characters)} Characters
• Protagonist: {protagonist.name if protagonist and hasattr(protagonist, 'name') else 'TBD'}
• {len(choices_list)} Opening Choices

[yellow]Next:[/yellow] ./run.sh {story_id}"""
        
        console.print(Panel(
            success_msg,
            title="Success!",
            border_style="green"
        ))
        
        logger.info(f"AI story created: {story_id}")
        
    except Exception as e:
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        console.print(f"[red]Error creating story: {error_msg}[/red]")
        logger.error(f"Story creation failed: {e}", exc_info=True)

@app.command()
def create_story_ai(
    story_id: str = typer.Argument(..., help="Unique identifier for the story"),
    title: str = typer.Option(..., "--title", help="Display title of the story"),
    description: str = typer.Option(..., "--description", help="Long description of the story"),
    genre: str = typer.Option("Unknown", "--genre", help="Genre (e.g., Fantasy, Sci-Fi, Mystery)"),
    world_input: str = typer.Option("", "--world", help="Optional: Your world vision (AI will expand if empty)"),
    first_scene_input: str = typer.Option("", "--scene", help="Optional: Opening scene direction (AI will create if empty)")
):
    """Create a story with AI-powered world and opening scene generation.
    
    The AI will:
    - Generate a LIVING WORLD if you don't provide world details
    - Create a captivating OPENING SCENE
    - Use your input to guide creative generation
    
    Example (with AI generation):
        python -m app.cli create-story-ai my_story \\
            --title "The Last Explorer" \\
            --description "A journey through forgotten lands" \\
            --genre "Adventure"
    
    Example (with user guidance):
        python -m app.cli create-story-ai my_story \\
            --title "The Last Explorer" \\
            --description "A journey through forgotten lands" \\
            --genre "Adventure" \\
            --world "A world where technology and nature merged" \\
            --scene "Start in an ancient ruins discovery"
    """
    asyncio.run(create_story_ai_async(story_id, title, description, genre, world_input, first_scene_input))

@app.command()
def list_stories():
    """List all available stories."""
    story_ids = Story.list_stories()
    if not story_ids:
        console.print("[yellow]No stories found.[/yellow]")
        return
    
    stories = []
    for story_id in story_ids:
        story = Story.load(story_id, story_id)
        if story:
            stories.append({
                "id": story.id,
                "title": story.title,
                "genre": story.genre,
                "description": story.description
            })
    
    if stories:
        display_stories(stories)
    else:
        console.print("[yellow]No stories could be loaded.[/yellow]")

@app.command()
def delete_story(story_id: str = typer.Argument(..., help="Story ID to delete")):
    """Delete a story and all associated data."""
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    confirm = typer.confirm(
        f"Delete '{story.title}' and all segments? This cannot be undone."
    )
    if confirm:
        try:
            story.delete()
            console.print(f"[green]✅ Story '{story_id}' deleted[/green]")
            logger.info(f"Story deleted: {story_id}")
        except Exception as e:
            console.print(f"[red]Error deleting story: {e}[/red]")
            logger.error(f"Failed to delete story {story_id}: {e}")
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")

@app.command()
def clear_state(story_id: str = typer.Argument(..., help="Story ID to reset")):
    """Reset a story's session to start (keeps segments, clears session state)."""
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    runner = StoryRunner(story)
    runner.clear_state()
    console.print(f"[green]✅ Session cleared for '{story_id}'[/green]")
    logger.info(f"State cleared for story: {story_id}")

async def _initialize_generator(config: Config, quiet: bool = False):
    """Initialize and return generator based on config."""
    logger.debug(f"[INIT_GEN_START] Initializing generator with provider: {config.generator.provider}")
    if config.generator.provider == "openrouter":
        logger.info(f"Initializing OpenRouter generator with model: {config.generator.model}")
        generator = OpenRouterGenerator(
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens,
            site_url=config.generator.site_url,
            site_name=config.generator.site_name,
            auto_fallback=True
        )
        if not quiet:
            console.print(f"[cyan]Using OpenRouter with model: {generator.model}[/cyan]")
    else:  # openai
        logger.info(f"Initializing OpenAI generator with model: {config.generator.model}")
        generator = OpenAIGenerator(
            api_base=config.generator.base_url,
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens
        )
        if not quiet:
            console.print(f"[cyan]Using OpenAI with model: {config.generator.model}[/cyan]")
    return generator

async def _run_story(runner: StoryRunner, generator, auto_pick: Optional[int] = None, dump: Optional[str] = None, dump_context: bool = False):
    """Run story in unified interactive mode.

    Displays the segment text, then presents a menu:
      [1-N] Pick a choice
      [L]   Toggle logs     [I] View segment info    [P] View AI prompt    [J] Raw JSON
      [U]   Go up (parent)  [D] Go down (child)      [T] Story tree view

    If dump is set ("info", "prompt", or "all"), auto-picks through scenes
    then prints the requested debug output and exits (no interaction).
    
    If dump_context is True, print the full context dict as JSON and exit.
    """
    from app.ui.story_debug_display import (
        display_segment,
        prompt_menu,
        toggle_logs,
        show_segment_info,
        show_prompt,
        show_raw_json,
        show_tree,
        prompt_down_choice,
        display_generation_result,
        show_segment_info_noninteractive,
        show_prompt_noninteractive,
    )
    from app.engine.segment_context_builder import SegmentContextBuilder

    auto_remaining = auto_pick  # None = interactive, 0 = unlimited, N = N picks left

    # ── Dump context: auto-pick N scenes, print context dict as JSON, exit ──
    if dump_context:
        # Auto-pick through scenes first (if auto_pick given)
        picks_to_do = auto_pick if auto_pick and auto_pick > 0 else 0
        for _ in range(picks_to_do):
            if not runner.current_segment:
                break
            choices = runner.get_available_choices()
            if not choices:
                break
            try:
                await _execute_choice(runner, choices[0].id, generator)
            except Exception as e:
                console.print(f"[red]Error during auto-pick: {e}[/red]")
                return
            runner.save_state()

        if not runner.current_segment:
            console.print("[red]No current segment[/red]")
            return

        # Build context for current segment
        context = None
        choices = runner.get_available_choices()
        try:
            context_builder = SegmentContextBuilder(runner.story)
            context = await context_builder.build_context(
                runner.current_segment.id,
                choices[0].text if choices else "unknown"
            )
        except Exception as e:
            logger.warning(f"Could not build context: {e}")
            console.print(f"[red]Context build failed: {e}[/red]", file=sys.stderr)
            context = {}

        # Dump full context as JSON
        import json
        console.print(json.dumps(context, indent=2, default=str))
        return

    # ── Dump mode: auto-pick N scenes, print debug, exit ──
    if dump:
        # Auto-pick through scenes first (if auto_pick given)
        picks_to_do = auto_pick if auto_pick and auto_pick > 0 else 0
        for _ in range(picks_to_do):
            if not runner.current_segment:
                break
            choices = runner.get_available_choices()
            if not choices:
                break
            try:
                await _execute_choice(runner, choices[0].id, generator)
            except Exception as e:
                console.print(f"[red]Error during auto-pick: {e}[/red]")
                return
            runner.save_state()

        if not runner.current_segment:
            console.print("[red]No current segment[/red]")
            return

        # Build context for current segment
        context = None
        choices = runner.get_available_choices()
        try:
            context_builder = SegmentContextBuilder(runner.story)
            context = await context_builder.build_context(
                runner.current_segment.id,
                choices[0].text if choices else "unknown"
            )
        except Exception as e:
            logger.warning(f"Could not build context: {e}")
            console.print(f"[red]Context build failed: {e}[/red]", file=sys.stderr)

        # Print requested dump
        dump_lower = dump.lower()
        if dump_lower in ("info", "all"):
            show_segment_info_noninteractive(runner.current_segment, context)
        if dump_lower in ("prompt", "all"):
            show_prompt_noninteractive(context)
        if dump_lower not in ("info", "prompt", "all"):
            console.print(f"[red]Unknown dump type: {dump}. Use info, prompt, or all.[/red]")
        return

    # ── Normal interactive mode ──
    try:
        while runner.current_segment is not None:

            # Build context (used by Info and Prompt views)
            context = None
            choices = runner.get_available_choices()
            try:
                context_builder = SegmentContextBuilder(runner.story)
                context = await context_builder.build_context(
                    runner.current_segment.id,
                    choices[0].text if choices else "unknown"
                )
            except Exception as e:
                logger.warning(f"Could not build context: {e}")
                console.print(f"[dim red]Context build failed: {e}[/dim red]")

            # Display the segment
            display_segment(runner.current_segment)

            if not choices:
                # Dead end — but user can still navigate up/view tree
                has_parent = bool(runner.current_segment.parent_segment_id or runner.current_segment.incoming_choices)
                if not has_parent:
                    console.print("[yellow]No choices and no parent. Story ended.[/yellow]")
                    break
                console.print("[yellow]No choices here (leaf node). Use [bold]U[/bold] to go up or [bold]T[/bold] for tree.[/yellow]")
                while True:
                    raw = Prompt.ask("[bold]>").strip().lower()
                    if raw == "u":
                        prev = runner.navigate_up()
                        if prev:
                            runner.save_state()
                            break
                        else:
                            console.print("[yellow]No parent segment.[/yellow]")
                    elif raw == "t":
                        from app.ui.story_debug_display import show_tree
                        show_tree(runner)
                        display_segment(runner.current_segment)
                    elif raw == "j":
                        show_raw_json(runner.current_segment)
                        display_segment(runner.current_segment)
                    elif raw == "i":
                        show_segment_info(runner.current_segment, context)
                        display_segment(runner.current_segment)
                    else:
                        console.print("[red]Enter U (up), T (tree), I (info), or J (json)[/red]")
                continue

            # Auto-pick path
            choice_id = None
            navigated = False
            
            if auto_remaining is not None and (auto_remaining == 0 or auto_remaining > 0):
                choice_id = choices[0].id
                seg = runner.current_segment
                ep = getattr(seg, 'episode_number', '?')
                seg_num = getattr(seg, 'segment_number_in_episode', '?')
                desc = getattr(seg, 'short_description', '') or ''
                preview = f"[dim]Ep {ep} Seg {seg_num}[/dim]"
                if desc:
                    preview += f" [dim italic]{desc[:80]}[/dim italic]"
                console.print(preview)
                console.print(f"[bold magenta]  [AUTO-PICK {auto_remaining if auto_remaining > 0 else '∞'}] {choices[0].text[:80]}[/bold magenta]")
                if auto_remaining > 0:
                    auto_remaining -= 1
                    if auto_remaining == 0:
                        auto_remaining = None  # switch to interactive
            else:
                # Interactive menu loop
                while True:
                    result = prompt_menu(runner.current_segment, choices, context, story=runner.story, runner=runner)

                    if result == "CMD_LOGS":
                        toggle_logs()
                        continue
                    if result == "CMD_INFO":
                        show_segment_info(runner.current_segment, context)
                        display_segment(runner.current_segment)
                        continue
                    if result == "CMD_PROMPT":
                        show_prompt(context)
                        display_segment(runner.current_segment)
                        continue
                    if result == "CMD_JSON":
                        show_raw_json(runner.current_segment)
                        display_segment(runner.current_segment)
                        continue
                    if result == "CMD_UP":
                        prev = runner.navigate_up()
                        if prev:
                            runner.save_state()
                            navigated = True
                            break
                        else:
                            console.print("[yellow]Already at root — no parent segment.[/yellow]")
                            continue
                    if result == "CMD_DOWN":
                        idx = prompt_down_choice(runner)
                        if idx is not None:
                            runner.navigate_down(idx)
                            runner.save_state()
                            navigated = True
                            break
                        display_segment(runner.current_segment)
                        continue
                    if result == "CMD_TREE":
                        show_tree(runner)
                        display_segment(runner.current_segment)
                        continue
                    # Otherwise it's a choice id
                    choice_id = result
                    break

            # If we navigated up/down, skip choice execution and loop back
            if navigated:
                continue

            # Execute the choice
            try:
                await _execute_choice(runner, choice_id, generator)
            except Exception as e:
                error_type, technical_msg = handle_api_error(e)
                message, suggestion = ErrorHandler.handle_error(
                    error_type, e, "Processing your choice"
                )
                console.print(f"[red]Error: {message}[/red]")
                console.print(f"[yellow]Suggestion:[/yellow]\n{suggestion}")
                continue

            # Brief generation result
            if runner.current_segment:
                display_generation_result(runner.current_segment)

            runner.save_state()

    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")


async def _execute_choice(runner: StoryRunner, choice_id: str, generator):
    """Execute a choice and advance the story."""
    logger.debug(f"Executing choice: {choice_id}")
    choice = runner.story.get_choice(choice_id)
    if not choice:
        console.print(f"[red]Choice '{choice_id}' not found[/red]")
        return

    if choice.to_segment_id:
        runner.make_choice(choice_id)
        logger.debug(f"Navigated to segment: {runner.current_segment.id}")
    else:
        console.print("[bold yellow]Generating next scene...[/bold yellow]")
        import time as _time
        t0 = _time.monotonic()
        try:
            new_segment = await runner.current_segment.generate_next_scene(choice, generator)
            elapsed = _time.monotonic() - t0
            runner.current_segment = new_segment
            runner.visited_segments.add(new_segment.id)
            console.print(f"[green]Scene generated in {elapsed:.1f}s[/green]")
        except Exception as e:
            elapsed = _time.monotonic() - t0
            logger.error(f"Generation failed after {elapsed:.1f}s: {str(e)}", exc_info=True)
            console.print(f"[red]Generation failed after {elapsed:.1f}s: {str(e)}[/red]")
            raise

async def run_story_async(story_name: str = None, resume: bool = False, log_level: str = "error", auto_pick: Optional[int] = None, dump: Optional[str] = None, dump_context: bool = False, start_from: Optional[str] = None, deterministic: bool = False, no_color: bool = False):
    """Run a story in the unified interactive mode.
    
    Args:
        story_name: Optional story ID to run directly (skips selection)
        resume: Resume from previous session if available
        log_level: error (default), warn, or debug
        auto_pick: If set, auto-select choice 1 for N turns (0 = unlimited)
        dump: If set, non-interactive mode. "info", "prompt", or "all"
        dump_context: If True, dump full context dict as JSON and exit
        start_from: If set, jump directly to this segment ID instead of start/resume
        deterministic: If True, don't shuffle choices (stable order for reproducible runs)
        no_color: If True, disable Rich color/markup for piped output
    """

    if no_color:
        global console
        console = Console(force_terminal=False, no_color=True, highlight=False)

    # Load configuration (this calls Config.setup_logging() internally)
    try:
        config = Config.load()
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG, e, "Loading configuration for story"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return

    # Apply CLI log level AFTER Config.load() so --log-level takes precedence over .env
    if dump:
        logging.disable(logging.CRITICAL)
    elif log_level:
        setup_logging(log_level)

    # Initialize generator (only needed if dump will auto-pick through generated scenes)
    generator = None
    needs_generator = not dump or (auto_pick and auto_pick > 0)
    if needs_generator:
        try:
            generator = await _initialize_generator(config, quiet=bool(dump))
        except Exception as e:
            console.print(f"[red]Failed to initialize generator: {e}[/red]")
            return

    # Get story selection
    if story_name:
        selected_story = {
            "id": story_name,
            "title": story_name,
            "genre": "Unknown",
            "description": "Story"
        }
    else:
        story_ids = Story.list_stories()
        stories = []
        for story_id in story_ids:
            story = Story.load(story_id, story_id)
            if story:
                stories.append({
                    "id": story.id,
                    "title": story.title,
                    "genre": story.genre,
                    "description": story.description
                })
        display_stories(stories)

        selected_story = select_story(stories)
        if not selected_story:
            return

    if not dump:
        console.print(Panel(
            f"[green]{selected_story.get('title', 'Untitled')}[/green]",
            title="Story Runner",
            border_style="green"
        ))

    # Load story
    story = Story.load(selected_story["id"], selected_story["id"])
    if not story:
        console.print("[red]Failed to load story![/red]")
        return

    runner = StoryRunner(story, deterministic=deterministic)
    
    try:
        runner.load_all_components(story)
        
        if start_from:
            try:
                runner.start_from_segment(start_from)
                if not dump:
                    console.print(f"[yellow]Jumped to segment: {runner.current_segment.short_description}[/yellow]")
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                return
        elif resume and runner.load_state():
            if not dump:
                console.print(f"[yellow]Resumed at: {runner.current_segment.short_description}[/yellow]")
        else:
            runner.start()
            if not dump:
                console.print("[green]Story started.[/green]")
        
        await _run_story(runner, generator, auto_pick=auto_pick, dump=dump, dump_context=dump_context)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

@app.command()
def run_story(
    story: str = typer.Argument(None, help="Optional story ID to run directly"),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume from previous session if available"
    ),
    log_level: str = typer.Option(
        "error",
        "--log-level",
        help="Logging level: error (default), warn, debug"
    ),
    auto_pick: Optional[int] = typer.Option(
        None,
        "--auto-pick",
        help="Auto-select choice 1 for N turns, then switch to interactive. Use 0 for unlimited auto-pick."
    ),
    dump: Optional[str] = typer.Option(
        None,
        "--dump",
        help="Non-interactive: auto-pick N scenes then dump debug info and exit. Values: info, prompt, all"
    ),
    dump_context: bool = typer.Option(
        False,
        "--dump-context",
        help="Non-interactive: auto-pick N scenes then dump full context dict as JSON and exit"
    ),
    start_from: Optional[str] = typer.Option(
        None,
        "--start-from",
        help="Jump directly to a specific segment ID (skips start/resume)"
    ),
    deterministic: bool = typer.Option(
        False,
        "--deterministic",
        help="Don't shuffle choices — stable order for reproducible auto-pick runs"
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colors/markup — clean output for piping to files"
    ),
):
    """Run a story in the interactive view.
    
    Shows the story text with an interactive menu:
      [1-N] Pick a choice     [L] Toggle logs     [I] Segment info     [P] View prompt
      [U] Go up (parent)      [D] Go down (child) [T] Story tree        [J] Raw JSON
    
    Non-interactive dump (for scripting/debugging):
      --dump info           Print segment info after N auto-picks, then exit
      --dump prompt         Print the AI prompt after N auto-picks, then exit
      --dump all            Print both
      --dump-context        Print full context dict as JSON after N auto-picks, then exit
    
    Examples:
      python -m app.cli run-story my_story
      python -m app.cli run-story my_story --resume
      python -m app.cli run-story my_story --start-from seg_abc123
      python -m app.cli run-story my_story --auto-pick 5 --dump info
      python -m app.cli run-story my_story --auto-pick 0 --dump prompt
      python -m app.cli run-story my_story --dump all
      python -m app.cli run-story my_story --auto-pick 2 --dump-context    # dump context dict
    """
    asyncio.run(run_story_async(story_name=story, resume=resume, log_level=log_level, auto_pick=auto_pick, dump=dump, dump_context=dump_context, start_from=start_from, deterministic=deterministic, no_color=no_color))

@app.command()
def list_models(
    provider: str = typer.Option(
        None,
        help="Provider to list models for (openrouter or openai). Leave empty to see all."
    ),
    use_case: str = typer.Option(
        None,
        help="Get recommendations for a use case (story, speed, quality, budget)"
    )
):
    """List available AI models and get recommendations."""
    if use_case:
        # Show recommendations
        recommendations = get_model_recommendations(use_case)
        console.print(f"\n[bold cyan]Recommended models for '{use_case}':[/bold cyan]")
        for model_name, reason in recommendations:
            console.print(f"  • [green]{model_name}[/green] - {reason}")
        return
    
    if provider:
        # Show models for specific provider
        provider = provider.lower()
        if provider not in ["openrouter", "openai"]:
            console.print(f"[red]Invalid provider '{provider}'. Must be 'openrouter' or 'openai'.[/red]")
            return
        console.print(format_model_list(provider))
    else:
        # Show all models and recommendations
        console.print("\n[bold cyan]=== Available AI Models ===[/bold cyan]")
        console.print(format_model_list("openrouter"))
        console.print(format_model_list("openai"))
        
        console.print("\n[bold cyan]=== Recommended Models by Use Case ===[/bold cyan]")
        for use_case in ["story", "speed", "quality", "budget"]:
            recommendations = get_model_recommendations(use_case)
            console.print(f"\n[yellow]{use_case.upper()}:[/yellow]")
            for model_name, reason in recommendations:
                console.print(f"  • {model_name} - {reason}")
        
        console.print("\n[bold cyan]=== Configuration ===[/bold cyan]")
        console.print("Set your preferred model in .env file:")
        console.print("  AI_PROVIDER=openrouter")
        console.print("  AI_MODEL=deepseek-v3  # Or any other model")

async def create_story_step_by_step_async(
    story_id: str,
    title: str,
    description: str,
    genre: str,
    step: Optional[int] = None,
    skip: Optional[int] = None,
    reset: Optional[int] = None,
    show_status: bool = False
):
    """Create story step-by-step with ability to skip and retry broken steps."""
    from app.engine.step_generation_manager import StepGenerationManager
    from app.engine.generators.story_planner import StoryPlanner
    from app.engine.generators.world_description_generator import WorldDescriptionGenerator
    from app.engine.generators.faction_generator import FactionGenerator
    from app.engine.generators.magic_system_generator import MagicSystemGenerator
    from app.engine.generators.location_generator import LocationGenerator
    from app.engine.generators.arc_generator import ArcGenerator
    from app.engine.generators.character_generator import CharacterGenerator
    from app.engine.generators.protagonist_selector import ProtagonistSelector
    from app.models.text_types import TextBlock
    from app.models.story_segment import StorySegment
    from app.models.story_choice import StoryChoice
    import uuid
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return
    
    # Initialize generator
    if config.generator.provider == "openrouter":
        generator = OpenRouterGenerator(
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens,
            site_url=config.generator.site_url,
            site_name=config.generator.site_name,
            auto_fallback=True
        )
    else:
        generator = OpenAIGenerator(
            api_base=config.generator.base_url,
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens
        )
    
    # Load or create story
    story = Story.load(story_id, story_id)
    if not story:
        story = Story(
            id=story_id,
            story_id=story_id,
            title=title,
            description=description,
            genre=genre,
            start_segment_id="opening"
        )
    
    # Initialize step manager
    step_manager = StepGenerationManager(story, generator)
    
    # Handle reset request
    if reset is not None:
        if reset < 0 or reset > 9:
            console.print(f"[red]Invalid step number: {reset}[/red]")
            return
        step_manager.reset_step(reset, delete_outputs=True)
        console.print(f"[yellow]Reset step {reset}. Downstream steps marked for rerun.[/yellow]")
        return
    
    # Handle skip request
    if skip is not None:
        if skip < 0 or skip > 9:
            console.print(f"[red]Invalid step number: {skip}[/red]")
            return
        if not step_manager._can_run_step(skip):
            missing = step_manager._get_missing_dependencies(skip)
            console.print(f"[red]Cannot skip step {skip}: missing dependencies: {missing}[/red]")
            return
        step_manager.mark_step_skipped(skip)
        console.print(f"[yellow]Skipped step {skip}. Downstream steps marked for rerun.[/yellow]")
        return
    
    # Show status if requested
    if show_status:
        status = step_manager.get_all_steps_status()
        summary = step_manager.get_step_summary()
        
        # Create rich status panel
        status_table = Table(title="Story Generation Pipeline", show_header=True)
        status_table.add_column("Step", style="cyan", width=6)
        status_table.add_column("Name", style="white")
        status_table.add_column("Status", style="yellow")
        status_table.add_column("Info", style="dim")
        
        for i in range(10):
            s = status[i]
            
            # Icon and status
            if s["status"] == "completed":
                icon = "✅"
                status_text = "[green]Completed[/green]"
            elif s["status"] == "skipped":
                icon = "⏭️"
                status_text = "[yellow]Skipped[/yellow]"
            elif s["status"] == "failed":
                icon = "❌"
                status_text = "[red]Failed[/red]"
            elif s["can_run"]:
                icon = "⏳"
                status_text = "[cyan]Ready[/cyan]"
            else:
                icon = "🔒"
                status_text = "[dim]Blocked[/dim]"
            
            # Info column
            info = ""
            if s["status"] == "failed" and s.get("error_message"):
                info = f"Error: {s['error_message'][:40]}"
            elif s["missing_deps"]:
                dep_names = [f"Step {d}" for d in s["missing_deps"]]
                info = f"Needs: {', '.join(dep_names)}"
            elif s["status"] == "completed" and s.get("completed_at"):
                info = "✓ Done"
            
            status_table.add_row(f"{icon} {i}", s['name'], status_text, info)
        
        console.print(Panel(
            f"[bold cyan]Overall Progress[/bold cyan]: {summary['progress']}\n"
            f"[bold cyan]Status[/bold cyan]: {summary['overall_status']}",
            title="Generation Summary",
            border_style="cyan"
        ))
        console.print(status_table)
        console.print("\n[dim]Next step to run:[/dim] ", end="")
        next_step = step_manager.get_next_runnable_step()
        if next_step is not None:
            console.print(f"[bold cyan]Step {next_step}: {step_manager.steps[next_step].name}[/bold cyan]")
        else:
            console.print("[green]All steps completed! ✨[/green]")
        
        return
    
    # Run specified step or next runnable step
    if step is not None:
        if step < 0 or step > 9:
            console.print(f"[red]Invalid step number: {step}[/red]")
            return
        if not step_manager._can_run_step(step):
            missing = step_manager._get_missing_dependencies(step)
            console.print(f"[red]Cannot run step {step}: missing dependencies: {missing}[/red]")
            return
        target_step = step
    else:
        target_step = step_manager.get_next_runnable_step()
        if target_step is None:
            summary = step_manager.get_step_summary()
            console.print(Panel(
                f"All steps completed!\nProgress: {summary['progress']}",
                title="Generation Complete",
                border_style="green"
            ))
            return
    
    console.print(Panel(
        f"[bold cyan]{step_manager.steps[target_step].name}[/bold cyan]\n{step_manager.steps[target_step].description}",
        title=f"Step {target_step}",
        border_style="yellow"
    ))
    
    try:
        # Execute the appropriate step
        if target_step == 0:
            console.print("[bold yellow]⏳ Planning story scope...[/bold yellow]")
            planner = StoryPlanner(generator)
            plan = await planner.plan_story_scope(title, description, genre)
            step_manager.mark_step_completed(target_step, plan)
            console.print(f"[green]✅ Step 0 complete! Factions: {plan.get('total_factions', '?')}, Locations: {plan.get('total_locations', '?')}[/green]")
        
        elif target_step == 1:
            world_gen = WorldDescriptionGenerator(generator)
            world_context = await world_gen.generate_world_description(story=story)
            step_manager.mark_step_completed(target_step, {"truths": len(world_context.fundamental_truths)})
            console.print(f"[green]✅ Step 1 complete! Generated {len(world_context.fundamental_truths)} fundamental truths[/green]")
        
        elif target_step == 2:
            plan = None  # Would need to load from previous step
            faction_gen = FactionGenerator(story, generator)
            factions = await faction_gen.generate_factions(3, "", [], "")
            step_manager.mark_step_completed(target_step, {"count": len(factions)})
            console.print(f"[green]✅ Step 2 complete! Generated {len(factions)} factions[/green]")
        
        elif target_step == 3:
            magic_gen = MagicSystemGenerator(story, generator)
            magic_system = await magic_gen.generate_magic_system("", genre, "")
            if magic_system:
                step_manager.mark_step_completed(target_step, {"name": magic_system.name})
                console.print(f"[green]✅ Step 3 complete! Power system: {magic_system.name}[/green]")
            else:
                step_manager.mark_step_completed(target_step, {"name": "none"})
                console.print(f"[green]✅ Step 3 complete! No power system needed[/green]")
        
        elif target_step == 4:
            loc_gen = LocationGenerator(story, generator)
            locations = await loc_gen.generate_world_locations("", [], "")
            step_manager.mark_step_completed(target_step, {"count": len(locations)})
            console.print(f"[green]✅ Step 4 complete! Generated {len(locations)} locations[/green]")
        
        elif target_step == 5:
            arc_gen = ArcGenerator(story, generator)
            arcs = await arc_gen.generate_future_arcs(count=3)
            step_manager.mark_step_completed(target_step, {"count": len(arcs)})
            console.print(f"[green]✅ Step 5 complete! Generated {len(arcs)} arcs[/green]")
        
        elif target_step == 6:
            char_gen = CharacterGenerator(story, generator)
            characters = await char_gen.generate_faction_characters([])  # Would need loaded factions
            step_manager.mark_step_completed(target_step, {"count": len(characters)})
            console.print(f"[green]✅ Step 6 complete! Generated {len(characters)} characters[/green]")
        
        elif target_step == 7:
            proto_sel = ProtagonistSelector(story, generator)
            protagonist = await proto_sel.select_or_develop_protagonist()
            step_manager.mark_step_completed(target_step, {"name": getattr(protagonist, 'name', 'Unknown')})
            console.print(f"[green]✅ Step 7 complete! Protagonist: {getattr(protagonist, 'name', 'Unknown')}[/green]")
        
        elif target_step == 8:
            console.print("[yellow]Opening scene generation (Step 8) - implement as needed[/yellow]")
            step_manager.mark_step_skipped(target_step)
        
        elif target_step == 9:
            console.print("[yellow]Choice generation (Step 9) - implement as needed[/yellow]")
            step_manager.mark_step_skipped(target_step)
        
        console.print(f"\n[yellow]Next runnable step: {step_manager.get_next_runnable_step() or 'None (complete)'}[/yellow]")
        
    except Exception as e:
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        step_manager.mark_step_failed(target_step, str(e))
        console.print(f"[red]Step {target_step} failed: {error_msg}[/red]")
        console.print(f"[yellow]To retry, run: create-story-step story_id --step {target_step}[/yellow]")
        console.print(f"[yellow]To skip, run: create-story-step story_id --skip {target_step}[/yellow]")
        logger.error(f"Step {target_step} failed: {e}", exc_info=True)

@app.command()
def create_story_step(
    story_id: str = typer.Argument(..., help="Story ID"),
    step: Optional[int] = typer.Option(None, "--step", help="Run specific step (0-9)"),
    skip: Optional[int] = typer.Option(None, "--skip", help="Skip a step"),
    reset: Optional[int] = typer.Option(None, "--reset", help="Reset a step to pending"),
    status: bool = typer.Option(False, "--status", help="Show generation status"),
    title: str = typer.Option("Untitled", "--title", help="Story title"),
    description: str = typer.Option("", "--description", help="Story description"),
    genre: str = typer.Option("Unknown", "--genre", help="Story genre"),
):
    """Create story step-by-step with ability to skip broken steps and rerun.
    
    Examples:
        # Show status of all steps
        python -m app.cli create-story-step my_story --status
        
        # Run next available step
        python -m app.cli create-story-step my_story
        
        # Run specific step
        python -m app.cli create-story-step my_story --step 2
        
        # Skip a broken step
        python -m app.cli create-story-step my_story --skip 4
        
        # Reset a step and rerun
        python -m app.cli create-story-step my_story --reset 3
        python -m app.cli create-story-step my_story --step 3
    """
    asyncio.run(create_story_step_by_step_async(
        story_id, title, description, genre, step, skip, reset, status
    ))

@app.command()
def inspect_story(
    story_id: str = typer.Argument(..., help="Story ID to inspect"),
    component: str = typer.Option(
        None, "--component", "-c",
        help="Inspect specific component type: arcs, episodes, segments, characters, locations, factions, magic, choices, context"
    ),
    detail: str = typer.Option(
        None, "--detail", "-d",
        help="Show full detail for a specific component ID"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON"
    ),
):
    """Inspect story state: arcs, episodes, segments, factions, magic systems, etc.
    
    Examples:
        # Overview of everything
        python -m app.cli inspect-story my_story
        
        # Inspect specific component type
        python -m app.cli inspect-story my_story -c arcs
        python -m app.cli inspect-story my_story -c factions
        
        # Full detail for a specific component
        python -m app.cli inspect-story my_story -d opening
        python -m app.cli inspect-story my_story -c arcs -d arc_my_story_abc123
        
        # Raw JSON output
        python -m app.cli inspect-story my_story -c arcs --json
    """
    import json as json_mod
    from app.models.story_arc import StoryArc
    from app.models.story_episode import StoryEpisode
    from app.models.story_segment import StorySegment
    from app.models.story_character import StoryCharacter
    from app.models.story_location import StoryLocation
    from app.models.story_context import StoryContext
    from app.models.story_faction import StoryFaction
    from app.models.story_magic_system import StoryMagicSystem
    from app.models.story_choice import StoryChoice
    
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Component type -> model class mapping
    component_map = {
        'arcs': StoryArc,
        'arc': StoryArc,
        'episodes': StoryEpisode,
        'episode': StoryEpisode,
        'segments': StorySegment,
        'segment': StorySegment,
        'characters': StoryCharacter,
        'character': StoryCharacter,
        'locations': StoryLocation,
        'location': StoryLocation,
        'factions': StoryFaction,
        'faction': StoryFaction,
        'magic': StoryMagicSystem,
        'magic_systems': StoryMagicSystem,
        'choices': StoryChoice,
        'choice': StoryChoice,
        'context': StoryContext,
    }
    
    # StoryBlock subclasses require a story object to load
    from app.models.story_block import StoryBlock
    _needs_story = {
        StorySegment, StoryChoice, StoryCharacter, StoryLocation,
        StoryFaction, StoryMagicSystem, StoryEpisode,
    }
    
    def _load_all(cls):
        """Load all instances of a component type."""
        ids = cls.list_all(story_id)
        items = []
        for cid in ids:
            try:
                if cls in _needs_story:
                    item = cls.load(story_id, cid, story=story)
                else:
                    item = cls.load(story_id, cid)
                if item:
                    items.append(item)
            except Exception as e:
                items.append({"id": cid, "error": str(e)})
        return items
    
    def _print_item_summary(item, cls_name: str):
        """Print a one-line summary of an item."""
        if isinstance(item, dict):
            console.print(f"  [red]{item['id']}: ERROR {item['error']}[/red]")
            return
        
        label = f"[cyan]{item.id}[/cyan]"
        
        if hasattr(item, 'title'):
            title_text = item.title[:60] + "..." if len(item.title) > 60 else item.title
            label += f" | {title_text}"
        if hasattr(item, 'name') and not hasattr(item, 'title'):
            label += f" | {item.name}"
        if hasattr(item, 'is_active'):
            label += f" | active={item.is_active}"
        if hasattr(item, 'is_future_arc'):
            label += f" | future={item.is_future_arc}"
        if hasattr(item, 'short_description') and item.short_description:
            label += f" | {item.short_description[:50]}"
        if hasattr(item, 'text') and item.text:
            label += f" | {item.text[:60]}"
        if hasattr(item, 'description') and item.description and not hasattr(item, 'title'):
            label += f" | {item.description[:50]}"
        if hasattr(item, 'arc_id') and item.arc_id:
            label += f" | arc={item.arc_id}"
        if hasattr(item, 'episode_number') and item.episode_number:
            label += f" | ep={item.episode_number}"
        if hasattr(item, 'from_segment_id'):
            label += f" | {item.from_segment_id} -> {item.to_segment_id or '???'}"
        
        console.print(f"  {label}")
    
    def _print_item_detail(item):
        """Print full detail of an item as formatted JSON."""
        if isinstance(item, dict):
            console.print(json_mod.dumps(item, indent=2, default=str))
            return
        data = item.model_dump()
        if json_output:
            console.print(json_mod.dumps(data, indent=2, default=str))
        else:
            for key, value in data.items():
                if value is None or value == "" or value == [] or value == {}:
                    continue
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + "..."
                console.print(f"  [cyan]{key}[/cyan]: {value}")
    
    def _load_one(cls, component_id):
        """Load a single instance, passing story if needed."""
        try:
            if cls in _needs_story:
                return cls.load(story_id, component_id, story=story)
            else:
                return cls.load(story_id, component_id)
        except Exception:
            return None
    
    # If a specific detail ID is requested with a component type
    if detail and component:
        cls = component_map.get(component)
        if not cls:
            console.print(f"[red]Unknown component type: {component}[/red]")
            return
        item = _load_one(cls, detail)
        if not item:
            console.print(f"[red]{component} '{detail}' not found[/red]")
            return
        console.print(Panel(f"[bold]{cls.__name__}: {detail}[/bold]", border_style="cyan"))
        _print_item_detail(item)
        return
    
    # If detail requested without component, try all types
    if detail:
        for cname, cls in component_map.items():
            if cname != cname.rstrip('s'):  # skip singular aliases
                continue
            item = _load_one(cls, detail)
            if item:
                console.print(Panel(f"[bold]{cls.__name__}: {detail}[/bold]", border_style="cyan"))
                _print_item_detail(item)
                return
        console.print(f"[red]Component '{detail}' not found in any type[/red]")
        return
    
    # If a specific component type is requested
    if component:
        cls = component_map.get(component)
        if not cls:
            console.print(f"[red]Unknown component type: {component}[/red]")
            console.print(f"[yellow]Valid types: {', '.join(set(component_map.keys()))}[/yellow]")
            return
        items = _load_all(cls)
        # Sort segments/episodes by narrative order
        if cls in (StorySegment, StoryEpisode):
            items.sort(key=lambda x: (
                getattr(x, 'episode_number', 0) if not isinstance(x, dict) else 0,
                getattr(x, 'segment_number_in_episode', 0) if not isinstance(x, dict) else 0,
            ))
        console.print(Panel(f"[bold]{cls.__name__}s ({len(items)})[/bold]", border_style="cyan"))
        for item in items:
            if json_output:
                _print_item_detail(item)
                console.print("---")
            else:
                _print_item_summary(item, cls.__name__)
        return
    
    # Full overview
    console.print(Panel(
        f"[bold cyan]{story.title}[/bold cyan]\n"
        f"ID: {story.id} | Genre: {story.genre}\n"
        f"Start: {story.start_segment_id}\n"
        f"Description: {story.description[:100]}...",
        title="Story Overview",
        border_style="cyan"
    ))
    
    # Show counts for each component type
    component_types = [
        ('Arcs', StoryArc),
        ('Episodes', StoryEpisode),
        ('Segments', StorySegment),
        ('Characters', StoryCharacter),
        ('Locations', StoryLocation),
        ('Factions', StoryFaction),
        ('Magic Systems', StoryMagicSystem),
        ('Choices', StoryChoice),
        ('Context', StoryContext),
    ]
    
    for label, cls in component_types:
        items = _load_all(cls)
        if not items:
            console.print(f"\n[dim]{label}: 0[/dim]")
            continue
        
        console.print(f"\n[bold yellow]{label} ({len(items)}):[/bold yellow]")
        for item in items:
            _print_item_summary(item, cls.__name__)

@app.command()
def generate_segment(
    story_id: str = typer.Argument(..., help="Story ID"),
    from_segment_id: str = typer.Argument(..., help="Current segment ID"),
    choice_text: str = typer.Argument(..., help="Choice text made by user"),
):
    """Generate a new segment from a choice.
    
    This command generates the next segment based on a user's choice.
    Useful for testing segment generation independently from story play mode.
    
    Example:
        python -m app.cli generate-segment my_story opening "I enter the tavern"
    """
    asyncio.run(generate_segment_async(story_id, from_segment_id, choice_text))

async def generate_segment_async(story_id: str, from_segment_id: str, choice_text: str):
    """Generate a new segment asynchronously."""
    # Load configuration
    try:
        config = Config.load()
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return
    
    # Initialize generator
    try:
        generator = await _initialize_generator(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize generator: {e}[/red]")
        return
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Get source segment
    from_segment = story.get_segment(from_segment_id)
    if not from_segment:
        console.print(f"[red]Segment '{from_segment_id}' not found[/red]")
        return
    
    # Find or create choice
    matching_choice = None
    for choice in from_segment.outgoing_choices.values():
        if choice.text.lower() == choice_text.lower():
            matching_choice = choice
            break
    
    if not matching_choice:
        console.print(f"[yellow]No existing choice matches '{choice_text}'[/yellow]")
        console.print(f"[cyan]Available choices:[/cyan]")
        for choice in from_segment.outgoing_choices.values():
            console.print(f"  • {choice.text}")
        return
    
    # Generate next segment
    console.print(Panel(
        f"[bold cyan]Generating segment from choice[/bold cyan]\n[yellow]{choice_text}[/yellow]",
        title="Generate Segment",
        border_style="cyan"
    ))
    
    try:
        with console.status("[bold yellow]Building context and generating...[/bold yellow]", spinner="dots"):
            new_segment = await from_segment.generate_next_scene(matching_choice, generator)
        
        console.print(Panel(
            f"[green]✅ Segment generated successfully![/green]\n\n"
            f"[cyan]Segment ID:[/cyan] {new_segment.id}\n"
            f"[cyan]Title:[/cyan] {new_segment.title}\n"
            f"[cyan]Choices:[/cyan] {len(new_segment.outgoing_choices)}\n\n"
            f"[bold cyan]Preview:[/bold cyan]\n{' '.join(b.content for b in new_segment.text_blocks[:3])[:200]}...",
            title="Generation Result",
            border_style="green"
        ))
        logger.info(f"Generated segment {new_segment.id} from choice in {from_segment_id}")
    except Exception as e:
        console.print(f"[red]❌ Generation failed: {str(e)}[/red]")
        logger.error(f"Segment generation failed: {str(e)}", exc_info=True)


@app.command()
def view_segment_context(
    story_id: str = typer.Argument(..., help="Story ID"),
    segment_id: str = typer.Argument(..., help="Current segment ID"),
    choice_text: str = typer.Argument(..., help="Choice text"),
    detail: str = typer.Option(
        "summary",
        "--detail",
        help="Detail level: summary, characters, episodes, arcs, full"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Preview the generation context that will be sent to AI for the next segment.
    
    This shows what the AI will 'see' when generating the next segment, helping debug
    why the generation might produce unexpected content.
    
    Example:
        python -m app.cli view-segment-context my_story opening "I enter the tavern" --detail=full
    """
    asyncio.run(view_segment_context_async(story_id, segment_id, choice_text, detail, json_output))

async def view_segment_context_async(story_id: str, segment_id: str, choice_text: str, detail: str, json_output: bool):
    """View segment generation context asynchronously."""
    from app.engine.segment_context_builder import SegmentContextBuilder
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Get segment
    segment = story.get_segment(segment_id)
    if not segment:
        console.print(f"[red]Segment '{segment_id}' not found[/red]")
        return
    
    # Build context
    console.print("[yellow]Building generation context...[/yellow]")
    try:
        context_builder = SegmentContextBuilder(story)
        context = await context_builder.build_context(segment_id, choice_text)
        
        if json_output:
            console.print(json.dumps(context, indent=2))
        else:
            # Display formatted context
            console.print(Panel(
                f"[bold cyan]Generation Context for: {segment_id}[/bold cyan]\n"
                f"[yellow]Choice:[/yellow] {choice_text}",
                title="Context Preview",
                border_style="cyan"
            ))
            
            if detail in ["summary", "full"]:
                console.print(f"\n[bold cyan]Characters ({len(context.get('characters', {}))}):[/bold cyan]")
                for char_id, char_info in list(context.get('characters', {}).items())[:5]:
                    console.print(f"  • {char_info.get('name', char_id)}")
                if len(context.get('characters', {})) > 5:
                    console.print(f"  ... and {len(context.get('characters', {})) - 5} more")
            
            if detail in ["episodes", "full"]:
                console.print(f"\n[bold cyan]Episodes ({len(context.get('episodes', []))}):[/bold cyan]")
                for ep in context.get('episodes', [])[-3:]:
                    console.print(f"  • Episode {ep.get('episode_number')}: {ep.get('recap', '')[:60]}...")
            
            if detail in ["arcs", "full"]:
                console.print(f"\n[bold cyan]Story Arcs ({len(context.get('arcs', {}))}):[/bold cyan]")
                for arc_id, arc_info in context.get('arcs', {}).items():
                    console.print(f"  • {arc_info.get('name', arc_id)}")
            
            if detail == "full":
                console.print(f"\n[bold cyan]Last 3 Segments:[/bold cyan]")
                for seg_recap in context.get('recent_segments', [])[:3]:
                    console.print(f"  • {seg_recap.get('id')}: {seg_recap.get('summary', '')[:60]}...")
        
        logger.info(f"Generated context for segment {segment_id}")
    except Exception as e:
        console.print(f"[red]Failed to build context: {str(e)}[/red]")
        logger.error(f"Context building failed: {str(e)}", exc_info=True)


@app.command()
def view_character_state(
    story_id: str = typer.Argument(..., help="Story ID"),
    character_id: str = typer.Argument(..., help="Character ID"),
    episode: Optional[int] = typer.Option(None, "--episode", "-e", help="Show state at specific episode"),
):
    """View character state at current point in story.
    
    Shows health, emotional state, relationships, goals, and other tracked state.
    
    Example:
        python -m app.cli view-character-state my_story hero_main
        python -m app.cli view-character-state my_story hero_main --episode 3
    """
    from app.models.story_episode import StoryEpisode
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Get character
    character = story.get_character(character_id)
    if not character:
        console.print(f"[red]Character '{character_id}' not found[/red]")
        return
    
    console.print(Panel(
        f"[bold cyan]{character.name}[/bold cyan] (ID: {character.id})",
        title="Character State",
        border_style="cyan"
    ))
    
    # Get state at specific episode or latest
    state_snapshot = None
    if episode:
        # Find episode and get state snapshot
        episodes = [ep for ep in story._episodes.values() if ep.episode_number == episode]
        if episodes:
            ep = episodes[0]
            if ep.character_states and character_id in [cs.character_id for cs in ep.character_states]:
                state_snapshot = next((cs for cs in ep.character_states if cs.character_id == character_id), None)
    else:
        # Get latest state from last episode
        if story._episodes:
            last_episode = max(story._episodes.values(), key=lambda e: e.episode_number)
            if last_episode.character_states:
                state_snapshot = next((cs for cs in last_episode.character_states if cs.character_id == character_id), None)
    
    if not state_snapshot:
        console.print("[yellow]No state snapshot found for this character[/yellow]")
        return
    
    # Display state
    table = Table(title="Character State")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Health", state_snapshot.health_status)
    table.add_row("Emotional Status", state_snapshot.emotional_status)
    table.add_row("Disposition", f"{state_snapshot.disposition:+.1f}")
    table.add_row("Location", state_snapshot.current_location or "Unknown")
    
    if state_snapshot.goals:
        table.add_row("Goals", ", ".join(state_snapshot.goals[:3]))
    
    if state_snapshot.relationships:
        rels = [f"{k}: {v}" for k, v in list(state_snapshot.relationships.items())[:3]]
        table.add_row("Relationships", ", ".join(rels) if rels else "None")
    
    console.print(table)
    logger.info(f"Viewed character state for {character_id}")


@app.command()
def view_episode(
    story_id: str = typer.Argument(..., help="Story ID"),
    episode_num: int = typer.Argument(..., help="Episode number"),
    detail: str = typer.Option(
        "summary",
        "--detail",
        help="Detail level: summary, full, recap"
    ),
):
    """View episode information and state.
    
    Shows episode metadata, character states at episode end, and recap.
    
    Example:
        python -m app.cli view-episode my_story 1
        python -m app.cli view-episode my_story 2 --detail=full
    """
    from app.models.story_episode import StoryEpisode
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Find episode
    episode = None
    for ep in story._episodes.values():
        if ep.episode_number == episode_num:
            episode = ep
            break
    
    if not episode:
        console.print(f"[red]Episode {episode_num} not found[/red]")
        return
    
    console.print(Panel(
        f"[bold cyan]Episode {episode_num}[/bold cyan]\n"
        f"[yellow]Segments:[/yellow] {len(episode.segment_ids)}\n"
        f"[yellow]Status:[/yellow] {episode.status if hasattr(episode, 'status') else 'active'}",
        title="Episode Info",
        border_style="cyan"
    ))
    
    if detail in ["summary", "full"]:
        console.print(f"\n[bold cyan]Character States at Episode End:[/bold cyan]")
        if episode.character_states:
            table = Table()
            table.add_column("Character", style="cyan")
            table.add_column("Health", style="yellow")
            table.add_column("Mood", style="magenta")
            table.add_column("Location", style="green")
            
            for state in episode.character_states[:10]:
                table.add_row(
                    state.name or state.character_id,
                    state.health_status or "—",
                    state.emotional_status or "—",
                    state.current_location or "—"
                )
            console.print(table)
        else:
            console.print("[dim]No character states recorded[/dim]")
    
    if detail in ["recap", "full"]:
        console.print(f"\n[bold cyan]Episode Recap:[/bold cyan]")
        if episode.recap:
            console.print(f"{episode.recap}")
        else:
            console.print("[dim]No recap available[/dim]")
    
    logger.info(f"Viewed episode {episode_num}")


@app.command()
def flush_episode(
    story_id: str = typer.Argument(..., help="Story ID"),
    episode_num: int = typer.Argument(..., help="Episode number to flush"),
):
    """Flush episode changes into character/location descriptions.
    
    This consolidates all changes accumulated during an episode and updates
    character/location descriptions to reflect what happened.
    
    Example:
        python -m app.cli flush-episode my_story 1
    """
    asyncio.run(flush_episode_async(story_id, episode_num))

async def flush_episode_async(story_id: str, episode_num: int):
    """Flush episode asynchronously."""
    from app.engine.episode_flush_generator import EpisodeFlushGenerator
    
    # Load configuration
    try:
        config = Config.load()
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return
    
    # Initialize generator
    try:
        generator = await _initialize_generator(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize generator: {e}[/red]")
        return
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Find episode
    episode = None
    for ep in story._episodes.values():
        if ep.episode_number == episode_num:
            episode = ep
            break
    
    if not episode:
        console.print(f"[red]Episode {episode_num} not found[/red]")
        return
    
    # Get all segments in the episode
    episode_segments = [story.get_segment(seg_id) for seg_id in episode.segment_ids]
    episode_segments = [s for s in episode_segments if s]
    
    if not episode_segments:
        console.print(f"[red]No segments found in episode {episode_num}[/red]")
        return
    
    console.print(Panel(
        f"[bold cyan]Flushing Episode {episode_num}[/bold cyan]\n"
        f"[yellow]Segments:[/yellow] {len(episode_segments)}\n"
        f"[yellow]Changes:[/yellow] Processing...",
        title="Episode Flush",
        border_style="cyan"
    ))
    
    try:
        with console.status("[bold yellow]Flushing changes to character/location models...[/bold yellow]", spinner="dots"):
            flush_gen = EpisodeFlushGenerator(story, generator)
            result = await flush_gen.flush_episode_changes(
                episode_segments,
                episode_num
            )
        
        console.print(Panel(
            f"[green]✅ Episode flushed successfully![/green]\n\n"
            f"[cyan]Characters Updated:[/cyan] {len(result.get('flushed_characters', {}))}\n"
            f"[cyan]Locations Updated:[/cyan] {len(result.get('flushed_locations', {}))}\n"
            f"[cyan]Summary:[/cyan] {result.get('changes_summary', 'Complete')}",
            title="Flush Result",
            border_style="green"
        ))
        logger.info(f"Flushed episode {episode_num}")
    except Exception as e:
        console.print(f"[red]❌ Flush failed: {str(e)}[/red]")
        logger.error(f"Episode flush failed: {str(e)}", exc_info=True)


@app.command()
def regenerate_episode_recap(
    story_id: str = typer.Argument(..., help="Story ID"),
    episode_num: int = typer.Argument(..., help="Episode number"),
):
    """Regenerate or create an episode recap.
    
    Walks through all segments in the episode and generates a summary,
    themes, hooks, and character state snapshots.
    
    Example:
        python -m app.cli regenerate-episode-recap my_story 1
    """
    asyncio.run(regenerate_episode_recap_async(story_id, episode_num))

async def regenerate_episode_recap_async(story_id: str, episode_num: int):
    """Regenerate episode recap asynchronously."""
    from app.engine.episode_recap_generator import EpisodeRecapGenerator
    
    # Load configuration
    try:
        config = Config.load()
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return
    
    # Initialize generator
    try:
        generator = await _initialize_generator(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize generator: {e}[/red]")
        return
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Find episode
    episode = None
    for ep in story._episodes.values():
        if ep.episode_number == episode_num:
            episode = ep
            break
    
    if not episode:
        console.print(f"[red]Episode {episode_num} not found[/red]")
        return
    
    console.print(Panel(
        f"[bold cyan]Regenerating Episode {episode_num} Recap[/bold cyan]",
        title="Episode Recap Generator",
        border_style="cyan"
    ))
    
    try:
        with console.status("[bold yellow]Analyzing segments and generating recap...[/bold yellow]", spinner="dots"):
            recap_gen = EpisodeRecapGenerator(story, generator)
            updated_episode = await recap_gen.generate_recap(episode_num)
        
        console.print(Panel(
            f"[green]✅ Recap generated successfully![/green]\n\n"
            f"[cyan]Title:[/cyan] {updated_episode.title or 'Untitled'}\n"
            f"[cyan]Characters Tracked:[/cyan] {len(updated_episode.character_states or [])}\n"
            f"\n[bold cyan]Summary (first 200 chars):[/bold cyan]\n"
            f"{(updated_episode.recap or 'No recap')[:200]}...",
            title="Recap Result",
            border_style="green"
        ))
        logger.info(f"Regenerated recap for episode {episode_num}")
    except Exception as e:
        console.print(f"[red]❌ Recap generation failed: {str(e)}[/red]")
        logger.error(f"Episode recap generation failed: {str(e)}", exc_info=True)


@app.command()
def validate_story(
    story_id: str = typer.Argument(..., help="Story ID"),
    repair: bool = typer.Option(False, "--repair", help="Auto-repair missing components"),
):
    """Validate story completeness and optionally repair missing pieces.
    
    Checks:
    - Story description
    - World context (fundamental truths)
    - Story arcs
    - Characters
    - Protagonist
    
    Example:
        python -m app.cli validate-story my_story
        python -m app.cli validate-story my_story --repair
    """
    asyncio.run(validate_story_async(story_id, repair))

async def validate_story_async(story_id: str, repair: bool):
    """Validate story asynchronously."""
    from app.engine.story_validator import StoryValidator
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # If repair is needed, load config and generator
    generator = None
    if repair:
        try:
            config = Config.load()
            generator = await _initialize_generator(config)
        except Exception as e:
            console.print(f"[yellow]Repair requested but generator unavailable: {e}[/yellow]")
            console.print("[yellow]Running validation only (no repairs).[/yellow]")
    
    console.print(Panel(
        f"[bold cyan]Validating Story: {story.title}[/bold cyan]",
        title="Story Validator",
        border_style="cyan"
    ))
    
    try:
        with console.status("[bold yellow]Validating story completeness...[/bold yellow]", spinner="dots"):
            validator = StoryValidator(story, generator)
            report = await validator.validate_and_repair()
        
        # Display results
        results = report.get('validation_results', {})
        
        table = Table(title="Validation Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Details", style="white")
        
        for component, result in results.items():
            if isinstance(result, dict):
                status_text = f"[green]✅ OK[/green]" if result.get('status') == 'valid' else "[yellow]⚠️ Generated[/yellow]"
                details = result.get('message', 'OK')
            else:
                status_text = "[green]✅ OK[/green]"
                details = str(result)[:50]
            
            table.add_row(component.replace('_', ' '), status_text, details)
        
        console.print(table)
        
        # Show generated items
        if report.get('generated'):
            console.print(f"\n[bold cyan]Auto-Generated:[/bold cyan]")
            for item in report['generated']:
                console.print(f"  • {item}")
        
        # Show errors
        if report.get('errors'):
            console.print(f"\n[bold red]Errors:[/bold red]")
            for error in report['errors']:
                console.print(f"  • {error}")
        
        logger.info(f"Validated story {story_id}")
    except Exception as e:
        console.print(f"[red]❌ Validation failed: {str(e)}[/red]")
        logger.error(f"Story validation failed: {str(e)}", exc_info=True)


@app.command()
def generate_choices(
    story_id: str = typer.Argument(..., help="Story ID"),
    segment_id: str = typer.Argument(..., help="Segment ID"),
    count: int = typer.Option(3, "--count", "-c", help="Number of choices to generate"),
):
    """Generate multiple choices for a segment.
    
    Tests choice generation separately from story play mode.
    
    Example:
        python -m app.cli generate-choices my_story opening --count=4
    """
    asyncio.run(generate_choices_async(story_id, segment_id, count))

async def generate_choices_async(story_id: str, segment_id: str, count: int):
    """Generate choices asynchronously."""
    from app.models.story_choice import StoryChoice
    from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec
    import uuid
    
    # Load configuration
    try:
        config = Config.load()
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return
    
    # Initialize generator
    try:
        generator = await _initialize_generator(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize generator: {e}[/red]")
        return
    
    # Load story
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found[/red]")
        return
    
    # Load story components
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    # Get segment
    segment = story.get_segment(segment_id)
    if not segment:
        console.print(f"[red]Segment '{segment_id}' not found[/red]")
        return
    
    console.print(Panel(
        f"[bold cyan]Generating {count} Choices[/bold cyan]\n"
        f"[yellow]Segment:[/yellow] {segment.title}",
        title="Choice Generator",
        border_style="cyan"
    ))
    
    try:
        with console.status(f"[bold yellow]Generating {count} choices...[/bold yellow]", spinner="dots"):
            # Generate choices using AI
            prompt = f"""Generate {count} compelling narrative choices for this story moment:

Segment: {segment.title}
Context: {' '.join(b.content for b in segment.text_blocks[:3])[:300]}...

Create {count} realistic choices that:
- Feel natural and consequential
- Offer meaningful branching paths
- Range from conservative to risky actions
- Are 1-2 sentences each

Format as numbered list only:
1. Choice text
2. Choice text
{f'3. Choice text' if count >= 3 else ''}
{f'4. Choice text' if count >= 4 else ''}"""
            
            system_prompt = """You are a narrative designer creating compelling story choices.
Choices should feel natural, consequential, and offer meaningful branching paths."""
            
            choices_text = await generator._generate_content(system_prompt, prompt)
            
            # Parse choices from response
            choice_lines = []
            for line in choices_text.split('\n'):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                    # Extract choice text after number
                    choice_text = line.split('.', 1)[1].strip() if '.' in line else line
                    if choice_text and len(choice_text) > 5:  # Ensure meaningful text
                        choice_lines.append(choice_text)
            
            # If parsing failed, create fallback choices
            if not choice_lines:
                choice_lines = [
                    "Continue cautiously forward",
                    "Take a bold action",
                    "Seek more information first"
                ][:count]
            
            # Create choice objects
            choices = []
            for i, choice_text in enumerate(choice_lines[:count]):
                choice_id = f"choice_{uuid.uuid4().hex[:8]}"
                choice = StoryChoice(
                    id=choice_id,
                    from_segment_id=segment_id,
                    text=choice_text,
                    to_segment_id=None  # Will be generated later
                )
                choices.append(choice)
        
        # Display results
        table = Table(title=f"Generated Choices ({len(choices)})")
        table.add_column("Choice", style="cyan")
        table.add_column("Text", style="white")
        
        for i, choice in enumerate(choices, 1):
            table.add_row(f"#{i}", choice.text)
        
        console.print(table)
        
        console.print(f"\n[green]✅ Generated {len(choices)} choices successfully![/green]")
        console.print("[dim]Note: Choices not saved. Use during story play to save them.[/dim]")
        logger.info(f"Generated {len(choices)} choices for segment {segment_id}")
    except Exception as e:
        console.print(f"[red]❌ Choice generation failed: {str(e)}[/red]")
        logger.error(f"Choice generation failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    app()
