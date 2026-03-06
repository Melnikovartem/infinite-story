"""World description generator for creating world context."""

import logging
from typing import Dict, Any, List

from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import ResponseSchema, FieldSpec

logger = logging.getLogger("infinite_story.engine.generators.world_generator")


# Reuse the same schema as WorldDescriptionGenerator — they do the same thing
_WORLD_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("world_description", type="str", required=True, aliases=["description", "overview", "world_overview"]),
        FieldSpec("fundamental_truths", type="list", required=True, aliases=["truths", "core_facts", "world_rules", "major_events"]),
        FieldSpec("magic_system", type="str", aliases=["magic", "technology_system"]),
        FieldSpec("technology_level", type="str", aliases=["technology", "tech_level"]),
        FieldSpec("political_system", type="str", aliases=["government", "politics", "power_structure"]),
        FieldSpec("cultures", type="list", aliases=["culture", "societies"]),
        FieldSpec("history", type="str", aliases=["backstory", "world_history"]),
        FieldSpec("religions", type="list", aliases=["religion", "beliefs"]),
    ],
    expect_array=False,
)

_WORLD_FALLBACK = {
    "world_description": "A mysterious world waiting to be discovered",
    "fundamental_truths": [
        "The world operates under its own fundamental laws",
        "History shapes the present in unexpected ways",
        "Power and conflict drive civilization forward",
        "Magic or technology defines what's possible",
        "Adventure and discovery await the brave",
    ],
    "magic_system": None,
    "technology_level": None,
    "political_system": None,
    "cultures": [],
    "history": None,
    "religions": [],
}


class WorldGenerator:
    """Generate world descriptions and context for stories."""
    
    def __init__(self, generator: TextGenerator):
        """Initialize world generator.
        
        Args:
            generator: AI text generator for content generation
        """
        self.generator = generator
    
    async def generate_world_context(
        self,
        story,
        user_input: str = ""
    ) -> StoryContext:
        """Generate world context from story details.
        
        Args:
            story: Story instance to generate context for
            user_input: Optional user-provided world information
            
        Returns:
            StoryContext with fundamental truths and worldbuilding
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating world context for story '{story.title}'")
            
            # Build prompt
            prompt = self._build_world_prompt(
                story.title,
                story.description,
                user_input
            )
            
            # Generate via generate_structured
            world_data = await self.generator.generate_structured(
                system_prompt="You are a world-building expert creating rich, detailed fantasy/sci-fi worlds.",
                user_prompt=prompt,
                schema=_WORLD_SCHEMA,
                fallback_defaults=[_WORLD_FALLBACK],
            )
            
            # Extract fundamental truths
            fundamental_truths = world_data.get('fundamental_truths', _WORLD_FALLBACK['fundamental_truths'])
            if isinstance(fundamental_truths, str):
                fundamental_truths = [fundamental_truths]
            if not fundamental_truths:
                fundamental_truths = list(_WORLD_FALLBACK['fundamental_truths'])
            
            # Build worldbuilding dict
            worldbuilding = {}
            if world_data.get('world_description'):
                worldbuilding['world_description'] = world_data['world_description']
            if world_data.get('history'):
                worldbuilding['history'] = world_data['history']
            if world_data.get('magic_system'):
                worldbuilding['magic_system'] = world_data['magic_system']
            if world_data.get('technology_level'):
                worldbuilding['technology'] = world_data['technology_level']
            if world_data.get('political_system'):
                worldbuilding['government'] = world_data['political_system']
            if world_data.get('cultures'):
                worldbuilding['cultures'] = world_data['cultures']
            if world_data.get('religions'):
                worldbuilding['religions'] = world_data['religions']
            
            # Ensure we have basic structure
            if not worldbuilding:
                worldbuilding = {
                    'history': 'To be determined',
                    'magic_system': 'To be determined',
                    'cultures': 'Multiple unique societies',
                    'government': 'Varies by region',
                    'technology': 'To be determined',
                }
            
            # Create context
            context = StoryContext(
                id=f"context_{story.id}",
                story_id=story.id,
                story=story,
                fundamental_truths=fundamental_truths[:5],
                worldbuilding=worldbuilding
            )
            
            logger.info(f"Generated world context with {len(fundamental_truths)} fundamental truths")
            return context
            
        except Exception as e:
            logger.error(f"Failed to generate world context: {e}", exc_info=True)
            raise ValueError(f"World generation failed: {str(e)}")
    
    def _build_world_prompt(
        self,
        story_title: str,
        story_description: str,
        user_input: str
    ) -> str:
        """Build prompt for world generation."""
        user_info = f"\n\nUser's world ideas: {user_input}" if user_input else ""
        
        return f"""Create a detailed world for a story with these details:

Title: {story_title}
Description: {story_description}
{user_info}

Generate a rich world by providing:

1. FUNDAMENTAL TRUTHS (3-5 core rules/facts about this world):
   - Magic system or technology level
   - Social structure or government
   - Key resources or conflicts
   - Historical events that shaped it
   - Any unique aspects

2. WORLDBUILDING DETAILS:
   - Setting (geography, climate, major regions)
   - Cultures and societies
   - Magic or technology systems
   - History and major events
   - Laws of nature or magic
   - Conflicts and tensions
   - Opportunities for adventure

Make the world feel alive and internally consistent."""
