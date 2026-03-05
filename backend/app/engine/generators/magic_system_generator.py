"""Magic/Tech system generator for world rules and limitations."""

import logging
import json
import re
import uuid
from typing import Dict, Any, List
from app.models.story import Story
from app.models.story_magic_system import StoryMagicSystem
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.magic_system_generator")


# Backward-compatible alias
MagicSystem = StoryMagicSystem


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
    ) -> StoryMagicSystem:
        """Generate magic or tech system for the world.
        
        Args:
            world_description: Description of the world
            genre: Story genre (determines magic vs tech)
            user_input: Optional user guidance
            
        Returns:
            StoryMagicSystem object (persistent, saveable)
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
    
    def _parse_magic_system(self, response: Any, genre: str) -> StoryMagicSystem:
        """Parse magic system from AI response into persistent StoryMagicSystem."""
        
        response_text = ""
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        # Known template headers to skip (these are prompt labels, not real names)
        _SKIP_NAMES = {
            'system name', 'name', 'magic system', 'tech system',
            'description', 'important', 'note', 'notes',
        }
        
        # Extract system name - find first **bold** text that isn't a template header
        name = "The Ancient Arts"
        for name_match in re.finditer(r'\*\*([^*]+)\*\*', response_text):
            candidate = name_match.group(1).strip().rstrip(':')
            if candidate.lower() not in _SKIP_NAMES and len(candidate) > 2:
                # Also skip if it looks like a section label
                if not re.match(r'^(What It|Costs?|Description|Limitations?|Capabilities)', candidate, re.IGNORECASE):
                    name = candidate
                    break
        
        # Extract description - single line after "Description:" label
        description = self._extract_field(response_text, r'Description:\s*([^\n]+)', 
                                         "A powerful system with real costs")
        
        # Extract capabilities - look for list items after the "What It Can Do" section
        capabilities_section = self._extract_section(response_text, 
            r'What It Can Do[^:]*:', r'What It (?:CANNOT|Cannot|can\'t)')
        capabilities = self._extract_list_items(capabilities_section)[:3]
        
        # Extract limitations - look for list items after the "What It CANNOT Do" section
        limitations_section = self._extract_section(response_text,
            r'What It (?:CANNOT|Cannot|can\'t) Do[^:]*:', r'Costs?')
        limitations = self._extract_list_items(limitations_section)[:4]
        
        # Extract costs - look for list items after the "Costs" section
        costs_section = self._extract_section(response_text,
            r'Costs?\s*(?:&|and)?\s*Consequences?[^:]*:', r'(?:IMPORTANT|$)')
        costs = self._extract_list_items(costs_section)[:4]
        
        # Defaults if parsing failed
        if not capabilities:
            capabilities = ["Channel energy", "Manipulate elements", "Communicate across distance"]
        if not limitations:
            limitations = ["Cannot create matter", "Cannot control minds", "Cannot reverse death", "Cannot break fundamental laws"]
        if not costs:
            costs = ["Physical exhaustion", "Spiritual debt", "Temporary vulnerability", "Unknown consequences"]
        
        system_id = f"magic_{uuid.uuid4().hex[:8]}"
        return StoryMagicSystem(
            id=system_id,
            story=self.story,
            name=name,
            description=description,
            rules=capabilities,
            limitations=limitations,
            costs=costs,
        )
    
    def _extract_section(self, text: str, start_pattern: str, end_pattern: str) -> str:
        """Extract text between two section headers."""
        start_match = re.search(start_pattern, text, re.IGNORECASE)
        if not start_match:
            return ""
        
        remaining = text[start_match.end():]
        end_match = re.search(end_pattern, remaining, re.IGNORECASE)
        if end_match:
            return remaining[:end_match.start()].strip()
        return remaining.strip()
    
    def _extract_list_items(self, text: str) -> List[str]:
        """Extract individual list items from text containing bullet points or numbered items."""
        if not text:
            return []
        
        items = []
        for line in text.split('\n'):
            line = line.strip()
            # Remove bullet/number prefixes
            line = re.sub(r'^[-•*]\s*|^\d+[\.\)]\s*', '', line).strip()
            if line and len(line) > 3:
                # Remove trailing commas/periods
                line = line.rstrip('.,;')
                items.append(line)
        
        return items
    
    def _extract_field(self, text: str, pattern: str, default: str = "") -> str:
        """Extract field using regex."""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
