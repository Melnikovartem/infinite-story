"""Faction generator for creating world factions and politics."""

import logging
import json
import re
import uuid
from typing import List, Dict, Any
from app.models.story import Story
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.faction_generator")


class Faction:
    """Simple faction data class."""
    def __init__(self, name: str, description: str, goals: List[str], 
                 leader: str, resources: str, alignment: str):
        self.id = f"faction_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description  # Short description
        self.goals = goals  # List of faction goals
        self.leader = leader
        self.resources = resources
        self.alignment = alignment  # Good, Evil, Neutral, etc
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goals": self.goals,
            "leader": self.leader,
            "resources": self.resources,
            "alignment": self.alignment
        }
    
    def short_summary(self) -> str:
        """Get short summary for prompts."""
        return f"{self.name}: {self.description}"


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
    ) -> List[Faction]:
        """Generate factions for the world.
        
        Args:
            count: Number of factions to generate
            world_description: Description of the world
            major_tensions: List of major tensions in the world
            user_input: Optional user guidance
            
        Returns:
            List of Faction objects
        """
        try:
            logger.info(f"Generating {count} factions for story '{self.story.id}'")
            
            prompt = self._build_faction_prompt(
                count,
                world_description,
                major_tensions,
                user_input
            )
            
            response = await self.generator.generate(
                system_prompt="""You are a political strategist creating faction dynamics.
Each faction should have clear goals, resources, and leadership.
Factions should create tension and conflict that drives the story.""",
                user_prompt=prompt,
                context_type="world"
            )
            
            if response.error:
                raise ValueError(f"Faction generation failed: {response.error}")
            
            factions = self._parse_factions(response, count)
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
        user_input: str
    ) -> str:
        """Build faction generation prompt."""
        
        tensions_text = "\n".join([f"- {t}" for t in major_tensions])
        
        return f"""Create {count} distinct factions for this world:

World: {world_description[:400]}

Major Tensions:
{tensions_text}

{f"User's faction ideas: {user_input}" if user_input else ""}

For EACH faction, provide:

**FACTION NAME**
- Description: One sentence summary (used in scene prompts)
- Goals: 2-3 short-term goals driving their actions
- Leader: Name and title of leader
- Resources: What they control/possess (gold, magic, military, influence, etc)
- Alignment: Good/Evil/Neutral or their moral stance

Make factions:
- Have conflicting goals
- Create tension with each other
- Drive the story's major conflicts
- Be distinct in philosophy and methods

Include opposition/rivalry between factions."""
    
    def _parse_factions(self, response: Any, count: int) -> List[Faction]:
        """Parse factions from AI response."""
        
        factions = []
        response_text = ""
        
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        logger.debug(f"Parsing {len(response_text)} chars for factions")
        
        # Try parsing with ** markers first
        sections = re.split(r'\*\*([^*]+)\*\*', response_text)
        
        if len(sections) > 2:
            # Parse markdown-style factions
            for i in range(1, len(sections), 2):
                faction_name = sections[i].strip()
                faction_content = sections[i + 1].strip() if i + 1 < len(sections) else ""
                
                if not faction_name or len(faction_name) < 2:
                    continue
                
                faction = self._parse_faction_content(faction_name, faction_content)
                factions.append(faction)
                logger.debug(f"Created faction (markdown): {faction.name}")
        
        # Try parsing numbered/lettered format if not enough factions found
        if len(factions) < count // 2:
            numbered_sections = re.split(r'^(?:\d+\.|[A-Z]\.)\s*(.+?)(?=\n(?:\d+\.|[A-Z]\.)|$)', 
                                        response_text, flags=re.MULTILINE | re.DOTALL)
            
            for i in range(1, len(numbered_sections), 2):
                faction_name = numbered_sections[i].split('\n')[0].strip()
                faction_content = numbered_sections[i].strip()
                
                if faction_name and len(faction_name) > 2:
                    faction = self._parse_faction_content(faction_name, faction_content)
                    factions.append(faction)
                    logger.debug(f"Created faction (numbered): {faction.name}")
        
        # If still not enough, create defaults
        while len(factions) < count:
            faction = Faction(
                name=f"Faction {len(factions) + 1}",
                description="A faction with distinct goals and resources",
                goals=["Gain influence", "Protect their interests", "Advance their agenda"],
                leader="Unknown",
                resources="Unknown",
                alignment="Neutral"
            )
            factions.append(faction)
            logger.debug(f"Created default faction: {faction.name}")
        
        return factions[:count]
    
    def _parse_faction_content(self, name: str, content: str) -> Faction:
        """Parse a single faction's content."""
        description = self._extract_field(content, r'Description:\s*([^\n]+)', "A faction with unclear motives")
        goals_text = self._extract_field(content, r'Goals?:\s*([^\n]+(?:\n[^\n]+){0,3})', "")
        leader = self._extract_field(content, r'Leader:\s*([^\n]+)', "Unknown")
        resources = self._extract_field(content, r'Resources?:\s*([^\n]+)', "Unknown")
        alignment = self._extract_field(content, r'Alignment:\s*([^\n]+)', "Neutral")
        
        # Parse goals as list
        goals = [g.strip() for g in re.split(r'[-•\n]', goals_text) if g.strip()][:3]
        if not goals:
            goals = ["Gain power", "Survive", "Influence others"]
        
        return Faction(
            name=name,
            description=description,
            goals=goals,
            leader=leader,
            resources=resources,
            alignment=alignment
        )
    
    def _extract_field(self, text: str, pattern: str, default: str = "") -> str:
        """Extract field using regex."""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
