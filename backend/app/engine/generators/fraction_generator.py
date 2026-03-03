"""Fraction generator for creating story fractions/acts."""

import logging
import json
import uuid
from typing import List, Any, Dict
from app.models.story import Story
from app.models.story_fraction import StoryFraction
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.models.text_types import StoryShapeResponse

logger = logging.getLogger("infinite_story.engine.generators.fraction_generator")


class FractionGenerator:
    """Generate story fractions (acts/major divisions)."""
    
    def __init__(self, generator: TextGenerator):
        """Initialize fraction generator.
        
        Args:
            generator: AI text generator for content generation
        """
        self.generator = generator
    
    async def generate_fractions(
        self,
        story: Story,
        world_context: StoryContext,
        story_shape: StoryShapeResponse
    ) -> List[StoryFraction]:
        """Generate story fractions based on world and shape.
        
        Args:
            story: Story instance
            world_context: StoryContext with world and plot data
            story_shape: StoryShapeResponse with calculated structure
            
        Returns:
            List of generated StoryFraction objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {story_shape.num_fractions} fractions for story '{story.id}'")
            
            # Build prompt
            prompt = self._build_fraction_prompt(
                story.title,
                story.genre,
                world_context,
                story_shape.num_fractions
            )
            
            # Generate fractions via AI
            response_text = await self.generator.generate(
                system_prompt="""You are a master story architect.
Create compelling story fractions (acts) with clear goals and themes.
Return ONLY valid JSON array with no additional text.""",
                user_prompt=prompt,
                context_type="world"
            )
            
            if hasattr(response_text, 'error') and response_text.error:
                raise ValueError(f"Fraction generation failed: {response_text.error}")
            
            # Parse response
            fraction_data_list = self._parse_fractions_response(response_text, story_shape.num_fractions)
            
            # Create StoryFraction objects
            fractions = []
            for i, fraction_data in enumerate(fraction_data_list, 1):
                fraction = StoryFraction(
                    id=f"frac_{story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=story.id,
                    story=story,
                    title=fraction_data.get('title', f'Fraction {i}'),
                    order=i,
                    short_description=fraction_data.get('short_description', ''),
                    full_description=fraction_data.get('full_description', ''),
                    main_goal=fraction_data.get('main_goal', ''),
                    themes=fraction_data.get('themes', []),
                    tone=fraction_data.get('tone', 'neutral'),
                    central_conflict=fraction_data.get('central_conflict', ''),
                    narrative_direction=fraction_data.get('narrative_direction', '')
                )
                fractions.append(fraction)
                logger.debug(f"Created fraction: {fraction.title}")
            
            logger.info(f"Generated {len(fractions)} fractions")
            return fractions
            
        except Exception as e:
            logger.error(f"Failed to generate fractions: {e}", exc_info=True)
            raise ValueError(f"Fraction generation failed: {str(e)}")
    
    def _build_fraction_prompt(
        self,
        title: str,
        genre: str,
        world_context: StoryContext,
        num_fractions: int
    ) -> str:
        """Build prompt for fraction generation."""
        
        # Extract world and plot data
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
        truths_text = "\n".join([f"- {t}" for t in world_context.fundamental_truths[:4]])
        
        return f"""Create {num_fractions} major story fractions (acts) for this story.

Story: {title}
Genre: {genre}

World:
{world_desc}

Plot:
{plot_desc}

Fundamental Truths:
{truths_text}

Central Conflicts:
{conflicts_text}

Themes: {themes_text}

Return ONLY a valid JSON array (no markdown, no explanation) like this:
[
  {{
    "title": "The Awakening",
    "short_description": "1-2 sentences",
    "full_description": "3-5 sentences with rich detail",
    "main_goal": "What happens in this fraction?",
    "themes": ["theme1", "theme2", "theme3"],
    "tone": "epic|dark|intimate|etc",
    "central_conflict": "The main conflict in this fraction",
    "narrative_direction": "Where this fraction heads"
  }},
  ...
]

For each fraction, provide:
- TITLE: Compelling name (e.g., "The Awakening", "Rising Conflict", "The Fall", "Redemption")
- SHORT DESCRIPTION: 1-2 sentences for use in prompts
- FULL DESCRIPTION: 3-5 rich, detailed sentences
- MAIN GOAL: What should happen in this fraction? What's the outcome?
- THEMES: 2-3 key themes for this fraction
- TONE: Emotional tone (epic, dark, intimate, hopeful, mysterious, etc)
- CENTRAL CONFLICT: Main conflict driving this fraction
- NARRATIVE DIRECTION: Where is this fraction heading?

Make fractions interconnected, building on each other toward the overall story arc."""
    
    def _parse_fractions_response(self, response: Any, num_expected: int) -> List[Dict[str, Any]]:
        """Parse fractions response into structured data."""
        
        # Extract content
        content = response
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        else:
            content = str(response)
        
        logger.debug(f"Fractions response content: {content[:200]}")
        
        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            json_str = str(content)
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0]
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0]
            
            data = json.loads(json_str.strip())
            
            # Validate it's a list
            if isinstance(data, list) and len(data) > 0:
                return data[:num_expected]
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"JSON parsing failed: {e}")
        
        # Fallback: create default fractions
        logger.warning(f"Using default {num_expected} fractions")
        defaults = [
            {
                "title": "The Beginning",
                "short_description": "The story opens with a mystery or challenge.",
                "full_description": "Our protagonists are introduced in their world. A force or event disrupts the status quo, compelling them to action. The stakes become clear.",
                "main_goal": "Establish the world, introduce characters, set up the central conflict",
                "themes": ["Discovery", "Challenge", "Beginning"],
                "tone": "Intriguing",
                "central_conflict": "Initial conflict emerges",
                "narrative_direction": "Toward escalating tension"
            },
            {
                "title": "The Struggle",
                "short_description": "Conflict deepens and complications multiply.",
                "full_description": "Characters face mounting obstacles and difficult choices. Alliances form and break. The true scope of the conflict becomes apparent. Stakes rise as the story moves toward its climax.",
                "main_goal": "Deepen conflict, develop characters, raise stakes",
                "themes": ["Conflict", "Growth", "Sacrifice"],
                "tone": "Intense",
                "central_conflict": "Multiple forces clash",
                "narrative_direction": "Toward climax"
            },
            {
                "title": "The Resolution",
                "short_description": "The conflict reaches its peak and moves toward resolution.",
                "full_description": "The climactic confrontation arrives. Characters make their final choices. Old conflicts resolve while new revelations emerge. The world is forever changed by the events that transpired.",
                "main_goal": "Climax, resolve central conflicts, show consequences",
                "themes": ["Resolution", "Change", "Consequence"],
                "tone": "Triumphant",
                "central_conflict": "Final confrontation",
                "narrative_direction": "Toward new beginning"
            }
        ]
        
        return defaults[:num_expected]
