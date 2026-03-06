"""Story planner - decides scope parameters before generation."""

import logging
from typing import Dict, Any
from app.models.story import Story
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.generators.story_planner")


# Schema for story scope planning
_PLAN_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("total_factions", type="int", required=True, aliases=["factions", "num_factions"]),
        FieldSpec("chars_per_faction_min", type="int", required=True, aliases=["min_chars_per_faction", "chars_min"]),
        FieldSpec("chars_per_faction_max", type="int", required=True, aliases=["max_chars_per_faction", "chars_max"]),
        FieldSpec("non_faction_chars", type="int", aliases=["independent_characters", "non_aligned"]),
        FieldSpec("total_locations", type="int", required=True, aliases=["locations", "num_locations"]),
        FieldSpec("major_tensions", type="list", required=True, aliases=["tensions", "conflicts", "core_conflicts"]),
        FieldSpec("world_backstory", type="str", aliases=["backstory_depth", "history_depth"]),
        FieldSpec("scope_summary", type="str", aliases=["summary", "scale_summary"]),
    ],
    expect_array=False,
)

_PLAN_EXAMPLE = {
    "total_factions": 3,
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

_PLAN_FALLBACK = {
    "total_factions": 3,
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
            
            format_instruction = AIResponseParser.get_prompt_instruction(
                _PLAN_SCHEMA, OutputFormat.JSON, example=_PLAN_EXAMPLE
            )
            
            prompt = f"""For this story, decide its scope/scale.

Story: {title}
Genre: {genre}
Description: {description}

Determine TOTAL POOL SIZES (many won't be introduced to player):
1. Total world factions (1-5): How many major factions exist in this world?
2. Characters per faction (range): How many characters per faction?
3. Non-faction characters (0-3): Independent characters not aligned with factions?
4. Total locations (5-15): How many distinct places in this world?
5. Major tensions (2-4): What are the core conflicts/tensions?
6. World backstory depth: Centuries-old history or recent events? (Ancient/Medieval/Recent)

{format_instruction}"""
            
            plan = await self.generator.generate_structured(
                system_prompt="You are a story architect planning narrative scope and world parameters.",
                user_prompt=prompt,
                schema=_PLAN_SCHEMA,
                fallback_defaults=[_PLAN_FALLBACK],
            )
            
            logger.info(f"Story scope planned: {len(plan.get('major_tensions', []))} tensions, "
                       f"{plan.get('total_factions', 2)} factions, "
                       f"{plan.get('total_locations', 8)} locations")
            
            return plan
            
        except Exception as e:
            logger.error(f"Story planning failed: {e}, using defaults")
            return dict(_PLAN_FALLBACK)
