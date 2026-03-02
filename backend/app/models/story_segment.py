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
        description="State snapshot of each character at this segment"
    )
    change_notes: List[str] = Field(
        default_factory=list,
        description="Lightweight notes about character/location changes"
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
        1. Gets the story context and background
        2. Gets summaries of previous scenes
        3. Gets current character and location states
        4. Generates a new scene based on the choice and context
        
        Args:
            connecting_choice: The choice that led to this new scene
            generator: The text generator to use for scene generation
            
        Returns:
            A new StorySegment instance
        """
        # Generate the scene prompt using all available context
        logger.debug(f"[GEN_SCENE_START] Starting scene generation for choice: {connecting_choice.text[:50]}...")
        logger.debug(f"Building prompt for choice: {connecting_choice.text[:50]}...")
        prompt_builder = ScenePromptBuilder(self)
        logger.debug(f"[GEN_SCENE_PROMPT_BUILD] Building prompt with ScenePromptBuilder")
        user_prompt = prompt_builder.build_prompt(connecting_choice.text)
        logger.debug(f"Built prompt with {len(user_prompt)} characters")
        logger.debug(f"[GEN_SCENE_PROMPT_DONE] Prompt built successfully")

        # Generate the new scene
        logger.debug("[GEN_SCENE_GEN_START] Calling generator.generate()")
        scene_response: SceneTextGeneratorResponse = await generator.generate(
            system_prompt="",  # Use default system prompt
            user_prompt=user_prompt,
            context_type="scene"
        )
        logger.debug(f"[GEN_SCENE_GEN_RESPONSE] Generator returned response")
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
            locations_present=scene_response.locations_present
        )
        logger.debug(f"[GEN_SCENE_CREATE_OK] StorySegment object created")

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
        logger.debug(f"[GEN_SCENE_SAVE_START] Saving segment and choices")
        new_segment.save()
        choice_1.save()
        choice_2.save()
        logger.debug(f"[GEN_SCENE_SAVE_DONE] All entities saved successfully")
        logger.debug(f"[GEN_SCENE_COMPLETE] Scene generation completed successfully. New segment: {new_segment.id}")
        connecting_choice.save()
        logger.debug(f"[GEN_SCENE_RETURN] Returning new segment")
        
        return new_segment
