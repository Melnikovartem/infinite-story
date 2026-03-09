"""Utility for loading story data from disk."""

import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_choice import StoryChoice
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_base import LOCAL_DATA_DIR

logger = logging.getLogger("infinite_story.utils.story_loader")


class StoryLoader:
    """Utility class for loading story data from disk."""
    
    @staticmethod
    def list_all_stories() -> List[Dict[str, Any]]:
        """Load metadata for all stories from disk.
        
        Returns:
            List of story metadata dictionaries
        """
        if not LOCAL_DATA_DIR.exists():
            return []
        
        stories = []
        for story_dir in LOCAL_DATA_DIR.iterdir():
            if not story_dir.is_dir():
                continue
            
            story_id = story_dir.name
            try:
                story_data = StoryLoader.load_story(story_id)
                if story_data:
                    stories.append({
                        "id": story_data.id,
                        "title": story_data.title,
                        "description": story_data.description,
                        "genre": story_data.genre,
                        "created_at": story_data.created_at.isoformat(),
                        "updated_at": story_data.updated_at.isoformat(),
                    })
            except Exception as e:
                logger.error(f"Error loading story {story_id}: {e}")
                continue
        
        return stories
    
    @staticmethod
    def load_story(story_id: str) -> Optional[Story]:
        """Load a single story with its metadata.
        
        Args:
            story_id: The ID of the story to load
            
        Returns:
            Story object or None if not found
        """
        story_file = LOCAL_DATA_DIR / story_id / "story" / f"{story_id}.json"
        
        if not story_file.exists():
            logger.warning(f"Story file not found: {story_file}")
            return None
        
        try:
            with open(story_file, "r") as f:
                data = json.load(f)
            
            # Create Story object
            story = Story(**data)
            logger.debug(f"Loaded story: {story_id}")
            return story
        except Exception as e:
            logger.error(f"Error loading story {story_id}: {e}")
            return None
    
    @staticmethod
    def load_full_story(story_id: str) -> Optional[Story]:
        """Load a story with ALL components wired up (segments, choices, characters, locations).
        
        This creates a fully connected graph where segments have their
        incoming/outgoing choices populated, making it suitable for
        AI generation which needs to walk the parent chain.
        
        Args:
            story_id: The ID of the story to load
            
        Returns:
            Story object with all components loaded, or None if not found
        """
        story = StoryLoader.load_story(story_id)
        if not story:
            return None
        
        # Load all segments
        segments_dir = LOCAL_DATA_DIR / story_id / "storysegment"
        if segments_dir.exists():
            for seg_file in segments_dir.glob("*.json"):
                try:
                    with open(seg_file, "r") as f:
                        data = json.load(f)
                    # StorySegment.__init__ calls story.add_segment(self)
                    StorySegment(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading segment {seg_file.stem}: {e}")
        
        # Load all choices
        choices_dir = LOCAL_DATA_DIR / story_id / "storychoice"
        if choices_dir.exists():
            for choice_file in choices_dir.glob("*.json"):
                try:
                    with open(choice_file, "r") as f:
                        data = json.load(f)
                    # StoryChoice.__init__ calls story.add_choice(self)
                    StoryChoice(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading choice {choice_file.stem}: {e}")
        
        # Load all characters
        chars_dir = LOCAL_DATA_DIR / story_id / "storycharacter"
        if chars_dir.exists():
            for char_file in chars_dir.glob("*.json"):
                try:
                    with open(char_file, "r") as f:
                        data = json.load(f)
                    StoryCharacter(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading character {char_file.stem}: {e}")
        
        # Load all locations
        locs_dir = LOCAL_DATA_DIR / story_id / "storylocation"
        if locs_dir.exists():
            for loc_file in locs_dir.glob("*.json"):
                try:
                    with open(loc_file, "r") as f:
                        data = json.load(f)
                    StoryLocation(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading location {loc_file.stem}: {e}")
        
        # Wire up segment incoming/outgoing choices
        for choice in story.get_all_choices():
            if choice.from_segment_id:
                from_seg = story.get_segment(choice.from_segment_id)
                if from_seg:
                    from_seg.add_outgoing_choice(choice)
            if choice.to_segment_id:
                to_seg = story.get_segment(choice.to_segment_id)
                if to_seg:
                    to_seg.add_incoming_choice(choice)
        
        # Load contexts
        contexts_dir = LOCAL_DATA_DIR / story_id / "storycontext"
        if contexts_dir.exists():
            from app.models.story_context import StoryContext
            for ctx_file in contexts_dir.glob("*.json"):
                try:
                    with open(ctx_file, "r") as f:
                        data = json.load(f)
                    StoryContext(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading context {ctx_file.stem}: {e}")
        
        # Load arcs
        arcs_dir = LOCAL_DATA_DIR / story_id / "storyarc"
        if arcs_dir.exists():
            from app.models.story_arc import StoryArc
            for arc_file in arcs_dir.glob("*.json"):
                try:
                    with open(arc_file, "r") as f:
                        data = json.load(f)
                    StoryArc(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading arc {arc_file.stem}: {e}")
        
        # Load episodes
        episodes_dir = LOCAL_DATA_DIR / story_id / "storyepisode"
        if episodes_dir.exists():
            from app.models.story_episode import StoryEpisode
            for ep_file in episodes_dir.glob("*.json"):
                try:
                    with open(ep_file, "r") as f:
                        data = json.load(f)
                    StoryEpisode(**data, story=story)
                except Exception as e:
                    logger.error(f"Error loading episode {ep_file.stem}: {e}")
        
        logger.info(
            f"Loaded full story '{story_id}': "
            f"{len(story.get_all_segments())} segments, "
            f"{len(story.get_all_choices())} choices, "
            f"{len(story.get_all_characters())} characters, "
            f"{len(story.get_all_locations())} locations"
        )
        
        return story

    @staticmethod
    def load_segment(story_id: str, segment_id: str) -> Optional[StorySegment]:
        """Load a single segment from disk.
        
        Args:
            story_id: The story ID
            segment_id: The segment ID to load
            
        Returns:
            StorySegment object or None if not found
        """
        segment_file = LOCAL_DATA_DIR / story_id / "storysegment" / f"{segment_id}.json"
        
        if not segment_file.exists():
            logger.warning(f"Segment file not found: {segment_file}")
            return None
        
        try:
            with open(segment_file, "r") as f:
                data = json.load(f)
            
            # We'll need to create a minimal Story object for the segment
            # Since the segment initialization calls story.add_segment()
            story_data = {"id": story_id, "story_id": story_id, "title": "", "description": ""}
            story = Story(**story_data)
            
            # Create segment with story reference
            segment = StorySegment(**data, story=story)
            logger.debug(f"Loaded segment: {segment_id} from story {story_id}")
            return segment
        except Exception as e:
            logger.error(f"Error loading segment {segment_id}: {e}")
            return None
    
    @staticmethod
    def load_choices_for_segment(story_id: str, segment_id: str) -> List[StoryChoice]:
        """Load all choices that start from a given segment.
        
        Args:
            story_id: The story ID
            segment_id: The segment ID to load choices for
            
        Returns:
            List of StoryChoice objects
        """
        choices_dir = LOCAL_DATA_DIR / story_id / "storychoice"
        
        if not choices_dir.exists():
            logger.warning(f"Choices directory not found: {choices_dir}")
            return []
        
        choices = []
        try:
            # Create a minimal story object for choices
            story_data = {"id": story_id, "story_id": story_id, "title": "", "description": ""}
            story = Story(**story_data)
            
            for choice_file in choices_dir.glob("*.json"):
                with open(choice_file, "r") as f:
                    data = json.load(f)
                
                # Only include choices that start from this segment
                if data.get("from_segment_id") == segment_id:
                    choice = StoryChoice(**data, story=story)
                    choices.append(choice)
            
            logger.debug(f"Loaded {len(choices)} choices for segment {segment_id}")
            return sorted(choices, key=lambda c: c.id)
        except Exception as e:
            logger.error(f"Error loading choices for segment {segment_id}: {e}")
            return []
    
    @staticmethod
    def load_character(story_id: str, character_id: str) -> Optional[StoryCharacter]:
        """Load a single character from disk.
        
        Args:
            story_id: The story ID
            character_id: The character ID to load
            
        Returns:
            StoryCharacter object or None if not found
        """
        char_file = LOCAL_DATA_DIR / story_id / "storycharacter" / f"{character_id}.json"
        
        if not char_file.exists():
            logger.warning(f"Character file not found: {char_file}")
            return None
        
        try:
            with open(char_file, "r") as f:
                data = json.load(f)
            
            character = StoryCharacter(**data)
            logger.debug(f"Loaded character: {character_id}")
            return character
        except Exception as e:
            logger.error(f"Error loading character {character_id}: {e}")
            return None
    
    @staticmethod
    def load_all_characters(story_id: str) -> List[StoryCharacter]:
        """Load all characters for a story.
        
        Args:
            story_id: The story ID
            
        Returns:
            List of StoryCharacter objects
        """
        chars_dir = LOCAL_DATA_DIR / story_id / "storycharacter"
        
        if not chars_dir.exists():
            return []
        
        characters = []
        try:
            # Create a minimal story object for characters
            story_data = {"id": story_id, "story_id": story_id, "title": "", "description": ""}
            story = Story(**story_data)
            
            for char_file in chars_dir.glob("*.json"):
                with open(char_file, "r") as f:
                    data = json.load(f)
                character = StoryCharacter(**data, story=story)
                characters.append(character)
            
            logger.debug(f"Loaded {len(characters)} characters for story {story_id}")
            return sorted(characters, key=lambda c: c.id)
        except Exception as e:
            logger.error(f"Error loading characters for story {story_id}: {e}")
            return []
    
    @staticmethod
    def load_location(story_id: str, location_id: str) -> Optional[StoryLocation]:
        """Load a single location from disk.
        
        Args:
            story_id: The story ID
            location_id: The location ID to load
            
        Returns:
            StoryLocation object or None if not found
        """
        loc_file = LOCAL_DATA_DIR / story_id / "storylocation" / f"{location_id}.json"
        
        if not loc_file.exists():
            logger.warning(f"Location file not found: {loc_file}")
            return None
        
        try:
            with open(loc_file, "r") as f:
                data = json.load(f)
            
            location = StoryLocation(**data)
            logger.debug(f"Loaded location: {location_id}")
            return location
        except Exception as e:
            logger.error(f"Error loading location {location_id}: {e}")
            return None
    
    @staticmethod
    def load_all_locations(story_id: str) -> List[StoryLocation]:
        """Load all locations for a story.
        
        Args:
            story_id: The story ID
            
        Returns:
            List of StoryLocation objects
        """
        locs_dir = LOCAL_DATA_DIR / story_id / "storylocation"
        
        if not locs_dir.exists():
            return []
        
        locations = []
        try:
            # Create a minimal story object for locations
            story_data = {"id": story_id, "story_id": story_id, "title": "", "description": ""}
            story = Story(**story_data)
            
            for loc_file in locs_dir.glob("*.json"):
                with open(loc_file, "r") as f:
                    data = json.load(f)
                location = StoryLocation(**data, story=story)
                locations.append(location)
            
            logger.debug(f"Loaded {len(locations)} locations for story {story_id}")
            return sorted(locations, key=lambda l: l.id)
        except Exception as e:
            logger.error(f"Error loading locations for story {story_id}: {e}")
            return []
