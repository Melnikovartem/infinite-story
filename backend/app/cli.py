import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from app.models.story_base import LOCAL_DATA_DIR
from app.models.story import Story
from app.engine.story_runner import StoryRunner

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

@app.command()
def run_story():
    """Run a story after selection."""
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
            
            # Get user input
            while True:
                try:
                    choice = Prompt.ask("Select an option", choices=[str(i) for i in range(1, 5)])
                    break
                except ValueError:
                    console.print("[red]Invalid option. Please try again.[/red]")
            
            if choice == "3" and len(choices) > 2:
                # Show all options
                console.print("\n[bold]All available options:[/bold]")
                for i, choice in enumerate(choices, 1):
                    console.print(f"{i}. {choice.text}")
                while True:
                    try:
                        sub_choice = Prompt.ask("Select an option", choices=[str(i) for i in range(1, len(choices) + 1)])
                        runner.make_choice(choices[int(sub_choice) - 1].id)
                        break
                    except ValueError:
                        console.print("[red]Invalid option. Please try again.[/red]")
            
            elif choice == "4":
                # Custom choice
                custom_choice = Prompt.ask("Enter your choice")
                if len(custom_choice) > 200:
                    console.print("[red]Choice is too long. Maximum length is 200 characters.[/red]")
                    continue
                # TODO: Implement custom choice handling
                console.print("[yellow]Custom choices are not yet implemented.[/yellow]")
            
            else:
                # Handle top 2 choices
                if int(choice) <= len(choices):
                    runner.make_choice(choices[int(choice) - 1].id)
                else:
                    console.print("[red]Invalid option. Please try again.[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    app()
