"""Faction generator for creating world factions and politics."""

import logging
import json
import re
import uuid
from typing import List, Dict, Any
from app.models.story import Story
from app.models.story_faction import StoryFaction
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.faction_generator")


# Backward-compatible alias - old code that imports Faction gets StoryFaction
Faction = StoryFaction


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
    
    def _parse_factions(self, response: Any, count: int) -> List[StoryFaction]:
        """Parse factions from AI response into persistent StoryFaction objects."""
        
        factions = []
        response_text = ""
        
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        logger.debug(f"Parsing {len(response_text)} chars for factions")
        
        # Collect raw faction data first
        raw_factions = []
        
        # Known prompt headers to skip (these are template labels, not real faction names)
        _SKIP_HEADERS = {
            'faction name', 'faction', 'name', 'description', 'goals', 'goal',
            'leader', 'resources', 'alignment', 'opposition', 'rivalry',
            'important', 'note', 'notes', 'instructions',
        }
        
        # Try parsing with ** markers first
        sections = re.split(r'\*\*([^*]+)\*\*', response_text)
        
        if len(sections) > 2:
            for i in range(1, len(sections), 2):
                faction_name = sections[i].strip()
                faction_content = sections[i + 1].strip() if i + 1 < len(sections) else ""
                
                if not faction_name or len(faction_name) < 2:
                    continue
                
                # Skip known prompt template headers
                if faction_name.lower().strip(':').strip() in _SKIP_HEADERS:
                    continue
                
                # Skip if it looks like a field label (e.g., "Description:", "Goals:")
                if re.match(r'^(Description|Goals?|Leader|Resources?|Alignment|Opposition|Rivalry)\s*:', faction_name, re.IGNORECASE):
                    continue
                
                raw = self._parse_faction_content(faction_name, faction_content)
                raw_factions.append(raw)
                logger.debug(f"Parsed faction (markdown): {raw['name']}")
        
        # Try numbered/lettered format if not enough
        if len(raw_factions) < count // 2:
            # Split on numbered lines like "1. ", "2. ", "A. ", etc.
            numbered_sections = re.split(r'\n(?=\d+[\.\)]\s+|[A-Z][\.\)]\s+)', 
                                        response_text)
            
            for section in numbered_sections:
                section = section.strip()
                if not section:
                    continue
                
                # Extract faction name from first line
                first_line = section.split('\n')[0].strip()
                # Remove leading number/letter prefix
                faction_name = re.sub(r'^\d+[\.\)]\s*|^[A-Z][\.\)]\s*', '', first_line).strip()
                # Remove markdown bold
                faction_name = re.sub(r'\*\*([^*]+)\*\*', r'\1', faction_name).strip()
                # Remove trailing colon
                faction_name = faction_name.rstrip(':').strip()
                
                if faction_name and len(faction_name) > 2 and faction_name.lower() not in _SKIP_HEADERS:
                    raw = self._parse_faction_content(faction_name, section)
                    raw_factions.append(raw)
                    logger.debug(f"Parsed faction (numbered): {raw['name']}")
        
        # Fill defaults if not enough
        while len(raw_factions) < count:
            raw_factions.append({
                'name': f"Faction {len(raw_factions) + 1}",
                'description': "A faction with distinct goals and resources",
                'goals': ["Gain influence", "Protect their interests", "Advance their agenda"],
                'leader': "Unknown",
                'resources': "Unknown",
                'alignment': "Neutral",
            })
        
        # Convert to persistent StoryFaction objects
        for raw in raw_factions[:count]:
            faction_id = f"faction_{uuid.uuid4().hex[:8]}"
            faction = StoryFaction(
                id=faction_id,
                story=self.story,
                name=raw['name'],
                description=raw['description'],
                goals=raw['goals'],
                leader=raw['leader'],
                resources=raw['resources'],
                alignment=raw['alignment'],
            )
            factions.append(faction)
            logger.debug(f"Created StoryFaction: {faction.name} ({faction.id})")
        
        return factions
    
    def _parse_faction_content(self, name: str, content: str) -> Dict[str, Any]:
        """Parse a single faction's content into a raw dict."""
        description = self._extract_field(content, r'Description:\s*([^\n]+)', "A faction with unclear motives")
        goals_text = self._extract_field(content, r'Goals?:\s*([^\n]+(?:\n[^\n]+){0,3})', "")
        leader = self._extract_field(content, r'Leader:\s*([^\n]+)', "Unknown")
        resources = self._extract_field(content, r'Resources?:\s*([^\n]+)', "Unknown")
        alignment = self._extract_field(content, r'Alignment:\s*([^\n]+)', "Neutral")
        
        # Parse goals as list
        goals = [g.strip() for g in re.split(r'[-•\n]', goals_text) if g.strip()][:3]
        if not goals:
            goals = ["Gain power", "Survive", "Influence others"]
        
        return {
            'name': name,
            'description': description,
            'goals': goals,
            'leader': leader,
            'resources': resources,
            'alignment': alignment,
        }
    
    def _extract_field(self, text: str, pattern: str, default: str = "") -> str:
        """Extract field using regex."""
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return default
