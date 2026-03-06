"""World description generator for creating world context."""

import logging
from typing import List, Dict, Any
from app.models.story import Story
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import ResponseSchema, FieldSpec

logger = logging.getLogger("infinite_story.engine.generators.world_description_generator")


# Schema for world generation
_WORLD_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("world_description", type="str", required=True, aliases=["description", "overview", "world_overview"]),
        FieldSpec("fundamental_truths", type="list", required=True, aliases=["truths", "core_facts", "world_rules"]),
        FieldSpec("magic_system", type="str", aliases=["magic", "technology_system"]),
        FieldSpec("technology_level", type="str", aliases=["technology", "tech_level"]),
        FieldSpec("political_system", type="str", aliases=["government", "politics", "power_structure"]),
        FieldSpec("cultures", type="list", aliases=["culture", "societies", "cultural_groups"]),
        FieldSpec("history", type="str", aliases=["backstory", "world_history", "major_events"]),
        FieldSpec("religions", type="list", aliases=["religion", "beliefs", "faiths"]),
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
    "magic_system": "To be determined",
    "technology_level": "To be determined",
    "political_system": "Varies by region",
    "cultures": [],
    "history": "To be determined",
    "religions": [],
}


class WorldDescriptionGenerator:
    """Generate world descriptions and context for stories."""
    
    def __init__(self, generator: TextGenerator):
        """Initialize world generator.
        
        Args:
            generator: AI text generator for content generation
        """
        self.generator = generator
    
    async def generate_world_description(
        self,
        story: Story,
        user_input: str = ""
    ) -> StoryContext:
        """Generate world description and context.
        
        Args:
            story: Story instance to generate world for
            user_input: Optional user-provided world information
            
        Returns:
            StoryContext with world description, fundamental truths, and systems
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating world description for story '{story.title}'")
            
            # Build prompt
            prompt = self._build_world_prompt(
                story.title,
                story.description,
                story.genre,
                user_input
            )
            
            # Generate via generate_structured
            world_data = await self.generator.generate_structured(
                system_prompt="""You are a world-building expert creating rich, detailed worlds.
Create immersive worlds with clear systems, cultures, and rules.
Provide structured information about the world.""",
                user_prompt=prompt,
                schema=_WORLD_SCHEMA,
                fallback_defaults=[_WORLD_FALLBACK],
            )
            
            # Extract fields from parsed data
            world_description = world_data.get('world_description', _WORLD_FALLBACK['world_description'])
            fundamental_truths = world_data.get('fundamental_truths', _WORLD_FALLBACK['fundamental_truths'])
            
            # Ensure fundamental_truths is a list of strings
            if isinstance(fundamental_truths, str):
                fundamental_truths = [fundamental_truths]
            if not fundamental_truths:
                fundamental_truths = list(_WORLD_FALLBACK['fundamental_truths'])
            
            # Build worldbuilding dict from all fields
            worldbuilding = {
                'world_description': world_description,
            }
            if world_data.get('magic_system'):
                worldbuilding['magic_system'] = world_data['magic_system']
            if world_data.get('technology_level'):
                worldbuilding['technology'] = world_data['technology_level']
            if world_data.get('political_system'):
                worldbuilding['government'] = world_data['political_system']
            if world_data.get('cultures'):
                worldbuilding['cultures'] = world_data['cultures']
            if world_data.get('history'):
                worldbuilding['history'] = world_data['history']
            if world_data.get('religions'):
                worldbuilding['religions'] = world_data['religions']
            
            # Ensure we have basic structure
            if len(worldbuilding) <= 1:
                worldbuilding.update({
                    'history': 'To be determined',
                    'magic_system': 'To be determined',
                    'cultures': 'Multiple unique societies',
                    'government': 'Varies by region',
                    'technology': 'To be determined',
                })
            
            # Create context
            context = StoryContext(
                id=f"context_{story.id}",
                story_id=story.id,
                story=story,
                fundamental_truths=fundamental_truths[:6],
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
        genre: str,
        user_input: str
    ) -> str:
        """Build prompt for world generation."""
        user_info = f"\n\nUser's world ideas:\n{user_input}" if user_input else ""
        
        return f"""Create a detailed, immersive world for this story:

Title: {story_title}
Description: {story_description}
Genre: {genre}
{user_info}

Generate a comprehensive world with:

1. WORLD DESCRIPTION: A vivid 3-4 sentence overview of this world's essence

2. FUNDAMENTAL TRUTHS (4-6 core facts):
   - Magic system or technology level
   - Social structure or government
   - Key resources or conflicts
   - Historical events that shaped it
   - Any unique or defining aspects
   - Cultural values and beliefs

3. MAGIC SYSTEM or TECHNOLOGY:
   - How it works
   - Limitations
   - How it affects society

4. POLITICAL SYSTEMS:
   - Who holds power
   - How decisions are made
   - Current tensions or conflicts

5. KEY CULTURES:
   - Major groups and their characteristics
   - Values and traditions
   - Relationships with other groups

6. HISTORY:
   - Major historical events
   - How the world came to be
   - Current state and tensions

Make the world feel alive, internally consistent, and full of potential for conflict and story."""
