from .user import User
from .story import Story
from .story_context import StoryContext
from .story_segment import StorySegment, CharacterStatus, LocationStatus
from .story_choice import StoryChoice, ChoiceFlags
from .story_character import StoryCharacter
from .story_location import StoryLocation
from .text_types import TextType, TextBlock
from .story_arc import StoryArc, ArcCompressionResult
from .story_episode import StoryEpisode, CharacterState, CharacterStateSnapshot
from .story_faction import StoryFaction
from .story_magic_system import StoryMagicSystem

# Backward-compatible aliases for removed models
EpisodeRecap = StoryEpisode
EpisodeMeta = StoryEpisode

__all__ = [
    'User',
    'Story',
    'StorySegment', 
    'CharacterStatus',
    'LocationStatus',
    'StoryChoice',
    'ChoiceFlags',
    'StoryContext',
    'StoryCharacter',
    'StoryLocation',
    'TextType',
    'TextBlock',
    'StoryEpisode',
    'CharacterState',
    'CharacterStateSnapshot',
    'StoryArc',
    'ArcCompressionResult',
    'StoryFaction',
    'StoryMagicSystem',
    # Backward-compatible aliases
    'EpisodeRecap',
    'EpisodeMeta',
]
