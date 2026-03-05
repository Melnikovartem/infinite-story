import json
import asyncio
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich import print as rprint

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

# Configure logging to show debug messages
def _setup_logging():
    """Configure logging to display debug messages during generation."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Writes to stderr, which shows through
        ]
    )
    # Reduce noise from verbose libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("h11").setLevel(logging.WARNING)

class RunMode(str, Enum):
    """CLI display modes."""
    IMMERSIVE = "immersive"
    UI_DEBUG = "ui_debug"
    STORY_DEBUG = "story_debug"
    DEV = "dev"

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
    from app.engine.generators.world_generator import WorldGenerator
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
        
        # Generate world context
        world_gen = WorldGenerator(generator)
        world_context = await world_gen.generate_world_context(story=story, user_input=world_input)
        console.print("[green]✅ World generated![/green]")
        console.print(f"[cyan]Fundamental Truths: {len(world_context.fundamental_truths)}[/cyan]")
        
        console.print("\n[bold yellow]⏳ Step 2: Generating factions and politics...[/bold yellow]")
        
        # Generate factions
        faction_gen = FactionGenerator(story, generator)
        factions = await faction_gen.generate_factions(
            count=story_plan['total_factions'],
            world_description=world_context.fundamental_truths[0] if world_context.fundamental_truths else "",
            major_tensions=story_plan['major_tensions'],
            user_input=world_input
        )
        console.print(f"[green]✅ Generated {len(factions)} factions![/green]")
        for faction in factions:
            console.print(f"  • {faction.name}: {faction.description[:50]}...")
        
        console.print("\n[bold yellow]⏳ Step 3: Generating magic/tech system...[/bold yellow]")
        
        # Generate magic/tech system
        magic_gen = MagicSystemGenerator(story, generator)
        magic_system = await magic_gen.generate_magic_system(
            world_description=world_context.fundamental_truths[0] if world_context.fundamental_truths else "",
            genre=genre,
            user_input=world_input
        )
        console.print(f"[green]✅ Generated magic system: {magic_system.name}![/green]")
        console.print(f"  [yellow]Limitations:[/yellow] {', '.join(magic_system.limitations[:2])}")
        console.print(f"  [yellow]Costs:[/yellow] {', '.join(magic_system.costs[:2])}")
        
        console.print("\n[bold yellow]⏳ Step 4: Generating world locations...[/bold yellow]")
        
        # Generate locations
        loc_gen = LocationGenerator(story, generator)
        locations = await loc_gen.generate_world_locations(
            world_description=world_context.fundamental_truths[0] if world_context.fundamental_truths else "",
            fundamental_truths=world_context.fundamental_truths,
            user_input=world_input
        )
        console.print(f"[green]✅ Generated {len(locations)} world locations![/green]")
        
        console.print("\n[bold yellow]⏳ Step 5: Generating story arcs...[/bold yellow]")
        
        # Generate arcs
        arc_gen = ArcGenerator(story, generator)
        arcs = await arc_gen.generate_future_arcs(count=3, user_input=world_input)
        console.print(f"[green]✅ Generated {len(arcs)} story arcs![/green]")
        
        console.print("\n[bold yellow]⏳ Step 6: Generating characters aligned to factions...[/bold yellow]")
        
        # Generate characters aligned to factions
        char_gen = CharacterGenerator(story, generator)
        try:
            characters = await char_gen.generate_faction_characters(factions, story_plan)
            console.print(f"[green]✅ Generated {len(characters)} faction-aligned characters![/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Character generation skipped: {str(e)[:50]}[/yellow]")
            characters = []
        
        console.print("\n[bold yellow]⏳ Step 7: Selecting protagonist...[/bold yellow]")
        
        # Select protagonist
        proto_sel = ProtagonistSelector(story, generator)
        try:
            protagonist = await proto_sel.select_or_develop_protagonist(user_choice=None)
            console.print(f"[green]✅ Protagonist selected: {protagonist.name if hasattr(protagonist, 'name') else 'Unknown'}![/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Protagonist selection skipped: {str(e)[:50]}[/yellow]")
            protagonist = None
        
        console.print("\n[bold yellow]⏳ Step 8: Creating the first scene of this world...[/bold yellow]")
        
        # If user provided scene input, use it; otherwise AI creates something
        if first_scene_input.strip():
            scene_direction = f"User's direction: {first_scene_input}"
        else:
            scene_direction = "Create something that brings this world to life - an atmospheric, engaging scene that hooks the reader and establishes the mood of this living, breathing world."
        
        # Generate first segment
        opening_prompt = f"""Create a CAPTIVATING opening scene for this story:

