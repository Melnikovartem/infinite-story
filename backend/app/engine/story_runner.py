from typing import List, Optional, Set
import json
import logging
from pathlib import Path
from ..models.story import Story
from ..models.story_segment import StorySegment
from ..models.story_character import StoryCharacter
from ..models.story_location import StoryLocation
from ..models.story_choice import StoryChoice
from ..models.story_context import StoryContext
from ..models.story_base import LOCAL_DATA_DIR


logger = logging.getLogger("infinite_story.engine.story_runner")

class StoryRunner:
    """Manages the runtime state of a story and handles the game loop."""

    def __init__(self, story: Story, generator=None, deterministic: bool = False):
        self.story = story
        self.current_segment: Optional[StorySegment] = None
        self.visited_segments: Set[str] = set()  # Set of segment IDs we've visited
        self.generator = generator  # Optional TextGenerator for AI-based generation
        self.deterministic = deterministic  # If True, don't shuffle choices (stable order for debugging)
    
    @property
    def is_running(self) -> bool:
        """Check if the story is still running (has current segment and choices available)."""
        return self.current_segment is not None and len(self.get_available_choices()) > 0
        
    def start(self) -> None:
        """Start the story from the beginning."""
        logger.info(f"Starting story '{self.story.id}' from segment '{self.story.start_segment_id}'")
        if not self.story.start_segment_id:
            raise ValueError("Story has no start segment")
        self.load_all_components(self.story)

        self.current_segment = self.story.get_segment(self.story.start_segment_id)
        if not self.current_segment:
            raise ValueError(f"Start segment '{self.story.start_segment_id}' not found after loading")

        logger.debug(f"Current segment set to '{self.current_segment.id}': {self.current_segment.short_description}")
        # Mark the start segment as visited
        self.visited_segments.add(self.story.start_segment_id)
        
    def get_available_choices(self) -> List[StoryChoice]:
        """Get the choices available in the current segment, sorted by logged clicks then click count.
        
        Tiebreaker: alphabetical by choice text (stable, reproducible).
        No random shuffling — auto-pick always gets the same first choice.
        """
        if not self.current_segment:
            return []
            
        choices = list(self.current_segment.outgoing_choices.values())
        
        # Primary sort: logged clicks desc, anonymous clicks desc, then text asc as stable tiebreaker
        choices.sort(key=lambda x: (
            -(getattr(x, 'clicks_logged', 0) or 0),
            -(getattr(x, 'clicks_anonymous', 0) or 0),
            getattr(x, 'text', '') or '',
        ))
            
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

    @property
    def current_episode_number(self) -> int:
        """Get the current episode number from the current segment."""
        if self.current_segment:
            return self.current_segment.episode_number
        return 1

    @property
    def current_arc_id(self) -> Optional[str]:
        """Get the current arc ID from the current segment."""
        if self.current_segment:
            return self.current_segment.arc_id
        return None

    @property
    def current_arc(self):
        """Get the current StoryArc object."""
        arc_id = self.current_arc_id
        if arc_id:
            return self.story.get_arc(arc_id)
        return None

    @property
    def segment_number_in_episode(self) -> int:
        """Get the current segment's position within its episode."""
        if self.current_segment:
            return self.current_segment.segment_number_in_episode
        return 1

    def get_current_state(self) -> dict:
        """Get the current state of the story, including episode/arc info."""
        state = {
            "current_segment": self.current_segment,
            "visited_segments": list(self.visited_segments),
        }
        
        # Add episode/arc info derived from current segment
        if self.current_segment:
            state["episode_number"] = self.current_segment.episode_number
            state["arc_id"] = self.current_segment.arc_id
            state["segment_number_in_episode"] = self.current_segment.segment_number_in_episode
            state["episode_tone"] = self.current_segment.episode_tone
            state["triggers_episode_transition"] = self.current_segment.triggers_episode_transition
            
            # Get arc info if available
            arc = self.current_arc
            if arc:
                state["arc_title"] = arc.title if hasattr(arc, 'title') else None
                state["arc_description"] = arc.description if hasattr(arc, 'description') else None
        
        return state
    
    def load_all_components(self, story) -> None:
        """Load all story components (characters, locations, segments, choices, context).

        This method loads all components directly from their storage directories
        and adds them to the story's internal caches.
        """
        logger.info(f"Loading all components for story '{story.id}'")

        # Load all characters
        char_dir = StoryCharacter.get_storage_dir(story.id)
        logger.debug(f"Loading characters from {char_dir}")
        char_count = 0
        for char_file in char_dir.glob("*.json"):
            char_id = char_file.stem
            logger.debug(f"  Loading character: {char_id}")
            character = StoryCharacter.load(story.id, char_id, story)
            if not character:
                raise ValueError(f"Failed to load character {char_id}")
            story.add_character(character)
            char_count += 1
        logger.info(f"Loaded {char_count} characters")

        # Load all locations
        loc_dir = StoryLocation.get_storage_dir(story.id)
        logger.debug(f"Loading locations from {loc_dir}")
        loc_count = 0
        for loc_file in loc_dir.glob("*.json"):
            loc_id = loc_file.stem
            logger.debug(f"  Loading location: {loc_id}")
            location = StoryLocation.load(story.id, loc_id, story)
            if not location:
                raise ValueError(f"Failed to load location {loc_id}")
            story.add_location(location)
            loc_count += 1
        logger.info(f"Loaded {loc_count} locations")

        # Load all segments
        segment_dir = StorySegment.get_storage_dir(story.id)
        logger.debug(f"Loading segments from {segment_dir}")
        seg_count = 0
        for segment_file in segment_dir.glob("*.json"):
            segment_id = segment_file.stem
            logger.debug(f"  Loading segment: {segment_id}")
            segment = StorySegment.load(story.id, segment_id, story)
            if not segment:
                raise ValueError(f"Failed to load segment {segment_id}")
            story.add_segment(segment)
            seg_count += 1
        logger.info(f"Loaded {seg_count} segments")

        # Load all choices
        choice_dir = StoryChoice.get_storage_dir(story.id)
        logger.debug(f"Loading choices from {choice_dir}")
        choice_count = 0
        for choice_file in choice_dir.glob("*.json"):
            choice_id = choice_file.stem
            logger.debug(f"  Loading choice: {choice_id}")
            choice = StoryChoice.load(story.id, choice_id, story)
            if not choice:
                raise ValueError(f"Failed to load choice {choice_id}")
            story.add_choice(choice)
            choice_count += 1
        logger.info(f"Loaded {choice_count} choices")

        # Connect choices to segments
        logger.debug("Connecting choices to segments")
        connected_count = 0
        for choice in story._choices.values():
            # Add choice to source segment's outgoing choices
            if choice.from_segment_id in story._segments:
                story._segments[choice.from_segment_id].add_outgoing_choice(choice)
                logger.debug(f"  Connected choice '{choice.id}' as outgoing from segment '{choice.from_segment_id}'")
                connected_count += 1

            # Add choice to destination segment's incoming choices
            if choice.to_segment_id in story._segments:
                story._segments[choice.to_segment_id].add_incoming_choice(choice)
                logger.debug(f"  Connected choice '{choice.id}' as incoming to segment '{choice.to_segment_id}'")
        logger.info(f"Connected {connected_count} choice-segment relationships")

        context_dir = StoryContext.get_storage_dir(story.id)
        logger.debug(f"Loading context from {context_dir}")
        ctx_count = 0
        for context_file in context_dir.glob("*.json"):
            context_id = context_file.stem
            logger.debug(f"  Loading context: {context_id}")
            context = StoryContext.load(story.id, context_id, story)
            if not context:
                raise ValueError(f"Failed to load context {context_id}")
            story.add_context(context)
            ctx_count += 1
        logger.info(f"Loaded {ctx_count} contexts")

        # Load all episodes
        from ..models.story_episode import StoryEpisode
        episode_dir = StoryEpisode.get_storage_dir(story.id)
        logger.debug(f"Loading episodes from {episode_dir}")
        ep_count = 0
        for episode_file in episode_dir.glob("*.json"):
            episode_id = episode_file.stem
            logger.debug(f"  Loading episode: {episode_id}")
            episode = StoryEpisode.load(story.id, episode_id, story)
            if not episode:
                logger.warning(f"Failed to load episode {episode_id}")
                continue
            story.add_episode(episode)
            ep_count += 1
        logger.info(f"Loaded {ep_count} episodes")

        # Load all factions
        from ..models.story_faction import StoryFaction
        faction_dir = StoryFaction.get_storage_dir(story.id)
        logger.debug(f"Loading factions from {faction_dir}")
        faction_count = 0
        for faction_file in faction_dir.glob("*.json"):
            faction_id = faction_file.stem
            logger.debug(f"  Loading faction: {faction_id}")
            faction = StoryFaction.load(story.id, faction_id, story)
            if not faction:
                logger.warning(f"Failed to load faction {faction_id}")
                continue
            story.add_faction(faction)
            faction_count += 1
        logger.info(f"Loaded {faction_count} factions")

        # Load all magic systems
        from ..models.story_magic_system import StoryMagicSystem
        magic_dir = StoryMagicSystem.get_storage_dir(story.id)
        logger.debug(f"Loading magic systems from {magic_dir}")
        magic_count = 0
        for magic_file in magic_dir.glob("*.json"):
            magic_id = magic_file.stem
            logger.debug(f"  Loading magic system: {magic_id}")
            magic = StoryMagicSystem.load(story.id, magic_id, story)
            if not magic:
                logger.warning(f"Failed to load magic system {magic_id}")
                continue
            story.add_magic_system(magic)
            magic_count += 1
        logger.info(f"Loaded {magic_count} magic systems")

        # Load all arcs
        from ..models.story_arc import StoryArc
        arc_dir = StoryArc.get_storage_dir(story.id)
        logger.debug(f"Loading arcs from {arc_dir}")
        arc_count = 0
        for arc_file in arc_dir.glob("*.json"):
            arc_id = arc_file.stem
            logger.debug(f"  Loading arc: {arc_id}")
            arc = StoryArc.load(story.id, arc_id)
            if not arc:
                logger.warning(f"Failed to load arc {arc_id}")
                continue
            story.add_arc(arc)
            arc_count += 1
        logger.info(f"Loaded {arc_count} arcs")

        logger.info(f"Finished loading all components for story '{story.id}'")

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

    def navigate_up(self) -> Optional[StorySegment]:
        """Navigate to the parent segment (go back one step in the story tree).
        
        Returns:
            The parent segment, or None if already at root
        """
        if not self.current_segment:
            return None
        
        parent_id = self.current_segment.parent_segment_id
        if not parent_id:
            # Try incoming choices as fallback
            if self.current_segment.incoming_choices:
                first_choice = next(iter(self.current_segment.incoming_choices.values()))
                parent_id = first_choice.from_segment_id
        
        if not parent_id:
            return None
        
        parent = self.story.get_segment(parent_id, include_archived=True)
        if not parent:
            return None
        
        self.current_segment = parent
        self.visited_segments.add(parent_id)
        return parent

    def navigate_down(self, child_index: int = 0) -> Optional[StorySegment]:
        """Navigate to a child segment (go forward to an already-generated branch).
        
        Only navigates to segments that already exist (to_segment_id is not None).
        
        Args:
            child_index: Which child to navigate to (0-indexed among generated children)
            
        Returns:
            The child segment, or None if no generated children exist
        """
        if not self.current_segment:
            return None
        
        # Get outgoing choices that have generated targets
        generated = [
            c for c in self.current_segment.outgoing_choices.values()
            if c.to_segment_id and self.story.get_segment(c.to_segment_id, include_archived=True)
        ]
        # Sort alphabetically by text for stable ordering
        generated.sort(key=lambda c: getattr(c, 'text', '') or '')
        
        if not generated or child_index >= len(generated):
            return None
        
        choice = generated[child_index]
        child = self.story.get_segment(choice.to_segment_id, include_archived=True)
        if not child:
            return None
        
        self.current_segment = child
        self.visited_segments.add(child.id)
        return child

    def get_children(self) -> list:
        """Get generated child segments of the current segment.
        
        Returns:
            List of (choice, segment) tuples for children that exist, sorted by choice text
        """
        if not self.current_segment:
            return []
        
        children = []
        for choice in self.current_segment.outgoing_choices.values():
            if choice.to_segment_id:
                seg = self.story.get_segment(choice.to_segment_id, include_archived=True)
                if seg:
                    children.append((choice, seg))
        
        children.sort(key=lambda x: getattr(x[0], 'text', '') or '')
        return children

    def get_local_tree(self, depth_up: int = 2, depth_down: int = 2) -> dict:
        """Build a local tree view around the current segment.
        
        Returns a dict describing the tree:
        {
            'ancestors': [(segment, connecting_choice_text), ...],  # root-first
            'current': segment,
            'children': [{'choice': choice, 'segment': segment, 'children': [...]}, ...]
        }
        """
        if not self.current_segment:
            return {'ancestors': [], 'current': None, 'children': []}
        
        # Walk up
        ancestors = []
        seg = self.current_segment
        for _ in range(depth_up):
            parent_id = seg.parent_segment_id
            if not parent_id:
                if seg.incoming_choices:
                    first_choice = next(iter(seg.incoming_choices.values()))
                    parent_id = first_choice.from_segment_id
            if not parent_id:
                break
            parent = self.story.get_segment(parent_id, include_archived=True)
            if not parent:
                break
            # Find which choice connected parent -> seg
            choice_text = None
            for c in parent.outgoing_choices.values():
                if c.to_segment_id == seg.id:
                    choice_text = c.text
                    break
            ancestors.append((parent, choice_text))
            seg = parent
        ancestors.reverse()  # root-first order
        
        # Walk down recursively
        def _build_children(segment, remaining_depth):
            if remaining_depth <= 0:
                return []
            result = []
            choices = sorted(
                segment.outgoing_choices.values(),
                key=lambda c: getattr(c, 'text', '') or ''
            )
            for choice in choices:
                child_seg = None
                if choice.to_segment_id:
                    child_seg = self.story.get_segment(choice.to_segment_id, include_archived=True)
                node = {
                    'choice': choice,
                    'segment': child_seg,
                    'children': _build_children(child_seg, remaining_depth - 1) if child_seg else [],
                }
                result.append(node)
            return result
        
        return {
            'ancestors': ancestors,
            'current': self.current_segment,
            'children': _build_children(self.current_segment, depth_down),
        }

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
