"""Story shape calculator for determining story structure."""

import logging
import json
from typing import Any, Dict
from app.models.story import Story
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.models.text_types import StoryShapeResponse
from app.engine.lenient_parser import LenientParser

logger = logging.getLogger("infinite_story.engine.generators.story_shape_calculator")


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
            
            # Request structured response with fallback
            response_text = await self.generator.generate_with_fallback(
                context_type="world",
                system_prompt="""You are a story structure expert.
Analyze a story and determine its optimal structure.
Return ONLY valid JSON with no additional text.""",
                user_prompt=prompt
            )
            
            # Extract JSON
            shape_data = self._parse_shape_response(response_text)
            
            # Create StoryShapeResponse
            shape = StoryShapeResponse(
                scale=shape_data.get('scale', 'medium'),
                num_fractions=shape_data.get('num_fractions', 3),
                num_locations=shape_data.get('num_locations', 10),
                characters_per_fraction=shape_data.get('characters_per_fraction', {'min': 2, 'max': 4}),
                num_independent_characters=shape_data.get('num_independent_characters', 2),
                reasoning=shape_data.get('reasoning', '')
            )
            
            logger.info(f"Calculated story shape: {shape.scale} with {shape.num_fractions} fractions")
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

Return ONLY valid JSON (no markdown, no explanation) with this structure:
{{
  "scale": "epic|large|medium|small",
  "num_fractions": <number 2-6>,
  "num_locations": <number 5-20>,
  "characters_per_fraction": {{"min": <number 2-4>, "max": <number 3-6>}},
  "num_independent_characters": <number 1-5>,
  "reasoning": "<brief explanation of why this structure works>"
}}

Consider:
- Scale: Is this an epic multi-act story or intimate narrative?
- Fractions: How many major story divisions/acts does this need?
- Locations: How many distinct places should the story span?
- Characters per fraction: How many main characters per act?
- Independent characters: How many antagonists/neutrals/side characters?"""
    
    def _parse_shape_response(self, response: Any) -> Dict[str, Any]:
        """Parse shape response into structured data."""
        
        # Try to extract content if it's an object
        content = response
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        else:
            content = str(response)
        
        logger.debug(f"Shape response content: {content[:200]}")
        
        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            json_str = str(content)
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0]
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0]
            
            data = json.loads(json_str.strip())
            
            # Validate required fields
            required = ['scale', 'num_fractions', 'num_locations', 'characters_per_fraction', 'num_independent_characters']
            if all(k in data for k in required):
                return data
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"JSON parsing failed: {e}")
        
        # Fallback to lenient parsing or defaults
        logger.warning("Using default story shape")
        return {
            'scale': 'medium',
            'num_fractions': 3,
            'num_locations': 10,
            'characters_per_fraction': {'min': 2, 'max': 4},
            'num_independent_characters': 2,
            'reasoning': 'Default balanced structure'
        }
