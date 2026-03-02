"""Arc generator for creating future arc outlines."""

import logging
from typing import List, Dict, Any
import uuid

from app.models.story import Story
from app.models.story_arc import StoryArc
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.arc_generator")


class ArcGenerator:
    """Generate high-level arc outlines for story progression."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize arc generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def generate_future_arcs(
        self,
        count: int = 3,
        user_input: str = ""
    ) -> List[StoryArc]:
        """Generate high-level arc outlines for the future.
        
        Args:
            count: Number of arcs to generate (default 3)
            user_input: Optional user guidance for arc direction
            
        Returns:
            List of generated StoryArc objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {count} future arc outlines for story '{self.story.id}'")
            
            # Build prompt
            prompt = self._build_arc_prompt(count, user_input)
            
            # Generate via AI
            response = await self.generator.generate(
                system_prompt="""You are a world-level story architect designing narrative progressions.
Your arcs describe how the WORLD ITSELF evolves and changes through major events.
Focus on world-scale conflicts, mysteries, and transformations - NOT individual character journeys.
Each arc shows a different phase of the world's evolution.""",
                user_prompt=prompt,
                context_type="world"  # Use world context type for structured generation
            )
            
            if response.error:
                raise ValueError(f"Arc generation failed: {response.error}")
            
            # Parse arc outlines
            arc_outlines = self._parse_arc_outlines(response, count)
            
            # Create and save StoryArc objects
            arcs = []
            for i, outline in enumerate(arc_outlines):
                arc = StoryArc(
                    id=f"arc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    title=outline.get('title', f"Arc {i+1}: Unknown"),
                    description=outline.get('description', ''),
                    premise=outline.get('premise', ''),
                    central_conflict=outline.get('central_conflict', ''),
                    narrative_direction=outline.get('narrative_direction', ''),
                    themes=outline.get('themes', []),
                    unresolved_mysteries=outline.get('mysteries', []),
                    plot_hooks=outline.get('hooks', []),
                    start_segment_id='',  # Will be set when arc becomes active
                )
                arc.save()
                arcs.append(arc)
                logger.info(f"Created arc outline: {arc.title}")
            
            return arcs
            
        except Exception as e:
            logger.error(f"Failed to generate arcs: {e}", exc_info=True)
            raise ValueError(f"Arc generation failed: {str(e)}")
    
    def _build_arc_prompt(self, count: int, user_input: str) -> str:
        """Build prompt for arc generation."""
        world_context = ""
        if self.story._context:
            world_context = f"""
Current World:
- Fundamental Truths: {', '.join(self.story._context.fundamental_truths[:3])}
- Setting: {self.story._context.worldbuilding.get('setting', 'Unknown') if isinstance(self.story._context.worldbuilding, dict) else 'Unknown'}"""
        
        story_context = f"""
Story: {self.story.title}
Description: {self.story.description}"""
        
        user_guidance = f"\n\nUser's Arc Direction: {user_input}" if user_input else ""
        
        return f"""Design {count} major WORLD-LEVEL story arcs showing how this world evolves:
{world_context}
{story_context}
{user_guidance}

IMPORTANT: Focus on how the WORLD ITSELF changes, not individual character journeys.
These are world phases, not personal arcs.

For each arc, describe:

TITLE: The phase/era of the world
(e.g., "The Age of Fractured Thrones", "The Rise of the Hidden Order")

PREMISE: What the world is experiencing in this phase
(e.g., "Political turmoil tears kingdoms apart", "Ancient powers awaken")

CENTRAL CONFLICT: The world-scale conflict that defines this phase
(e.g., "Factions clash for dominance", "Old magic vs. new order", "Civilization faces extinction")

THEMES: 3-5 major themes the world experiences
(e.g., corruption, survival, rebirth, decay, transformation)

NARRATIVE DIRECTION: How the world changes from arc to arc
(e.g., "Chaos of Arc 1 gives way to organization in Arc 2", "Hidden truths revealed")

MYSTERIES/QUESTIONS: 2-3 world mysteries that unfold in this phase
(e.g., "What caused the cataclysm?", "Who controls the shadow order?")

PLOT HOOKS: 2-3 major world events or turning points
(e.g., "The Great Schism splits the largest faction", "Prophecy of the return begins to manifest")

Make sure the arcs:
- Show clear world evolution (Arc 1 → Arc 2 → Arc 3)
- Each introduces new world conditions or conflicts
- Build progressively toward a climax
- Are driven by WORLD EVENTS not character choices"""
    
    def _parse_arc_outlines(self, response: Any, count: int) -> List[Dict[str, any]]:
        """Parse arc outlines from AI response."""
        import re
        import json
        outlines = []
        
        # Get response text
        response_text = ""
        if hasattr(response, 'content'):
            response_text = response.content
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        logger.debug(f"Parsing arc response ({len(response_text)} chars)")
        logger.debug(f"First 200 chars of response: {response_text[:200]}")
        
        # Try to parse as JSON first (may be wrapped in markdown code blocks)
        try:
            # Remove markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = response_text
            
            parsed_json = json.loads(json_text)
            
            # Extract arcs from JSON structure
            if isinstance(parsed_json, dict):
                # Try different possible keys for arcs
                arcs_data = parsed_json.get('arcs') or parsed_json.get('story_arcs') or []
                
                if not arcs_data and len(parsed_json) >= count:
                    # Try to use top-level keys like "arc_1", "arc_2", etc
                    arcs_data = [parsed_json.get(f'arc_{i+1}') or parsed_json.get(f'Arc {i+1}') 
                                 for i in range(count)]
                    arcs_data = [a for a in arcs_data if a]
            else:
                arcs_data = parsed_json if isinstance(parsed_json, list) else []
            
            # Build outlines from parsed data
            for i in range(count):
                if i < len(arcs_data) and isinstance(arcs_data[i], dict):
                    arc_data = arcs_data[i]
                    outline = {
                        'title': arc_data.get('title') or arc_data.get('name') or f"Arc {i+1}",
                        'description': arc_data.get('description') or arc_data.get('premise') or "",
                        'premise': arc_data.get('premise') or arc_data.get('description') or "",
                        'central_conflict': arc_data.get('central_conflict') or arc_data.get('conflict') or "",
                        'narrative_direction': arc_data.get('narrative_direction') or arc_data.get('direction') or "",
                        'themes': arc_data.get('themes') or [],
                        'mysteries': arc_data.get('mysteries') or arc_data.get('questions') or [],
                        'hooks': arc_data.get('hooks') or arc_data.get('plot_hooks') or []
                    }
                else:
                    outline = self._create_placeholder_arc(i)
                
                logger.debug(f"Parsed arc {i+1}: {outline['title']}")
                outlines.append(outline)
                
            return outlines
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Could not parse as JSON: {e}, falling back to text parsing")
        
        # Fallback: Parse as text with field markers
        # Try splitting by common arc delimiters
        arc_sections = re.split(r'(?:^|\n)(?:ARC\s+\d+|TITLE:|##\s+|^Arc\s+|^\d+\.)', response_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # First section is usually preamble, skip it
        if len(arc_sections) > 1:
            arc_sections = arc_sections[1:]
        
        logger.debug(f"Found {len(arc_sections)} arc sections via text parsing")
        
        for i in range(count):
            section = arc_sections[i].strip() if i < len(arc_sections) else ""
            
            outline = {
                'title': self._extract_field(section, r'(?:TITLE|NAME):?\s*([^\n]+)', f"Arc {i+1}"),
                'description': self._extract_field(section, r'(?:PREMISE|DESCRIPTION):?\s*([^\n]+)', ""),
                'premise': self._extract_field(section, r'(?:PREMISE|DESCRIPTION):?\s*([^\n]+)', ""),
                'central_conflict': self._extract_field(section, r'(?:CENTRAL\s+CONFLICT|CONFLICT):?\s*([^\n]+)', ""),
                'narrative_direction': self._extract_field(section, r'(?:NARRATIVE\s+DIRECTION|DIRECTION):?\s*([^\n]+)', ""),
                'themes': self._extract_list(section, r'THEMES:?\s*([^\n]+)', []),
                'mysteries': self._extract_list(section, r'MYSTERIES?(?:\s*/\s*QUESTIONS)?:?\s*([^\n]+)', []),
                'hooks': self._extract_list(section, r'(?:PLOT\s+HOOKS|HOOKS):?\s*([^\n]+)', [])
            }
            
            logger.debug(f"Parsed arc {i+1}: {outline['title']} - {len(outline.get('themes', []))} themes")
            outlines.append(outline)
        
        return outlines
    
    def _create_placeholder_arc(self, index: int) -> Dict[str, Any]:
        """Create a placeholder arc when parsing fails."""
        return {
            'title': f"Arc {index+1}",
            'description': "High-level narrative outline to be filled in",
            'premise': "",
            'central_conflict': "",
            'narrative_direction': "",
            'themes': [],
            'mysteries': [],
            'hooks': []
        }
    
    def _extract_field(self, text: str, pattern: str, default: str = "") -> str:
        """Extract a single field from text using regex."""
        import re
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default
    
    def _extract_list(self, text: str, pattern: str, default: List[str] = None) -> List[str]:
        """Extract a list of items from text."""
        import re
        if default is None:
            default = []
        
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return default
        
        items_text = match.group(1)
        # Split by comma, dash, or numbers
        items = re.split(r'[,\-\n]|\d+\.\s*', items_text)
        items = [item.strip() for item in items if item.strip()]
        
        return items[:5]  # Return max 5 items
