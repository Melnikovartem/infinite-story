from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
from pydantic import BaseModel, Field

from app.models.types import TextType
from .story_block import StoryBlock
from .text_types import TextBlock
from .story_choice import StoryChoice

if TYPE_CHECKING:
    from ..engine.generator import TextGenerator
    from ..models.text_types import SceneTextGeneratorResponse

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
    
    # Stored Information
    from_choice_id: Optional[str] = None

    # Core Scene Information
    short_description: str = Field(description="Brief summary of the scene")
    atmosphere: str = Field(description="The overall mood and atmosphere of the scene")
    time_of_day: Optional[str] = Field(None, description="When the scene takes place")
    weather: Optional[str] = Field(None, description="Weather conditions during the scene")
    key_items: List[str] = Field(default_factory=list, description="Important items present or mentioned in the scene")

    text_blocks: List[TextBlock] = Field(default_factory=list, description="Sequence of text blocks that make up the scene")

    # Running Status of the Characters and Locations
    characters: List[CharacterStatus] = Field(default_factory=list)
    locations: List[LocationStatus] = Field(default_factory=list)
    
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
        # Get plain text content
        info = f"{self.get_short_overview()}\n\n"
        
        # Get character information
        character_info = []
        for char_status in self.characters:
            character = self.story.get_character(char_status.character_id)
            if character:
                character_info.append(character.get_full_overview())

        if character_info:
            info += f"\n\nCharacters Present:\n{chr(10).join(character_info)}"
        
        
        return info

    def _generate_scene_prompt(self, choice_text: str) -> str:
        """Generate a comprehensive prompt for scene generation.
        
        This method combines all available context to create a rich prompt for the AI model.
        
        Args:
            choice_text: The text of the choice that led to this new scene
            
        Returns:
            A formatted prompt string containing all relevant context
        """

        # Combine all context into a comprehensive prompt
        prompt = f"""Generate a new scene that follows from the player's choice."""

        return prompt
        
    async def generate_next_scene(
        self,
        choice_text: str,
        generator: 'TextGenerator',
    ) -> Tuple['StorySegment', StoryChoice]:
        """Generate a new scene based on the current scene and the player's choice.
        
        This method:
        1. Gets the story context and background
        2. Gets summaries of previous scenes
        3. Gets current character and location states
        4. Generates a new scene based on the choice and context
        
        Args:
            choice_text: The text of the choice that led to this new scene
            generator: The text generator to use for scene generation
            
        Returns:
            A tuple containing:
            - A new StorySegment instance
            - A new StoryChoice instance connecting the current segment to the new one
        """
        from ..engine.generator_types import SceneTextGeneratorResponse
        
        # Generate the scene prompt using all available context
        user_prompt = self._generate_scene_prompt(choice_text)
        
        # Generate the new scene
        scene_response = await generator.generate(
            system_prompt="",  # Use default system prompt
            user_prompt=user_prompt,
            context_type="scene"
        )
        
        # Create new segment
        new_segment = StorySegment(
            story=self.story,
            id=f"segment_{int(self.id.split('_')[-1]) + 1}",  # Increment segment number
            from_choice_id=None,  # This will be set when we create the choice
            short_description=scene_response.short_description,
            text_blocks=scene_response.text_blocks,
            characters=self.characters,  # Keep the same characters for now
            locations=self.locations  # Keep the same locations for now
        )
        
        # Create new choice connecting current segment to new segment
        new_choice = StoryChoice(
            story=self.story,
            id=f"choice_{len(self.outgoing_choices) + 1}",
            from_segment_id=self.id,
            to_segment_id=new_segment.id,
            text=choice_text
        )
        
        # Set up the choice pointers
        new_segment.from_choice_id = new_choice.id
        new_segment.add_incoming_choice(new_choice)
        self.add_outgoing_choice(new_choice)
        
        # Save the new segment and choice to link them to the story
        new_segment.save()
        new_choice.save()
        
        return new_segment, new_choice
