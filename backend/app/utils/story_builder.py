"""Utilities for building and creating new stories."""

import uuid
import logging
from typing import List, Dict, Any, Optional
from app.models.story import Story
from app.models.story_segment import StorySegment, SegmentStatus
from app.models.story_choice import StoryChoice
from app.models.story_character import StoryCharacter, AvatarShape
from app.models.story_location import StoryLocation
from app.models.story_context import StoryContext
from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode as EpisodeRecap
from app.models.text_types import TextBlock, TextType

logger = logging.getLogger("infinite_story.utils.story_builder")


class StoryBuilder:
    """Builder for creating new stories with a fluent API."""
    
    def __init__(self, story_id: str, title: str, description: str, genre: str = "Unknown"):
        """Initialize a story builder.
        
        Args:
            story_id: Unique identifier for the story (e.g., "my_first_story")
            title: Display title of the story
            description: Long description of the story
            genre: Genre tag (e.g., "Dark Fantasy", "Sci-Fi", "Mystery")
        """
        self.story = Story(
            id=story_id,
            title=title,
            description=description,
            genre=genre,
            start_segment_id=None  # Will be set when first segment is created
        )
        self.characters: Dict[str, StoryCharacter] = {}
        self.locations: Dict[str, StoryLocation] = {}
        self.segments: Dict[str, StorySegment] = {}
        self.choices: Dict[str, StoryChoice] = {}
        logger.info(f"Created story builder for '{story_id}': {title}")
    
    def add_worldbuilding(
        self,
        fundamental_truths: List[str],
        worldbuilding: Dict[str, Any]
    ) -> "StoryBuilder":
        """Add worldbuilding context to the story.
        
        Args:
            fundamental_truths: List of core truths about the world
            worldbuilding: Dictionary of worldbuilding elements
            
        Returns:
            Self for chaining
        """
        context = StoryContext(
            story=self.story,
            id="main_context",
            fundamental_truths=fundamental_truths,
            worldbuilding=worldbuilding
        )
        logger.info(f"Added worldbuilding context with {len(fundamental_truths)} truths")
        return self
    
    def add_character(
        self,
        char_id: str,
        name: str,
        description: str,
        background: str,
        avatar_shape: str = "circle",
        avatar_color: str = "#FF6B6B"
    ) -> "StoryBuilder":
        """Add a character to the story.
        
        Args:
            char_id: Unique character identifier
            name: Character's name
            description: Brief description
            background: Character's backstory
            avatar_shape: Avatar shape (circle, square, triangle, diamond, star, pentagon)
            avatar_color: Hex color code for avatar
            
        Returns:
            Self for chaining
        """
        try:
            shape = AvatarShape(avatar_shape.lower())
        except ValueError:
            logger.warning(f"Invalid avatar shape '{avatar_shape}', defaulting to circle")
            shape = AvatarShape.CIRCLE
        
        character = StoryCharacter(
            story=self.story,
            id=char_id,
            name=name,
            description=description,
            background=background,
            avatar_shape=shape,
            avatar_color=avatar_color
        )
        self.characters[char_id] = character
        logger.info(f"Added character '{name}' ({char_id})")
        return self
    
    def add_location(
        self,
        loc_id: str,
        name: str,
        description: str
    ) -> "StoryBuilder":
        """Add a location to the story.
        
        Args:
            loc_id: Unique location identifier
            name: Location's name
            description: Location's description
            
        Returns:
            Self for chaining
        """
        location = StoryLocation(
            story=self.story,
            id=loc_id,
            name=name,
            description=description
        )
        self.locations[loc_id] = location
        logger.info(f"Added location '{name}' ({loc_id})")
        return self
    
    def add_opening_segment(
        self,
        segment_id: str,
        title: str,
        content: str,
        atmosphere: str = "neutral",
        episode_number: int = 1,
        episode_tone: Optional[str] = None
    ) -> "StoryBuilder":
        """Add the opening segment to the story.
        
        Args:
            segment_id: Unique segment identifier
            title: Short description of the scene
            content: Narrative content
            atmosphere: Atmospheric descriptor
            episode_number: Episode number (default 1)
            episode_tone: Tone descriptor for the episode
            
        Returns:
            Self for chaining
        """
        text_block = TextBlock(
            type=TextType.NARRATOR_DESCRIBING,
            content=content
        )
        
        segment = StorySegment(
            story=self.story,
            id=segment_id,
            short_description=title,
            text_blocks=[text_block],
            atmosphere=atmosphere,
            episode_number=episode_number,
            episode_tone=episode_tone,
            segment_number_in_episode=1,
            status=SegmentStatus.GENERATED
        )
        
        self.segments[segment_id] = segment
        
        # Set as start segment if this is the first
        if self.story.start_segment_id is None:
            self.story.start_segment_id = segment_id
            logger.info(f"Set '{segment_id}' as opening segment")
        else:
            logger.info(f"Added segment '{title}' ({segment_id})")
        
        return self
    
    def add_segment(
        self,
        segment_id: str,
        title: str,
        content: str,
        atmosphere: str = "neutral",
        episode_number: int = 1,
        episode_tone: Optional[str] = None,
        parent_segment_id: Optional[str] = None
    ) -> "StoryBuilder":
        """Add a segment to the story.
        
        Args:
            segment_id: Unique segment identifier
            title: Short description of the scene
            content: Narrative content
            atmosphere: Atmospheric descriptor
            episode_number: Episode number
            episode_tone: Tone descriptor
            parent_segment_id: ID of the segment that leads to this one
            
        Returns:
            Self for chaining
        """
        text_block = TextBlock(
            type=TextType.NARRATOR_DESCRIBING,
            content=content
        )
        
        # Calculate segment number in episode based on parent
        segment_number = 1
        if parent_segment_id and parent_segment_id in self.segments:
            parent = self.segments[parent_segment_id]
            if parent.episode_number == episode_number:
                segment_number = parent.segment_number_in_episode + 1
        
        segment = StorySegment(
            story=self.story,
            id=segment_id,
            short_description=title,
            text_blocks=[text_block],
            atmosphere=atmosphere,
            episode_number=episode_number,
            episode_tone=episode_tone,
            segment_number_in_episode=segment_number,
            parent_segment_id=parent_segment_id,
            status=SegmentStatus.GENERATED
        )
        
        self.segments[segment_id] = segment
        logger.info(f"Added segment '{title}' ({segment_id})")
        return self
    
    def add_choice(
        self,
        choice_id: str,
        from_segment_id: str,
        text: str,
        to_segment_id: Optional[str] = None
    ) -> "StoryBuilder":
        """Add a choice connecting two segments.
        
        Args:
            choice_id: Unique choice identifier
            from_segment_id: Source segment ID
            text: Choice text shown to player
            to_segment_id: Destination segment ID (None for AI generation)
            
        Returns:
            Self for chaining
        """
        if from_segment_id not in self.segments:
            raise ValueError(f"Source segment '{from_segment_id}' not found")
        
        if to_segment_id and to_segment_id not in self.segments:
            raise ValueError(f"Destination segment '{to_segment_id}' not found")
        
        choice = StoryChoice(
            story=self.story,
            id=choice_id,
            from_segment_id=from_segment_id,
            to_segment_id=to_segment_id,
            text=text
        )
        
        # Connect choice to segment
        self.segments[from_segment_id].add_outgoing_choice(choice)
        if to_segment_id:
            self.segments[to_segment_id].add_incoming_choice(choice)
        
        self.choices[choice_id] = choice
        logger.info(f"Added choice '{text}' ({choice_id}) from '{from_segment_id}'")
        return self
    
    def save(self) -> str:
        """Save the story and all components to disk.
        
        Returns:
            The story ID
            
        Raises:
            ValueError: If story is incomplete
        """
        # Validate story is complete
        if not self.story.start_segment_id:
            raise ValueError("Story must have a starting segment")
        
        if self.story.start_segment_id not in self.segments:
            raise ValueError(f"Start segment '{self.story.start_segment_id}' not in segments")
        
        start_segment = self.segments[self.story.start_segment_id]
        if not start_segment.outgoing_choices:
            raise ValueError("Start segment must have at least one outgoing choice")
        
        # Save story metadata
        self.story.save()
        logger.info(f"Saved story metadata: {self.story.id}")
        
        # Save characters
        for character in self.characters.values():
            character.save()
        logger.info(f"Saved {len(self.characters)} characters")
        
        # Save locations
        for location in self.locations.values():
            location.save()
        logger.info(f"Saved {len(self.locations)} locations")
        
        # Save segments
        for segment in self.segments.values():
            segment.save()
        logger.info(f"Saved {len(self.segments)} segments")
        
        # Save choices
        for choice in self.choices.values():
            choice.save()
        logger.info(f"Saved {len(self.choices)} choices")
        
        # Create and save story arc
        arc_id = f"arc_1"
        story_arc = StoryArc(
            story_id=self.story.id,
            id=arc_id,
            title=f"Arc 1: {self.story.title}",
            description=f"The beginning of {self.story.title}",
            episode_ids=["episode_1"],
            episode_count=1,
            start_segment_id=self.story.start_segment_id,
            current_segment_id=max(
                self.segments.keys(),
                key=lambda k: len(self.segments[k].id)
            ) if self.segments else self.story.start_segment_id,
            premise=f"Explore the world of {self.story.title}",
            narrative_direction="The story unfolds..."
        )
        story_arc.save()
        logger.info(f"Created story arc: {arc_id}")
        
        # Update segments with arc reference
        for segment in self.segments.values():
            if segment.arc_id is None:
                segment.arc_id = arc_id
                segment.save()
        logger.info("Updated segments with arc references")
        
        # Create and save first episode recap
        episode_recap = EpisodeRecap(
            story=self.story,
            story_id=self.story.id,
            id="episode_1",
            episode_number=1,
            arc_id=arc_id,
            title=f"Episode 1: {self.story.title}",
            summary=self.story.description,
            key_themes=["beginning", "discovery"],
            tone="mysterious"
        )
        episode_recap.save()
        logger.info("Created first episode recap")
        
        logger.info(f"✅ Story '{self.story.id}' saved successfully!")
        return self.story.id

