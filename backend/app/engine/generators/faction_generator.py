"""Faction generator for creating world factions and politics."""

import logging
import uuid
from typing import List, Dict, Any
from app.models.story import Story
from app.models.story_faction import StoryFaction
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.generators.faction_generator")


# Backward-compatible alias - old code that imports Faction gets StoryFaction
Faction = StoryFaction


# Schema for faction generation
FACTION_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", type="str", required=True, aliases=["faction_name", "title"]),
        FieldSpec("description", type="str", required=True, aliases=["desc", "summary", "overview"]),
        FieldSpec("goals", type="list", required=True, aliases=["objectives", "aims", "goal_list"]),
        FieldSpec("leader", type="str", aliases=["leader_name", "head", "ruler"]),
        FieldSpec("resources", type="str", aliases=["assets", "power", "capabilities"]),
        FieldSpec("alignment", type="str", aliases=["morality", "stance", "moral_stance"]),
    ],
    expect_array=True,
    min_items=2,
    max_items=8,
    item_tag="faction",
    root_tag="factions",
)

# Example for prompt instruction
FACTION_EXAMPLE = {
    "name": "The Ashen Covenant",
    "description": "A secretive order of pyromancers seeking to restore the old fire temples",
    "goals": ["Reclaim the Ember Sanctum", "Convert nobles to the flame faith", "Undermine the water guilds"],
    "leader": "High Pyromancer Veshra",
    "resources": "Ancient fire magic, network of loyal acolytes, hidden caches of ember crystals",
    "alignment": "Chaotic Neutral",
}

# Fallback defaults when parsing fails completely
FACTION_FALLBACK = {
    "name": "Unknown Faction",
    "description": "A faction with distinct goals and resources",
    "goals": ["Gain influence", "Protect their interests", "Advance their agenda"],
    "leader": "Unknown",
    "resources": "Unknown",
    "alignment": "Neutral",
}


class FactionGenerator:
    """Generate factions for a world."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize faction generator.
        
        Args:
            story: The Story instance
            generator: AI text generator
        """
        self.story = story
        self.generator = generator
    
    async def generate_factions(
        self,
        count: int,
        world_description: str,
        major_tensions: List[str],
        user_input: str = ""
    ) -> List[StoryFaction]:
        """Generate factions for the world.
        
        Args:
            count: Number of factions to generate
            world_description: Description of the world
            major_tensions: List of major tensions in the world
            user_input: Optional user guidance
            
        Returns:
            List of StoryFaction objects (persistent, saveable)
        """
        try:
            logger.info(f"Generating {count} factions for story '{self.story.id}'")
            
            # Build schema with correct count
            schema = ResponseSchema(
                fields=FACTION_SCHEMA.fields,
                expect_array=True,
                min_items=count,
                max_items=count + 2,
                item_tag="faction",
                root_tag="factions",
            )
            
            prompt = self._build_faction_prompt(
                count,
                world_description,
                major_tensions,
                user_input,
                schema,
            )
            
            fallback_defaults = [
                {**FACTION_FALLBACK, "name": f"Faction {i+1}"}
                for i in range(count)
            ]
            parsed_factions = await self.generator.generate_structured(
                system_prompt="""You are a political strategist creating faction dynamics.
Each faction should have clear goals, resources, and leadership.
Factions should create tension and conflict that drives the story.""",
                user_prompt=prompt,
                schema=schema,
                fallback_defaults=fallback_defaults,
            )
            
            logger.debug(f"Parsed {len(parsed_factions)} faction outlines")
            
            # Convert to persistent StoryFaction objects
            factions = []
            for raw in parsed_factions[:count]:
                faction_id = f"faction_{uuid.uuid4().hex[:8]}"
                faction = StoryFaction(
                    id=faction_id,
                    story=self.story,
                    name=raw.get('name', FACTION_FALLBACK['name']),
                    description=raw.get('description', FACTION_FALLBACK['description']),
                    goals=raw.get('goals', FACTION_FALLBACK['goals']),
                    leader=raw.get('leader', FACTION_FALLBACK['leader']),
                    resources=raw.get('resources', FACTION_FALLBACK['resources']),
                    alignment=raw.get('alignment', FACTION_FALLBACK['alignment']),
                )
                factions.append(faction)
                logger.debug(f"Created StoryFaction: {faction.name} ({faction.id})")
            
            logger.info(f"Generated {len(factions)} factions")
            return factions
            
        except Exception as e:
            logger.error(f"Failed to generate factions: {e}", exc_info=True)
            raise ValueError(f"Faction generation failed: {str(e)}")
    
    def _build_faction_prompt(
        self,
        count: int,
        world_description: str,
        major_tensions: List[str],
        user_input: str,
        schema: ResponseSchema,
    ) -> str:
        """Build faction generation prompt."""
        
        tensions_text = "\n".join([f"- {t}" for t in major_tensions])
        
        # Get format-agnostic response instructions
        format_instruction = AIResponseParser.get_prompt_instruction(
            schema, OutputFormat.JSON, example=FACTION_EXAMPLE
        )
        
        return f"""Create {count} distinct factions for this world:

World: {world_description[:400]}

Major Tensions:
{tensions_text}

{f"User's faction ideas: {user_input}" if user_input else ""}

For EACH faction, provide:
- name: Faction name
- description: One sentence summary (used in scene prompts)
- goals: 2-3 short-term goals driving their actions
- leader: Name and title of leader
- resources: What they control/possess (gold, magic, military, influence, etc)
- alignment: Good/Evil/Neutral or their moral stance

Make factions:
- Have conflicting goals
- Create tension with each other
- Drive the story's major conflicts
- Be distinct in philosophy and methods

Include opposition/rivalry between factions.

{format_instruction}"""
