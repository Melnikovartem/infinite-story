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

async def test_generation_async(story_id: str):
    """Test scene generation for debugging."""
    import os

    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for generation test"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return

    # Initialize generator based on provider
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
    else:  # openai
        logger.info(f"Initializing OpenAI generator with model: {config.generator.model}")
        generator = OpenAIGenerator(
            api_base=config.generator.base_url,
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens
        )

    console.print(f"[cyan]Testing scene generation for story: {story_id}[/cyan]")

    # Load story
    logger.info(f"Loading story: {story_id}")
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found![/red]")
        return

    # Initialize runner
    runner = StoryRunner(story)
    runner.load_all_components(story)

    # Get start segment
    start_segment = story.get_segment(story.start_segment_id)
    if not start_segment:
        console.print(f"[red]Start segment not found![/red]")
        return

    console.print(f"[green]Loaded story: {story.title}[/green]")
    console.print(f"[green]Start segment: {start_segment.short_description}[/green]")

    # Get first choice
    choices = list(start_segment.outgoing_choices.values())
    if not choices:
        console.print(f"[red]No choices available![/red]")
        return

    first_choice = choices[0]
    console.print(f"[yellow]Testing generation with choice: {first_choice.text}[/yellow]\n")

    # Generate new scene
    with console.status("[bold yellow]Generating next scene...[/bold yellow]", spinner="dots"):
        try:
            new_segment = await start_segment.generate_next_scene(
                first_choice,
                generator
            )

            console.print("[green]Scene generated successfully![/green]\n")
            console.print(f"[bold cyan]New Segment ID:[/bold cyan] {new_segment.id}")
            console.print(f"[bold cyan]Description:[/bold cyan] {new_segment.short_description}")
            console.print(f"[bold cyan]Atmosphere:[/bold cyan] {new_segment.atmosphere}")
            console.print(f"[bold cyan]Text Blocks:[/bold cyan] {len(new_segment.text_blocks)}")

            console.print("\n[bold]Generated Choices:[/bold]")
            for i, choice in enumerate(new_segment.outgoing_choices.values(), 1):
                console.print(f"  {i}. {choice.text}")

            console.print("\n[bold]Scene Preview:[/bold]")
            for block in new_segment.text_blocks[:3]:  # Show first 3 blocks
                console.print(f"  [{block.type}] {block.content[:100]}...")

        except Exception as e:
            console.print(f"[red]Error generating scene: {str(e)}[/red]")
            logger.error(f"Generation error: {e}", exc_info=True)

@app.command()
def test_generation(
    story_id: str = typer.Option("veil_of_thornreach", help="Story ID to test with")
):
    """Test scene generation with a story."""
    asyncio.run(test_generation_async(story_id))

async def test_world_generation_async(story_id: str, user_input: str = ""):
    """Test world generation for a story."""
    from app.engine.generators.world_generator import WorldGenerator
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for world generation test"
        )
        console.print(f"[red]Error: {message}[/red]")
        console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
        return

    # Initialize generator based on provider
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
    else:  # openai
        logger.info(f"Initializing OpenAI generator with model: {config.generator.model}")
        generator = OpenAIGenerator(
            api_base=config.generator.base_url,
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens
        )

    console.print(f"[cyan]Testing world generation for story: {story_id}[/cyan]")

    # Load story
    logger.info(f"Loading story: {story_id}")
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found![/red]")
        return

    console.print(f"[green]Loaded story: {story.title}[/green]")
    console.print(f"[green]Description: {story.description}[/green]")
    console.print(f"[green]Genre: {story.genre}[/green]\n")

    # Initialize world generator
    world_gen = WorldGenerator(generator)

    # Generate world context
    console.print("[bold yellow]⏳ Generating world context...[/bold yellow]")
    try:
        context = await world_gen.generate_world_context(
            story=story,
            user_input=user_input
        )

        console.print("[green]✅ World context generated successfully![/green]\n")
        
        # Display fundamental truths
        console.print("[bold cyan]Fundamental Truths:[/bold cyan]")
        for i, truth in enumerate(context.fundamental_truths, 1):
            console.print(f"  {i}. {truth}")
        
        # Display worldbuilding details
        console.print("\n[bold cyan]Worldbuilding Details:[/bold cyan]")
        for key, value in context.worldbuilding.items():
            console.print(f"  [yellow]{key.upper()}:[/yellow]")
            # Truncate long values for display
            if isinstance(value, str) and len(value) > 200:
                console.print(f"    {value[:200]}...")
            else:
                console.print(f"    {value}")

    except Exception as e:
        console.print(f"[red]Error generating world context: {str(e)}[/red]")
        logger.error(f"World generation error: {e}", exc_info=True)

