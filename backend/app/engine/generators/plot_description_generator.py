"""Plot description generator for creating main story plot."""

import logging
from typing import List, Any
from app.models.story import Story
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.plot_description_generator")


class PlotDescriptionGenerator:
    """Generate main plot/storyline for stories."""
    
    def __init__(self, generator: TextGenerator):
        """Initialize plot generator.
        
        Args:
            generator: AI text generator for content generation
        """
        self.generator = generator
    
    async def generate_plot_description(
        self,
        story: Story,
        world_context: StoryContext
    ) -> StoryContext:
        """Generate plot description and enrich story context.
        
        Args:
            story: Story instance to generate plot for
            world_context: StoryContext with world data
            
        Returns:
            Enhanced StoryContext with plot information
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating plot description for story '{story.title}'")
            
            # Build prompt with world context
            world_description = ""
            if isinstance(world_context.worldbuilding, dict):
                world_description = world_context.worldbuilding.get('world_description', '')
            
            prompt = self._build_plot_prompt(
                story.title,
                story.description,
                story.genre,
                world_description,
                world_context.fundamental_truths
            )
            
            # Generate via AI with fallback
            response = await self.generator.generate_with_fallback(
                context_type="world",
                system_prompt="""You are a master story architect.
Create compelling plot outlines with clear central conflicts and character arcs.
Make the story engaging and full of potential.""",
                user_prompt=prompt
            )
            
            # Extract plot data
            plot_description = self._extract_plot_description(response)
            central_conflicts = self._extract_conflicts(response)
            story_themes = self._extract_themes(response)
            story_tone = self._extract_tone(response)
            
            # Enrich world context with plot data
            if isinstance(world_context.worldbuilding, dict):
                world_context.worldbuilding['plot_description'] = plot_description
                world_context.worldbuilding['central_conflicts'] = central_conflicts
                world_context.worldbuilding['story_themes'] = story_themes
                world_context.worldbuilding['story_tone'] = story_tone
            
            logger.info(f"Generated plot with {len(central_conflicts)} central conflicts")
            return world_context
            
        except Exception as e:
            logger.error(f"Failed to generate plot description: {e}", exc_info=True)
            raise ValueError(f"Plot generation failed: {str(e)}")
    
    def _build_plot_prompt(
        self,
        story_title: str,
        story_description: str,
        genre: str,
        world_description: str,
        fundamental_truths: List[str]
    ) -> str:
        """Build prompt for plot generation."""
        truths_text = "\n".join([f"- {truth}" for truth in fundamental_truths[:4]])
        
        return f"""Create a compelling main plot/storyline for this story:

Title: {story_title}
Description: {story_description}
Genre: {genre}

World Context:
{world_description}

Fundamental Truths:
{truths_text}

Generate a detailed plot outline with:

1. PLOT DESCRIPTION: A 3-4 sentence summary of the main story
   - What's the inciting incident?
   - What drives the story forward?
   - What's at stake?

2. CENTRAL CONFLICTS (2-3 major conflicts):
   - The main conflict(s) that drive the narrative
   - What opposing forces or interests clash?
   - Why can't they be easily resolved?

3. STORY THEMES (3-5 key themes):
   - Major themes to explore
   - What questions does the story ask?
   - What insights does it provide?

4. STORY TONE:
   - Overall emotional tone (epic, intimate, dark, hopeful, mysterious, etc)
   - Mood and atmosphere
   - How does it feel?

Make the plot feel inevitable yet surprising, with clear stakes and compelling conflicts."""
    
    def _extract_plot_description(self, response: Any) -> str:
        """Extract plot description from response."""
        if hasattr(response, 'backstory') and response.backstory:
            # Extract first few sentences
            sentences = response.backstory.split('.')[:3]
            return '.'.join(sentences).strip() + '.'
        
        if hasattr(response, 'content') and response.content:
            sentences = response.content.split('.')[:3]
            return '.'.join(sentences).strip() + '.'
        
        return "A story of conflict, growth, and discovery"
    
    def _extract_conflicts(self, response: Any) -> List[str]:
        """Extract central conflicts from response."""
        conflicts = []
        
        if hasattr(response, 'major_events') and response.major_events:
            conflicts.extend(response.major_events[:3])
        
        # If we don't have enough, add defaults
        if len(conflicts) < 2:
            conflicts.extend([
                "Internal conflict between opposing goals",
                "External conflict with opposing forces"
            ])
        
        return conflicts[:3]
    
    def _extract_themes(self, response: Any) -> List[str]:
        """Extract themes from response."""
        themes = []
        
        # Try to extract from response
        if hasattr(response, 'backstory') and response.backstory:
            # Look for theme keywords
            backstory_lower = response.backstory.lower()
            potential_themes = ['power', 'love', 'betrayal', 'redemption', 'sacrifice', 'growth', 'justice', 'survival']
            for theme in potential_themes:
                if theme in backstory_lower:
                    themes.append(theme.capitalize())
        
        # If still empty, use defaults
        if not themes:
            themes = ['Conflict', 'Growth', 'Discovery', 'Choice', 'Consequence']
        
        return themes[:5]
    
    def _extract_tone(self, response: Any) -> str:
        """Extract story tone from response."""
        if hasattr(response, 'backstory') and response.backstory:
            backstory_lower = response.backstory.lower()
            
            # Detect tone from content
            if any(word in backstory_lower for word in ['dark', 'grim', 'tragic', 'horror']):
                return "Dark"
            elif any(word in backstory_lower for word in ['epic', 'grand', 'legendary']):
                return "Epic"
            elif any(word in backstory_lower for word in ['mystery', 'secret', 'hidden']):
                return "Mysterious"
            elif any(word in backstory_lower for word in ['hope', 'light', 'triumph']):
                return "Hopeful"
            elif any(word in backstory_lower for word in ['intimate', 'personal', 'individual']):
                return "Intimate"
        
        return "Compelling"
