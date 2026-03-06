from typing import List, Optional, Dict, Tuple, Any, TYPE_CHECKING
from enum import Enum
import logging
from pydantic import BaseModel, Field

from app.models.text_types import TextType
from .story_block import StoryBlock
from .text_types import TextBlock
from .story_choice import StoryChoice
from app.utils.prompt_builder import ScenePromptBuilder
from app.utils.ai_response_parser import ResponseSchema, FieldSpec

if TYPE_CHECKING:
    from ..engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.models.story_segment")


# ---------------------------------------------------------------------------
# Scene generation schema for generate_structured()
# ---------------------------------------------------------------------------

# Valid TextType values for prompt instruction
_TEXT_TYPE_VALUES = ", ".join([t.value for t in TextType])

_SCENE_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("short_description", type="str", required=True, aliases=["description", "scene_description", "summary"]),
        FieldSpec("atmosphere", type="str", aliases=["mood", "tone"]),
        FieldSpec("time_of_day", type="str", aliases=["time", "timeOfDay"]),
        FieldSpec("weather", type="str", aliases=["weather_conditions"]),
        FieldSpec("key_items", type="list", aliases=["items", "important_items"]),
        FieldSpec("text_blocks", type="list", required=True, aliases=["blocks", "text", "narrative", "scene_text"]),
        FieldSpec("characters_present", type="list", aliases=["characters", "present_characters"]),
        FieldSpec("locations_present", type="list", aliases=["locations", "present_locations"]),
        FieldSpec("character_status_change", type="dict", aliases=["character_changes", "status_changes"]),
        FieldSpec("location_status_change", type="dict", aliases=["location_changes"]),
        FieldSpec("change_notes", type="list", aliases=["changes", "notes", "episode_changes"]),
        FieldSpec("choice_1", type="str", required=True, aliases=["first_choice", "option_1"]),
        FieldSpec("choice_2", type="str", required=True, aliases=["second_choice", "option_2"]),
    ],
    expect_array=False,
)

_SCENE_FALLBACK = {
    "short_description": "The scene continues",
    "atmosphere": "neutral",
    "time_of_day": None,
    "weather": None,
    "key_items": [],
    "text_blocks": [{"type": "narrator_describing", "content": "The story continues..."}],
    "characters_present": [],
    "locations_present": [],
    "character_status_change": {},
    "location_status_change": {},
    "change_notes": [],
    "choice_1": "Continue forward",
    "choice_2": "Reconsider your options",
}


def _parse_text_blocks(raw_blocks: Any) -> List[TextBlock]:
    """Convert raw text_blocks data from AI into TextBlock objects.

    Handles:
    - List of dicts with type/content keys  (standard)
    - A single string (treated as narrator_describing)
    - A list of strings (each becomes a narrator_describing block)
    - Malformed dicts missing type (defaults to narrator_describing)
    """
    if not raw_blocks:
        return []

    # Single string → one narrator block
    if isinstance(raw_blocks, str):
        return [TextBlock(type=TextType.NARRATOR_DESCRIBING, content=raw_blocks)]

    if not isinstance(raw_blocks, list):
        return [TextBlock(type=TextType.NARRATOR_DESCRIBING, content=str(raw_blocks))]

    blocks: List[TextBlock] = []
    for item in raw_blocks:
        if isinstance(item, str):
            blocks.append(TextBlock(type=TextType.NARRATOR_DESCRIBING, content=item))
            continue
        if isinstance(item, TextBlock):
            blocks.append(item)
            continue
        if isinstance(item, dict):
            content = item.get("content", "")
            if not content:
                continue
            # Resolve type — default to narrator_describing
            raw_type = item.get("type", "narrator_describing")
            try:
                block_type = TextType(raw_type)
            except ValueError:
                block_type = TextType.NARRATOR_DESCRIBING
            blocks.append(TextBlock(
                type=block_type,
                content=content,
                emotion=item.get("emotion"),
                character=item.get("character"),
            ))
    return blocks


