"""Magic/Tech/Power system generator for world rules and limitations.

Supports three paradigms:
- magic: Supernatural forces with rules and costs (fantasy, dark fantasy, etc.)
- tech: Advanced technology with capabilities and consequences (sci-fi, cyberpunk, etc.)
- none: No special power system — the world runs on mundane rules (realistic fiction, historical, etc.)

The LLM decides which paradigm fits the world, so not every story is forced to have magic.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from app.models.story import Story
from app.models.story_magic_system import StoryMagicSystem
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.generators.magic_system_generator")


# Backward-compatible alias
MagicSystem = StoryMagicSystem


# Step 1 schema: LLM decides the paradigm
PARADIGM_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("paradigm", type="str", required=True, aliases=["type", "system_type", "power_type"]),
        FieldSpec("reason", type="str", aliases=["explanation", "rationale", "why"]),
    ],
    expect_array=False,
)

# Step 2 schema: full system details (only used if paradigm != "none")
SYSTEM_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", type="str", required=True, aliases=["system_name", "title"]),
        FieldSpec("description", type="str", required=True, aliases=["desc", "summary", "overview"]),
        FieldSpec("rules", type="list", required=True, aliases=["capabilities", "powers", "abilities", "what_it_can_do"]),
        FieldSpec("limitations", type="list", required=True, aliases=["limits", "restrictions", "cannot_do", "hard_limits"]),
        FieldSpec("costs", type="list", required=True, aliases=["consequences", "prices", "costs_and_consequences"]),
        FieldSpec("origin", type="str", aliases=["source", "where_it_comes_from"]),
        FieldSpec("practitioners", type="str", aliases=["users", "who_can_use_it"]),
        FieldSpec("technology_level", type="str", aliases=["tech_level"]),
    ],
    expect_array=False,
)

SYSTEM_EXAMPLE = {
    "name": "The Ember Weave",
    "description": "A volatile magical force drawn from underground ember veins, channeled through ritual scarring",
    "rules": [
        "Channel heat and fire through scarred conduits on the body",
        "Sense ember veins and geothermal energy underground",
        "Forge-bond with metal, shaping it by touch while the scars glow"
    ],
    "limitations": [
        "Cannot affect water or ice — ember magic is extinguished by cold",
        "Cannot heal — the Weave only destroys and reshapes",
        "Cannot be used at night when ember veins cool",
        "Cannot affect living tissue — only dead matter and metal"
    ],
    "costs": [
        "Each use deepens the ritual scars, eventually crippling the practitioner",
        "Prolonged use causes feverish hallucinations of the Deep Forge",
        "Overuse permanently raises body temperature, making human contact painful",
        "Drawing too much burns out the nearest ember vein, leaving the land barren"
    ],
    "origin": "Ancient ember veins running beneath the continent, remnants of a primordial forge-god",
    "practitioners": "Scarred channelers called Embersmiths, rare and feared — perhaps 1 in 10,000",
    "technology_level": "Late medieval with magical metallurgy far beyond normal capability",
}

SYSTEM_FALLBACK = {
    "name": "The Ancient Arts",
    "description": "A powerful system with real costs and hard limitations",
    "rules": ["Channel energy", "Manipulate elements", "Communicate across distance"],
    "limitations": ["Cannot create matter", "Cannot control minds", "Cannot reverse death", "Cannot break fundamental laws"],
    "costs": ["Physical exhaustion", "Spiritual debt", "Temporary vulnerability", "Unknown consequences"],
    "origin": "",
    "practitioners": "",
    "technology_level": "",
}


class MagicSystemGenerator:
    """Generate magic/tech systems for a world, or decide the world needs neither."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize magic system generator.
        
        Args:
            story: The Story instance
            generator: AI text generator
        """
        self.story = story
        self.generator = generator
    
    async def generate_magic_system(
        self,
        world_description: str,
        genre: str,
        user_input: str = ""
    ) -> Optional[StoryMagicSystem]:
        """Generate magic/tech system for the world, or None if the world doesn't need one.
        
        The LLM first decides the paradigm (magic / tech / none), then generates
        the full system details if applicable.
        
        Args:
            world_description: Description of the world
            genre: Story genre
            user_input: Optional user guidance
            
        Returns:
            StoryMagicSystem object, or None if the world has no special power system
        """
        try:
            logger.info(f"Generating power system for '{self.story.id}' (genre: {genre})")
            
            # Step 1: Decide paradigm
            paradigm = await self._decide_paradigm(world_description, genre, user_input)
            logger.info(f"Power paradigm decided: {paradigm}")
            
            if paradigm == "none":
                logger.info("World has no magic/tech system — skipping generation")
                return None
            
            # Step 2: Generate the full system
            system = await self._generate_system(world_description, genre, paradigm, user_input)
            logger.info(f"Generated power system: {system.name}")
            return system
            
        except Exception as e:
            logger.error(f"Failed to generate power system: {e}", exc_info=True)
            raise ValueError(f"Power system generation failed: {str(e)}")
    
    async def _decide_paradigm(
        self,
        world_description: str,
        genre: str,
        user_input: str,
    ) -> str:
        """Ask LLM whether the world uses magic, tech, or neither.
        
        Returns:
            One of: "magic", "tech", "none"
        """
        format_instruction = AIResponseParser.get_prompt_instruction(
            PARADIGM_SCHEMA, OutputFormat.JSON,
            example={"paradigm": "magic", "reason": "The world has supernatural forces woven into its fabric"}
        )
        
        prompt = f"""Analyze this world and decide what kind of power system it should have:

