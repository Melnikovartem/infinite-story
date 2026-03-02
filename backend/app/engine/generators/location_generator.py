"""Location generator for creating world locations."""

import logging
import json
from typing import List, Dict, Any
import uuid

from app.models.story import Story
from app.models.story_location import StoryLocation
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.location_generator")


class LocationGenerator:
    """Generate locations for a story world."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize location generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def generate_world_locations(
        self,
        world_description: str,
        fundamental_truths: List[str],
        user_input: str = ""
    ) -> List[StoryLocation]:
        """Generate locations for the world.
        
        LLM decides how many locations to create based on world complexity.
        
        Args:
            world_description: Description of the world
            fundamental_truths: List of fundamental world truths
            user_input: Optional user guidance
            
        Returns:
            List of generated StoryLocation objects
        """
        try:
            logger.info(f"Generating world locations for story '{self.story.id}'")
            
            # Build prompt
            prompt = self._build_location_prompt(
                world_description,
                fundamental_truths,
                user_input
            )
            
            # Generate via AI
            response = await self.generator.generate(
                system_prompt="""You are a master world builder creating detailed, interconnected locations.
Each location should feel alive and tie into the world's fundamental truths.
Generate as many locations as needed (5-15) to fully flesh out this world.""",
                user_prompt=prompt,
                context_type="world"
            )
            
            if response.error:
                raise ValueError(f"Location generation failed: {response.error}")
            
            # Parse locations from response
            locations = self._parse_locations(response)
            
            logger.info(f"Generated {len(locations)} world locations")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to generate locations: {e}", exc_info=True)
            raise ValueError(f"Location generation failed: {str(e)}")
    
    def _build_location_prompt(
        self,
        world_description: str,
        fundamental_truths: List[str],
        user_input: str
    ) -> str:
        """Build the location generation prompt."""
        
        truths_text = "\n".join([f"- {truth}" for truth in fundamental_truths[:5]])
        
        return f"""Create a detailed set of locations for this world:

Story: {self.story.title}
Genre: {self.story.genre}

World Description: {world_description[:500]}

Fundamental Truths:
{truths_text}

{f"User's Location Ideas: {user_input}" if user_input else ""}

Generate a comprehensive set of interconnected locations (decide the number based on world complexity, 5-15 locations).

For EACH location, provide:

**LOCATION NAME**
Short: One sentence description (used in scene prompts)
Full: 3-5 sentences with rich details (used for deep context)
Connections: How it connects to other locations
Importance: Why this location matters to the story

Make locations diverse:
- Some major/important
- Some minor/hidden
- Some dangerous
- Some safe/peaceful
- Some mysterious
- Some common/everyday

Format as a clear list with Location Name as headers."""
    
    def _parse_locations(self, response: Any) -> List[StoryLocation]:
        """Parse locations from AI response."""
        
        locations = []
        response_text = ""
        
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        logger.debug(f"Parsing locations from response ({len(response_text)} chars)")
        
        # Split by location headers (lines starting with ** or uppercase)
        import re
        sections = re.split(r'\*\*([^*]+)\*\*', response_text)
        
        for i in range(1, len(sections), 2):
            location_name = sections[i].strip()
            location_content = sections[i + 1].strip() if i + 1 < len(sections) else ""
            
            if not location_name or len(location_name) < 2:
                continue
            
            # Parse short and full descriptions
            short_desc = self._extract_field(location_content, r'Short:\s*([^\n]+)', "A mysterious location")
            full_desc = self._extract_field(location_content, r'Full:\s*([^\n]+(?:\n[^\n]+){0,4})', "")
            
            # Create location
            location = StoryLocation(
                id=f"loc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                story_id=self.story.id,
                story=self.story,
                name=location_name,
                description=short_desc,
                full_description=full_desc if full_desc else short_desc
            )
            
            locations.append(location)
            logger.debug(f"Created location: {location.name}")
        
        # If no locations parsed, create defaults
        if not locations:
            logger.warning("No locations parsed from response, creating defaults")
            default_names = ["The Starting Place", "The Hidden Sanctuary", "The Dangerous Lands"]
            for i, name in enumerate(default_names):
                location = StoryLocation(
                    id=f"loc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    story=self.story,
                    name=name,
                    description=f"A mysterious location in {self.story.title}",
                    full_description=f"A detailed and important location in the world of {self.story.title}"
                )
                locations.append(location)
        
        return locations
    
    def _extract_field(self, text: str, pattern: str, default: str = "") -> str:
        """Extract a field from text using regex."""
        import re
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
