import json
import asyncio
import logging
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

class RunMode(str, Enum):
    """CLI display modes."""
    IMMERSIVE = "immersive"
    DEBUG = "debug"

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
                await _execute_choice(runner, choice_id, generator, is_debug=False)
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

async def _run_debug_mode(runner: StoryRunner, generator):
    """Run story in debug mode - full transparency."""
    from app.ui.debug_display import display_segment_debug, display_next_context_debug, prompt_choice_debug
    
    try:
        logger.info("[DEBUG_MODE_START] Starting debug mode game loop")
        while runner.is_running:
            logger.debug(f"[DEBUG_LOOP_ITER] Game loop iteration. Current segment: {runner.current_segment.id if runner.current_segment else 'None'}")
            
            # Display with full context
            if runner.current_segment:
                logger.debug(f"[DEBUG_DISPLAY_SEG] Displaying segment: {runner.current_segment.id}")
                display_segment_debug(runner.current_segment)
            
            # Show generation context for next choice
            try:
                logger.debug("[DEBUG_DISPLAY_CONTEXT] Displaying generation context")
                display_next_context_debug(runner, runner.current_segment)
            except Exception as e:
                logger.debug(f"Could not display next context: {e}")
            
            # Get choices
            logger.debug("[DEBUG_GET_CHOICES] Getting available choices")
            choices = runner.get_available_choices()
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
                logger.info("Story ended - no more choices available")
                break
            
            logger.debug(f"[DEBUG_CHOICES_COUNT] Found {len(choices)} available choices")
            
            # Get user choice
            logger.debug("[DEBUG_PROMPT_CHOICE] Waiting for user choice input")
            choice_id = prompt_choice_debug(runner.current_segment, choices)
            logger.debug(f"[DEBUG_CHOICE_SELECTED] User selected choice: {choice_id}")
            
            # Execute choice
            try:
                logger.debug(f"[DEBUG_EXEC_CHOICE] Calling _execute_choice for choice: {choice_id}")
                await _execute_choice(runner, choice_id, generator, is_debug=True)
                logger.debug(f"[DEBUG_EXEC_CHOICE_DONE] Choice execution completed")
            except Exception as e:
                error_type, technical_msg = handle_api_error(e)
                message, suggestion = ErrorHandler.handle_error(
                    error_type,
                    e,
                    "Processing your choice"
                )
                console.print(f"[red]Error: {message}[/red]")
                console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
                logger.error(f"[DEBUG_EXEC_CHOICE_ERROR] Choice execution failed: {str(e)}", exc_info=True)
                continue
            
            # Auto-save state
            logger.debug("[DEBUG_SAVE_STATE] Saving game state")
            runner.save_state()
            logger.debug("[DEBUG_SAVE_STATE_DONE] Game state saved")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

async def _execute_choice(runner: StoryRunner, choice_id: str, generator, is_debug: bool = False):
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
        if is_debug:
            console.print(f"\n[cyan]Navigated to segment: {runner.current_segment.id}[/cyan]")
        logger.debug(f"[EXEC_CHOICE_NAV_DONE] Navigation complete. Current segment: {runner.current_segment.id}")
    else:
        # Generate new segment
        logger.debug(f"[EXEC_CHOICE_GEN_START] Starting generation for choice: {choice.text}")
        with console.status("[bold yellow]Generating next scene...[/bold yellow]", spinner="dots"):
            logger.debug(f"[EXEC_CHOICE_GEN_CALL] Calling generate_next_scene()")
            new_segment = await runner.current_segment.generate_next_scene(choice, generator)
            logger.debug(f"[EXEC_CHOICE_GEN_RECEIVED] Received new segment: {new_segment.id}")
            runner.current_segment = new_segment
            runner.visited_segments.add(new_segment.id)
            console.print("[green]Scene generated successfully![/green]")
            logger.debug(f"[EXEC_CHOICE_GEN_DONE] New segment set as current: {new_segment.id}")
            
            if is_debug:
                console.print(f"\n[cyan]New segment: {new_segment.id}[/cyan]")

async def run_story_async(story_name: str = None, mode: RunMode = RunMode.IMMERSIVE, resume: bool = False):
    """Run a story in immersive or debug mode.
    
    Args:
        story_name: Optional story ID to run directly (skips selection)
        mode: RunMode.IMMERSIVE (default) or RunMode.DEBUG
        resume: Resume from previous session if available
    """
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
        else:
            await _run_debug_mode(runner, generator)
    
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
        help="CLI mode: immersive (default, beautiful narrative) or debug (transparent, all details)"
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume from previous session if available"
    ),
):
    """
    Run a story with two modes:
    
    Immersive (default):
      python -m app.cli run-story story_name
      Beautiful narrative experience, focus on prose.
    
    Debug:
      python -m app.cli run-story story_name --mode debug
      Transparent view of segments, choices, context.
    """
    asyncio.run(run_story_async(story_name=story, mode=mode, resume=resume))

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