World: {world_description[:400]}
Genre: {genre}
{f"User guidance: {user_input}" if user_input else ""}

Choose exactly ONE paradigm:

- "magic": The world has supernatural, mystical, or arcane forces (fantasy, dark fantasy, mythological settings)
- "tech": The world has advanced technology beyond our current level (sci-fi, cyberpunk, space opera)
- "none": The world runs on mundane real-world rules — no magic, no advanced tech (realistic fiction, historical, contemporary, noir, literary)

IMPORTANT: Not every world needs a power system. Historical dramas, realistic thrillers, literary fiction, and similar genres should use "none".

{format_instruction}"""
        
        parsed = await self.generator.generate_structured(
            system_prompt="You are a worldbuilding analyst. Decide what kind of power system fits this world. Be honest — not every world needs magic or advanced tech.",
            user_prompt=prompt,
            schema=PARADIGM_SCHEMA,
            fallback_defaults=[{"paradigm": self._genre_heuristic(genre), "reason": "Fallback"}],
        )
        
        if parsed:
            raw_paradigm = str(parsed.get("paradigm", "")).strip().lower()
            if raw_paradigm in ("magic", "tech", "none"):
                return raw_paradigm
            # Try to coerce near-matches
            if "magic" in raw_paradigm or "supernatural" in raw_paradigm or "arcane" in raw_paradigm:
                return "magic"
            if "tech" in raw_paradigm or "sci" in raw_paradigm or "cyber" in raw_paradigm:
                return "tech"
            if "none" in raw_paradigm or "mundane" in raw_paradigm or "realistic" in raw_paradigm:
                return "none"
        
        return self._genre_heuristic(genre)
    
    def _genre_heuristic(self, genre: str) -> str:
        """Fallback: guess paradigm from genre string."""
        g = (genre or "").lower()
        if any(kw in g for kw in ("fantasy", "magic", "myth", "fairy", "dark fantasy", "supernatural")):
            return "magic"
        if any(kw in g for kw in ("sci-fi", "science fiction", "cyberpunk", "space", "futur")):
            return "tech"
        return "none"
    
    async def _generate_system(
        self,
        world_description: str,
        genre: str,
        paradigm: str,
        user_input: str,
    ) -> StoryMagicSystem:
        """Generate the full magic/tech system details."""
        
        system_label = "magical" if paradigm == "magic" else "technological"
        
        format_instruction = AIResponseParser.get_prompt_instruction(
            SYSTEM_SCHEMA, OutputFormat.JSON, example=SYSTEM_EXAMPLE
        )
        
        prompt = f"""Create a {system_label} system for this world:

World: {world_description[:400]}
Genre: {genre}

{f"User's idea: {user_input}" if user_input else ""}

Design the system with these fields:
- name: A distinctive name for the system
- description: One sentence (used in scene prompts)
- rules: 2-3 capabilities — what it can actually do
- limitations: 3-4 HARD LIMITS — what it absolutely CANNOT do (MORE IMPORTANT than rules!)
  Examples: Can't resurrect the dead, Can't read minds, Can't violate conservation of energy
- costs: 3-4 consequences of using it — the price of power
  Examples: Physical exhaustion, permanent scarring, spiritual debt, environmental damage
- origin: Where this power comes from
- practitioners: Who can use it and how common they are
- technology_level: The world's overall tech level and how this system fits in

CRITICAL DESIGN PRINCIPLES:
- Limitations matter MORE than capabilities
- Every use should have a meaningful cost
- The system should create tension: "use power but pay the price" vs "find another way"
- Make consequences real, escalating, and permanent where possible
- The system should feel grounded and dangerous, not omnipotent

{format_instruction}"""
        
        raw = await self.generator.generate_structured(
            system_prompt=f"""You are a worldbuilding expert designing {system_label} systems.
LIMITATIONS and COSTS are MORE IMPORTANT than capabilities.
Power should have real consequences that create meaningful choices.""",
            user_prompt=prompt,
            schema=SYSTEM_SCHEMA,
            fallback_defaults=[SYSTEM_FALLBACK],
        )
        
        system_id = f"magic_{uuid.uuid4().hex[:8]}"
        return StoryMagicSystem(
            id=system_id,
            story=self.story,
            name=raw.get('name', SYSTEM_FALLBACK['name']),
            description=raw.get('description', SYSTEM_FALLBACK['description']),
            rules=raw.get('rules', SYSTEM_FALLBACK['rules']),
            limitations=raw.get('limitations', SYSTEM_FALLBACK['limitations']),
            costs=raw.get('costs', SYSTEM_FALLBACK['costs']),
            origin=raw.get('origin', ''),
            practitioners=raw.get('practitioners', ''),
            technology_level=raw.get('technology_level', ''),
        )
