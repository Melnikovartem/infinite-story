"""Arc generator for creating future arc outlines."""

import logging
from typing import List, Dict, Any, Optional
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

# Schema for character arc goals generation (separate from world-level arc)
_CHAR_GOALS_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("character_goals", type="list", required=True,
                  aliases=["goals", "character_arc_goals", "characters"]),
    ],
    expect_array=False,
)

_CHAR_GOALS_EXAMPLE = {
    "character_goals": [
        {"character_id": "char_abc123", "goal": "Learn to trust others despite past betrayals"},
        {"character_id": "char_def456", "goal": "Prove their loyalty is not weakness but strength"},
    ]
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
            
            # Select active characters and generate character arc goals for each arc
            all_characters = self.story.get_all_characters()
            if all_characters:
                for arc in arcs:
                    try:
                        # Select which characters are active in this arc
                        active_ids = await self.select_active_characters_for_arc(arc)
                        if active_ids:
                            arc.active_characters = active_ids
                            arc.key_characters = active_ids[:3]  # Top 3 are key characters
                        
                        # Generate personal arc goals for active characters
                        goals = await self._generate_character_arc_goals(arc, all_characters)
                        if goals:
                            arc.character_arc_goals = goals
                            logger.info(
                                f"Generated {len(goals)} character arc goals for '{arc.title}': "
                                f"{list(goals.keys())}"
                            )
                        
                        arc.save()
                    except Exception as e:
                        logger.warning(f"Failed to generate character goals for arc '{arc.title}': {e}")
            
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
    
    async def _generate_character_arc_goals(
        self,
        arc: StoryArc,
        all_characters: Optional[list] = None
    ) -> Dict[str, str]:
        """Generate personal arc goals for characters active in this arc.
        
        Uses the arc's themes, premise, and conflict plus each character's
        personality/background to produce a personal goal per character.
        
        Args:
            arc: The StoryArc to generate goals for
            all_characters: Optional pre-fetched character list
            
        Returns:
            Dict mapping character_id -> goal string
        """
        try:
            if all_characters is None:
                all_characters = self.story.get_all_characters()
            
            if not all_characters:
                return {}
            
            # Focus on active characters if set, otherwise use all
            target_ids = set(arc.active_characters) if arc.active_characters else None
            target_chars = []
            for char in all_characters:
                if target_ids is None or char.id in target_ids:
                    target_chars.append(char)
            
            if not target_chars:
                return {}
            
            # Build character profiles for the prompt
            char_profiles = []
            for char in target_chars:
                personality_str = ", ".join(char.personality) if char.personality else "unknown"
                profile = (
                    f"- {char.name} (ID: {char.id}, role: {char.role.value})\n"
                    f"  Description: {char.description}\n"
                    f"  Background: {char.background}\n"
                    f"  Personality: {personality_str}\n"
                    f"  Current goals: {char.goals or 'None defined'}"
                )
                char_profiles.append(profile)
            
            char_profiles_text = "\n".join(char_profiles)
            
            format_instruction = AIResponseParser.get_prompt_instruction(
                _CHAR_GOALS_SCHEMA, OutputFormat.JSON, example=_CHAR_GOALS_EXAMPLE
            )
            
            prompt = f"""Given this story arc and its characters, generate a personal arc goal for each character.

ARC: {arc.title}
Premise: {arc.premise}
Central Conflict: {arc.central_conflict}
Themes: {', '.join(arc.themes)}
Narrative Direction: {arc.narrative_direction}

CHARACTERS:
{char_profiles_text}

For each character, create a personal arc goal that:
- Connects to the arc's themes and conflict
- Reflects their personality, background, and existing goals
- Represents internal growth or a personal challenge (not just plot objectives)
- Is specific enough to track progress but broad enough to develop over multiple episodes
- Examples: "Learn to trust despite past betrayals", "Choose between duty and personal desire",
  "Confront the truth about their origins", "Find redemption for past mistakes"

{format_instruction}"""
            
            data = await self.generator.generate_structured(
                system_prompt=(
                    "You are a character development specialist. "
                    "You design personal growth arcs that interweave with world-level narrative arcs. "
                    "Each character's goal should feel organic to who they are."
                ),
                user_prompt=prompt,
                schema=_CHAR_GOALS_SCHEMA,
                fallback_defaults=[{"character_goals": []}],
            )
            
            # Parse the response into a dict
            goals_dict: Dict[str, str] = {}
            raw_goals = data.get("character_goals", [])
            if isinstance(raw_goals, list):
                for entry in raw_goals:
                    if isinstance(entry, dict):
                        cid = entry.get("character_id", "")
                        goal = entry.get("goal", "")
                        if cid and goal:
                            goals_dict[cid] = goal
                    elif isinstance(entry, str):
                        # Handle case where AI returns flat strings
                        logger.debug(f"Skipping non-dict character goal entry: {entry[:80]}")
            
            return goals_dict
            
        except Exception as e:
            logger.warning(f"Failed to generate character arc goals: {e}", exc_info=True)
            return {}
