"""World description generator for creating world context."""

import logging
from typing import Dict, Any, List

from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.world_generator")


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
        story_id: str,
        story_title: str,
        story_description: str,
        user_input: str = ""
    ) -> StoryContext:
        """Generate world context from story details.
        
        Args:
            story_id: ID of the story
            story_title: Title of the story
            story_description: Description of the story
            user_input: Optional user-provided world information
            
        Returns:
            StoryContext with fundamental truths and worldbuilding
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating world context for story '{story_title}'")
            
            # Build prompt
            prompt = self._build_world_prompt(
                story_title,
                story_description,
                user_input
            )
            
            # Generate via AI
            response = await self.generator.generate(
                system_prompt="You are a world-building expert creating rich, detailed fantasy/sci-fi worlds.",
                user_prompt=prompt,
                context_type="world"
            )
            
            if response.error:
                raise ValueError(f"World generation failed: {response.error}")
            
            # Extract fundamental truths
            fundamental_truths = self._extract_fundamental_truths(response)
            
            # Extract worldbuilding
            worldbuilding = self._extract_worldbuilding(response)
            
            # Create context
            context = StoryContext(
                id=f"context_{story_id}",
                story_id=story_id,
                fundamental_truths=fundamental_truths,
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
    
    def _extract_fundamental_truths(self, response: Any) -> List[str]:
        """Extract fundamental truths from AI response."""
        # Parse from major_events or similar field if available
        if hasattr(response, 'major_events') and response.major_events:
            return response.major_events[:5]
        
        # Fallback: extract from worldbuilding
        if hasattr(response, 'worldbuilding') and response.worldbuilding:
            truths = [
                "The world has its own unique magic or technology",
                "Ancient history shapes current conflicts",
                "Multiple factions compete for power",
                "Mysteries and secrets await discovery",
                "Change is constant and unavoidable"
            ]
            return truths
        
        return [
            "The world operates under its own fundamental laws",
            "History shapes the present in unexpected ways",
            "Power and conflict drive civilization forward",
            "Magic or technology defines what's possible",
            "Adventure and discovery await the brave"
        ]
    
    def _extract_worldbuilding(self, response: Any) -> Dict[str, str]:
        """Extract worldbuilding details from AI response."""
        worldbuilding = {}
        
        # Map response fields to worldbuilding sections
        if hasattr(response, 'backstory'):
            worldbuilding['history'] = response.backstory
        if hasattr(response, 'magic_system'):
            worldbuilding['magic_system'] = response.magic_system
        if hasattr(response, 'technology_level'):
            worldbuilding['technology'] = response.technology_level
        if hasattr(response, 'political_system'):
            worldbuilding['government'] = response.political_system
        if hasattr(response, 'cultures'):
            worldbuilding['cultures'] = str(response.cultures)
        if hasattr(response, 'religions'):
            worldbuilding['religions'] = str(response.religions)
        
        # Ensure we have basic structure
        if not worldbuilding:
            worldbuilding = {
                'history': 'To be determined',
                'magic_system': 'To be determined',
                'cultures': 'Multiple unique societies',
                'government': 'Varies by region',
                'technology': 'To be determined'
            }
        
        return worldbuilding
