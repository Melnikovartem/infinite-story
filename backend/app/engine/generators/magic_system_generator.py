"""Magic/Tech system generator for world rules and limitations."""

import logging
import json
import re
import uuid
from typing import Dict, Any, List
from app.models.story import Story
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.magic_system_generator")


class MagicSystem:
    """Magic or tech system for a world."""
    def __init__(self, name: str, description: str, rules: List[str], 
                 limitations: List[str], costs: List[str]):
        self.id = f"magic_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description  # Short description
        self.rules = rules  # What it can do
        self.limitations = limitations  # What it CAN'T do (more important)
        self.costs = costs  # Consequences of using it
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rules": self.rules,
            "limitations": self.limitations,
            "costs": self.costs
        }
    
    def short_summary(self) -> str:
        """Get short summary for prompts."""
        return f"{self.name}: {self.description}"


class MagicSystemGenerator:
    """Generate magic/tech systems for a world."""
    
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
    ) -> MagicSystem:
        """Generate magic or tech system for the world.
        
        Args:
            world_description: Description of the world
            genre: Story genre (determines magic vs tech)
            user_input: Optional user guidance
            
        Returns:
            MagicSystem object
        """
        try:
            logger.info(f"Generating magic/tech system for '{self.story.id}'")
            
            prompt = self._build_magic_prompt(
                world_description,
                genre,
                user_input
            )
            
            response = await self.generator.generate(
                system_prompt="""You are a worldbuilding expert designing magic or technology systems.
LIMITATIONS and COSTS are MORE IMPORTANT than capabilities.
Magic should have real consequences. Power should have a price.
This grounds the world in tension and meaningful choices.""",
                user_prompt=prompt,
                context_type="world"
            )
            
            if response.error:
                raise ValueError(f"Magic system generation failed: {response.error}")
            
            magic = self._parse_magic_system(response, genre)
            logger.info(f"Generated magic system: {magic.name}")
            return magic
            
        except Exception as e:
            logger.error(f"Failed to generate magic system: {e}", exc_info=True)
            raise ValueError(f"Magic system generation failed: {str(e)}")
    
    def _build_magic_prompt(
        self,
        world_description: str,
        genre: str,
        user_input: str
    ) -> str:
        """Build magic system generation prompt."""
        
        system_type = "magical" if "Fantasy" in genre else "technological"
        
        return f"""Create a {system_type} system for this world:

World: {world_description[:400]}
Genre: {genre}

{f"User's idea: {user_input}" if user_input else ""}

Design a {system_type} system with these sections:

**SYSTEM NAME**
- Description: One sentence (used in scenes)
- What It Can Do (2-3 capabilities): The actual powers/tech available
- What It CANNOT Do (3-4 limitations): THE HARD LIMITS (more important!)
  Examples: Can't resurrect dead, Can't read minds, Can't violate laws of physics
- Costs & Consequences (3-4 prices): What using it costs
  Examples: Physical exhaustion, Mental strain, Permanent mark, Debt to entity
  
IMPORTANT:
- Limitations matter MORE than capabilities
- Every use should have a cost
- This creates meaningful choices: "Use magic but pay the price" vs "find another way"
- Make consequences real and impactful

Make the system feel grounded and dangerous, not omnipotent."""
    
    def _parse_magic_system(self, response: Any, genre: str) -> MagicSystem:
        """Parse magic system from AI response."""
        
        response_text = ""
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        # Extract system name
        name_match = re.search(r'\*\*([^*]+)\*\*', response_text)
        name = name_match.group(1).strip() if name_match else "The Ancient Arts"
        
        # Extract fields
        description = self._extract_field(response_text, r'Description:\s*([^\n]+)', 
                                         "A powerful system with real costs")
        
        capabilities_text = self._extract_field(response_text, r'What It Can Do.*?:\s*([^\n]+(?:\n[^\n]+){0,2})', "")
        capabilities = [c.strip() for c in re.split(r'[-•\n]', capabilities_text) if c.strip()][:3]
        
        limitations_text = self._extract_field(response_text, r'What It CANNOT Do.*?:\s*([^\n]+(?:\n[^\n]+){0,3})', "")
        limitations = [l.strip() for l in re.split(r'[-•\n]', limitations_text) if l.strip()][:4]
        
        costs_text = self._extract_field(response_text, r'Costs? & Consequences.*?:\s*([^\n]+(?:\n[^\n]+){0,3})', "")
        costs = [c.strip() for c in re.split(r'[-•\n]', costs_text) if c.strip()][:4]
        
        # Defaults if parsing failed
        if not capabilities:
            capabilities = ["Channel energy", "Manipulate elements", "Communicate across distance"]
        if not limitations:
            limitations = ["Cannot create matter", "Cannot control minds", "Cannot reverse death", "Cannot break fundamental laws"]
        if not costs:
            costs = ["Physical exhaustion", "Spiritual debt", "Temporary vulnerability", "Unknown consequences"]
        
        return MagicSystem(
            name=name,
            description=description,
            rules=capabilities,
            limitations=limitations,
            costs=costs
        )
    
    def _extract_field(self, text: str, pattern: str, default: str = "") -> str:
        """Extract field using regex."""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
