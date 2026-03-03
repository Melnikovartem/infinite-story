from typing import List, Optional, Dict, Tuple, Any, TYPE_CHECKING
from enum import Enum
import logging
from pydantic import BaseModel, Field

from app.models.text_types import TextType
from .story_block import StoryBlock
from .text_types import TextBlock
from .story_choice import StoryChoice
from app.utils.prompt_builder import ScenePromptBuilder

if TYPE_CHECKING:
    from ..engine.generator import TextGenerator
    from ..models.text_types import SceneTextGeneratorResponse
    from .character_state import CharacterStateSnapshot

logger = logging.getLogger("infinite_story.models.story_segment")


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
        description="[DEPRECATED] Keep for backward compatibility - use EpisodeMeta.character_state_snapshot instead"
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
    
    def get_short_overview(self) -> str:
        """Get a short descriptor of this story segment.
        
        Returns:
            A string describing the key events in this segment
        """
        # Get previous segments
        prev_segments = self.get_story_segments_before(max_depth=10)
        
        # Get plain text content
        content = self.get_plain_text_script()
        
        # Format the overview
        overview = f"Scene: {self.short_description}\n\n"
        if prev_segments:
            overview += f"Previous Scenes:\n{prev_segments}\n\n"
        overview += f"Scene Script:\n{content}"
            
        return overview

    def get_full_overview(self) -> str:
        """Get detailed information about this story segment.
        
        Returns:
            A string containing comprehensive scene information
        """
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
                character_info.append(character.get_full_overview())

        if character_info:
            overview += f"\n\nCharacters Present:\n{'\n'.join(character_info)}"

        location_info = []
        for loc_status in self.locations_running_status:
            location = self.story.get_location(loc_status.location_id)
            if location:
                location_info.append(location.get_full_overview())

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
            segment_id=self.id,
            player_choice=connecting_choice.text
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

        # Generate the new scene
        logger.info("[GEN_SCENE_GEN_START] ⚙️  Calling generator.generate()")
        gen_api_start = time.time()
        scene_response: SceneTextGeneratorResponse = await generator.generate(
            system_prompt="",  # Use default system prompt
            user_prompt=user_prompt,
            context_type="scene"
        )
        gen_api_duration = time.time() - gen_api_start
        logger.debug(f"[GEN_SCENE_GEN_RESPONSE] Generator returned response in {gen_api_duration:.2f}s")
        logger.debug(f"Generator returned response")

        # Check if there was an error during generation
        if scene_response.error:
            logger.error(f"[GEN_SCENE_ERROR] Scene generation failed: {scene_response.error}")
            raise ValueError(f"Scene generation failed: {scene_response.error}")

        logger.debug(f"[GEN_SCENE_RESPONSE_OK] Response validated successfully")

        # Generate unique segment ID based on total number of segments
        import uuid
        logger.debug(f"[GEN_SCENE_ID_GEN] Generating unique segment ID")
        segment_count = len(self.story.get_all_segments())
        new_segment_id = f"segment_{segment_count + 1}_{uuid.uuid4().hex[:8]}"
        logger.debug(f"[GEN_SCENE_ID_CREATED] New segment ID: {new_segment_id}")

        # Create new segment
        logger.debug(f"[GEN_SCENE_CREATE_OBJ] Creating new StorySegment object")
        new_segment = StorySegment(
            story=self.story,
            id=new_segment_id,
            short_description=scene_response.short_description,
            atmosphere=scene_response.atmosphere,
            time_of_day=scene_response.time_of_day,
            weather=scene_response.weather,
            key_items=scene_response.key_items,
            text_blocks=scene_response.text_blocks,
            characters_present=scene_response.characters_present,
            locations_present=scene_response.locations_present,
            # Link to parent segment for genealogy tracking
            parent_segment_id=self.id,
            # Inherit arc and episode info from parent segment
            arc_id=self.arc_id,
            episode_number=self.episode_number,
            episode_tone=self.episode_tone,
            episode_end_condition=self.episode_end_condition,
            segment_number_in_episode=self.segment_number_in_episode + 1,
            protagonist_id=self.protagonist_id
        )
        logger.debug(f"[GEN_SCENE_CREATE_OK] StorySegment object created")
        logger.debug(f"[GEN_SCENE_ARC_INHERIT] Inherited arc_id={new_segment.arc_id}, episode={new_segment.episode_number}")

        # Copy over existing running status from current segment
        logger.debug(f"[GEN_SCENE_COPY_STATUS] Copying character and location statuses")
        new_segment.characters_running_status.extend(self.characters_running_status)
        new_segment.locations_running_status.extend(self.locations_running_status)

        # Update character and location statuses based on changes
        logger.debug(f"Processing {len(scene_response.character_status_change)} character status changes")
        for char_id, new_status in scene_response.character_status_change.items():
            # Add new status after existing one
            new_segment.characters_running_status.append(
                CharacterStatus(character_id=char_id, current_status=new_status)
            )
            logger.debug(f"  Character '{char_id}' status: {new_status}")

        logger.debug(f"Processing {len(scene_response.location_status_change)} location status changes")
        for loc_id, new_status in scene_response.location_status_change.items():
            # Add new status after existing one
            new_segment.locations_running_status.append(
                LocationStatus(location_id=loc_id, current_status=new_status)
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
            text=scene_response.choice_1
        )

        choice_2 = StoryChoice(
            story=self.story,
            id=choice_2_id,
            from_segment_id=new_segment.id,
            to_segment_id=None,
            text=scene_response.choice_2
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
