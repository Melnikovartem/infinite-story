"""Test the new fraction-based story creation system."""

import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.story import Story
from app.models.story_context import StoryContext
from app.models.story_fraction import StoryFraction
from app.models.story_location import StoryLocation
from app.models.story_character import StoryCharacter
from app.models.text_types import StoryShapeResponse


class MockTextGenerator:
    """Mock text generator for testing without API calls."""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate(self, system_prompt: str = "", user_prompt: str = "", context_type: str = ""):
        """Mock generation that returns realistic test data."""
        self.call_count += 1
        
        # Return different responses based on context
        if "world" in user_prompt.lower():
            return MagicMock(
                content="In this world, ancient civilizations left behind technological marvels that defy modern understanding. The land is divided into distinct regions, each with its own culture, resources, and power structures. Magic and technology coexist in an uneasy balance.",
                status="success",
                error=None
            )
        elif "plot" in user_prompt.lower():
            return MagicMock(
                content="The plot revolves around competing factions seeking control of ancient artifacts. The central conflict is between those who wish to preserve the old ways and those who embrace the new. Hidden conspiracies threaten to destabilize the entire world.",
                status="success",
                error=None
            )
        elif "shape" in user_prompt.lower():
            return MagicMock(
                content='{"scale": "epic", "num_fractions": 3, "num_locations": 5, "characters_per_fraction": {"min": 2, "max": 4}, "num_independent_characters": 2}',
                status="success",
                error=None
            )
        elif "fraction" in user_prompt.lower() and "Generate" in user_prompt:
            return MagicMock(
                content='[{"name": "The Keepers", "short_description": "Guardians of ancient knowledge", "full_description": "A faction dedicated to preserving ancient artifacts and knowledge. They are secretive, scholarly, and believe that some technologies are too dangerous for the world.", "main_goal": "Protect and control access to ancient artifacts", "themes": ["Knowledge", "Preservation", "Secrecy"], "tone": "Mysterious", "central_conflict": "Preventing others from accessing dangerous artifacts"}]',
                status="success",
                error=None
            )
        elif "location" in user_prompt.lower():
            return MagicMock(
                content='[{"name": "The Ruined Archive", "short_description": "An ancient library in decay", "full_description": "Once a grand repository of knowledge, this location now stands partially buried and overgrown. Its stone halls echo with whispers of forgotten civilizations.", "region": "Northern Wastes", "population": "Few scholars and monks", "key_features": ["Ancient texts", "Collapsed sections", "Hidden chambers"], "associated_fractions": ["frac_1"], "importance": "major"}]',
                status="success",
                error=None
            )
        elif "character" in user_prompt.lower():
            return MagicMock(
                content='[{"name": "Aria", "short_description": "A curious archaeologist", "full_description": "Aria is a brilliant but reckless archaeologist obsessed with uncovering the truth about the ancient world. She has few allies but boundless determination.", "role": "Explorer", "personality": "Curious, determined, reckless", "goals": "Uncover the truth of the ancient world", "relationships": []}]',
                status="success",
                error=None
            )
        elif "opening" in user_prompt.lower() and "scene" in user_prompt.lower():
            return MagicMock(
                content="The morning mist clings to the ancient stones as you approach the entrance. Behind you, the world you knew fades into memory. Ahead lies mystery, danger, and the possibility of changing everything. Your heart races with anticipation. What do you do?",
                status="success",
                error=None
            )
        elif "choice" in user_prompt.lower():
            return MagicMock(
                content="1. Enter the ruins with caution, searching for signs of civilization\n2. Follow the faint trail of smoke rising from deeper within\n3. Scout the perimeter first to understand what dangers await",
                status="success",
                error=None
            )
        else:
            return MagicMock(
                content="Generated content for testing",
                status="success",
                error=None
            )


