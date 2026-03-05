"""World description generator for creating world context."""

import logging
from typing import List, Dict, Any
from app.models.story import Story
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.models.text_types import WorldTextGeneratorResponse
from app.engine.lenient_parser import LenientParser

logger = logging.getLogger("infinite_story.engine.generators.world_description_generator")


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
            
            # Generate via AI
            response = await self.generator.generate(
                system_prompt="""You are a world-building expert creating rich, detailed worlds.
Create immersive worlds with clear systems, cultures, and rules.
Provide structured information about the world.""",
                user_prompt=prompt,
                context_type="world"
            )
            
            if response.error:
                raise ValueError(f"World generation failed: {response.error}")
            
            # Extract world data
            world_description = self._extract_world_description(response)
            fundamental_truths = self._extract_fundamental_truths(response)
            worldbuilding = self._extract_worldbuilding(response)
            
            # Create context
            context = StoryContext(
                id=f"context_{story.id}",
                story_id=story.id,
                story=story,
                fundamental_truths=fundamental_truths,
                worldbuilding=worldbuilding
            )
            
            # Store the world description in worldbuilding
            if isinstance(context.worldbuilding, dict):
                context.worldbuilding['world_description'] = world_description
            
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
    
    def _extract_world_description(self, response: Any) -> str:
        """Extract world description from response."""
        if hasattr(response, 'backstory') and response.backstory:
            return response.backstory[:500]
        
        if hasattr(response, 'raw_response') and response.raw_response:
            return response.raw_response[:500]
        
        return "A mysterious world waiting to be discovered"
    
    def _extract_fundamental_truths(self, response: Any) -> List[str]:
        """Extract fundamental truths from response."""
        truths = []
        
        # Try major_events field
        if hasattr(response, 'major_events') and response.major_events:
            truths.extend(response.major_events[:6])
        
        # Add system info if available
        if hasattr(response, 'magic_system') and response.magic_system:
            truths.append(f"Magic System: {response.magic_system}")
        
        if hasattr(response, 'technology_level') and response.technology_level:
            truths.append(f"Technology: {response.technology_level}")
        
        if hasattr(response, 'political_system') and response.political_system:
            truths.append(f"Government: {response.political_system}")
        
        # If still empty, use defaults
        if not truths:
            truths = [
                "The world operates under its own fundamental laws",
                "History shapes the present in unexpected ways",
                "Power and conflict drive civilization forward",
                "Magic or technology defines what's possible",
                "Adventure and discovery await the brave"
            ]
        
        return truths[:6]
    
    def _extract_worldbuilding(self, response: Any) -> Dict[str, Any]:
        """Extract worldbuilding details from response."""
        worldbuilding = {}
        
        # Map response fields to worldbuilding sections
        if hasattr(response, 'backstory') and response.backstory:
            worldbuilding['history'] = response.backstory
        
        if hasattr(response, 'magic_system') and response.magic_system:
            worldbuilding['magic_system'] = response.magic_system
        
        if hasattr(response, 'technology_level') and response.technology_level:
            worldbuilding['technology'] = response.technology_level
        
        if hasattr(response, 'political_system') and response.political_system:
            worldbuilding['government'] = response.political_system
        
        if hasattr(response, 'cultures') and response.cultures:
            worldbuilding['cultures'] = response.cultures
        
        if hasattr(response, 'religions') and response.religions:
            worldbuilding['religions'] = response.religions
        
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
