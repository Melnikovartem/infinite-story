import json
import asyncio
import logging
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

async def run_story_async():
    """Run a story after selection (async version)."""
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
        console.print(f"[cyan]Using OpenAI with model: {config.generator.model}[/cyan]")

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
        f"[green]Starting story: {selected_story.get('title', 'Untitled')}[/green]",
        title="Story Runner",
        border_style="green"
    ))

    # Initialize story runner with selected story
    logger.info(f"Loading story data for: {selected_story['id']}")
    story = Story.load(selected_story["id"], selected_story["id"])
    if not story:
        console.print("[red]Failed to load story![/red]")
        logger.error(f"Failed to load story: {selected_story['id']}")
        return

    logger.info(f"Initializing StoryRunner for: {story.id}")
    runner = StoryRunner(story)
    try:
        # Load all story components first (required before accessing segments)
        runner.load_all_components(story)
        
        # Then try to load previous state
        if runner.load_state():
            console.print("[yellow]Resuming from saved state...[/yellow]")
            logger.info("Loaded previous state, resuming story")
            console.print(f"[green]Resumed at segment: {runner.current_segment.short_description}[/green]")
            logger.info(f"Resumed at segment: {runner.current_segment.id}")
        else:
            # Start from beginning
            logger.info("No previous state found, starting from beginning")
            runner.start()
            console.print("[green]Story started successfully![/green]")
            logger.info(f"Story started at segment: {runner.current_segment.id}")

        # Main story loop
        while True:
            # Display current segment
            if runner.current_segment:
                console.print("\n" + "="*80)
                for block in runner.current_segment.text_blocks:
                    if block.type == "scene_title":
                        console.print(f"\n[bold cyan]{block.content}[/bold cyan]")
                    elif block.type == "narrator_describing":
                        console.print(f"\n{block.content}")
                    elif block.type == "character_speech":
                        console.print(f"\n[bold]{block.character}:[/bold] {block.content}")
                    elif block.type == "sfx":
                        console.print(f"\n[italic]{block.content}[/italic]")
                console.print("\n" + "="*80)

            # Get available choices
            choices = runner.get_available_choices()
            logger.debug(f"Current segment '{runner.current_segment.id}' has {len(choices)} available choices")

            # Check if there are any choices
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
                logger.info("Story ended - no more choices available")
                break

            # Display options
            console.print("\n[bold]What would you like to do?[/bold]")

            # Display top 2 choices if available
            for i, choice in enumerate(choices[:2], 1):
                console.print(f"{i}. {choice.text}")

            # Display "Show all options" if there are more than 2 choices
            if len(choices) > 2:
                console.print("3. Show all options")

            # Display custom choice option
            console.print("4. Write your own choice")
            console.print("5. Save and exit")
            console.print("6. Exit without saving")

            # Get user input
            max_option = 6
            while True:
                try:
                    user_choice = Prompt.ask("Select an option", choices=[str(i) for i in range(1, max_option + 1)])
                    break
                except ValueError:
                    console.print("[red]Invalid option. Please try again.[/red]")

            # Handle exit options
            if user_choice == "5":
                # Save and exit
                runner.save_state()
                console.print("[green]Progress saved![/green]")
                console.print("[yellow]Thanks for playing![/yellow]")
                break
            elif user_choice == "6":
                # Exit without saving
                console.print("[yellow]Thanks for playing![/yellow]")
                break

            selected_choice = None

            if user_choice == "3" and len(choices) > 2:
                # Show all options
                console.print("\n[bold]All available options:[/bold]")
                for i, choice in enumerate(choices, 1):
                    console.print(f"{i}. {choice.text}")
                while True:
                    try:
                        sub_choice = Prompt.ask("Select an option", choices=[str(i) for i in range(1, len(choices) + 1)])
                        selected_choice = choices[int(sub_choice) - 1]
                        break
                    except ValueError:
                        console.print("[red]Invalid option. Please try again.[/red]")

            elif user_choice == "4":
                # Custom choice
                custom_choice_text = Prompt.ask("Enter your choice")
                if len(custom_choice_text) > 200:
                    console.print("[red]Choice is too long. Maximum length is 200 characters.[/red]")
                    continue

                # Create a new choice from user input
                choice_id = f"custom_choice_{len(runner.story.get_all_choices()) + 1}"
                selected_choice = StoryChoice(
                    story=runner.story,
                    id=choice_id,
                    from_segment_id=runner.current_segment.id,
                    to_segment_id=None,  # Will be set by generate_next_scene
                    text=custom_choice_text
                )
                # Add to current segment's outgoing choices
                runner.current_segment.add_outgoing_choice(selected_choice)

            else:
                # Handle top 2 choices
                choice_num = int(user_choice)
                if choice_num <= len(choices):
                    selected_choice = choices[choice_num - 1]
                else:
                    console.print("[red]Invalid option. Please try again.[/red]")
                    continue

            # Process the selected choice
            if selected_choice:
                # Check if the choice leads to an existing segment
                if selected_choice.to_segment_id:
                    # Navigate to existing segment
                    runner.make_choice(selected_choice.id)
                else:
                    # Generate new segment with AI
                    with console.status("[bold yellow]Generating next scene...[/bold yellow]", spinner="dots"):
                        try:
                            new_segment = await runner.current_segment.generate_next_scene(
                                selected_choice,
                                generator
                            )

                            # Update runner state
                            runner.current_segment = new_segment
                            runner.visited_segments.add(new_segment.id)

                            # Auto-save state after generating new content
                            runner.save_state()

                            console.print("[green]Scene generated successfully![/green]")

                        except Exception as e:
                            error_type, technical_msg = handle_api_error(e)
                            message, suggestion = ErrorHandler.handle_error(
                                error_type,
                                e,
                                "Generating next scene"
                            )
                            console.print(f"[red]Error: {message}[/red]")
                            console.print(f"\n[yellow]Suggestion:[/yellow]\n{suggestion}")
                            continue

    except KeyboardInterrupt:
        console.print("\n[yellow]Story interrupted. Thanks for playing![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

@app.command()
def run_story():
    """Run a story after selection."""
    asyncio.run(run_story_async())

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