class SegmentStatus(str, Enum):
    """Status of a story segment during generation and use."""
    UNEXPLORED = "unexplored"      # Not yet generated
    GENERATING = "generating"      # In progress
    GENERATED = "generated"        # Ready
    ARCHIVED = "archived"          # Replaced by compression

class CharacterStatus(BaseModel):
    """Status of a character in a story segment."""
    character_id: str
    current_status: str

class LocationStatus(BaseModel):
    """Status of a location in a story segment."""
    location_id: str
    current_status: str

class EntityChange(BaseModel):
    """A change to a character or location state during a segment.
    
    Tracks what changed during this segment so episode-end flush can update
    the actual character/location model with evolved descriptions.
    """
    entity_id: str  # "char_thorne" or "loc_veil"
    entity_type: str  # "character" or "location"
    entity_name: str  # "Thorne" or "Veil Edge" - for reference
    property: str  # "mood", "status", "stability", "description", etc.
    from_value: Optional[str] = None  # Previous value
    to_value: Optional[str] = None  # New value
    description: str = ""  # Human-readable: "Thorne's mood changed from hopeful to determined"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'entity_name': self.entity_name,
            'property': self.property,
            'from_value': self.from_value,
            'to_value': self.to_value,
            'description': self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityChange':
        """Create from dict."""
        return cls(**data)

