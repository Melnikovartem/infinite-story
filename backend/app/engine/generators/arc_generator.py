"""Arc generator for creating future arc outlines."""

import logging
from typing import List, Dict, Any
import uuid

from app.models.story import Story
from app.models.story_arc import StoryArc
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.arc_generator")


class ArcGenerator:
    """Generate high-level arc outlines for story progression."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize arc generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def generate_future_arcs(
        self,
        count: int = 3,
        user_input: str = ""
    ) -> List[StoryArc]:
        """Generate high-level arc outlines for the future.
        
        Args:
            count: Number of arcs to generate (default 3)
            user_input: Optional user guidance for arc direction
            
        Returns:
            List of generated StoryArc objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {count} future arc outlines for story '{self.story.id}'")
            
            # Build prompt
            prompt = self._build_arc_prompt(count, user_input)
            
            # Generate via AI
            response = await self.generator.generate(
                system_prompt="""You are a story structure expert creating compelling narrative arcs.
Your arcs should be interconnected, build on each other, and create an overall epic journey.
Focus on high-level structure and themes, not character details.""",
                user_prompt=prompt,
                context_type="world"  # Use world context type for structured generation
            )
            
            if response.error:
                raise ValueError(f"Arc generation failed: {response.error}")
            
            # Parse arc outlines
            arc_outlines = self._parse_arc_outlines(response, count)
            
            # Create and save StoryArc objects
            arcs = []
            for i, outline in enumerate(arc_outlines):
                arc = StoryArc(
                    id=f"arc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    title=outline.get('title', f"Arc {i+1}: Unknown"),
                    description=outline.get('description', ''),
                    premise=outline.get('premise', ''),
                    central_conflict=outline.get('central_conflict', ''),
                    narrative_direction=outline.get('narrative_direction', ''),
                    themes=outline.get('themes', []),
                    unresolved_mysteries=outline.get('mysteries', []),
                    plot_hooks=outline.get('hooks', []),
                    start_segment_id='',  # Will be set when arc becomes active
                )
                arc.save()
                arcs.append(arc)
                logger.info(f"Created arc outline: {arc.title}")
            
            return arcs
            
        except Exception as e:
            logger.error(f"Failed to generate arcs: {e}", exc_info=True)
            raise ValueError(f"Arc generation failed: {str(e)}")
    
    def _build_arc_prompt(self, count: int, user_input: str) -> str:
        """Build prompt for arc generation."""
        world_context = ""
        if self.story._context:
            world_context = f"""
Current World:
- Fundamental Truths: {', '.join(self.story._context.fundamental_truths[:3])}
- Setting: {self.story._context.worldbuilding.get('setting', 'Unknown') if isinstance(self.story._context.worldbuilding, dict) else 'Unknown'}"""
        
        story_context = f"""
Story: {self.story.title}
Description: {self.story.description}"""
        
        user_guidance = f"\n\nUser's Arc Direction: {user_input}" if user_input else ""
        
        return f"""Design {count} major story arcs that form a compelling narrative progression:
{world_context}
{story_context}
{user_guidance}

For each arc, provide:

TITLE: A compelling name for the arc

PREMISE: The core narrative idea (e.g., "Power corrupts the innocent")

CENTRAL CONFLICT: The main struggle that drives this arc
(e.g., "Hero vs. their own ambition", "Kingdom vs. external threat")

THEMES: 3-5 major themes explored
(e.g., betrayal, redemption, loss, growth, power)

NARRATIVE DIRECTION: Where this arc takes the story
(e.g., "Escalates conflicts introduced in Arc 1", "Reveals hidden truths")

MYSTERIES/QUESTIONS: 2-3 mysteries that will drive this arc
(e.g., "Who is the real villain?", "Can trust be rebuilt?")

PLOT HOOKS: 2-3 key events or hooks to explore
(e.g., "Discovery of ancient prophecy", "Betrayal by trusted ally")

Make sure the arcs are:
- Connected to each other (each builds on the previous)
- Distinct in tone and focus
- Progressively raise stakes
- All lead toward a satisfying conclusion"""
    
    def _parse_arc_outlines(self, response: Any, count: int) -> List[Dict[str, any]]:
        """Parse arc outlines from AI response."""
        outlines = []
        
        # Try to extract from response fields
        # For now, create placeholder outlines
        for i in range(count):
            outline = {
                'title': f"Arc {i+1}: TBD",
                'description': "High-level narrative outline to be filled in",
                'premise': "",
                'central_conflict': "",
                'narrative_direction': "",
                'themes': [],
                'mysteries': [],
                'hooks': []
            }
            
            # TODO: Parse actual response fields
            if hasattr(response, 'backstory'):
                outline['premise'] = response.backstory if i == 0 else ""
            
            outlines.append(outline)
        
        return outlines
