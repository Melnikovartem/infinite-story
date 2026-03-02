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
            for char_file in chars_dir.glob("*.json"):
                with open(char_file, "r") as f:
                    data = json.load(f)
                character = StoryCharacter(**data)
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
            for loc_file in locs_dir.glob("*.json"):
                with open(loc_file, "r") as f:
                    data = json.load(f)
                location = StoryLocation(**data)
                locations.append(location)
            
            logger.debug(f"Loaded {len(locations)} locations for story {story_id}")
            return sorted(locations, key=lambda l: l.id)
        except Exception as e:
            logger.error(f"Error loading locations for story {story_id}: {e}")
            return []
