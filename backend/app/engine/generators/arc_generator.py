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
                system_prompt="""You are a story structure expert creating compelling narrative arcs.
Your arcs should be interconnected, build on each other, and create an overall epic journey.
Focus on high-level structure and themes, not character details.""",
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
        
        return f"""Design {count} major story arcs that form a compelling narrative progression:
{world_context}
{story_context}
{user_guidance}

For each arc, provide:

TITLE: A compelling name for the arc

PREMISE: The core narrative idea (e.g., "Power corrupts the innocent")

CENTRAL CONFLICT: The main struggle that drives this arc
(e.g., "Hero vs. their own ambition", "Kingdom vs. external threat")

THEMES: 3-5 major themes explored
(e.g., betrayal, redemption, loss, growth, power)

NARRATIVE DIRECTION: Where this arc takes the story
(e.g., "Escalates conflicts introduced in Arc 1", "Reveals hidden truths")

MYSTERIES/QUESTIONS: 2-3 mysteries that will drive this arc
(e.g., "Who is the real villain?", "Can trust be rebuilt?")

PLOT HOOKS: 2-3 key events or hooks to explore
(e.g., "Discovery of ancient prophecy", "Betrayal by trusted ally")

Make sure the arcs are:
- Connected to each other (each builds on the previous)
- Distinct in tone and focus
- Progressively raise stakes
- All lead toward a satisfying conclusion"""
    
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
        arc_sections = re.split(r'(?:^|\n)(?:ARC\s+\d+|TITLE:|\d+\.)', response_text, flags=re.IGNORECASE)
        
        # First section is usually preamble, skip it
        if len(arc_sections) > 1:
            arc_sections = arc_sections[1:]
        
        for i in range(count):
            section = arc_sections[i].strip() if i < len(arc_sections) else ""
            
            outline = {
                'title': self._extract_field(section, r'TITLE:?\s*([^\n]+)', f"Arc {i+1}"),
                'description': self._extract_field(section, r'PREMISE:?\s*([^\n]+)', ""),
                'premise': self._extract_field(section, r'PREMISE:?\s*([^\n]+)', ""),
                'central_conflict': self._extract_field(section, r'CENTRAL\s+CONFLICT:?\s*([^\n]+)', ""),
                'narrative_direction': self._extract_field(section, r'NARRATIVE\s+DIRECTION:?\s*([^\n]+)', ""),
                'themes': self._extract_list(section, r'THEMES:?\s*([^\n]+)', []),
                'mysteries': self._extract_list(section, r'MYSTERIES?(?:/QUESTIONS)?:?\s*([^\n]+)', []),
                'hooks': self._extract_list(section, r'PLOT\s+HOOKS:?\s*([^\n]+)', [])
            }
            
            logger.debug(f"Parsed arc {i+1}: {outline['title']}")
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
