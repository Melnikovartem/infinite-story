"""Enhanced location generator for creating world locations with fraction mapping."""

import logging
import json
import uuid
from typing import List, Dict, Any
from app.models.story import Story
from app.models.story_location import StoryLocation
from app.models.story_fraction import StoryFraction
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.models.text_types import StoryShapeResponse

logger = logging.getLogger("infinite_story.engine.generators.location_generator_new")


class LocationGeneratorNew:
    """Generate locations for world, aware of fractions."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize location generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def generate_locations(
        self,
        world_context: StoryContext,
        fractions: List[StoryFraction],
        story_shape: StoryShapeResponse
    ) -> List[StoryLocation]:
        """Generate locations for the world with fraction mapping.
        
        Args:
            world_context: StoryContext with world data
            fractions: List of StoryFraction objects
            story_shape: StoryShapeResponse with location count
            
        Returns:
            List of generated StoryLocation objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {story_shape.num_locations} locations for story '{self.story.id}'")
            
            # Build prompt with fraction context
            prompt = self._build_location_prompt(
                self.story.title,
                self.story.genre,
                world_context,
                fractions,
                story_shape.num_locations
            )
            
            # Generate locations via AI
            response_text = await self.generator.generate_with_fallback(
                context_type="world",
                system_prompt="""You are a master world builder creating interconnected locations.
Each location ties into the world's fractions and themes.
Return ONLY valid JSON array with no additional text.""",
                user_prompt=prompt
            )
            
            # Parse response
            location_data_list = self._parse_locations_response(response_text, story_shape.num_locations)
            
            # Create StoryLocation objects
            locations = []
            for location_data in location_data_list:
                # Ensure associated_fractions are strings (they might come as integers from JSON)
                assoc_fracs = location_data.get('associated_fractions', [])
                if assoc_fracs and isinstance(assoc_fracs, list):
                    assoc_fracs = [str(f) for f in assoc_fracs]
                
                location = StoryLocation(
                    id=f"loc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    story=self.story,
                    name=location_data.get('name', 'Unknown Location'),
                    description=location_data.get('short_description', ''),
                    full_description=location_data.get('full_description', ''),
                    associated_fractions=assoc_fracs,
                    importance=location_data.get('importance', 'minor')
                )
                locations.append(location)
                logger.debug(f"Created location: {location.name}")
            
            logger.info(f"Generated {len(locations)} locations")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to generate locations: {e}", exc_info=True)
            raise ValueError(f"Location generation failed: {str(e)}")
    
    def _build_location_prompt(
        self,
        title: str,
        genre: str,
        world_context: StoryContext,
        fractions: List[StoryFraction],
        num_locations: int
    ) -> str:
        """Build prompt for location generation."""
        
        # Extract world data
        world_desc = ""
        if isinstance(world_context.worldbuilding, dict):
            world_desc = world_context.worldbuilding.get('world_description', '')
        
        # Build fractions text
        fractions_text = "\n".join([
            f"{i}. {frac.title}: {frac.short_description}"
            for i, frac in enumerate(fractions, 1)
        ])
        
        # Build fundamental truths
        truths_text = "\n".join([f"- {t}" for t in world_context.fundamental_truths[:4]])
        
        return f"""Create {num_locations} interconnected locations for this world.

Story: {title}
Genre: {genre}

World Description:
{world_desc}

Fundamental Truths:
{truths_text}

Story Fractions:
{fractions_text}

Return ONLY a valid JSON array (no markdown, no explanation) like this:
[
  {{
    "name": "Location Name",
    "short_description": "One sentence description",
    "full_description": "3-5 sentences with rich details",
    "associated_fractions": [1, 2],
    "importance": "major|minor",
    "connections": "How it connects to other places/fractions"
  }},
  ...
]

For each location, provide:
- NAME: A memorable location name
- SHORT_DESCRIPTION: One sentence (used in scene prompts)
- FULL_DESCRIPTION: 3-5 sentences with rich details (used for deep context)
- ASSOCIATED_FRACTIONS: Which fractions occur here? (list by number, e.g., [1, 2, 3])
- IMPORTANCE: "major" (central to plot) or "minor" (background)
- CONNECTIONS: How does this location connect to others and the fractions?

Make locations diverse:
- Some major/important
- Some minor/hidden
- Some dangerous
- Some safe/peaceful
- Some mysterious
- Some common/everyday

Ensure locations tie into the fractions and world."""
    
    def _parse_locations_response(self, response: Any, num_expected: int) -> List[Dict[str, Any]]:
        """Parse locations response into structured data."""
        
        # Extract content
        content = response
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        else:
            content = str(response)
        
        logger.debug(f"Locations response content: {content[:200]}")
        
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
        
        # Fallback: create default locations
        logger.warning(f"Using default {num_expected} locations")
        defaults = [
            {
                "name": "The Starting Place",
                "short_description": "Where the story begins",
                "full_description": "A place of significance where the first fraction begins. It holds clues to the larger world.",
                "associated_fractions": [1],
                "importance": "major",
                "connections": "Central hub for the first fraction"
            },
            {
                "name": "The Hidden Sanctuary",
                "short_description": "A place of refuge and secrets",
                "full_description": "A location known only to those who seek it. Here, characters find answers and make difficult choices.",
                "associated_fractions": [2],
                "importance": "major",
                "connections": "Important for the second fraction's developments"
            },
            {
                "name": "The Dangerous Lands",
                "short_description": "Where conflict is born",
                "full_description": "A hostile or chaotic place where the central conflict manifests. Characters are tested here.",
                "associated_fractions": [3],
                "importance": "major",
                "connections": "Critical for the final fraction"
            }
        ]
        
        return defaults[:num_expected]
