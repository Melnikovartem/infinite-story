"""Story shape calculator for determining story structure."""

import logging
from typing import Any, Dict
from app.models.story import Story
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.models.text_types import StoryShapeResponse
from app.utils.ai_response_parser import ResponseSchema, FieldSpec

logger = logging.getLogger("infinite_story.engine.generators.story_shape_calculator")

# Schema for story shape calculation
_SHAPE_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("scale", type="str", required=True, aliases=["story_scale", "size"]),
        FieldSpec("num_factions", type="int", required=True, aliases=["factions", "num_fractions", "total_factions"]),
        FieldSpec("num_locations", type="int", required=True, aliases=["locations", "total_locations"]),
        FieldSpec("characters_per_faction", type="dict", required=True, aliases=["chars_per_faction", "characters_per_fraction"]),
        FieldSpec("num_independent_characters", type="int", required=True, aliases=["independent_characters", "independents"]),
        FieldSpec("reasoning", type="str", aliases=["explanation", "rationale"]),
    ],
    expect_array=False,
)

_SHAPE_FALLBACK = {
    "scale": "medium",
    "num_factions": 3,
    "num_locations": 10,
    "characters_per_faction": {"min": 2, "max": 4},
    "num_independent_characters": 2,
    "reasoning": "Default balanced structure",
}


class StoryShapeCalculator:
    """Calculate story shape (scale, counts, structure)."""
    
    def __init__(self, generator: TextGenerator):
        """Initialize story shape calculator.
        
        Args:
            generator: AI text generator for content generation
        """
        self.generator = generator
    
    async def calculate_story_shape(
        self,
        story: Story,
        world_context: StoryContext
    ) -> StoryShapeResponse:
        """Calculate the shape and structure of the story.
        
        Args:
            story: Story instance
            world_context: StoryContext with world and plot data
            
        Returns:
            StoryShapeResponse with calculated counts and scales
            
        Raises:
            ValueError: If calculation fails
        """
        try:
            logger.info(f"Calculating story shape for story '{story.title}'")
            
            # Build prompt
            prompt = self._build_shape_prompt(
                story.title,
                story.description,
                story.genre,
                world_context
            )
            
            # Call generate_structured with schema
            shape_data = await self.generator.generate_structured(
                system_prompt="You are a story structure expert. Analyze a story and determine its optimal structure.",
                user_prompt=prompt,
                schema=_SHAPE_SCHEMA,
                fallback_defaults=[_SHAPE_FALLBACK],
            )
            
            # Ensure characters_per_faction is a dict with min/max
            cpf = shape_data.get('characters_per_faction', {'min': 2, 'max': 4})
            if not isinstance(cpf, dict):
                cpf = {'min': 2, 'max': 4}
            
            # Create StoryShapeResponse
            shape = StoryShapeResponse(
                scale=shape_data.get('scale', 'medium'),
                num_factions=shape_data.get('num_factions', 3),
                num_locations=shape_data.get('num_locations', 10),
                characters_per_faction=cpf,
                num_independent_characters=shape_data.get('num_independent_characters', 2),
                reasoning=shape_data.get('reasoning', '')
            )
            
            logger.info(f"Calculated story shape: {shape.scale} with {shape.num_factions} factions")
            return shape
            
        except Exception as e:
            logger.error(f"Failed to calculate story shape: {e}", exc_info=True)
            raise ValueError(f"Story shape calculation failed: {str(e)}")
    
    def _build_shape_prompt(
        self,
        title: str,
        description: str,
        genre: str,
        world_context: StoryContext
    ) -> str:
        """Build prompt for story shape calculation."""
        
        # Extract world and plot info
        world_desc = ""
        plot_desc = ""
        central_conflicts = []
        themes = []
        
        if isinstance(world_context.worldbuilding, dict):
            world_desc = world_context.worldbuilding.get('world_description', '')
            plot_desc = world_context.worldbuilding.get('plot_description', '')
            central_conflicts = world_context.worldbuilding.get('central_conflicts', [])
            themes = world_context.worldbuilding.get('story_themes', [])
        
        conflicts_text = "\n".join([f"- {c}" for c in central_conflicts[:3]])
        themes_text = ", ".join(themes[:4])
        
        return f"""Analyze this story and determine its optimal structure.

Title: {title}
Description: {description}
Genre: {genre}

World: {world_desc[:200]}

Plot: {plot_desc}

Central Conflicts:
{conflicts_text}

Themes: {themes_text}

Consider:
- Scale: Is this an epic multi-act story or intimate narrative?
- Factions: How many major factions/groups does this story need?
- Locations: How many distinct places should the story span?
- Characters per faction: How many main characters per faction?
- Independent characters: How many antagonists/neutrals/side characters?"""
