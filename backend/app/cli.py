import json
import asyncio
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
from app.config import Config

app = typer.Typer()
console = Console()

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
    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        console.print("\n[yellow]Please create a .env file based on .env.example[/yellow]")
        return

    # Initialize generator
    generator = OpenAIGenerator(
        api_base=config.generator.base_url,
        api_key=config.generator.api_key,
        model=config.generator.model,
        temperature=config.generator.temperature,
        max_tokens=config.generator.max_tokens
    )

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

    console.print(Panel(
        f"[green]Starting story: {selected_story.get('title', 'Untitled')}[/green]",
        title="Story Runner",
        border_style="green"
    ))

    # Initialize story runner with selected story
    story = Story.load(selected_story["id"], selected_story["id"])
    if not story:
        console.print("[red]Failed to load story![/red]")
        return

    runner = StoryRunner(story)
    try:
        # Try to load previous state
        if runner.load_state():
            console.print("[yellow]Resuming from saved state...[/yellow]")
            # Need to load components first
            runner.load_all_components(story)
            console.print(f"[green]Resumed at segment: {runner.current_segment.short_description}[/green]")
        else:
            # Start from beginning
            runner.start()
            console.print("[green]Story started successfully![/green]")

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

            # Check if there are any choices
            if not choices:
                console.print("\n[yellow]No more choices available. The story has ended.[/yellow]")
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
                            console.print(f"[red]Error generating scene: {str(e)}[/red]")
                            console.print("[yellow]Please try a different choice or check your API configuration.[/yellow]")
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

if __name__ == "__main__":
    app()
