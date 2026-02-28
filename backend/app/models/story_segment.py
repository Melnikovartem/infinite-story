from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
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
    and location statuses.
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
        prompt_builder = ScenePromptBuilder(self)
        user_prompt = prompt_builder.build_prompt(connecting_choice.text)

        # Generate the new scene
        scene_response: SceneTextGeneratorResponse = await generator.generate(
            system_prompt="",  # Use default system prompt
            user_prompt=user_prompt,
            context_type="scene"
        )

        # Check if there was an error during generation
        if scene_response.error:
            raise ValueError(f"Scene generation failed: {scene_response.error}")

        # Generate unique segment ID based on total number of segments
        import uuid
        segment_count = len(self.story.get_all_segments())
        new_segment_id = f"segment_{segment_count + 1}_{uuid.uuid4().hex[:8]}"

        # Create new segment
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

        # Copy over existing running status from current segment
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

        # Set up the choice pointers for connecting choice
        connecting_choice.to_segment_id = new_segment.id
        new_segment.add_incoming_choice(connecting_choice)
        self.add_outgoing_choice(connecting_choice)

        # Generate unique choice IDs based on total number of choices
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

        # Add outgoing choices to new segment
        new_segment.add_outgoing_choice(choice_1)
        new_segment.add_outgoing_choice(choice_2)
        
        # Save everything
        new_segment.save()
        choice_1.save()
        choice_2.save()
        connecting_choice.save()
        
        return new_segment