Title: {title}
Genre: {genre}
World Description: {world_context.fundamental_truths[0] if world_context.fundamental_truths else 'A mysterious world'}

Scene Direction: {scene_direction}

Write an opening narrative that:
- Immediately draws the reader into this LIVING world
- Establishes the atmosphere and mood
- Shows the world as a character - alive, breathing, with personality
- Hints at the story's core conflicts or mysteries
- Creates compelling story hooks that make readers want to know more
- Is vivid, atmospheric, and engaging"""
        
        opening_response = await generator.generate(
            system_prompt="""You are a master storyteller creating immersive opening scenes. 
Write with vivid sensory details that make the reader feel present in this living world. 
Your opening scenes hook readers immediately and establish mood, setting, and possibility.""",
            user_prompt=opening_prompt,
            context_type="scene"
        )
        
        opening_text = opening_response.content if hasattr(opening_response, 'content') else str(opening_response)
        
        console.print("[green]✅ First scene generated![/green]")
        
        # Create opening segment
        from app.models.story_segment import StorySegment
        
        # Link opening segment to the first generated arc
        first_arc_id = arcs[0].id if arcs else "arc_1"
        
        opening_segment = StorySegment(
            id="opening",
            story_id=story_id,
            story=story,  # Pass the story object
            short_description="The Story Begins",
            atmosphere="atmospheric",
            episode_number=1,
            arc_id=first_arc_id,
            protagonist_id=protagonist.id if protagonist and hasattr(protagonist, 'id') else None
        )
        
        # Add text block
        text_block = TextBlock(
            type="narrator_describing",
            content=opening_text,
            emotion="mysterious"
        )
        opening_segment.text_blocks = [text_block]
        story.add_segment(opening_segment)
        
        # Generate choices for opening segment
        console.print("\n[bold yellow]⏳ Step 9: Generating choices for opening scene...[/bold yellow]")
        
        from app.models.story_choice import StoryChoice
        import uuid
        
        try:
            # Generate 2-3 choices for the opening
            choice_prompt = f"""Create 2-3 compelling choices for the opening scene of this story:

Story: {title}
World: {world_context.fundamental_truths[0] if world_context.fundamental_truths else 'A mysterious world'}
Opening Scene: {opening_text[:300]}...

Generate realistic story choices that:
- Branch the narrative in different directions
- Let players engage with the world
- Create meaningful consequences
- Move the story forward

