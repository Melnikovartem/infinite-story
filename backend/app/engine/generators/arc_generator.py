"""Arc generator for creating future arc outlines."""

import logging
from typing import List, Dict, Any
import uuid

from app.models.story import Story
from app.models.story_arc import StoryArc
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.generators.arc_generator")

# Schema for arc outlines
ARC_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("title", type="str", required=True, aliases=["name", "arc_title", "arc_name"]),
        FieldSpec("premise", type="str", required=True, aliases=["description", "overview"]),
        FieldSpec("central_conflict", type="str", required=True, aliases=["conflict", "main_conflict"]),
        FieldSpec("narrative_direction", type="str", aliases=["direction", "arc_direction"]),
        FieldSpec("themes", type="list", required=True, aliases=["theme_list", "major_themes"]),
        FieldSpec("mysteries", type="list", aliases=["questions", "unresolved_mysteries", "mysteries_questions"]),
        FieldSpec("hooks", type="list", aliases=["plot_hooks", "key_events", "turning_points"]),
    ],
    expect_array=True,
    min_items=3,
    max_items=5,
    item_tag="arc",
    root_tag="arcs",
)

# Example for prompt instruction
ARC_EXAMPLE = {
    "title": "The Age of Fractured Thrones",
    "premise": "Political turmoil tears kingdoms apart as old alliances crumble",
    "central_conflict": "Rival factions clash for dominance over the shattered realm",
    "narrative_direction": "Chaos gives way to new power structures",
    "themes": ["corruption", "loyalty", "survival"],
    "mysteries": ["Who assassinated the High King?", "What lies beneath the Sunken Citadel?"],
    "hooks": ["The Great Schism splits the largest faction", "A prophet emerges from the wasteland"],
}


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
            
            # Build schema with correct count
            schema = ResponseSchema(
                fields=ARC_SCHEMA.fields,
                expect_array=True,
                min_items=count,
                max_items=count + 2,
                item_tag="arc",
                root_tag="arcs",
            )
            
            # Build prompt with format-agnostic instructions
            prompt = self._build_arc_prompt(count, user_input, schema)
            
            # Generate via AI with structured parsing
            fallback_defaults = [self._create_placeholder_arc(i) for i in range(count)]
            arc_outlines = await self.generator.generate_structured(
                system_prompt="""You are a world-level story architect designing narrative progressions.
Your arcs describe how the WORLD ITSELF evolves and changes through major events.
Focus on world-scale conflicts, mysteries, and transformations - NOT individual character journeys.
Each arc shows a different phase of the world's evolution.""",
                user_prompt=prompt,
                schema=schema,
                fallback_defaults=fallback_defaults,
            )
            
            logger.debug(f"Parsed {len(arc_outlines)} arc outlines")
            
            # Create and save StoryArc objects
            arcs = []
            for i, outline in enumerate(arc_outlines[:count]):
                arc = StoryArc(
                    id=f"arc_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    title=outline.get('title', f"Arc {i+1}: Unknown"),
                    description=outline.get('premise', ''),
                    premise=outline.get('premise', ''),
                    central_conflict=outline.get('central_conflict', ''),
                    narrative_direction=outline.get('narrative_direction', ''),
                    themes=outline.get('themes', []),
                    unresolved_mysteries=outline.get('mysteries', []),
                    plot_hooks=outline.get('hooks', []),
                    start_segment_id='',  # Will be set when arc becomes active
                    is_active=(i == 0),  # First arc is active by default
                    is_future_arc=(i > 0),  # Subsequent arcs are future arcs
                )
                arc.save()
                arcs.append(arc)
                logger.info(f"Created arc outline: {arc.title} (active={arc.is_active})")
            
            return arcs
            
        except Exception as e:
            logger.error(f"Failed to generate arcs: {e}", exc_info=True)
            raise ValueError(f"Arc generation failed: {str(e)}")
    
    def _build_arc_prompt(self, count: int, user_input: str, schema: ResponseSchema) -> str:
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
        
        # Get format-agnostic response instructions
        format_instruction = AIResponseParser.get_prompt_instruction(
            schema, OutputFormat.JSON, example=ARC_EXAMPLE
        )
        
        return f"""Design {count} major WORLD-LEVEL story arcs showing how this world evolves:
{world_context}
{story_context}
{user_guidance}

IMPORTANT: Focus on how the WORLD ITSELF changes, not individual character journeys.
These are world phases, not personal arcs.

For each arc, provide:
- title: The phase/era name (e.g., "The Age of Fractured Thrones")
- premise: What the world is experiencing in this phase
- central_conflict: The world-scale conflict defining this phase
- themes: 3-5 major themes (e.g., corruption, survival, rebirth)
- narrative_direction: How the world changes from arc to arc
- mysteries: 2-3 world mysteries that unfold in this phase
- hooks: 2-3 major world events or turning points

Make sure the arcs:
- Show clear world evolution (Arc 1 -> Arc 2 -> Arc 3)
- Each introduces new world conditions or conflicts
- Build progressively toward a climax
- Are driven by WORLD EVENTS not character choices

{format_instruction}"""
    
    def _create_placeholder_arc(self, index: int) -> Dict[str, Any]:
        """Create a placeholder arc when parsing fails."""
        return {
            'title': f"Arc {index+1}",
            'premise': "High-level narrative outline to be filled in",
            'central_conflict': "",
            'narrative_direction': "",
            'themes': [],
            'mysteries': [],
            'hooks': []
        }
    
    async def select_active_characters_for_arc(
        self,
        arc: StoryArc
    ) -> List[str]:
        """Use LLM to designate most likely active characters for an arc.
        
        Args:
            arc: The StoryArc to select characters for
            
        Returns:
            List of character IDs most likely to be active in this arc
        """
        try:
            logger.info(f"Selecting active characters for arc: {arc.title}")
            
            # Get all characters in story
            all_characters = self.story.get_all_characters()
            char_list = "\n".join([
                f"- {char.name} (ID: {char.id}): {char.description}"
                for char in all_characters
            ])
            
            # Build prompt
            prompt = f"""Given this story arc, identify 3-5 characters most likely to be active and prominent.

ARC DETAILS:
Title: {arc.title}
Premise: {arc.premise}
Central Conflict: {arc.central_conflict}
Themes: {', '.join(arc.themes)}
Character Arc Goals: {arc.character_arc_goals}

AVAILABLE CHARACTERS:
{char_list}

Based on the arc's premise, conflict, themes, and character development goals, which 3-5 characters 
will likely be the most active and central to this arc? Consider:
- Which characters have arc goals defined?
- Which character traits/backgrounds fit the arc themes?
- Who would naturally be involved in the central conflict?

Respond with a JSON object:
{{
  "active_characters": [
    {{"character_id": "char_xxx", "reason": "brief explanation why they're central to this arc"}}
  ]
}}

Include exactly the character IDs. Be selective - focus on the most important characters."""
            
            active_char_schema = ResponseSchema(
                fields=[
                    FieldSpec("active_characters", type="list", required=True, aliases=["characters"]),
                ],
                expect_array=False,
            )
            result = await self.generator.generate_structured(
                system_prompt="You are a narrative director selecting which characters will be most prominent in an upcoming arc.",
                user_prompt=prompt,
                schema=active_char_schema,
                fallback_defaults=[{"active_characters": []}],
            )
            
            active_chars = result.get("active_characters", [])
            active_ids = []
            for char in active_chars:
                if isinstance(char, dict):
                    cid = char.get("character_id")
                    if cid:
                        active_ids.append(cid)
                elif isinstance(char, str):
                    active_ids.append(char)
            
            logger.info(f"Selected {len(active_ids)} active characters for arc {arc.id}: {active_ids}")
            return active_ids
            
        except Exception as e:
            logger.error(f"Failed to select active characters: {e}", exc_info=True)
            return []
