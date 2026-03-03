"""Story creation CLI module with new fraction-based world generation."""

import asyncio
import logging
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live

from app.models.story import Story
from app.models.story_context import StoryContext
from app.config import Config
from app.engine.openrouter_generator import OpenRouterGenerator
from app.engine.openai_generator import OpenAIGenerator
from app.engine.generators.world_description_generator import WorldDescriptionGenerator
from app.engine.generators.plot_description_generator import PlotDescriptionGenerator
from app.engine.generators.story_shape_calculator import StoryShapeCalculator
from app.engine.generators.fraction_generator import FractionGenerator
from app.engine.generators.location_generator_new import LocationGeneratorNew
from app.engine.generators.character_generator_new import CharacterGeneratorNew
from app.engine.generators.opening_scene_generator import OpeningSceneGenerator

console = Console()
logger = logging.getLogger("infinite_story.cli.story_creation")


async def create_story_ai_new(
    story_id: str,
    title: str,
    description: str,
    genre: str,
    world_input: str = ""
) -> str:
    """Create a story with new fraction-based world generation.
    
    PHASE 1: World Setup
    - Generate world description + fundamental truths + systems
    
    PHASE 2: Calculate Story Shape
    - LLM determines scale, counts, structure
    
    PHASE 3: Component Generation
    - Generate fractions → locations → characters
    
    Args:
        story_id: Unique story identifier
        title: Story title
        description: Story description
        genre: Story genre
        world_input: Optional user world vision
        
    Returns:
        The story ID
    """
    
    # Load configuration
    try:
        config = Config.load()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return ""
    
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
        f"[bold cyan]Creating Story with Fractions: {title}[/bold cyan]\n[yellow]Genre: {genre}[/yellow]",
        title="🎭 Story Creator",
        border_style="cyan"
    ))
    
    try:
        # Check if story already exists
        existing = Story.load(story_id, story_id)
        if existing:
            console.print(f"[red]Story '{story_id}' already exists![/red]")
            return ""
        
        # Create story object
        story = Story(
            id=story_id,
            story_id=story_id,
            title=title,
            description=description,
            genre=genre,
            start_segment_id="opening"
        )
        
        # ========================
        # PHASE 1: WORLD SETUP
        # ========================
        
        console.print("\n[bold yellow]⏳ Phase 1: Setting up the world...[/bold yellow]")
        
        # Step 1.1: Generate world description
        console.print("[yellow]  Step 1.1: Generating world description...[/yellow]")
        world_gen = WorldDescriptionGenerator(generator)
        world_context = await world_gen.generate_world_description(story=story, user_input=world_input)
        console.print("[green]  ✅ World description generated![/green]")
        
        # Step 1.2: Generate plot description
        console.print("[yellow]  Step 1.2: Generating plot...[/yellow]")
        plot_gen = PlotDescriptionGenerator(generator)
        world_context = await plot_gen.generate_plot_description(story=story, world_context=world_context)
        console.print("[green]  ✅ Plot description generated![/green]")
        
        # ========================
        # PHASE 2: STORY SHAPE
        # ========================
        
        console.print("\n[bold yellow]⏳ Phase 2: Calculating story structure...[/bold yellow]")
        shape_calc = StoryShapeCalculator(generator)
        story_shape = await shape_calc.calculate_story_shape(story=story, world_context=world_context)
        console.print(f"[green]✅ Story shape calculated:[/green]")
        console.print(f"  [cyan]Scale: {story_shape.scale}[/cyan]")
        console.print(f"  [cyan]Fractions: {story_shape.num_fractions}[/cyan]")
        console.print(f"  [cyan]Locations: {story_shape.num_locations}[/cyan]")
        console.print(f"  [cyan]Characters per fraction: {story_shape.characters_per_fraction.get('min', 2)}-{story_shape.characters_per_fraction.get('max', 4)}[/cyan]")
        console.print(f"  [cyan]Independent characters: {story_shape.num_independent_characters}[/cyan]")
        
        # ========================
        # PHASE 3: GENERATION
        # ========================
        
        console.print("\n[bold yellow]⏳ Phase 3: Generating story components...[/bold yellow]")
        
        # Step 3.1: Generate fractions
        console.print("[yellow]  Step 3.1: Generating fractions...[/yellow]")
        frac_gen = FractionGenerator(generator)
        fractions = await frac_gen.generate_fractions(
            story=story,
            world_context=world_context,
            story_shape=story_shape
        )
        console.print(f"[green]  ✅ Generated {len(fractions)} fractions![/green]")
        for frac in fractions:
            story.add_fraction(frac)
        
        # Step 3.2: Generate locations
        console.print("[yellow]  Step 3.2: Generating locations...[/yellow]")
        loc_gen = LocationGeneratorNew(story, generator)
        locations = await loc_gen.generate_locations(
            world_context=world_context,
            fractions=fractions,
            story_shape=story_shape
        )
        console.print(f"[green]  ✅ Generated {len(locations)} locations![/green]")
        for loc in locations:
            story.add_location(loc)
        
        # Step 3.3: Generate fraction-based characters
        console.print("[yellow]  Step 3.3: Generating faction characters...[/yellow]")
        char_gen = CharacterGeneratorNew(story, generator)
        faction_characters = await char_gen.generate_fraction_characters(
            world_context=world_context,
            fractions=fractions,
            locations=locations,
            story_shape=story_shape
        )
        console.print(f"[green]  ✅ Generated {len(faction_characters)} faction characters![/green]")
        for char in faction_characters:
            story.add_character(char)
        
        # Step 3.4: Generate independent characters
        console.print("[yellow]  Step 3.4: Generating independent characters...[/yellow]")
        independent_characters = await char_gen.generate_independent_characters(
            world_context=world_context,
            fractions=fractions,
            locations=locations,
            existing_characters=faction_characters,
            story_shape=story_shape
        )
        console.print(f"[green]  ✅ Generated {len(independent_characters)} independent characters![/green]")
        for char in independent_characters:
            story.add_character(char)
        
        # ========================
        # OPENING SCENE & CHOICES
        # ========================
        
        console.print("\n[bold yellow]⏳ Phase 4: Creating opening scene...[/bold yellow]")
        opening_gen = OpeningSceneGenerator(generator)
        opening_segment = await opening_gen.generate_opening_scene(
            story=story,
            world_context=world_context
        )
        console.print("[green]  ✅ Opening scene generated![/green]")
        
        console.print("[yellow]  Step 4.2: Generating opening choices...[/yellow]")
        opening_choices = await opening_gen.generate_opening_choices(
            story=story,
            world_context=world_context,
            opening_segment=opening_segment
        )
        console.print(f"[green]  ✅ Generated {len(opening_choices)} opening choices![/green]")
        
        story.add_segment(opening_segment)
        for choice in opening_choices:
            story.add_choice(choice)
        
        story.start_segment_id = opening_segment.id
        
        # ========================
        # SAVE
        # ========================
        
        console.print("\n[bold yellow]💾 Saving story...[/bold yellow]")
        story.save()
        world_context.save()
        for frac in fractions:
            frac.save()
        for loc in locations:
            loc.save()
        for char in faction_characters + independent_characters:
            char.save()
        opening_segment.save()
        for choice in opening_choices:
            choice.save()
        
        console.print(Panel(
            f"""[green]✅ Story '{title}' created successfully![/green]

[cyan]Story ID: {story_id}[/cyan]
[cyan]Genre: {genre}[/cyan]

[green]✨ Generated:[/green]
• World with fundamental truths
• Plot description
• {len(fractions)} Factions
• {len(locations)} Locations
• {len(faction_characters + independent_characters)} Characters
• Opening scene with {len(opening_choices)} choices

[yellow]🚀 Next:[/yellow]
Play the story to explore the world and its factions.""",
            title="Success",
            border_style="green"
        ))
        logger.info(f"Story created: {story_id}")
        
        return story_id
        
    except Exception as e:
        console.print(f"[red]❌ Error creating story: {e}[/red]")
        logger.error(f"Story creation failed: {e}", exc_info=True)
        return ""
