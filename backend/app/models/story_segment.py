from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
from pydantic import BaseModel, Field
from .story_block import StoryBlock
from .text_types import TextBlock
from .story_choice import StoryChoice

if TYPE_CHECKING:
    from ..engine.generator import TextGenerator
    from ..engine.generator_types import SceneTextGeneratorResponse

class CharacterStatus(BaseModel):
    """Status of a character in a story segment."""
    character_id: str
    ai_status: str

class LocationStatus(BaseModel):
    """Status of a location in a story segment."""
    location_id: str
    ai_status: str

class StorySegment(StoryBlock):
    """A segment in a story.
    
    This represents a segment of the story with text blocks, character statuses,
    and location statuses.
    """
    
    from_choice_id: Optional[str] = None
    short_description: str  # Brief description of what happens in this segment
    text_blocks: List[TextBlock] = Field(default_factory=list)
    characters: List[CharacterStatus] = Field(default_factory=list)
    locations: List[LocationStatus] = Field(default_factory=list)
    
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
        
        # Generate the new scene
        scene_response = await generator.generate(
            system_prompt="You are a creative writing expert. Generate a scene that follows from the player's choice.",
            user_prompt=f"Previous scene: {self.short_description}\nPlayer's choice: {choice_text}",
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
