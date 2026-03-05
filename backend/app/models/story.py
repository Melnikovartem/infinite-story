from typing import Optional, List, Dict, TYPE_CHECKING
import logging
from pydantic import PrivateAttr
from .story_base import StoryBase

logger = logging.getLogger("infinite_story.models.story")


if TYPE_CHECKING:
    from .story_character import StoryCharacter
    from .story_location import StoryLocation
    from .story_segment import StorySegment
    from .story_choice import StoryChoice
    from .story_context import StoryContext
    from .story_segment import SegmentStatus
    from .story_episode import StoryEpisode
    from .story_faction import StoryFaction
    from .story_magic_system import StoryMagicSystem
    from .story_arc import StoryArc

class Story(StoryBase):
    """A story in the system.
    
    This represents a complete story with metadata and references to its segments.
    """
    title: str
    description: str
    genre: Optional[str] = None
    user_id: Optional[str] = None
    start_segment_id: Optional[str] = None  # Reference to the first segment of the story
    
    # Private component caches
    _characters: Dict[str, 'StoryCharacter'] = PrivateAttr(default_factory=dict)
    _locations: Dict[str, 'StoryLocation'] = PrivateAttr(default_factory=dict)
    _segments: Dict[str, 'StorySegment'] = PrivateAttr(default_factory=dict)
    _choices: Dict[str, 'StoryChoice'] = PrivateAttr(default_factory=dict)
    _context: Optional['StoryContext'] = PrivateAttr(default=None)
    _episodes: Dict[str, 'StoryEpisode'] = PrivateAttr(default_factory=dict)
    _factions: Dict[str, 'StoryFaction'] = PrivateAttr(default_factory=dict)
    _magic_systems: Dict[str, 'StoryMagicSystem'] = PrivateAttr(default_factory=dict)
    _arcs: Dict[str, 'StoryArc'] = PrivateAttr(default_factory=dict)
    
    def __init__(self, **data):
        """Initialize a Story instance.
        
        For Story instances, the story_id is always the same as the id.
        """
        if 'id' in data and 'story_id' not in data:
            data['story_id'] = data['id']
        super().__init__(**data)
    
    def add_context(self, context: 'StoryContext') -> None:
        """Add context to the story.

        Args:
            context: The context to add
        """
        if context.story_id != self.id:
            raise ValueError(f"Context belongs to story {context.story_id}, not {self.id}")
        logger.debug(f"Adding context '{context.id}' to story '{self.id}'")
        self._context = context
        context.story = self
    
    def add_character(self, character: 'StoryCharacter') -> None:
        """Add a character to the story.

        Args:
            character: The character to add
        """
        if character.story_id != self.id:
            raise ValueError(f"Character {character.id} belongs to story {character.story_id}, not {self.id}")
        logger.debug(f"Adding character '{character.id}' ({character.name}) to story '{self.id}'")
        self._characters[character.id] = character
        character.story = self
        
    def add_location(self, location: 'StoryLocation') -> None:
        """Add a location to the story.

        Args:
            location: The location to add
        """
        if location.story_id != self.id:
            raise ValueError(f"Location {location.id} belongs to story {location.story_id}, not {self.id}")
        logger.debug(f"Adding location '{location.id}' ({location.name}) to story '{self.id}'")
        self._locations[location.id] = location
        location.story = self
        
    def add_segment(self, segment: 'StorySegment') -> None:
        """Add a segment to the story.

        Args:
            segment: The segment to add
        """
        if segment.story_id != self.id:
            raise ValueError(f"Segment {segment.id} belongs to story {segment.story_id}, not {self.id}")
        logger.debug(f"Adding segment '{segment.id}' to story '{self.id}'")
        self._segments[segment.id] = segment
        segment.story = self
        
    def add_choice(self, choice: 'StoryChoice') -> None:
        """Add a choice to the story.

        Args:
            choice: The choice to add
        """
        if choice.story_id != self.id:
            raise ValueError(f"Choice {choice.id} belongs to story {choice.story_id}, not {self.id}")
        logger.debug(f"Adding choice '{choice.id}' (from: {choice.from_segment_id}, to: {choice.to_segment_id}) to story '{self.id}'")
        self._choices[choice.id] = choice
        choice.story = self
        
    def get_character(self, character_id: str) -> Optional['StoryCharacter']:
        """Get a character by ID.
        
        Args:
            character_id: The ID of the character to get
            
        Returns:
            The character, or None if not found
        """
        return self._characters.get(character_id)
        
    def get_location(self, location_id: str) -> Optional['StoryLocation']:
        """Get a location by ID.
        
        Args:
            location_id: The ID of the location to get
            
        Returns:
            The location, or None if not found
        """
        return self._locations.get(location_id)
        
    def get_segment(self, segment_id: str, include_archived: bool = False) -> Optional['StorySegment']:
        """Get a segment by ID, respecting archive status.
        
        Args:
            segment_id: The ID of the segment to get
            include_archived: If False (default), archived segments return None
            
        Returns:
            The segment, or None if not found or archived (unless include_archived=True)
        """
        seg = self._segments.get(segment_id)
        
        if seg and not include_archived:
            # Import locally to avoid circular dependency
            from .story_segment import SegmentStatus
            if seg.status == SegmentStatus.ARCHIVED:
                return None
        
        return seg
        
    def get_choice(self, choice_id: str) -> Optional['StoryChoice']:
        """Get a choice by ID.
        
        Args:
            choice_id: The ID of the choice to get
            
        Returns:
            The choice, or None if not found
        """
        return self._choices.get(choice_id)
    
    def add_episode(self, episode: 'StoryEpisode') -> None:
        """Add an episode to the story.

        Args:
            episode: The episode to add
        """
        if episode.story_id != self.id:
            raise ValueError(f"Episode {episode.id} belongs to story {episode.story_id}, not {self.id}")
        logger.debug(f"Adding episode '{episode.id}' to story '{self.id}'")
        self._episodes[episode.id] = episode
        episode.story = self
    
    def get_episode(self, episode_id: str) -> Optional['StoryEpisode']:
        """Get an episode by ID.
        
        Args:
            episode_id: The ID of the episode to get
            
        Returns:
            The episode, or None if not found
        """
        return self._episodes.get(episode_id)
    
    def get_all_episodes(self) -> List['StoryEpisode']:
        """Get all episodes in the story.
        
        Returns:
            A list of all episodes, sorted by episode_number
        """
        episodes = list(self._episodes.values())
        return sorted(episodes, key=lambda e: e.episode_number)
    
    # ========================================================================
    # Faction (political groups/organizations) cache
    # ========================================================================
    
    def add_faction(self, faction: 'StoryFaction') -> None:
        """Add a faction to the story.

        Args:
            faction: The faction to add
        """
        if faction.story_id != self.id:
            raise ValueError(f"Faction {faction.id} belongs to story {faction.story_id}, not {self.id}")
        logger.debug(f"Adding faction '{faction.id}' ({faction.name}) to story '{self.id}'")
        self._factions[faction.id] = faction
        faction.story = self
    
    def get_faction(self, faction_id: str) -> Optional['StoryFaction']:
        """Get a faction by ID."""
        return self._factions.get(faction_id)
    
    def get_all_factions(self) -> List['StoryFaction']:
        """Get all factions in the story."""
        return list(self._factions.values())
    
    def get_factions_for_arc(self, arc_id: str) -> List['StoryFaction']:
        """Get factions active in a specific arc."""
        return [f for f in self._factions.values() if f.arc_id == arc_id]
    
    # ========================================================================
    # Magic System cache
    # ========================================================================
    
    def add_magic_system(self, magic_system: 'StoryMagicSystem') -> None:
        """Add a magic system to the story.

        Args:
            magic_system: The magic system to add
        """
        if magic_system.story_id != self.id:
            raise ValueError(f"MagicSystem {magic_system.id} belongs to story {magic_system.story_id}, not {self.id}")
        logger.debug(f"Adding magic system '{magic_system.id}' ({magic_system.name}) to story '{self.id}'")
        self._magic_systems[magic_system.id] = magic_system
        magic_system.story = self
    
    def get_magic_system(self, system_id: str) -> Optional['StoryMagicSystem']:
        """Get a magic system by ID."""
        return self._magic_systems.get(system_id)
    
    def get_all_magic_systems(self) -> List['StoryMagicSystem']:
        """Get all magic systems in the story."""
        return list(self._magic_systems.values())
    
    def get_magic_systems_for_arc(self, arc_id: str) -> List['StoryMagicSystem']:
        """Get magic systems active in a specific arc."""
        return [m for m in self._magic_systems.values() if m.arc_id == arc_id]
    
    # ========================================================================
    # Arc (story arc) cache
    # ========================================================================
    
    def add_arc(self, arc: 'StoryArc') -> None:
        """Add an arc to the story.

        Args:
            arc: The arc to add
        """
        if arc.story_id != self.id:
            raise ValueError(f"Arc {arc.id} belongs to story {arc.story_id}, not {self.id}")
        logger.debug(f"Adding arc '{arc.id}' ({arc.title}) to story '{self.id}'")
        self._arcs[arc.id] = arc
    
    def get_arc(self, arc_id: str) -> Optional['StoryArc']:
        """Get an arc by ID."""
        return self._arcs.get(arc_id)
    
    def get_all_arcs(self) -> List['StoryArc']:
        """Get all arcs in the story."""
        return list(self._arcs.values())
    
    def get_active_arc(self) -> Optional['StoryArc']:
        """Get the currently active arc."""
        for arc in self._arcs.values():
            if arc.is_active and not arc.is_finalized:
                return arc
        return None
    
    def get_future_arcs(self) -> List['StoryArc']:
        """Get all future (pre-generated, not yet active) arcs."""
        return [a for a in self._arcs.values() if a.is_future_arc]
    
    def get_available_choices(self, segment_id: str) -> List['StoryChoice']:
        """Get available choices from a segment, excluding archived destinations.
        
        This method returns only choices that lead to non-archived segments.
        
        Args:
            segment_id: The ID of the segment to get choices from
            
        Returns:
            A list of available choices from the segment
        """
        seg = self.get_segment(segment_id)
        if not seg:
            return []
        
        choices = []
        for choice_id in seg.outgoing_choices if hasattr(seg, 'outgoing_choices') else {}:
            choice = self._choices.get(choice_id)
            if not choice:
                continue
            
            # Check if destination is archived
            if choice.to_segment_id:
                dest = self.get_segment(choice.to_segment_id, include_archived=False)
                if dest is None:
                    # Destination is either missing or archived - skip this choice
                    continue
            
            choices.append(choice)
        
        return choices
        
    def get_all_characters(self) -> List['StoryCharacter']:
        """Get all characters in the story.
        
        Returns:
            A list of all characters
        """
        return list(self._characters.values())
        
    def get_all_locations(self) -> List['StoryLocation']:
        """Get all locations in the story.
        
        Returns:
            A list of all locations
        """
        return list(self._locations.values())
        
    def get_all_segments(self) -> List['StorySegment']:
        """Get all segments in the story.
        
        Returns:
            A list of all segments
        """
        return list(self._segments.values())
        
    def get_all_choices(self) -> List['StoryChoice']:
        """Get all choices in the story.
        
        Returns:
            A list of all choices
        """
        return list(self._choices.values())

    def get_story_id(self) -> str:
        """Get the story ID for this object.
        
        For the Story class, the story ID is the same as the object's ID.
        """
        return self.id