@app.command()
def test_world_generation(
    story_id: str = typer.Option("veil_of_thornreach", help="Story ID to test with"),
    user_input: str = typer.Option("", help="Optional user input for world generation")
):
    """Test world generation with a story."""
    asyncio.run(test_world_generation_async(story_id, user_input))

async def test_story_validation_async(story_id: str):
    """Test complete story validation pipeline."""
    from app.engine.story_validator import StoryValidator
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for story validation test"
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

    console.print(f"[cyan]Testing story validation for: {story_id}[/cyan]\n")

    # Load story
    logger.info(f"Loading story: {story_id}")
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found![/red]")
        return

    console.print(f"[green]✓ Loaded story: {story.title}[/green]")
    console.print(f"[green]✓ Genre: {story.genre}[/green]")
    console.print(f"[green]✓ Start segment: {story.start_segment_id}[/green]\n")

    # Run validation
    console.print("[bold yellow]⏳ Running story validation pipeline...[/bold yellow]\n")
    
    try:
        validator = StoryValidator(story, generator)
        report = await validator.validate_and_repair()

        # Display results
        console.print("[bold cyan]Validation Results:[/bold cyan]")
        
        # Story Description
        status = report['validation_results'].get('story_description', {})
        status_icon = "✅" if status.get('valid') else "⚠️"
        console.print(f"\n{status_icon} [bold]Story Description:[/bold]")
        console.print(f"   Valid: {status.get('valid')}")
        if status.get('generated'):
            console.print(f"   Generated: Yes")
        
        # World Description
        status = report['validation_results'].get('world_description', {})
        status_icon = "✅" if status.get('valid') else "⚠️"
        console.print(f"\n{status_icon} [bold]World Description:[/bold]")
        console.print(f"   Valid: {status.get('valid')}")
        if status.get('generated'):
            console.print(f"   Generated: Yes")
            if status.get('fundamental_truths'):
                console.print(f"   Fundamental Truths: {len(status['fundamental_truths'])}")
        
        # Arcs
        status = report['validation_results'].get('arcs', {})
        status_icon = "✅" if status.get('valid') else "⚠️"
        console.print(f"\n{status_icon} [bold]Story Arcs:[/bold]")
        console.print(f"   Valid: {status.get('valid')}")
        if status.get('arcs'):
            console.print(f"   Total arcs: {len(status['arcs'])}")
            for i, arc in enumerate(status['arcs'], 1):
                arc_title = arc.get('title', 'Unnamed Arc')
                console.print(f"     {i}. {arc_title}")
        if status.get('generated'):
            console.print(f"   Generated: Yes")
        
        # Characters
        status = report['validation_results'].get('characters', {})
        status_icon = "✅" if status.get('valid') else "⚠️"
        console.print(f"\n{status_icon} [bold]Characters:[/bold]")
        console.print(f"   Valid: {status.get('valid')}")
        if status.get('characters'):
            console.print(f"   Total characters: {len(status['characters'])}")
            for char in status['characters'][:5]:  # Show first 5
                console.print(f"     • {char.get('name', 'Unknown')} ({char.get('role', 'N/A')})")
            if len(status['characters']) > 5:
                console.print(f"     ... and {len(status['characters']) - 5} more")
        if status.get('generated'):
            console.print(f"   Generated: Yes")
        
        # Protagonist
        status = report['validation_results'].get('protagonist', {})
        status_icon = "✅" if status.get('valid') else "⚠️"
        console.print(f"\n{status_icon} [bold]Protagonist:[/bold]")
        console.print(f"   Valid: {status.get('valid')}")
        if status.get('protagonist'):
            proto = status['protagonist']
            console.print(f"   Name: {proto.get('name', 'Unknown')}")
            console.print(f"   Role: {proto.get('role', 'N/A')}")
            if proto.get('arc_goals'):
                console.print(f"   Arc Goals: {proto.get('arc_goals')}")
        if status.get('generated'):
            console.print(f"   Generated: Yes")
        
        # Summary
        console.print(f"\n[bold cyan]Summary:[/bold cyan]")
        console.print(f"Generated: {', '.join(report['generated'])}")
        if report.get('errors'):
            console.print(f"\n[yellow]Errors:[/yellow]")
            for error in report['errors']:
                console.print(f"  • {error}")

    except Exception as e:
        console.print(f"[red]Error during validation: {str(e)}[/red]")
        logger.error(f"Validation error: {e}", exc_info=True)

