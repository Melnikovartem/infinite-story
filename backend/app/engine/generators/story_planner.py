"""Story planner - decides scope parameters before generation."""

import logging
import json
from typing import Dict, Any
from app.models.story import Story
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.story_planner")


class StoryPlanner:
    """Plans story scope parameters before generation begins."""
    
    def __init__(self, generator: TextGenerator):
        """Initialize story planner.
        
        Args:
            generator: AI text generator for planning
        """
        self.generator = generator
    
    async def plan_story_scope(
        self,
        title: str,
        description: str,
        genre: str
    ) -> Dict[str, Any]:
        """Determine story scope: how many chars, locations, factions, etc.
        
        Args:
            title: Story title
            description: Story description
            genre: Story genre
            
        Returns:
            Dict with scope parameters
        """
        try:
            logger.info(f"Planning story scope for '{title}'")
            
            prompt = f"""For this story, decide its scope/scale.

Story: {title}
Genre: {genre}
Description: {description}

Determine TOTAL POOL SIZES (many won't be introduced to player):
1. Total world factions (1-5): How many major factions exist in this world?
2. Characters per faction (range like "2-4" or "3-5"): How many characters per faction?
3. Non-faction characters (0-3): Independent characters not aligned with factions?
4. Total locations (5-15): How many distinct places in this world?
5. Major tensions (2-4): What are the core conflicts/tensions?
6. World backstory depth: Centuries-old history or recent events? (Ancient/Medieval/Recent)

Output as JSON:
{{
    "total_factions": <number 1-5>,
    "chars_per_faction_min": <number>,
    "chars_per_faction_max": <number>,
    "non_faction_chars": <number>,
    "total_locations": <number>,
    "major_tensions": [<list of tensions>],
    "world_backstory": "<Ancient/Medieval/Recent>",
    "scope_summary": "<1-2 sentence summary of story scale>"
}}"""
            
            response = await self.generator.generate(
                system_prompt="You are a story architect planning narrative scope and world parameters.",
                user_prompt=prompt,
                context_type="world"
            )
            
            # Extract JSON from response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON
            json_match = response_text.find('{')
            if json_match >= 0:
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_match:json_end]
                plan = json.loads(json_str)
            else:
                plan = self._create_default_plan()
            
            logger.info(f"Story scope planned: {len(plan.get('major_tensions', []))} tensions, "
                       f"{plan.get('total_factions', 2)} factions, "
                       f"{plan.get('total_locations', 8)} locations")
            
            return plan
            
        except Exception as e:
            logger.error(f"Story planning failed: {e}, using defaults")
            return self._create_default_plan()
    
    def _create_default_plan(self) -> Dict[str, Any]:
        """Create default story plan."""
        return {
            "total_factions": 3,  # Can be 1-5
            "chars_per_faction_min": 2,
            "chars_per_faction_max": 4,
            "non_faction_chars": 2,
            "total_locations": 8,
            "major_tensions": [
                "Power struggle between factions",
                "Mystery surrounding the protagonist",
                "Moral dilemma between sides"
            ],
            "world_backstory": "Medieval",
            "scope_summary": "A medium-scale world with multiple factions vying for control."
        }