class StorySegment(StoryBlock):
    """A segment in a story.
    
    This represents a segment of the story with text blocks, character statuses,
    and location statuses, enhanced with episode context and state tracking.
    """

    # Core Scene Information
    short_description: str = Field(description="Brief summary of the scene")
    recap: Optional[str] = Field(None, description="AI-generated recap of this segment (set after generation or at episode end)")
    atmosphere: Optional[str] = Field(None, description="The overall mood and atmosphere of the scene")
    time_of_day: Optional[str] = Field(None, description="When the scene takes place")
    weather: Optional[str] = Field(None, description="Weather conditions during the scene")
    key_items: List[str] = Field(default_factory=list, description="Important items present or mentioned in the scene")

    text_blocks: List[TextBlock] = Field(default_factory=list, description="Sequence of text blocks that make up the scene")

    characters_present: List[str] = Field(default_factory=list, description="List of character ids present in the scene")
    locations_present: List[str] = Field(default_factory=list, description="List of location ids present in the scene")

    # Running Status of the Characters and Locations
    characters: List[CharacterStatus] = Field(default_factory=list, description="List of character statuses in the scene")
    locations: List[LocationStatus] = Field(default_factory=list, description="List of location statuses in the scene")
    characters_running_status: List[CharacterStatus] = Field(default_factory=list)
    locations_running_status: List[LocationStatus] = Field(default_factory=list)
    
    # -- Parent/History Tracking (E0-1) --
    parent_segment_id: Optional[str] = Field(
        None,
        description="Which segment came before this one"
    )
    parent_choice_id: Optional[str] = Field(
        None,
        description="Which choice led to this segment"
    )
    
    # -- Episode Context (E0-1) --
    arc_id: Optional[str] = Field(
        None,
        description="Which story arc this segment belongs to"
    )
    episode_number: int = Field(
        1,
        description="Which episode (1-indexed)"
    )
    episode_tone: Optional[str] = Field(
        None,
        description="Tone tag for this episode (e.g., 'dark_and_mysterious')"
    )
    episode_end_condition: Optional[str] = Field(
        None,
        description="What should happen at end of episode"
    )
    segment_number_in_episode: int = Field(
        1,
        description="Position within episode (1-indexed, max ~20)"
    )
    pacing_weight: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="How close to episode end (0.0=start, 1.0=end)"
    )
    
    # -- Character & Location State (E0-1) --
    protagonist_id: Optional[str] = Field(
        None,
        description="Main character this episode"
    )
    character_states: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="[DEPRECATED] Keep for backward compatibility - use StoryEpisode.character_state_snapshot instead"
    )
    change_notes: List[str] = Field(
        default_factory=list,
        description="Running log of character/location changes in this segment (e.g., 'Knight discovered the betrayal', 'Relationship with King changed')"
    )
    
    # ========================================================================
    # NEW: RUNNING CHANGES - Entity State Changes in This Segment
    # ========================================================================
    # Structured tracking of what changed (character moods, location states, etc.)
    # These accumulate during the episode and are flushed at episode-end to update
    # the actual character/location model descriptions
    running_changes: List[EntityChange] = Field(
        default_factory=list,
        description="Structured changes to character/location state in this segment"
    )
    
    # ========================================================================
    # E2: Episode Metadata Fields (NEW)
    # ========================================================================
    episode_selected_themes: List[str] = Field(
        default_factory=list,
        description="Themes selected for this episode (from EpisodeMeta)"
    )
    episode_focus: str = Field(
        default="",
        description="Episode focus - which character/plot to advance (from EpisodeMeta)"
    )
    story_hooks: List[str] = Field(
        default_factory=list,
        description="Hooks to explore this episode (from EpisodeMeta)"
    )
    
    # -- Episode Completion Signals (E0-1) --
    end_condition_proximity: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="How close (0.0=far, 1.0=end condition met)"
    )
    protagonist_alive: bool = Field(
        True,
        description="Is the protagonist still alive (for death endings)"
    )
    triggers_episode_transition: bool = Field(
        False,
        description="Should this segment end the episode and start a new one"
    )
    
    # -- Immutability (E0-1) --
    status: SegmentStatus = Field(
        default=SegmentStatus.UNEXPLORED,
        description="State of this segment"
    )
    
    # -- Arc Finalization (E2-5) --
    is_mainline: bool = Field(
        False,
        description="Whether this segment is part of the arc's canonical mainline path"
    )
    
    # Non-Stored Information
    # Pointers to choices
    incoming_choices: Dict[str, StoryChoice] = Field(default_factory=dict, exclude=True)  # Choices that lead to this segment
    outgoing_choices: Dict[str, StoryChoice] = Field(default_factory=dict, exclude=True)  # Choices that lead from this segment

    def __init__(self, **data):
        """Initialize a StorySegment instance.
        
        Args:
            story: Optional Story instance to add this segment to
            **data: Segment data fields
        """
        super().__init__(**data)
        self.story.add_segment(self)
    
    @property
    def is_locked(self) -> bool:
        """Segment cannot be modified after generation."""
        return self.status == SegmentStatus.GENERATED
    
    def validate_locked(self) -> None:
        """Raise error if locked."""
        if self.is_locked:
            raise ValueError(f"Segment {self.id} is locked after generation and cannot be modified")
    
    def add_incoming_choice(self, choice: StoryChoice) -> None:
        """Add a choice that leads to this segment."""
        self.incoming_choices[choice.id] = choice
        
    def add_outgoing_choice(self, choice: StoryChoice) -> None:
        """Add a choice that leads from this segment."""
        self.outgoing_choices[choice.id] = choice

    def get_story_segments_before(self, max_depth: int = None) -> str:
        """Get all story segments before this one.
        
        Args:
            max_depth: Maximum number of segments to traverse backwards. If None, traverse all.
            
        Returns:
            String containing concatenated short descriptions of previous segments
        """
        segments = []
        current_depth = 0
        current_segment = self
        
        while True:
            # Stop if we've reached max depth
            if max_depth is not None and current_depth >= max_depth:
                break
                
            # Get first incoming choice
            if not current_segment.incoming_choices:
                break
                
            first_choice = next(iter(current_segment.incoming_choices.values()))
            if not first_choice.from_segment_id:
                break
                
            # Get previous segment and add to list
            prev_segment = self.story.get_segment(first_choice.from_segment_id)
            if not prev_segment:
                break
                
            segments.append(prev_segment.short_description)
            current_segment = prev_segment
            current_depth += 1
            
        # Return descriptions in chronological order
        return "- " + "\n- ".join(reversed(segments))


    def get_plain_text_script(self) -> str:
        """Get the text blocks formatted as plain text.
        
        This method combines all text blocks into a single, readable text format,
        preserving the sequence and type of each block.
        
        Returns:
            A string containing all text blocks formatted as plain text
        """
        if not self.text_blocks:
            return ""
            
        formatted_blocks = []
        for block in self.text_blocks:
            # Add a newline before each block except the first one
            if formatted_blocks:
                formatted_blocks.append("")
            
            # Format based on text type
            if block.type == TextType.SCENE_TITLE:
                formatted_blocks.append(f"# {block.content}")
            elif block.type == TextType.LOCATION_LABEL:
                formatted_blocks.append(f"📍 {block.content}")
            elif block.type == TextType.CHARACTER_SPEECH:
                formatted_blocks.append(f"\"{block.content}\"")
            elif block.type == TextType.CHARACTER_THOUGHT:
                formatted_blocks.append(f"*{block.content}*")
            elif block.type == TextType.SFX:
                formatted_blocks.append(f"*{block.content}*")
            elif block.type == TextType.VISUAL_CUE:
                formatted_blocks.append(f"[Visual: {block.content}]")
            elif block.type == TextType.MEDIA_OVERLAY:
                formatted_blocks.append(f"[Media: {block.content}]")
            elif block.type == TextType.SYSTEM_MESSAGE:
                formatted_blocks.append(f"⚠️ {block.content}")
            elif block.type == TextType.POEM_OR_SONG:
                formatted_blocks.append(f"🎵 {block.content}")
            elif block.type == TextType.LETTER_OR_NOTE:
                formatted_blocks.append(f"📝 {block.content}")
            elif block.type == TextType.FLASHBACK:
                formatted_blocks.append(f"[Flashback]\n{block.content}")
            elif block.type == TextType.DREAM_SEQUENCE:
                formatted_blocks.append(f"[Dream]\n{block.content}")
            elif block.type == TextType.NARRATOR_COMMENTARY:
                formatted_blocks.append(f"*{block.content}*")
            else:  # NARRATOR_DESCRIBING or any other type
                formatted_blocks.append(block.content)
            
        return "\n".join(formatted_blocks)
    
    def to_context_short(self) -> str:
        """Short context: short_description + recap if available."""
        parts = [self.short_description]
        if self.recap:
            parts.append(self.recap)
        return " | ".join(parts)

    def to_context_full(self) -> str:
        """Full context: scene info + characters + locations."""
         # Get previous segments
        prev_segments = self.get_story_segments_before(max_depth=10)
        
        # Get plain text content
        content = self.get_plain_text_script()
        
        # Format the overview
        overview = f"Scene: {self.short_description}\n\n"
        if prev_segments:
            overview += f"Previous Scenes:\n{prev_segments}\n\n"
        overview += f"Scene Script:\n{content}"
        
        # Get character information
        character_info = []
        for char_status in self.characters:
            character = self.story.get_character(char_status.character_id)
            if character:
                character_info.append(character.to_context_full())

        if character_info:
            overview += f"\n\nCharacters Present:\n{'\n'.join(character_info)}"

        location_info = []
        for loc_status in self.locations_running_status:
            location = self.story.get_location(loc_status.location_id)
            if location:
                location_info.append(location.to_context_full())

        if location_info:
            overview += f"\n\nLocations Present:\n{'\n'.join(location_info)}"
        
        
        return overview

    async def generate_next_scene(
        self,
        connecting_choice: 'StoryChoice',
        generator: 'TextGenerator',
    ) -> 'StorySegment':
        """Generate a new scene based on the current scene and the player's choice.
        
        This method:
        1. Builds rich context using SegmentContextBuilder (walks full parent chain)
        2. Gets summaries of previous scenes and arcs
        3. Gets current character and location states
        4. Generates a new scene based on the choice and full context
        
        Args:
            connecting_choice: The choice that led to this new scene
            generator: The text generator to use for scene generation
            
        Returns:
            A new StorySegment instance
        """
        import time
        from ..engine.segment_context_builder import SegmentContextBuilder
        from ..utils.prompt_formatter import PromptFormatter
        
        gen_start_time = time.time()
        
        # Build rich context using full parent chain walking
        logger.info(f"🎬 Starting scene generation for choice: {connecting_choice.text[:50]}...")
        logger.debug(f"Building context with SegmentContextBuilder (walks full parent chain)")
        
        context_start = time.time()
        context_builder = SegmentContextBuilder(self.story, generator)
        context = await context_builder.build_context(
            current_segment_id=self.id,
            user_choice=connecting_choice.text
        )
        context_duration = time.time() - context_start
        logger.debug(f"Built generation context in {context_duration:.2f}s with full parent chain")
        
        # Format the context into a readable prompt
        prompt_start = time.time()
        formatter = PromptFormatter()
        user_prompt = formatter.format_scene_context(
            context=context,
            choice_text=connecting_choice.text
        )
        prompt_duration = time.time() - prompt_start
        logger.debug(f"Formatted prompt with {len(user_prompt)} characters in {prompt_duration:.2f}s")

        # Generate the new scene via generate_structured()
        logger.info("[GEN_SCENE_GEN_START] Calling generator.generate_structured()")
        gen_api_start = time.time()

        # Build a supplementary note about text_blocks format for the LLM.
        # generate_structured() appends the schema format instruction automatically,
        # but text_blocks has special nested structure that benefits from an explicit hint.
        text_blocks_hint = (
            "\n\nIMPORTANT: text_blocks must be a JSON array of objects, each with:\n"
            f"  - type: one of [{_TEXT_TYPE_VALUES}]\n"
            "  - content: the actual text\n"
            "  - emotion: (optional) the emotional tone\n"
            "  - character: (optional) who is speaking\n"
        )

        scene_data: dict = await generator.generate_structured(
            system_prompt=generator.DEFAULT_SYSTEM_PROMPT,
            user_prompt=user_prompt + text_blocks_hint,
            schema=_SCENE_SCHEMA,
            fallback_defaults=[_SCENE_FALLBACK],
        )
        gen_api_duration = time.time() - gen_api_start
        logger.debug(f"[GEN_SCENE_GEN_RESPONSE] Generator returned response in {gen_api_duration:.2f}s")

        # Convert raw text_blocks dicts into TextBlock objects
        scene_text_blocks = _parse_text_blocks(scene_data.get("text_blocks", []))
        if not scene_text_blocks:
            # Absolute fallback — should rarely happen
            scene_text_blocks = [TextBlock(type=TextType.NARRATOR_DESCRIBING, content="The story continues...")]
            logger.warning("[GEN_SCENE_FALLBACK] No text blocks parsed, using fallback")

        # Generate unique segment ID based on total number of segments
        import uuid
        logger.debug(f"[GEN_SCENE_ID_GEN] Generating unique segment ID")
        segment_count = len(self.story.get_all_segments())
        new_segment_id = f"segment_{segment_count + 1}_{uuid.uuid4().hex[:8]}"
        logger.debug(f"[GEN_SCENE_ID_CREATED] New segment ID: {new_segment_id}")

        # ================================================================
        # Episode & Arc Lifecycle Management
        # ================================================================
        # Check if this segment should trigger an episode transition
        should_transition = context.get('should_transition_episode', False)
        
        # Default: inherit from parent
        next_episode_number = self.episode_number
        next_episode_tone = self.episode_tone
        next_episode_end_condition = self.episode_end_condition
        next_segment_number = self.segment_number_in_episode + 1
        next_arc_id = self.arc_id
        next_episode_selected_themes = self.episode_selected_themes
        next_episode_focus = self.episode_focus
        next_story_hooks = self.story_hooks
        
        if should_transition and self.arc_id:
            logger.info(f"[GEN_SCENE_EP_TRANSITION] Episode transition detected at segment {self.segment_number_in_episode}")
            try:
                from ..engine.episode_recap_generator import EpisodeRecapGenerator
                from ..engine.arc_transition_manager import ArcTransitionManager, ARC_COMPLETION_THRESHOLD
                from ..models.story_arc import StoryArc
                
                recap_generator = EpisodeRecapGenerator(self.story, generator)
                
                # Step 1: Generate recap for the ending episode
                try:
                    recap = await recap_generator.generate_recap(
                        episode_number=self.episode_number,
                        arc_id=self.arc_id,
                        triggering_segment_id=self.id
                    )
                    logger.info(f"[GEN_SCENE_RECAP_OK] Generated recap for episode {self.episode_number}: {recap.title}")
                except Exception as e:
                    logger.warning(f"[GEN_SCENE_RECAP_FAIL] Failed to generate episode recap: {e}")
                    recap = None
                
                # Step 1b: Flush episode changes to character/location descriptions
                try:
                    from ..engine.episode_flush_generator import EpisodeFlushGenerator
                    flush_gen = EpisodeFlushGenerator(self.story, generator)
                    # Walk the episode segments for flushing
                    episode_segs = recap_generator._walk_episode_segments(self.episode_number, self.arc_id)
                    if episode_segs:
                        flush_result = await flush_gen.flush_episode_changes(
                            episode_segs,
                            self.episode_number,
                            self.arc_id
                        )
                        flushed_chars = len(flush_result.get('flushed_characters', {}))
                        flushed_locs = len(flush_result.get('flushed_locations', {}))
                        logger.info(f"[GEN_SCENE_FLUSH_OK] Flushed {flushed_chars} characters, {flushed_locs} locations")
                except Exception as e:
                    logger.warning(f"[GEN_SCENE_FLUSH_FAIL] Episode flush failed (non-fatal): {e}")
                
                # Step 2: Increment arc.episode_count and save
                arc = StoryArc.load(self.story.id, self.arc_id)
                if arc:
                    arc.episode_count = (arc.episode_count or 0) + 1
                    arc.save()
                    # Update in-memory cache too
                    if self.story.get_arc(self.arc_id):
                        self.story.get_arc(self.arc_id).episode_count = arc.episode_count
                    logger.info(f"[GEN_SCENE_ARC_EP_COUNT] Arc {self.arc_id} episode_count now {arc.episode_count}")
                
                # Step 3: Check for arc transition (after ARC_COMPLETION_THRESHOLD episodes)
                if arc and arc.episode_count >= ARC_COMPLETION_THRESHOLD:
                    logger.info(f"[GEN_SCENE_ARC_TRANSITION] Arc {self.arc_id} reached {ARC_COMPLETION_THRESHOLD} episodes, checking transition")
                    try:
                        transition_manager = ArcTransitionManager(self.story, generator)
                        new_arc_id = await transition_manager.check_and_handle_arc_completion(
                            self.arc_id,
                            arc.episode_count
                        )
                        if new_arc_id and new_arc_id != self.arc_id:
                            logger.info(f"[GEN_SCENE_ARC_SWITCH] Switching arc: {self.arc_id} -> {new_arc_id}")
                            next_arc_id = new_arc_id
                            next_episode_number = 1  # Reset episode count for new arc
                        else:
                            next_episode_number = self.episode_number + 1
                    except Exception as e:
                        logger.warning(f"[GEN_SCENE_ARC_TRANSITION_FAIL] Arc transition failed: {e}")
                        next_episode_number = self.episode_number + 1
                else:
                    next_episode_number = self.episode_number + 1
                
                # Step 4: Generate new episode context
                #   Pass triggering_segment_id so the new episode's ID is
                #   episode_{arc_id}_{self.id}, and previous recap is stored
                #   inside the new episode's previous_episode_recap field.
                try:
                    new_ep_context = await recap_generator.generate_new_episode_context(
                        next_arc_id,
                        recap,
                        triggering_segment_id=self.id
                    )
                    next_episode_tone = new_ep_context.get('tone_tags', [next_episode_tone])[0] if new_ep_context.get('tone_tags') else next_episode_tone
                    next_episode_end_condition = new_ep_context.get('end_condition', next_episode_end_condition)
                    next_episode_selected_themes = new_ep_context.get('selected_themes', [])
                    next_episode_focus = new_ep_context.get('episode_focus', '')
                    next_story_hooks = new_ep_context.get('story_hooks', [])
                    logger.info(f"[GEN_SCENE_NEW_EP_OK] Generated context for episode {next_episode_number}")
                except Exception as e:
                    logger.warning(f"[GEN_SCENE_NEW_EP_FAIL] Failed to generate new episode context: {e}")
                
                # Reset segment counter for new episode
                next_segment_number = 1
                
            except Exception as e:
                logger.error(f"[GEN_SCENE_LIFECYCLE_ERROR] Episode/arc lifecycle error: {e}", exc_info=True)
                # Fall through with inherited values — story continues even if lifecycle fails
        
        # Create new segment
        logger.debug(f"[GEN_SCENE_CREATE_OBJ] Creating new StorySegment object")
        new_segment = StorySegment(
            story=self.story,
            id=new_segment_id,
            short_description=scene_data.get("short_description") or "The scene continues",
            atmosphere=scene_data.get("atmosphere"),
            time_of_day=scene_data.get("time_of_day"),
            weather=scene_data.get("weather"),
            key_items=scene_data.get("key_items") or [],
            text_blocks=scene_text_blocks,
            characters_present=scene_data.get("characters_present") or [],
            locations_present=scene_data.get("locations_present") or [],
            # Link to parent segment for genealogy tracking
            parent_segment_id=self.id,
            # Episode/arc info (may be updated by lifecycle management above)
            arc_id=next_arc_id,
            episode_number=next_episode_number,
            episode_tone=next_episode_tone,
            episode_end_condition=next_episode_end_condition,
            segment_number_in_episode=next_segment_number,
            protagonist_id=self.protagonist_id,
            # Episode metadata
            episode_selected_themes=next_episode_selected_themes,
            episode_focus=next_episode_focus,
            story_hooks=next_story_hooks,
            # Mark if this was the start of a new episode
            triggers_episode_transition=should_transition,
            # Episode tracking: change notes from AI
            change_notes=scene_data.get("change_notes") or [],
        )
        logger.debug(f"[GEN_SCENE_CREATE_OK] StorySegment object created")
        logger.debug(f"[GEN_SCENE_ARC_INFO] arc_id={new_segment.arc_id}, episode={new_segment.episode_number}, seg_in_ep={new_segment.segment_number_in_episode}")

        # Copy over existing running status from current segment
        # On episode transition, reset running status (it's been captured in the recap)
        # Otherwise, carry forward but prune to last 50 entries per list to prevent unbounded growth
        MAX_RUNNING_STATUS = 50
        logger.debug(f"[GEN_SCENE_COPY_STATUS] Copying character and location statuses")
        if should_transition:
            # Episode boundary: start fresh — running status was captured in the episode recap
            logger.debug(f"[GEN_SCENE_STATUS_RESET] Resetting running status for new episode")
        else:
            # Within episode: carry forward, pruning old entries if needed
            carried_chars = self.characters_running_status[-MAX_RUNNING_STATUS:] if len(self.characters_running_status) > MAX_RUNNING_STATUS else self.characters_running_status
            carried_locs = self.locations_running_status[-MAX_RUNNING_STATUS:] if len(self.locations_running_status) > MAX_RUNNING_STATUS else self.locations_running_status
            new_segment.characters_running_status.extend(carried_chars)
            new_segment.locations_running_status.extend(carried_locs)

        # Update character and location statuses based on changes
        char_status_changes = scene_data.get("character_status_change") or {}
        if not isinstance(char_status_changes, dict):
            char_status_changes = {}
        logger.debug(f"Processing {len(char_status_changes)} character status changes")
        for char_id, new_status in char_status_changes.items():
            new_segment.characters_running_status.append(
                CharacterStatus(character_id=str(char_id), current_status=str(new_status))
            )
            logger.debug(f"  Character '{char_id}' status: {new_status}")

        loc_status_changes = scene_data.get("location_status_change") or {}
        if not isinstance(loc_status_changes, dict):
            loc_status_changes = {}
        logger.debug(f"Processing {len(loc_status_changes)} location status changes")
        for loc_id, new_status in loc_status_changes.items():
            new_segment.locations_running_status.append(
                LocationStatus(location_id=str(loc_id), current_status=str(new_status))
            )
            logger.debug(f"  Location '{loc_id}' status: {new_status}")

        logger.debug(f"[GEN_SCENE_UPDATE_STATUS_DONE] Status updates completed")

        # Set up the choice pointers for connecting choice
        logger.debug(f"[GEN_SCENE_CONNECT_CHOICE] Connecting choice to new segment")
        connecting_choice.to_segment_id = new_segment.id
        new_segment.add_incoming_choice(connecting_choice)
        self.add_outgoing_choice(connecting_choice)

        # Generate unique choice IDs based on total number of choices
        logger.debug(f"[GEN_SCENE_CREATE_CHOICES] Creating new choices for the segment")
        choice_count = len(self.story.get_all_choices())
        choice_1_id = f"choice_{choice_count + 1}_{uuid.uuid4().hex[:8]}"
        choice_2_id = f"choice_{choice_count + 2}_{uuid.uuid4().hex[:8]}"

        # Create the two new choices leading from new segment
        choice_1 = StoryChoice(
            story=self.story,
            id=choice_1_id,
            from_segment_id=new_segment.id,
            to_segment_id=None,
            text=scene_data.get("choice_1") or "Continue forward"
        )

        choice_2 = StoryChoice(
            story=self.story,
            id=choice_2_id,
            from_segment_id=new_segment.id,
            to_segment_id=None,
            text=scene_data.get("choice_2") or "Reconsider your options"
        )
        logger.debug(f"[GEN_SCENE_CHOICES_CREATED] Created choices: {choice_1_id}, {choice_2_id}")

        # Add outgoing choices to new segment
        new_segment.add_outgoing_choice(choice_1)
        new_segment.add_outgoing_choice(choice_2)
        
        # Save everything
        save_start = time.time()
        logger.debug(f"[GEN_SCENE_SAVE_START] Saving segment and choices")
        new_segment.save()
        choice_1.save()
        choice_2.save()
        save_duration = time.time() - save_start
        logger.debug(f"[GEN_SCENE_SAVE_DONE] All entities saved in {save_duration:.2f}s")
        logger.info(f"[GEN_SCENE_COMPLETE] Scene generation completed successfully. New segment: {new_segment.id}")
        connecting_choice.save()
        
        total_gen_duration = time.time() - gen_start_time
        logger.info(f"⏱️  Total generation time: {total_gen_duration:.2f}s (Prompt: {prompt_duration:.2f}s + API: {gen_api_duration:.2f}s + Save: {save_duration:.2f}s)")
        logger.debug(f"[GEN_SCENE_RETURN] Returning new segment")
        
        return new_segment
