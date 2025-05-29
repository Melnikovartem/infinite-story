from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field
from .story_base import StoryBase
from .types import TextBlock, SceneGenerationResponse, ChoiceGenerationResponse
from .story_choice import StoryChoice
from ..engine.generator import Generator

class CharacterStatus(BaseModel):
    """Status of a character in a story segment."""
    character_id: str
    ai_status: str

class LocationStatus(BaseModel):
    """Status of a location in a story segment."""
    location_id: str
    ai_status: str

class StorySegment(StoryBase):
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
    incoming_choices: Dict[str, StoryChoice] = Field(default_factory=dict)  # Choices that lead to this segment
    outgoing_choices: Dict[str, StoryChoice] = Field(default_factory=dict)  # Choices that lead from this segment
    
    def add_incoming_choice(self, choice: StoryChoice) -> None:
        """Add a choice that leads to this segment."""
        self.incoming_choices[choice.id] = choice
        
    def add_outgoing_choice(self, choice: StoryChoice) -> None:
        """Add a choice that leads from this segment."""
        self.outgoing_choices[choice.id] = choice
        
    def generate_next_scene(
        self,
        choice_text: str,
        scene_generator: Generator[SceneGenerationResponse],
        choice_generator: Generator[ChoiceGenerationResponse]
    ) -> Tuple['StorySegment', StoryChoice]:
        """Generate a new scene based on the current scene and the player's choice.
        
        This is a stub implementation that will be replaced with actual AI generation.
        In the future, this will:
        1. Get the story context and background
        2. Get summaries of previous scenes
        3. Get current character and location states
        4. Generate a new scene based on the choice and context
        
        Args:
            choice_text: The text of the choice that led to this new scene
            scene_generator: The generator to use for scene generation
            choice_generator: The generator to use for choice generation
            
        Returns:
            A tuple containing:
            - A new StorySegment instance
            - A new StoryChoice instance connecting the current segment to the new one
        """
        
        # Generate the new scene
        scene_response = scene_generator.generate("")  # Empty prompt for now
        
        # Generate the choice
        choice_response = choice_generator.generate("")  # Empty prompt for now
        
        # Create new segment
        new_segment = StorySegment(
            id=f"segment_{int(self.id.split('_')[-1]) + 1}",  # Increment segment number
            story_id=self.story_id,
            from_choice_id=None,  # This will be set when we create the choice
            short_description=scene_response.scene_summary,
            text_blocks=[
                TextBlock(
                    type="narrator_describing",
                    content=scene_response.scene_text
                )
            ],
            characters=self.characters,  # Keep the same characters for now
            locations=self.locations  # Keep the same locations for now
        )
        
        # Create new choice connecting current segment to new segment
        new_choice = StoryChoice(
            id=f"choice_{len(self.outgoing_choices) + 1}",
            story_id=self.story_id,
            from_segment_id=self.id,
            to_segment_id=new_segment.id,
            text=choice_response.choice_text
        )
        
        # Set up the choice pointers
        new_segment.from_choice_id = new_choice.id
        new_segment.add_incoming_choice(new_choice)
        self.add_outgoing_choice(new_choice)
        
        # Save the new segment and choice to link them to the story
        new_segment.save()
        new_choice.save()
        
        return new_segment, new_choice
