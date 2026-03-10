"""Reusable story creation orchestrator.

Extracts the 10-step generation pipeline from CLI into a reusable class
that can be driven by CLI, API endpoints, or tests.
"""

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from app.models.story import Story
from app.models.story_segment import StorySegment, _SCENE_SCHEMA, _SCENE_FALLBACK, _parse_text_blocks
from app.models.story_choice import StoryChoice
from app.models.text_types import TextBlock
from app.engine.generator import TextGenerator
from app.engine.step_generation_manager import StepGenerationManager

logger = logging.getLogger("infinite_story.engine.story_creation_orchestrator")


@dataclass
class StepProgress:
    """Progress information for a single generation step."""
    step: int
    name: str
    status: str  # pending, running, completed, failed, skipped
    message: str = ""
    detail: Optional[Dict[str, Any]] = None


@dataclass
class CreationResult:
    """Result of story creation."""
    success: bool
    story_id: str
    story: Optional[Story] = None
    error: Optional[str] = None
    steps_completed: int = 0
    steps_total: int = 10
    artifacts: Dict[str, Any] = field(default_factory=dict)


# Callback type for progress updates
ProgressCallback = Callable[[StepProgress], None]


class StoryCreationOrchestrator:
    """Orchestrates the 10-step story creation pipeline.
    
    Extracted from CLI create_story_ai_async to be reusable
    across CLI, API, and tests.
    """
    
    def __init__(
        self,
        generator: TextGenerator,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.generator = generator
        self.progress_callback = progress_callback or (lambda p: None)
    
    def _emit(self, step: int, name: str, status: str, message: str = "", detail: Optional[Dict[str, Any]] = None):
        """Emit a progress update."""
        progress = StepProgress(step=step, name=name, status=status, message=message, detail=detail)
        self.progress_callback(progress)
        if status == "completed":
            logger.info(f"Step {step} ({name}): {message}")
        elif status == "failed":
            logger.error(f"Step {step} ({name}) failed: {message}")
        elif status == "running":
            logger.info(f"Step {step} ({name}): starting...")
    
    async def create_story(
        self,
        story_id: str,
        title: str,
        description: str,
        genre: str,
        world_input: str = "",
        first_scene_input: str = "",
    ) -> CreationResult:
        """Run the full 10-step story creation pipeline.
        
        Args:
            story_id: Unique identifier for the story
            title: Display title
            description: Story description
            genre: Genre (Fantasy, Sci-Fi, etc.)
            world_input: Optional user world vision
            first_scene_input: Optional opening scene direction
            
        Returns:
            CreationResult with the created story and artifacts
        """
        from app.engine.generators.story_planner import StoryPlanner
        from app.engine.generators.world_description_generator import WorldDescriptionGenerator
        from app.engine.generators.faction_generator import FactionGenerator
        from app.engine.generators.magic_system_generator import MagicSystemGenerator
        from app.engine.generators.arc_generator import ArcGenerator
        from app.engine.generators.character_generator import CharacterGenerator
        from app.engine.generators.protagonist_selector import ProtagonistSelector
        from app.engine.generators.location_generator import LocationGenerator
        
        result = CreationResult(success=False, story_id=story_id)
        
        try:
            # Check if story already exists
            existing = Story.load(story_id, story_id)
            if existing:
                result.error = f"Story '{story_id}' already exists"
                return result
            
            # Create base story object
            story = Story(
                id=story_id,
                story_id=story_id,
                title=title,
                description=description,
                genre=genre,
                start_segment_id="opening",
            )
            result.story = story
            
            # ── Step 0: Plan story scope ──
            self._emit(0, "Story Planner", "running")
            planner = StoryPlanner(self.generator)
            story_plan = await planner.plan_story_scope(title, description, genre)
            self._emit(0, "Story Planner", "completed",
                       f"{story_plan.get('total_factions', 0)} factions, "
                       f"{story_plan.get('total_locations', 0)} locations planned",
                       detail=story_plan)
            result.artifacts["story_plan"] = story_plan
            result.steps_completed = 1
            
            # ── Step 1: Generate world ──
            self._emit(1, "World Generator", "running")
            world_gen = WorldDescriptionGenerator(self.generator)
            world_context = await world_gen.generate_world_description(story=story, user_input=world_input)
            world_desc_full = ""
            if isinstance(world_context.worldbuilding, dict):
                world_desc_full = world_context.worldbuilding.get("world_description", "")
            if not world_desc_full:
                world_desc_full = ". ".join(world_context.fundamental_truths[:3])
            self._emit(1, "World Generator", "completed",
                       f"{len(world_context.fundamental_truths)} fundamental truths")
            result.artifacts["world_context"] = world_context
            result.steps_completed = 2
            
            # ── Steps 2-4: Factions, magic, locations (parallel) ──
            self._emit(2, "Faction Generator", "running")
            self._emit(3, "Magic System Generator", "running")
            self._emit(4, "Location Generator", "running")
            
            faction_gen = FactionGenerator(story, self.generator)
            magic_gen = MagicSystemGenerator(story, self.generator)
            loc_gen = LocationGenerator(story, self.generator)
            
            factions_task = faction_gen.generate_factions(
                count=story_plan.get("total_factions", 3),
                world_description=world_desc_full,
                major_tensions=story_plan.get("major_tensions", []),
                user_input=world_input,
            )
            magic_task = magic_gen.generate_magic_system(
                world_description=world_desc_full,
                genre=genre,
                user_input=world_input,
            )
            loc_task = loc_gen.generate_world_locations(
                world_description=world_desc_full,
                fundamental_truths=world_context.fundamental_truths,
                user_input=world_input,
            )
            
            factions_result, magic_result, loc_result = await asyncio.gather(
                factions_task, magic_task, loc_task,
                return_exceptions=True,
            )
            
            # Process factions
            factions: List[Any] = []
            if isinstance(factions_result, Exception):
                self._emit(2, "Faction Generator", "failed", str(factions_result)[:100])
            else:
                factions = factions_result
                self._emit(2, "Faction Generator", "completed", f"{len(factions)} factions")
            result.artifacts["factions"] = factions
            
            # Process magic system
            magic_system = None
            if isinstance(magic_result, Exception):
                self._emit(3, "Magic System Generator", "failed", str(magic_result)[:100])
            else:
                magic_system = magic_result
                name = magic_system.name if magic_system and hasattr(magic_system, "name") else "none"
                self._emit(3, "Magic System Generator", "completed", f"System: {name}")
            result.artifacts["magic_system"] = magic_system
            
            # Process locations
            locations: List[Any] = []
            if isinstance(loc_result, Exception):
                self._emit(4, "Location Generator", "failed", str(loc_result)[:100])
            else:
                locations = loc_result
                self._emit(4, "Location Generator", "completed", f"{len(locations)} locations")
            result.artifacts["locations"] = locations
            result.steps_completed = 5
            
            # ── Steps 5-6: Arcs and characters (parallel) ──
            self._emit(5, "Arc Generator", "running")
            self._emit(6, "Character Generator", "running")
            
            arc_gen = ArcGenerator(story, self.generator)
            arcs_task = arc_gen.generate_future_arcs(count=3, user_input=world_input)
            
            char_gen = CharacterGenerator(story, self.generator)
            chars_task = char_gen.generate_faction_characters(factions, story_plan)
            
            arcs_result, chars_result = await asyncio.gather(
                arcs_task, chars_task,
                return_exceptions=True,
            )
            
            arcs: List[Any] = []
            if isinstance(arcs_result, Exception):
                self._emit(5, "Arc Generator", "failed", str(arcs_result)[:100])
            else:
                arcs = arcs_result
                self._emit(5, "Arc Generator", "completed", f"{len(arcs)} arcs")
            result.artifacts["arcs"] = arcs
            
            characters: List[Any] = []
            if isinstance(chars_result, Exception):
                self._emit(6, "Character Generator", "failed", str(chars_result)[:100])
            else:
                characters = chars_result
                self._emit(6, "Character Generator", "completed", f"{len(characters)} characters")
            result.artifacts["characters"] = characters
            result.steps_completed = 7
            
            # ── Step 7: Protagonist selection ──
            self._emit(7, "Protagonist Selector", "running")
            protagonist = None
            proto_sel = ProtagonistSelector(story, self.generator)
            try:
                protagonist = await proto_sel.select_or_develop_protagonist(user_choice=None)
                name = protagonist.name if protagonist and hasattr(protagonist, "name") else "Unknown"
                self._emit(7, "Protagonist Selector", "completed", f"Protagonist: {name}")
            except Exception as e:
                self._emit(7, "Protagonist Selector", "failed", str(e)[:100])
            result.artifacts["protagonist"] = protagonist
            result.steps_completed = 8
            
            # ── Step 8-9: Opening scene + choices (single structured call) ──
            self._emit(8, "Opening Scene", "running")
            
            scene_direction = (
                f"User's direction: {first_scene_input}"
                if first_scene_input.strip()
                else "Create something that brings this world to life."
            )
            
            factions_summary = "\n".join(
                [f"- {f.name}: {f.description[:80]}" for f in factions[:3]]
            ) if factions else "None yet"
            locations_summary = "\n".join(
                [f"- {loc.name}: {loc.description[:80]}" for loc in locations[:3]]
            ) if locations else "None yet"
            protagonist_name = (
                protagonist.name
                if protagonist and hasattr(protagonist, "name")
                else "Unknown"
            )
            
            opening_prompt = f"""Create a CAPTIVATING opening scene for this story:

Title: {title}
Genre: {genre}
World Description: {world_desc_full}

Key Factions:
{factions_summary}

Key Locations:
{locations_summary}

Protagonist: {protagonist_name}

Scene Direction: {scene_direction}

Write an opening scene that:
- Immediately draws the reader into this LIVING world
- Establishes the atmosphere and mood
- Shows the world as a character - alive, breathing, with personality
- Hints at the story's core conflicts or mysteries
- Creates compelling story hooks
- Is vivid, atmospheric, and 2-3 paragraphs
- Ends with two meaningful choices for the player"""
            
            scene_data = await self.generator.generate_structured(
                system_prompt=(
                    "You are a master storyteller creating immersive opening scenes. "
                    "Write with vivid sensory details. Always provide two compelling, "
                    "distinct choices for the player at the end."
                ),
                user_prompt=opening_prompt,
                schema=_SCENE_SCHEMA,
                fallback_defaults=[_SCENE_FALLBACK],
            )
            
            first_arc_id = arcs[0].id if arcs else "arc_1"
            scene_text_blocks = _parse_text_blocks(scene_data.get("text_blocks", []))
            if not scene_text_blocks:
                scene_text_blocks = [
                    TextBlock(type="narrator_describing", content="The story begins...", emotion="mysterious")
                ]
            
            opening_segment = StorySegment(
                id="opening",
                story_id=story_id,
                story=story,
                short_description=scene_data.get("short_description") or "The Story Begins",
                atmosphere=scene_data.get("atmosphere") or "atmospheric",
                time_of_day=scene_data.get("time_of_day"),
                weather=scene_data.get("weather"),
                key_items=scene_data.get("key_items") or [],
                text_blocks=scene_text_blocks,
                characters_present=scene_data.get("characters_present") or [],
                locations_present=scene_data.get("locations_present") or [],
                episode_number=1,
                arc_id=first_arc_id,
                protagonist_id=protagonist.id if protagonist and hasattr(protagonist, "id") else None,
            )
            story.add_segment(opening_segment)
            self._emit(8, "Opening Scene", "completed", "Opening scene generated")
            result.steps_completed = 9
            
            # ── Step 9: Choices ──
            self._emit(9, "Choice Generator", "running")
            choices_list: List[StoryChoice] = []
            choice_count = 0
            
            # Get choices from either new format (choices array) or old format (choice_1, choice_2)
            choices_data = scene_data.get("choices")
            if not choices_data:
                # Fallback to old format for compatibility
                choices_data = []
                for choice_key in ["choice_1", "choice_2"]:
                    choice_text = scene_data.get(choice_key)
                    if choice_text:
                        choices_data.append({"text": choice_text})
            
            # Create up to 4 choices
            for choice_item in choices_data[:4]:
                choice_text = None
                choice_tone = None
                choice_consequence = None
                
                if isinstance(choice_item, dict):
                    choice_text = choice_item.get("text")
                    choice_tone = choice_item.get("tone")
                    choice_consequence = choice_item.get("consequence_hint")
                elif isinstance(choice_item, str):
                    choice_text = choice_item
                
                if choice_text and len(str(choice_text).strip()) > 5:
                    choice_count += 1
                    choice_id = f"choice_{choice_count}_{uuid.uuid4().hex[:8]}"
                    choice = StoryChoice(
                        story=story,
                        id=choice_id,
                        from_segment_id="opening",
                        to_segment_id=None,
                        text=str(choice_text).strip(),
                        tone=choice_tone,
                        consequence_hint=choice_consequence,
                    )
                    opening_segment.add_outgoing_choice(choice)
                    story.add_choice(choice)
                    choices_list.append(choice)
            
            self._emit(9, "Choice Generator", "completed", f"{len(choices_list)} choices")
            result.artifacts["choices"] = choices_list
            result.steps_completed = 10
            
            # Set start segment and update first arc
            story.start_segment_id = "opening"
            if arcs:
                arcs[0].start_segment_id = "opening"
                arcs[0].current_segment_id = "opening"
            
            # ── Save everything to disk ──
            story.save()
            world_context.save()
            for faction in factions:
                faction.save()
            if magic_system:
                magic_system.save()
            for location in locations:
                location.save()
            for arc in arcs:
                arc.save()
            for char in characters:
                char.save()
            if protagonist:
                protagonist.save()
            opening_segment.save()
            for choice in choices_list:
                choice.save()
            
            result.success = True
            logger.info(f"Story '{story_id}' created successfully with {result.steps_completed} steps")
            return result
            
        except Exception as e:
            logger.error(f"Story creation failed: {e}", exc_info=True)
            result.error = str(e)
            return result
    
    def get_creation_summary(self, result: CreationResult) -> Dict[str, Any]:
        """Build a summary dict from a CreationResult."""
        artifacts = result.artifacts
        return {
            "story_id": result.story_id,
            "success": result.success,
            "error": result.error,
            "steps_completed": result.steps_completed,
            "steps_total": result.steps_total,
            "summary": {
                "factions": len(artifacts.get("factions") or []),
                "locations": len(artifacts.get("locations") or []),
                "arcs": len(artifacts.get("arcs") or []),
                "characters": len(artifacts.get("characters") or []),
                "choices": len(artifacts.get("choices") or []),
                "has_protagonist": artifacts.get("protagonist") is not None,
                "has_magic_system": artifacts.get("magic_system") is not None,
            },
        }
