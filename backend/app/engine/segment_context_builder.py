"""Builds rich context for segment generation based on episode history."""

from typing import Dict, List, Optional, Any
import logging

from app.models import Story, StorySegment
from app.models.story_segment import SegmentStatus

logger = logging.getLogger("infinite_story.engine.segment_context_builder")


class SegmentContextBuilder:
    """Build rich context for segment generation.
    
    This class walks backward through the parent chain, accumulates character
    state changes, detects episode transitions, and calculates pacing signals
    to inform the AI generation engine.
    """
    
    def __init__(self, story: Story):
        """Initialize the context builder.
        
        Args:
            story: The Story instance to build context from
        """
        self.story = story
    
    def build_context(
        self,
        current_segment_id: str,
        user_choice: str  # The choice text the user made
    ) -> Dict[str, Any]:
        """Build generation context for a new segment.
        
        Walks backward through the parent chain, accumulates changes,
        detects episode transitions, and calculates pacing weight.
        
        Args:
            current_segment_id: ID of the segment the user is in
            user_choice: The text of the choice the user made
            
        Returns:
            A context dict with all information needed for segment generation:
            {
                'previous_segments': [...],  # Last 3-5 scenes
                'character_states': {...},   # Latest character snapshot
                'accumulated_changes': [...],  # All change_notes in chain
                'episode_context': {...},    # Tone, end_condition, pacing
                'should_transition': bool,   # Start new episode?
                'pacing_weight': 0.0-1.0,   # Progress to episode end
                'protagonist_id': 'char_1',  # Main character this episode
            }
        """
        # 1. Get the current segment
        current_seg = self.story.get_segment(current_segment_id)
        if not current_seg:
            raise ValueError(f"Segment {current_segment_id} not found")
        
        # 2. Walk backward to episode start
        episode_chain = self._walk_episode_chain(current_segment_id)
        
        # 3. Accumulate character changes
        accumulated_changes = self._accumulate_changes(episode_chain)
        
        # 4. Detect episode transition
        should_transition = self._should_transition_episode(
            current_seg,
            accumulated_changes
        )
        
        # 5. Calculate pacing weight
        pacing = self._calculate_pacing_weight(
            current_seg,
            should_transition
        )
        
        # 6. Assemble context
        return {
            'previous_segments': [
                self.story.get_segment(seg_id).get_short_overview()
                for seg_id in episode_chain[-5:]  # Last 5 scenes
            ],
            'character_states': current_seg.character_states,
            'accumulated_changes': accumulated_changes,
            'episode_number': current_seg.episode_number,
            'episode_tone': current_seg.episode_tone,
            'episode_end_condition': current_seg.episode_end_condition,
            'segment_number_in_episode': current_seg.segment_number_in_episode,
            'should_transition_episode': should_transition,
            'pacing_weight': pacing,
            'protagonist_id': current_seg.protagonist_id,
            'user_choice': user_choice,
        }
    
    def _walk_episode_chain(self, segment_id: str) -> List[str]:
        """Walk backward from segment to episode start.
        
        Traverses the parent_segment_id chain backward, collecting all segment
        IDs that belong to the current episode, until reaching the episode start
        or a segment from a different episode.
        
        Args:
            segment_id: The ID of the segment to start walking from
            
        Returns:
            List of segment IDs in chronological order (start to current)
        """
        chain = []
        current = self.story.get_segment(segment_id)
        if not current:
            return chain
        
        episode_num = current.episode_number
        visited = set()  # Prevent circular references
        
        while current and current.episode_number == episode_num:
            # Prevent infinite loops
            if current.id in visited:
                logger.warning(f"Circular reference detected at segment {current.id}")
                break
            visited.add(current.id)
            
            chain.insert(0, current.id)  # Prepend (walking backward)
            
            if not current.parent_segment_id:
                break
            
            current = self.story.get_segment(current.parent_segment_id)
        
        return chain
    
    def _accumulate_changes(self, segment_chain: List[str]) -> List[str]:
        """Collect all change_notes from segment chain.
        
        Walks through the chain and aggregates all character/location change
        notes to provide context about what has happened in the episode.
        
        Args:
            segment_chain: List of segment IDs to process
            
        Returns:
            List of all change_notes found in the chain
        """
        all_changes = []
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg:
                all_changes.extend(seg.change_notes)
        return all_changes
    
    def _should_transition_episode(
        self,
        current_segment: StorySegment,
        changes: List[str]
    ) -> bool:
        """Decide if this segment should end the episode.
        
        Triggers episode transition if:
        1. end_condition_proximity >= 0.8 (AI said we're near end)
        2. segment_number_in_episode >= 18 (hard limit)
        3. Changes mention explicit end condition keywords
        
        Args:
            current_segment: The current segment being evaluated
            changes: Accumulated change notes from the episode
            
        Returns:
            True if episode should transition, False otherwise
        """
        # Check proximity to end condition
        if current_segment.end_condition_proximity >= 0.8:
            logger.debug(
                f"Segment {current_segment.id}: end_condition_proximity "
                f"{current_segment.end_condition_proximity} >= 0.8, transitioning"
            )
            return True
        
        # Check segment count (max ~20 per episode)
        if current_segment.segment_number_in_episode >= 18:
            logger.debug(
                f"Segment {current_segment.id}: segment_number_in_episode "
                f"{current_segment.segment_number_in_episode} >= 18, transitioning"
            )
            return True
        
        # Check for explicit end condition keywords
        end_keywords = ['chapter', 'end', 'conclusion', 'climax', 'finale']
        for change in changes:
            if any(kw in change.lower() for kw in end_keywords):
                logger.debug(
                    f"Segment {current_segment.id}: found end keyword in changes, transitioning"
                )
                return True
        
        return False
    
    def _calculate_pacing_weight(
        self,
        segment: StorySegment,
        will_transition: bool
    ) -> float:
        """Calculate pacing weight (0.0 to 1.0).
        
        Provides a signal to the AI about how much "room" is left in the episode.
        Uses a quadratic curve: slow at start, accelerating toward end.
        
        - 0.0 = start of episode (lots of room)
        - 0.5 = halfway through (some room)
        - 0.9+ = very close to end
        - 1.0 (reserved for actual episode end)
        
        Args:
            segment: The current segment
            will_transition: Whether this segment will transition to next episode
            
        Returns:
            Float between 0.0 and 1.0 representing progress through episode
        """
        if will_transition:
            return 0.9  # Very close to end
        
        # Quadratic curve: (seg_num / max)^2 gives nonlinear progression
        seg_num = segment.segment_number_in_episode
        max_segments = 20
        
        weight = (seg_num / max_segments) ** 2
        return min(weight, 0.99)  # Cap at 0.99 (leave 1.0 for actual end)
