"""Location generator for creating world locations."""

import logging
import uuid
from typing import List, Any
from app.models.story import Story
from app.models.story_location import StoryLocation
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.generators.location_generator")


# Schema for location generation — LLM decides count (5-15)
LOCATION_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", type="str", required=True, aliases=["location_name", "title", "place"]),
        FieldSpec("description", type="str", required=True, aliases=["short", "short_description", "summary", "desc"]),
        FieldSpec("full_description", type="str", required=True, aliases=["full", "detailed", "details", "long_description"]),
    ],
    expect_array=True,
    min_items=5,
    max_items=15,
    item_tag="location",
    root_tag="locations",
)

# Example for prompt instruction
LOCATION_EXAMPLE = {
    "name": "The Sunken Bazaar",
    "description": "A sprawling underground market built in flooded catacombs beneath the capital",
    "full_description": "Beneath the cobblestone streets of the capital lies the Sunken Bazaar, a vast network of flooded catacombs converted into a thriving black market. Merchants pole flat-bottomed boats between pillars draped in bioluminescent moss, hawking contraband, rare artifacts, and forbidden knowledge. The air is thick with incense meant to mask the smell of canal water. Guards rarely venture below — the Bazaar is governed by its own code, enforced by the masked Tide Wardens.",
}

# Fallback defaults when parsing fails completely
LOCATION_FALLBACK = {
    "name": "Unknown Location",
    "description": "A mysterious location in this world",
    "full_description": "A detailed and important location whose true nature remains to be discovered.",
}


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
        
        LLM decides how many locations to create (5-15) based on world complexity.
        
        Args:
            world_description: Description of the world
            fundamental_truths: List of fundamental world truths
            user_input: Optional user guidance
            
        Returns:
            List of generated StoryLocation objects
        """
        try:
            logger.info(f"Generating world locations for story '{self.story.id}'")
            
            prompt = self._build_location_prompt(
                world_description,
                fundamental_truths,
                user_input,
            )
            
            fallback_defaults = [
                {**LOCATION_FALLBACK, "name": name}
                for name in ["The Starting Place", "The Hidden Sanctuary", "The Dangerous Lands",
                             "The Ancient Ruins", "The Market District"]
            ]
            parsed_locations = await self.generator.generate_structured(
                system_prompt="""You are a master world builder creating detailed, interconnected locations.
Each location should feel alive and tie into the world's fundamental truths.
Generate as many locations as needed (5-15) to fully flesh out this world.""",
                user_prompt=prompt,
                schema=LOCATION_SCHEMA,
                fallback_defaults=fallback_defaults,
            )
            
            logger.debug(f"Parsed {len(parsed_locations)} location outlines")
            
            # Convert to persistent StoryLocation objects
            locations = []
            for raw in parsed_locations:
                name = raw.get('name', LOCATION_FALLBACK['name'])
                short_desc = raw.get('description', LOCATION_FALLBACK['description'])
                full_desc = raw.get('full_description', '') or short_desc
                
                location = StoryLocation(
                    id=f"loc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    story=self.story,
                    name=name,
                    description=short_desc,
                    full_description=full_desc,
                )
                locations.append(location)
                logger.debug(f"Created location: {location.name}")
            
            logger.info(f"Generated {len(locations)} world locations")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to generate locations: {e}", exc_info=True)
            raise ValueError(f"Location generation failed: {str(e)}")
    
    def _build_location_prompt(
        self,
        world_description: str,
        fundamental_truths: List[str],
        user_input: str,
    ) -> str:
        """Build the location generation prompt."""
        
        truths_text = "\n".join([f"- {truth}" for truth in fundamental_truths[:5]])
        
        # Get format-agnostic response instructions
        format_instruction = AIResponseParser.get_prompt_instruction(
            LOCATION_SCHEMA, OutputFormat.JSON, example=LOCATION_EXAMPLE
        )
        
        return f"""Create a detailed set of locations for this world:

Story: {self.story.title}
Genre: {self.story.genre}

World Description: {world_description[:500]}

Fundamental Truths:
{truths_text}

{f"User's Location Ideas: {user_input}" if user_input else ""}

Generate a comprehensive set of interconnected locations. Decide how many based on world complexity (5-15 locations).

For EACH location, provide:
- name: Location name
- description: One sentence (used in scene prompts)
- full_description: 3-5 sentences with rich details (used for deep context — include atmosphere, inhabitants, dangers, connections to other locations)

Make locations diverse:
- Some major/important, some minor/hidden
- Some dangerous, some safe/peaceful
- Some mysterious, some common/everyday
- Connected to each other through geography, trade, or conflict

{format_instruction}"""