async def test_story_creation():
    """Test the complete story creation pipeline."""
    print("\n" + "="*70)
    print("Testing Fraction-Based Story Creation System")
    print("="*70)
    
    # Create story
    print("\n[1] Creating story object...")
    story = Story(
        id="test_story_001",
        story_id="test_story_001",
        title="The Last Explorer",
        description="A solitary adventurer journeys through a world where ancient ruins hold forgotten knowledge",
        genre="Adventure",
        start_segment_id="opening"
    )
    print(f"✅ Story created: {story.title}")
    
    # Create mock generator
    print("\n[2] Initializing mock generator...")
    generator = MockTextGenerator()
    print(f"✅ Mock generator ready")
    
    # Test world generation
    print("\n[3] Testing world description generation...")
    from app.engine.generators.world_description_generator import WorldDescriptionGenerator
    world_gen = WorldDescriptionGenerator(generator)
    world_context = await world_gen.generate_world_description(story=story, user_input="")
    world_desc = world_context.worldbuilding.get('world_description', 'No description') if isinstance(world_context.worldbuilding, dict) else str(world_context.worldbuilding)
    print(f"✅ World description generated: {world_desc[:60]}...")
    
    # Test plot generation
    print("\n[4] Testing plot description generation...")
    from app.engine.generators.plot_description_generator import PlotDescriptionGenerator
    plot_gen = PlotDescriptionGenerator(generator)
    world_context = await plot_gen.generate_plot_description(story=story, world_context=world_context)
    plot_desc = world_context.worldbuilding.get('plot_description', 'No plot') if isinstance(world_context.worldbuilding, dict) else str(world_context.worldbuilding)
    print(f"✅ Plot description generated: {plot_desc[:60]}...")
    
    # Test story shape calculation
    print("\n[5] Testing story shape calculation...")
    from app.engine.generators.story_shape_calculator import StoryShapeCalculator
    shape_calc = StoryShapeCalculator(generator)
    story_shape = await shape_calc.calculate_story_shape(story=story, world_context=world_context)
    print(f"✅ Story shape calculated:")
    print(f"   - Scale: {story_shape.scale}")
    print(f"   - Fractions: {story_shape.num_fractions}")
    print(f"   - Locations: {story_shape.num_locations}")
    print(f"   - Characters per fraction: {story_shape.characters_per_fraction.get('min', 2)}-{story_shape.characters_per_fraction.get('max', 4)}")
    
    # Test fraction generation
    print("\n[6] Testing fraction generation...")
    from app.engine.generators.fraction_generator import FractionGenerator
    frac_gen = FractionGenerator(generator)
    fractions = await frac_gen.generate_fractions(story=story, world_context=world_context, story_shape=story_shape)
    for frac in fractions:
        story.add_fraction(frac)
    print(f"✅ Generated {len(fractions)} fractions:")
    for frac in fractions:
        print(f"   - {frac.name if hasattr(frac, 'name') else 'Unknown'}")
    
    # Test location generation
    print("\n[7] Testing location generation...")
    from app.engine.generators.location_generator_new import LocationGeneratorNew
    loc_gen = LocationGeneratorNew(story, generator)
    locations = await loc_gen.generate_locations(
        world_context=world_context,
        fractions=fractions,
        story_shape=story_shape
    )
    for loc in locations:
        story.add_location(loc)
    print(f"✅ Generated {len(locations)} locations:")
    for loc in locations:
        print(f"   - {loc.name if hasattr(loc, 'name') else 'Unknown'}")
    
    # Test character generation
    print("\n[8] Testing character generation...")
    from app.engine.generators.character_generator_new import CharacterGeneratorNew
    char_gen = CharacterGeneratorNew(story, generator)
    
    faction_characters = await char_gen.generate_fraction_characters(
        world_context=world_context,
        fractions=fractions,
        locations=locations,
        story_shape=story_shape
    )
    for char in faction_characters:
        story.add_character(char)
    
    independent_characters = await char_gen.generate_independent_characters(
        world_context=world_context,
        fractions=fractions,
        locations=locations,
        existing_characters=faction_characters,
        story_shape=story_shape
    )
    for char in independent_characters:
        story.add_character(char)
    
    all_characters = faction_characters + independent_characters
    print(f"✅ Generated {len(all_characters)} characters:")
    print(f"   - {len(faction_characters)} faction characters")
    print(f"   - {len(independent_characters)} independent characters")
    
    # Test opening scene generation
    print("\n[9] Testing opening scene generation...")
    from app.engine.generators.opening_scene_generator import OpeningSceneGenerator
    opening_gen = OpeningSceneGenerator(generator)
    opening_segment = await opening_gen.generate_opening_scene(story=story, world_context=world_context)
    story.add_segment(opening_segment)
    print(f"✅ Opening scene generated:")
    if opening_segment.text_blocks:
        content = opening_segment.text_blocks[0].content if hasattr(opening_segment.text_blocks[0], 'content') else str(opening_segment.text_blocks[0])
        print(f"   {content[:80]}...")
    
    # Test opening choices generation
    print("\n[10] Testing opening choices generation...")
    opening_choices = await opening_gen.generate_opening_choices(
        story=story,
        world_context=world_context,
        opening_segment=opening_segment
    )
    for choice in opening_choices:
        story.add_choice(choice)
    print(f"✅ Generated {len(opening_choices)} opening choices:")
    for i, choice in enumerate(opening_choices, 1):
        print(f"   {i}. {choice.text if hasattr(choice, 'text') else 'Choice'}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print(f"\nStory Summary:")
    print(f"  Title: {story.title}")
    print(f"  ID: {story.id}")
    print(f"  Fractions: {len(story.get_all_fractions())}")
    print(f"  Locations: {len(story.get_all_locations())}")
    print(f"  Characters: {len(story.get_all_characters())}")
    print(f"  Segments: {len(story.get_all_segments())}")
    print(f"  Choices: {len(story.get_all_choices())}")
    print("\n" + "="*70 + "\n")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_story_creation())
    sys.exit(0 if result else 1)