Format as a simple list of 2-3 choices, each 1-2 sentences."""
            
            choices_response = await generator.generate(
                system_prompt="You are a narrative designer creating compelling story choices that feel natural and consequential.",
                user_prompt=choice_prompt,
                context_type="scene"
            )
            
            choices_text = choices_response.content if hasattr(choices_response, 'content') else str(choices_response)
            
            # Parse choices from response (simple line-by-line parsing)
            choice_lines = [line.strip() for line in choices_text.split('\n') if line.strip() and not line.startswith('#')]
            
            # Create choice objects
            choices_list = []
            for i, choice_text in enumerate(choice_lines[:3]):  # Max 3 choices
                choice_id = f"choice_{uuid.uuid4().hex[:8]}"
                
                choice = StoryChoice(
                    id=choice_id,
                    story_id=story_id,
                    story=story,
                    from_segment_id="opening",
                    to_segment_id=None,  # Will be AI-generated when chosen
                    text=choice_text
                )
                
                story.add_choice(choice)
                choices_list.append(choice)
            
            console.print(f"[green]✅ Generated {len(choices_list)} choices for opening scene![/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Choice generation skipped: {str(e)[:50]}[/yellow]")
            choices_list = []
        
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

async def _initialize_generator(config: Config):
    """Initialize and return generator based on config."""
    logger.debug(f"[INIT_GEN_START] Initializing generator with provider: {config.generator.provider}")
    if config.generator.provider == "openrouter":
        logger.info(f"Initializing OpenRouter generator with model: {config.generator.model}")
        logger.debug(f"[INIT_GEN_OPENROUTER] Creating OpenRouter generator instance")
        generator = OpenRouterGenerator(
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens,
            site_url=config.generator.site_url,
            site_name=config.generator.site_name,
            auto_fallback=True
        )
        logger.debug(f"[INIT_GEN_OPENROUTER_DONE] OpenRouter generator initialized")
        console.print(f"[cyan]Using OpenRouter with model: {generator.model}[/cyan]")
    else:  # openai
        logger.info(f"Initializing OpenAI generator with model: {config.generator.model}")
        logger.debug(f"[INIT_GEN_OPENAI] Creating OpenAI generator instance")
        generator = OpenAIGenerator(
            api_base=config.generator.base_url,
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens
        )
        logger.debug(f"[INIT_GEN_OPENAI_DONE] OpenAI generator initialized")
        console.print(f"[cyan]Using OpenAI with model: {config.generator.model}[/cyan]")
    logger.debug(f"[INIT_GEN_DONE] Generator initialization complete")
    return generator

async def _run_immersive_mode(runner: StoryRunner, generator):
    """Run story in immersive mode - beautiful narrative focus."""
    from app.ui.formatter import display_segment_immersive, prompt_choice_immersive
    
    try:
        while runner.is_running:
            # Display current segment beautifully
            if runner.current_segment:
                display_segment_immersive(runner.current_segment)
            
            # Get user choice
            choices = runner.get_available_choices()
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
                logger.info("Story ended - no more choices available")
                break
            
            choice_id = prompt_choice_immersive(runner.current_segment, choices)
            
            # Execute choice
            try:
                await _execute_choice(runner, choice_id, generator, mode=RunMode.IMMERSIVE)
            except Exception as e:
                error_type, technical_msg = handle_api_error(e)
                message, suggestion = ErrorHandler.handle_error(
                    error_type,
                    e,
                    "Processing your choice"
                )
                console.print(f"[red]Error: {message}[/red]")
                console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
                continue
            
            # Auto-save state
            runner.save_state()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")


async def _run_ui_debug_mode(runner: StoryRunner, generator):
    """Run story in UI debug mode - blocks appear one-by-one with space."""
    from app.ui.ui_debug_display import display_segment_ui_debug, prompt_choice_ui_debug
    
    try:
        while runner.is_running:
            if runner.current_segment:
                display_segment_ui_debug(runner.current_segment)
            
            choices = runner.get_available_choices()
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
                break
            
            choice_id = prompt_choice_ui_debug(runner.current_segment, choices)
            
            try:
                await _execute_choice(runner, choice_id, generator, mode=RunMode.UI_DEBUG)
            except Exception as e:
                error_type, technical_msg = handle_api_error(e)
                message, suggestion = ErrorHandler.handle_error(
                    error_type,
                    e,
                    "Processing your choice"
                )
                console.print(f"[red]Error: {message}[/red]")
                console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
                continue
            
            runner.save_state()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")


async def _run_story_debug_mode(runner: StoryRunner, generator):
    """Run story in story debug mode - comprehensive generation context."""
    from app.ui.story_debug_display import (
        display_segment_story_debug,
        display_generation_context_story_debug,
        display_generation_result_story_debug,
        prompt_choice_story_debug
    )
    from app.engine.segment_context_builder import SegmentContextBuilder
    
    try:
        while runner.is_running:
            if runner.current_segment:
                display_segment_story_debug(runner.current_segment)
            
            choices = runner.get_available_choices()
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
                break
            
            # Build generation context to show what will be sent to AI
            context = None
            try:
                # Don't pass generator here - story_debug mode should display EXISTING context only,
                # not auto-generate missing data (which would be slow and block the UI)
                context_builder = SegmentContextBuilder(runner.story)
                context = await context_builder.build_context(
                    runner.current_segment.id,
                    choices[0].text if choices else "unknown"  # This will be updated after choice
                )
            except Exception as e:
                logger.debug(f"Could not build context: {e}")
            
            # Show generation context before each choice
            display_generation_context_story_debug(runner, runner.current_segment, context)
            
            choice_id = prompt_choice_story_debug(runner.current_segment, choices)
            
            # Update context with actual chosen text
            if context:
                choice_text = next((c.text for c in choices if c.id == choice_id), "unknown")
                context['user_choice'] = choice_text
            
            try:
                await _execute_choice(runner, choice_id, generator, mode=RunMode.STORY_DEBUG)
            except Exception as e:
                error_type, technical_msg = handle_api_error(e)
                message, suggestion = ErrorHandler.handle_error(
                    error_type,
                    e,
                    "Processing your choice"
                )
                console.print(f"[red]Error: {message}[/red]")
                console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
                continue
            
            # Show result with context info
            if runner.current_segment:
                display_generation_result_story_debug(runner.current_segment, context)
            
            runner.save_state()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")


async def _run_dev_mode(runner: StoryRunner, generator):
    """Run story in dev mode - minimal info with important details."""
    from app.ui.dev_display import display_segment_dev, display_generation_context_dev, prompt_choice_dev
    
    try:
        while runner.is_running:
            if runner.current_segment:
                display_segment_dev(runner.current_segment)
            
            # Show minimal context
            display_generation_context_dev(runner, runner.current_segment)
            
            choices = runner.get_available_choices()
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
                break
            
            choice_id = prompt_choice_dev(runner.current_segment, choices)
            
            try:
                await _execute_choice(runner, choice_id, generator, mode=RunMode.DEV)
            except Exception as e:
                error_type, technical_msg = handle_api_error(e)
                message, suggestion = ErrorHandler.handle_error(
                    error_type,
                    e,
                    "Processing your choice"
                )
                console.print(f"[red]Error: {message}[/red]")
                console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
                continue
            
            runner.save_state()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")



async def _execute_choice(runner: StoryRunner, choice_id: str, generator, mode: RunMode = RunMode.IMMERSIVE):
    """Execute a choice and advance the story."""
    logger.debug(f"[EXEC_CHOICE_START] Executing choice: {choice_id}")
    choice = runner.story.get_choice(choice_id)
    if not choice:
        console.print(f"[red]Choice '{choice_id}' not found[/red]")
        logger.error(f"[EXEC_CHOICE_ERROR] Choice not found: {choice_id}")
        return
    
    # Check if choice leads to existing segment or needs generation
    if choice.to_segment_id:
        # Navigate to existing segment
        logger.debug(f"[EXEC_CHOICE_NAV] Navigating to existing segment: {choice.to_segment_id}")
        runner.make_choice(choice_id)
        if mode != RunMode.IMMERSIVE:
            console.print(f"\n[cyan]Navigated to segment: {runner.current_segment.id}[/cyan]")
        logger.debug(f"[EXEC_CHOICE_NAV_DONE] Navigation complete. Current segment: {runner.current_segment.id}")
    else:
        # Generate new segment
        logger.debug(f"[EXEC_CHOICE_GEN_START] Starting generation for choice: {choice.text}")
        console.print("[bold yellow]⏳ Generating next scene...[/bold yellow]")
        logger.debug(f"[EXEC_CHOICE_GEN_CALL] Calling generate_next_scene()")
        
        try:
            new_segment = await runner.current_segment.generate_next_scene(choice, generator)
            logger.debug(f"[EXEC_CHOICE_GEN_RECEIVED] Received new segment: {new_segment.id}")
            runner.current_segment = new_segment
            runner.visited_segments.add(new_segment.id)
            console.print("[green]✅ Scene generated successfully![/green]")
            logger.debug(f"[EXEC_CHOICE_GEN_DONE] New segment set as current: {new_segment.id}")
            
            if mode != RunMode.IMMERSIVE:
                console.print(f"\n[cyan]New segment: {new_segment.id}[/cyan]")
        except Exception as e:
            logger.error(f"[EXEC_CHOICE_GEN_ERROR] Generation failed: {str(e)}", exc_info=True)
            console.print(f"[red]❌ Scene generation failed: {str(e)}[/red]")
            raise

async def run_story_async(story_name: str = None, mode: RunMode = RunMode.IMMERSIVE, resume: bool = False, log_level: str = "error"):
    """Run a story in one of four modes.
    
    Args:
        story_name: Optional story ID to run directly (skips selection)
        mode: IMMERSIVE (default), UI_DEBUG, STORY_DEBUG, or DEV
        resume: Resume from previous session if available
        log_level: error (default), warn, or debug
    """

    # Setup logging based on mode
    if log_level:
        setup_logging(log_level)
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for story"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return

    # Initialize generator
    try:
        generator = await _initialize_generator(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize generator: {e}[/red]")
        logger.error(f"Generator initialization failed: {e}")
        return

    # Get story selection
    if story_name:
        logger.info(f"Using provided story: {story_name}")
        selected_story = {
            "id": story_name,
            "title": story_name,
            "genre": "Unknown",
            "description": "Story"
        }
    else:
        # List and let user select
        logger.info("Listing available stories")
        story_ids = Story.list_stories()
        logger.debug(f"Found {len(story_ids)} story IDs: {story_ids}")
        stories = []
        for story_id in story_ids:
            logger.debug(f"Loading story: {story_id}")
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
            logger.warning("No story selected")
            return
    
    logger.info(f"Selected story: {selected_story['id']}")

    console.print(Panel(
        f"[green]Starting story: {selected_story.get('title', 'Untitled')}[/green]\n[cyan]Mode: {mode.value}[/cyan]",
        title="Story Runner",
        border_style="green"
    ))

    # Load story and runner
    logger.info(f"Loading story data for: {selected_story['id']}")
    story = Story.load(selected_story["id"], selected_story["id"])
    if not story:
        console.print("[red]Failed to load story![/red]")
        logger.error(f"Failed to load story: {selected_story['id']}")
        return

    logger.info(f"Initializing StoryRunner for: {story.id}")
    runner = StoryRunner(story)
    
    try:
        # Load all story components first
        runner.load_all_components(story)
        
        # Load or start story
        if resume and runner.load_state():
            console.print("[yellow]Resuming from saved state...[/yellow]")
            logger.info("Loaded previous state, resuming story")
            console.print(f"[green]Resumed at segment: {runner.current_segment.short_description}[/green]")
            logger.info(f"Resumed at segment: {runner.current_segment.id}")
        else:
            logger.info("Starting story from beginning")
            runner.start()
            console.print("[green]Story started successfully![/green]")
            logger.info(f"Story started at segment: {runner.current_segment.id}")
        
        # Run appropriate mode
        if mode == RunMode.IMMERSIVE:
            await _run_immersive_mode(runner, generator)
        elif mode == RunMode.UI_DEBUG:
            await _run_ui_debug_mode(runner, generator)
        elif mode == RunMode.STORY_DEBUG:
            await _run_story_debug_mode(runner, generator)
        elif mode == RunMode.DEV:
            await _run_dev_mode(runner, generator)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

@app.command()
def run_story(
    story: str = typer.Argument(None, help="Optional story ID to run directly"),
    mode: RunMode = typer.Option(
        RunMode.IMMERSIVE,
        "--mode",
        help="CLI mode: immersive (beautiful), ui_debug (blocks one-by-one), story_debug (generation context), dev (minimal)"
    ),
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
):
    """
    Run a story with four modes:
    
    Immersive (default):
      python -m app.cli run-story story_name
      Beautiful narrative experience, focus on prose.
    
    UI Debug:
      python -m app.cli run-story story_name --mode ui_debug
      Blocks appear one-by-one, press ENTER to continue.
    
    Story Debug:
      python -m app.cli run-story story_name --mode story_debug
      See comprehensive generation context before each choice.
    
    Dev:
      python -m app.cli run-story story_name --mode dev
      Minimal interface with important details (arc, parent, etc).
    """
    asyncio.run(run_story_async(story_name=story, mode=mode, resume=resume, log_level=log_level))

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
    from app.engine.generators.world_generator import WorldGenerator
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
        
        console.print(Panel(
            f"Progress: {summary['progress']} | Status: {summary['overall_status']}",
            title="Generation Status",
            border_style="cyan"
        ))
        
        console.print("\n[bold cyan]Step Status:[/bold cyan]")
        for i in range(10):
            s = status[i]
            icon = "✅" if s["status"] == "completed" else (
                "⏭️" if s["status"] == "skipped" else (
                    "❌" if s["status"] == "failed" else "⏳"
                )
            )
            can_run = "✓" if s["can_run"] else "✗"
            console.print(f"{icon} Step {i}: {s['name']} [{s['status']}] (runnable: {can_run})")
            if s["status"] == "failed" and s.get("error_message"):
                console.print(f"   Error: {s['error_message'][:80]}...")
            if s["missing_deps"]:
                console.print(f"   Missing: {s['missing_deps']}")
        
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
            world_gen = WorldGenerator(generator)
            world_context = await world_gen.generate_world_context(story=story)
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
            step_manager.mark_step_completed(target_step, {"name": magic_system.name})
            console.print(f"[green]✅ Step 3 complete! Magic system: {magic_system.name}[/green]")
        
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

if __name__ == "__main__":
    app()