@app.command()
def test_story_validation(
    story_id: str = typer.Option("veil_of_thornreach", help="Story ID to validate")
):
    """Test complete story validation pipeline (world, arcs, characters, protagonist)."""
    asyncio.run(test_story_validation_async(story_id))

async def test_arc_generation_async(story_id: str, count: int = 3):
    """Test arc generation for a story."""
    from app.engine.generators.arc_generator import ArcGenerator
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for arc generation test"
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

    console.print(f"[cyan]Testing arc generation for story: {story_id}[/cyan]")

    # Load story
    logger.info(f"Loading story: {story_id}")
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found![/red]")
        return

    console.print(f"[green]Loaded story: {story.title}[/green]")
    console.print(f"[green]Genre: {story.genre}[/green]\n")

    # Initialize arc generator
    arc_gen = ArcGenerator(story, generator)

    # Generate arcs
    console.print(f"[bold yellow]⏳ Generating {count} arc outlines...[/bold yellow]")
    try:
        arcs = await arc_gen.generate_future_arcs(count=count, user_input="")

        console.print(f"[green]✅ Generated {len(arcs)} arcs successfully![/green]\n")
        
        # Display each arc
        for i, arc in enumerate(arcs, 1):
            console.print(f"[bold cyan]Arc {i}: {arc.title}[/bold cyan]")
            console.print(f"  [yellow]Description:[/yellow] {arc.description[:150]}...")
            console.print(f"  [yellow]Central Conflict:[/yellow] {arc.central_conflict[:100]}...")
            
            if arc.themes:
                console.print(f"  [yellow]Themes:[/yellow] {', '.join(arc.themes[:3])}")
            
            if arc.unresolved_mysteries:
                console.print(f"  [yellow]Mysteries:[/yellow] {len(arc.unresolved_mysteries)} unresolved")
            
            if arc.plot_hooks:
                console.print(f"  [yellow]Hooks:[/yellow] {len(arc.plot_hooks)} story hooks")
            
            console.print()

    except Exception as e:
        console.print(f"[red]Error generating arcs: {str(e)}[/red]")
        logger.error(f"Arc generation error: {e}", exc_info=True)

@app.command()
def test_arc_generation(
    story_id: str = typer.Option("veil_of_thornreach", help="Story ID to test with"),
    count: int = typer.Option(3, help="Number of arcs to generate")
):
    """Test arc generation with a story."""
    asyncio.run(test_arc_generation_async(story_id, count))

