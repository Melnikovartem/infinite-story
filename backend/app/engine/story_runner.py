from typing import Dict, List, Optional, Set
import json
from pathlib import Path
from ..models.story import Story
from ..models.story_segment import StorySegment
from ..models.story_character import StoryCharacter
from ..models.story_location import StoryLocation
from ..models.story_choice import StoryChoice
from ..models.story_context import StoryContext
from ..models.story_base import LOCAL_DATA_DIR

class StoryRunner:
    """Manages the runtime state of a story and handles the game loop."""

    def __init__(self, story: Story):
        self.story = story
        self.current_segment: Optional[StorySegment] = None
        self.visited_segments: Set[str] = set()  # Set of segment IDs we've visited
        
    def start(self) -> None:
        """Start the story from the beginning."""
        if not self.story.start_segment_id:
            raise ValueError("Story has no start segment")
        self.load_all_components(self.story)
        
        self.current_segment = self.story.get_segment(self.story.start_segment_id)
        
        # Mark the start segment as visited
        self.visited_segments.add(self.story.start_segment_id)
        
    def get_available_choices(self) -> List[StoryChoice]:
        """Get the choices available in the current segment, sorted by logged clicks then click count."""
        if not self.current_segment:
            return []
            
        # Get choices and sort by logged clicks first, then click count
        choices = list(self.current_segment.outgoing_choices.values())
        # Limit to top 100 choices by click count
        
        # Runtime sort is not a great idea, but here we are
        # Sort by logged clicks first if available
        choices.sort(key=lambda x: (
            x.logged_clicks if hasattr(x, 'logged_clicks') else 0,
            x.click_count if hasattr(x, 'click_count') else 0
        ), reverse=True)
        
        # If all choices have same counts, randomize order
        if all(
            getattr(x, 'logged_clicks', 0) == getattr(choices[0], 'logged_clicks', 0) and
            getattr(x, 'click_count', 0) == getattr(choices[0], 'click_count', 0)
            for x in choices
        ):
            from random import shuffle
            shuffle(choices)
            
        return choices[:100]
        
    def make_choice(self, choice_id: str) -> None:
        """Make a choice and progress the story."""
        if not self.current_segment:
            raise ValueError("No current segment")
            
        # Load the choice
        choice = self.story.get_choice(choice_id)
        if not choice:
            raise ValueError(f"Choice {choice_id} not found")
            
        if choice.from_segment_id != self.current_segment.id:
            raise ValueError(f"Choice {choice_id} is not available in the current segment")
            
        # Load the next segment
        next_segment = self.story.get_segment(choice.to_segment_id)
        if not next_segment:
            raise ValueError(f"Next segment {choice.to_segment_id} not found")
            
        # Move to the next segment
        self.current_segment = next_segment
        self.visited_segments.add(choice.to_segment_id)

    def get_current_state(self) -> dict:
        """Get the current state of the story."""
        return {
            "current_segment": self.current_segment,
            "visited_segments": list(self.visited_segments)
        }
    
    def load_all_components(self, story) -> None:
        """Load all story components (characters, locations, segments, choices, context).
        
        This method loads all components directly from their storage directories
        and adds them to the story's internal caches.
        """
        # Load all characters
        char_dir = StoryCharacter.get_storage_dir(story.id)
        for char_file in char_dir.glob("*.json"):
            char_id = char_file.stem
            character = StoryCharacter.load(story.id, char_id, story)
            if not character:
                raise ValueError(f"Failed to load character {char_id}")
            story.add_character(character)
                
        # Load all locations
        loc_dir = StoryLocation.get_storage_dir(story.id)
        for loc_file in loc_dir.glob("*.json"):
            loc_id = loc_file.stem
            location = StoryLocation.load(story.id, loc_id, story)
            if not location:
                raise ValueError(f"Failed to load location {loc_id}")
            story.add_location(location)

        # Load all segments
        segment_dir = StorySegment.get_storage_dir(story.id)
        for segment_file in segment_dir.glob("*.json"):
            segment_id = segment_file.stem
            segment = StorySegment.load(story.id, segment_id, story)
            if not segment:
                raise ValueError(f"Failed to load segment {segment_id}")
            story.add_segment(segment)

        # Load all choices
        choice_dir = StoryChoice.get_storage_dir(story.id)
        for choice_file in choice_dir.glob("*.json"):
            choice_id = choice_file.stem
            choice = StoryChoice.load(story.id, choice_id, story)
            if not choice:
                raise ValueError(f"Failed to load choice {choice_id}")
            story.add_choice(choice)
        
        # Connect choices to segments
        for choice in story._choices.values():
            # Add choice to source segment's outgoing choices
            if choice.from_segment_id in story._segments:
                story._segments[choice.from_segment_id].add_outgoing_choice(choice)
            
            # Add choice to destination segment's incoming choices 
            if choice.to_segment_id in story._segments:
                story._segments[choice.to_segment_id].add_incoming_choice(choice)

        context_dir = StoryContext.get_storage_dir(story.id)
        for context_file in context_dir.glob("*.json"):
            context_id = context_file.stem
            context = StoryContext.load(story.id, context_id, story)
            if not context:
                raise ValueError(f"Failed to load context {context_id}")
            story.add_context(context)

    def save_all_components(self, story) -> None:
        """Save all story components (characters, locations, segments, choices, context).
        
        This method saves all components in the story's internal caches to their
        respective storage directories.
        """
        # Save all characters
        for character in story._characters.values():
            character.save()
                
        # Save all locations
        for location in story._locations.values():
            location.save()

        # Save all segments
        for segment in story._segments.values():
            segment.save()

        # Save all choices
        for choice in story._choices.values():
            choice.save()

        # Save story context
        if story._context:
            story._context.save()

    def get_state_file_path(self) -> Path:
        """Get the path to the state file for this story.

        Returns:
            Path to the runner state JSON file
        """
        state_dir = LOCAL_DATA_DIR / self.story.id
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "runner_state.json"

    def save_state(self) -> None:
        """Save the current runner state to disk.

        This saves the current segment ID and visited segments,
        allowing the session to be resumed later.
        """
        state = {
            "current_segment_id": self.current_segment.id if self.current_segment else None,
            "visited_segments": list(self.visited_segments)
        }

        state_file = self.get_state_file_path()
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> bool:
        """Load a previously saved runner state.

        Returns:
            True if state was loaded successfully, False if no saved state exists
        """
        state_file = self.get_state_file_path()

        if not state_file.exists():
            return False

        try:
            with open(state_file, "r") as f:
                state = json.load(f)

            # Restore current segment
            if state.get("current_segment_id"):
                self.current_segment = self.story.get_segment(state["current_segment_id"])

            # Restore visited segments
            self.visited_segments = set(state.get("visited_segments", []))

            return True
        except Exception as e:
            # If loading fails, return False (will start from beginning)
            print(f"Warning: Failed to load state: {e}")
            return False

    def clear_state(self) -> None:
        """Clear the saved state file."""
        state_file = self.get_state_file_path()
        if state_file.exists():
            state_file.unlink()

    def start_from_segment(self, segment_id: str) -> None:
        """Start the story from a specific segment.

        Args:
            segment_id: The ID of the segment to start from

        Raises:
            ValueError: If the segment doesn't exist
        """
        self.load_all_components(self.story)

        segment = self.story.get_segment(segment_id)
        if not segment:
            raise ValueError(f"Segment {segment_id} not found")

        self.current_segment = segment
        self.visited_segments.add(segment_id)
