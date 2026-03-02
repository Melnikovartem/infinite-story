"""Builds rich, comprehensive context for segment generation based on full story history."""

from typing import Dict, List, Optional, Any
import logging

from app.models import Story, StorySegment
from app.models.story_segment import SegmentStatus
from app.engine.story_validator import StoryValidator

logger = logging.getLogger("infinite_story.engine.segment_context_builder")


class SegmentContextBuilder:
    """Build comprehensive context for segment generation.
    
    Walks through story history and collects:
    - All character summaries (short) + extended info if in last 3 segments
    - Full current episode information
    - Last 3 episode recaps
    - Last 10 arc recaps
    - Full current arc information
    - Last 10 segment recaps
    - Last 3 segment full text (for conversation continuation)
    - Character evolution tracking
    - Pacing signals
    
    Also validates story completeness before building context and auto-generates
    missing pieces (world, arcs, characters, protagonist) if needed.
    """
    
    def __init__(self, story: Story, generator: Optional[Any] = None):
        """Initialize the context builder.
        
        Args:
            story: The Story instance to build context from
            generator: Optional AI generator for auto-generation of missing pieces
        """
        self.story = story
        self.generator = generator
    
    async def build_context(
        self,
        current_segment_id: str,
        user_choice: str
    ) -> Dict[str, Any]:
        """Build comprehensive generation context for a new segment.
        
        FIRST: Validates story completeness and auto-generates missing pieces:
        - World description (if missing)
        - Story description (if missing)
        - Arcs (3 future outlines if no active arcs)
        - Characters (parsed from segments or generated)
        - Protagonist (selected or developed)
        
        THEN: Collects:
        1. All character summaries + extended info for last 3 segments
        2. Full episode information
        3. Last 3 episode recaps
        4. Last 10 arc recaps
        5. Full arc information
        6. Last 10 segment recaps
        7. Last 3 segment full text
        8. Pacing weight
        9. Episode transition signals
        
        Args:
            current_segment_id: ID of the segment the user is in
            user_choice: The text of the choice the user made
            
        Returns:
            Comprehensive context dict for generation
            
        Raises:
            ValueError: If story validation/repair fails or segment not found
        """
        # VALIDATION: Validate and auto-generate missing story pieces
        if self.generator:
            try:
                validator = StoryValidator(self.story, self.generator)
                validation_report = await validator.validate_and_repair()
                logger.info(f"Story validation complete. Generated: {validation_report.get('generated', [])}")
            except Exception as e:
                logger.error(f"Story validation failed: {e}")
                # Don't fail here - continue with what we have
        
        # Get the current segment
        current_seg = self.story.get_segment(current_segment_id)
        if not current_seg:
            raise ValueError(f"Segment {current_segment_id} not found")
        
        # Walk backward to episode start
        episode_chain = self._walk_episode_chain(current_segment_id)
        
        # Accumulate character changes
        accumulated_changes = self._accumulate_changes(episode_chain)
        
        # Detect episode transition
        should_transition = self._should_transition_episode(
            current_seg,
            accumulated_changes
        )
        
        # Calculate pacing weight
        pacing = self._calculate_pacing_weight(
            current_seg,
            should_transition
        )
        
        # Build comprehensive context
        context_dict = {
            # ====================================================================
            # CHARACTER CONTEXT
            # ====================================================================
            'all_characters': self._get_all_character_summaries(),
            'extended_characters': self._get_extended_character_info(episode_chain[-3:]),
            'character_changes_this_episode': accumulated_changes,
            
            # ====================================================================
            # EPISODE CONTEXT
            # ====================================================================
            'current_episode': self._get_current_episode_info(current_seg),
            'recent_episode_recaps': self._get_recent_episode_recaps(
                current_seg.episode_number,
                current_seg.arc_id,
                count=3
            ),
            
            # ====================================================================
            # ARC CONTEXT
            # ====================================================================
            'current_arc': self._get_current_arc_info(current_seg.arc_id),
            'recent_arc_recaps': self._get_recent_arc_recaps(count=10),
            
            # ====================================================================
            # SEGMENT CONTEXT
            # ====================================================================
            'segment_recaps': self._get_segment_recaps(
                episode_chain,
                count=10
            ),
            'recent_segments_full': self._get_recent_segments_full(
                episode_chain[-3:]
            ),
            
            # ====================================================================
            # NAVIGATION & SIGNALS
            # ====================================================================
            'should_transition_episode': should_transition,
            'pacing_weight': pacing,
            'episode_number': current_seg.episode_number,
            'segment_number_in_episode': current_seg.segment_number_in_episode,
            'user_choice': user_choice,
        }
        
        # Add arc context if available
        if current_seg.arc_id:
            try:
                from app.models.story_arc import StoryArc
                arc = StoryArc.load(self.story.id, current_seg.arc_id)
                if arc:
                    context_dict.update({
                        'arc_premise': arc.premise,
                        'arc_themes': arc.themes,
                        'arc_tone': arc.arc_tone,
                        'character_arc_goals': arc.character_arc_goals,
                        'unresolved_mysteries': arc.unresolved_mysteries,
                        'central_conflict': arc.central_conflict,
                    })
            except Exception as e:
                logger.warning(f"Failed to load arc context: {e}")
        
        # Add episode metadata if available
        if current_seg.arc_id and current_seg.episode_number:
            try:
                from app.models.episode_meta import EpisodeMeta
                episode_meta_id = f"episode_meta_{current_seg.episode_number}_{current_seg.arc_id}"
                episode_meta = EpisodeMeta.load(self.story.id, episode_meta_id)
                if episode_meta:
                    context_dict.update({
                        'episode_selected_themes': episode_meta.selected_themes,
                        'episode_focus': episode_meta.episode_focus,
                        'story_hooks': episode_meta.story_hooks,
                    })
            except Exception as e:
                logger.debug(f"Episode metadata not found: {e}")
        
        return context_dict
    
    def _walk_episode_chain(self, segment_id: str) -> List[str]:
        """Walk backward from segment to episode start."""
        chain = []
        current = self.story.get_segment(segment_id)
        if not current:
            return chain
        
        episode_num = current.episode_number
        visited = set()
        
        while current and current.episode_number == episode_num:
            if current.id in visited:
                logger.warning(f"Circular reference detected at segment {current.id}")
                break
            visited.add(current.id)
            
            chain.insert(0, current.id)
            
            if not current.parent_segment_id:
                break
            
            current = self.story.get_segment(current.parent_segment_id)
        
        return chain
    
    def _accumulate_changes(self, segment_chain: List[str]) -> List[str]:
        """Collect all change_notes from segment chain."""
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
        """Decide if this segment should end the episode."""
        if current_segment.end_condition_proximity >= 0.8:
            logger.debug(f"Segment {current_segment.id}: proximity >= 0.8, transitioning")
            return True
        
        if current_segment.segment_number_in_episode >= 18:
            logger.debug(f"Segment {current_segment.id}: count >= 18, transitioning")
            return True
        
        end_keywords = ['chapter', 'end', 'conclusion', 'climax', 'finale']
        for change in changes:
            if any(kw in change.lower() for kw in end_keywords):
                logger.debug(f"Segment {current_segment.id}: found end keyword, transitioning")
                return True
        
        return False
    
    def _calculate_pacing_weight(
        self,
        segment: StorySegment,
        will_transition: bool
    ) -> float:
        """Calculate pacing weight (0.0 to 1.0)."""
        if will_transition:
            return 0.9
        
        seg_num = segment.segment_number_in_episode
        max_segments = 20
        
        weight = (seg_num / max_segments) ** 2
        return min(weight, 0.99)
    
    # ========================================================================
    # NEW: Comprehensive Context Builders
    # ========================================================================
    
    def _get_all_character_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get short recaps for ALL characters in story."""
        from app.models.character_recap import CharacterRecap
        
        summaries = {}
        try:
            for character in self.story.get_all_characters():
                try:
                    recap = CharacterRecap.load(self.story.id, character.id)
                    if recap:
                        summaries[character.id] = {
                            'name': recap.character_name,
                            'status': recap.current_status,
                            'emotion': recap.current_emotion,
                            'description': recap.short_description,
                            'relationships': recap.key_relationships,
                            'last_seen': recap.last_seen_episode,
                        }
                except:
                    # Fallback to character data
                    summaries[character.id] = {
                        'name': character.name,
                        'description': character.description,
                        'status': 'unknown',
                    }
        except Exception as e:
            logger.warning(f"Failed to get character summaries: {e}")
        
        return summaries
    
    def _get_extended_character_info(self, recent_segments: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get full character info for characters in last 3 segments."""
        extended = {}
        
        # Collect character IDs from recent segments
        recent_char_ids = set()
        for seg_id in recent_segments:
            seg = self.story.get_segment(seg_id)
            if seg:
                recent_char_ids.update(seg.characters_present)
        
        # Get full info for these characters
        for char_id in recent_char_ids:
            try:
                character = self.story.get_character(char_id)
                if character:
                    extended[char_id] = {
                        'name': character.name,
                        'description': character.description,
                        'background': character.background,
                        'avatar': f"{character.avatar_shape}:{character.avatar_color}",
                    }
            except Exception as e:
                logger.debug(f"Failed to get extended info for {char_id}: {e}")
        
        return extended
    
    def _get_current_episode_info(self, segment: StorySegment) -> Dict[str, Any]:
        """Get full current episode information."""
        return {
            'episode_number': segment.episode_number,
            'episode_tone': segment.episode_tone,
            'episode_end_condition': segment.episode_end_condition,
            'segment_number': segment.segment_number_in_episode,
            'pacing_weight': segment.pacing_weight,
            'protagonist_id': segment.protagonist_id,
        }
    
    def _get_recent_episode_recaps(
        self,
        current_episode: int,
        arc_id: Optional[str],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """Get last N episode recaps."""
        from app.models.episode_recap import EpisodeRecap
        
        recaps = []
        
        # Look back from current episode
        for ep_num in range(current_episode - 1, max(0, current_episode - count - 1), -1):
            try:
                recap_id = f"recap_{self.story.id}_ep{ep_num}_{arc_id or 'main'}"
                recap = EpisodeRecap.load(self.story.id, recap_id)
                if recap:
                    recaps.append({
                        'episode': ep_num,
                        'title': recap.title,
                        'summary': recap.summary,
                        'themes': recap.key_themes,
                        'hook_for_next': recap.hook_for_next,
                    })
            except:
                pass
        
        return recaps
    
    def _get_current_arc_info(self, arc_id: Optional[str]) -> Dict[str, Any]:
        """Get full current arc information."""
        if not arc_id:
            return {}
        
        try:
            from app.models.story_arc import StoryArc
            arc = StoryArc.load(self.story.id, arc_id)
            if arc:
                return {
                    'title': arc.title,
                    'premise': arc.premise,
                    'narrative_direction': arc.narrative_direction,
                    'central_conflict': arc.central_conflict,
                    'themes': arc.themes,
                    'character_arc_goals': arc.character_arc_goals,
                    'unresolved_mysteries': arc.unresolved_mysteries,
                    'plot_hooks': arc.plot_hooks,
                    'episode_count': arc.episode_count,
                    'tone': arc.arc_tone,
                    'mood': arc.arc_mood,
                }
        except Exception as e:
            logger.warning(f"Failed to get arc info: {e}")
        
        return {}
    
    def _get_recent_arc_recaps(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get last N arc recaps from story."""
        # TODO: Implement arc recap storage and loading
        # For now, return empty as arcs are tracked in StoryArc model
        return []
    
    def _get_segment_recaps(self, segment_chain: List[str], count: int = 10) -> List[Dict[str, Any]]:
        """Get recaps for recent segments."""
        from app.models.segment_recap import SegmentRecap
        
        recaps = []
        
        # Get last N segments from chain
        for seg_id in segment_chain[-count:]:
            try:
                recap = SegmentRecap.load(self.story.id, f"segment_recap_{seg_id}")
                if recap:
                    recaps.append({
                        'segment_id': recap.segment_id,
                        'description': recap.short_description,
                        'key_events': recap.key_events,
                        'characters': recap.characters_present,
                        'changes': recap.character_changes,
                    })
            except:
                # Fallback: create basic recap from segment
                seg = self.story.get_segment(seg_id)
                if seg:
                    recaps.append({
                        'segment_id': seg.id,
                        'description': seg.short_description,
                        'characters': seg.characters_present,
                    })
        
        return recaps
    
    def _get_recent_segments_full(self, recent_segment_ids: List[str]) -> List[Dict[str, Any]]:
        """Get full text of last 3 segments for conversation continuation."""
        full_segments = []
        
        for seg_id in recent_segment_ids:
            seg = self.story.get_segment(seg_id)
            if seg:
                full_segments.append({
                    'segment_id': seg.id,
                    'description': seg.short_description,
                    'text': seg.get_plain_text_script() if hasattr(seg, 'get_plain_text_script') else '',
                    'characters': seg.characters_present,
                    'changes': seg.change_notes,
                })
        
        return full_segments