async def test_character_generation_async(story_id: str):
    """Test character generation for a story."""
    from app.engine.generators.character_generator import CharacterGenerator
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for character generation test"
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

    console.print(f"[cyan]Testing character parsing for story: {story_id}[/cyan]")

    # Load story
    logger.info(f"Loading story: {story_id}")
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found![/red]")
        return

    console.print(f"[green]Loaded story: {story.title}[/green]")
    console.print(f"[green]Genre: {story.genre}[/green]\n")

    # Load all components first
    from app.engine.story_runner import StoryRunner
    runner = StoryRunner(story)
    runner.load_all_components(story)
    
    console.print(f"[bold yellow]⏳ Parsing characters from existing segments...[/bold yellow]")
    
    try:
        # Initialize character generator
        char_gen = CharacterGenerator(story, generator)
        
        # Parse characters from existing segments
        characters = await char_gen.parse_characters_from_segments()

        if characters:
            console.print(f"[green]✅ Parsed {len(characters)} characters from segments![/green]\n")
            
            # Display each character
            for i, char in enumerate(characters[:5], 1):  # Show first 5
                console.print(f"[bold cyan]Character {i}: {char.name if hasattr(char, 'name') else 'Unknown'}[/bold cyan]")
                if hasattr(char, 'role'):
                    console.print(f"  [yellow]Role:[/yellow] {char.role}")
                if hasattr(char, 'description'):
                    desc = char.description if isinstance(char.description, str) else str(char.description)
                    console.print(f"  [yellow]Description:[/yellow] {desc[:100]}...")
                console.print()
            
            if len(characters) > 5:
                console.print(f"... and {len(characters) - 5} more characters")
        else:
            console.print("[yellow]No characters parsed from segments[/yellow]")

    except Exception as e:
        console.print(f"[red]Error parsing characters: {str(e)}[/red]")
        logger.error(f"Character parsing error: {e}", exc_info=True)

@app.command()
def test_character_generation(
    story_id: str = typer.Option("veil_of_thornreach", help="Story ID to test with")
):
    """Test character generation with a story."""
    asyncio.run(test_character_generation_async(story_id))

async def test_protagonist_selection_async(story_id: str):
    """Test protagonist selection for a story."""
    from app.engine.generators.protagonist_selector import ProtagonistSelector
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        message, suggestion = ErrorHandler.handle_error(
            ErrorType.MISSING_CONFIG,
            e,
            "Loading configuration for protagonist selection test"
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

    console.print(f"[cyan]Testing protagonist selection for story: {story_id}[/cyan]")

    # Load story
    logger.info(f"Loading story: {story_id}")
    story = Story.load(story_id, story_id)
    if not story:
        console.print(f"[red]Story '{story_id}' not found![/red]")
        return

    console.print(f"[green]Loaded story: {story.title}[/green]")
    console.print(f"[green]Genre: {story.genre}[/green]\n")

    # Load all components first
    from app.engine.story_runner import StoryRunner
    runner = StoryRunner(story)
    runner.load_all_components(story)

    # Initialize protagonist selector
    proto_sel = ProtagonistSelector(story, generator)

    # Select protagonist
    console.print("[bold yellow]⏳ Selecting protagonist...[/bold yellow]")
    try:
        protagonist = await proto_sel.select_or_develop_protagonist(
            user_choice=None
        )

        if protagonist:
            console.print("[green]✅ Protagonist selected successfully![/green]\n")
            
            console.print("[bold cyan]Selected Protagonist:[/bold cyan]")
            if hasattr(protagonist, 'name'):
                console.print(f"  [yellow]Name:[/yellow] {protagonist.name}")
            if hasattr(protagonist, 'id'):
                console.print(f"  [yellow]ID:[/yellow] {protagonist.id}")
            if hasattr(protagonist, 'description'):
                console.print(f"  [yellow]Description:[/yellow] {protagonist.description[:150]}...")
            if hasattr(protagonist, 'role'):
                console.print(f"  [yellow]Role:[/yellow] {protagonist.role}")
            if hasattr(protagonist, 'background'):
                console.print(f"  [yellow]Background:[/yellow] {protagonist.background[:150]}...")
            if hasattr(protagonist, 'arc_goals'):
                console.print(f"  [yellow]Arc Goals:[/yellow] {protagonist.arc_goals}")
        else:
            console.print("[yellow]No protagonist selected[/yellow]")

    except Exception as e:
        console.print(f"[red]Error selecting protagonist: {str(e)}[/red]")
        logger.error(f"Protagonist selection error: {e}", exc_info=True)

@app.command()
def test_protagonist_selection(
    story_id: str = typer.Option("veil_of_thornreach", help="Story ID to test with")
):
    """Test protagonist selection with a story."""
    asyncio.run(test_protagonist_selection_async(story_id))

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

if __name__ == "__main__":
    app()
