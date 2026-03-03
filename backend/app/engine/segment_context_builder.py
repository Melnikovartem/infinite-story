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
        
        # Walk full parent chain to include previous episodes
        full_parent_chain = self._walk_full_parent_chain(current_segment_id)
        
        # Build structured character context (arc -> episode -> segment hierarchy)
        char_context = self._get_structured_character_context(current_seg, episode_chain)
        
        # Build comprehensive context
        context_dict = {
            # ====================================================================
            # CHARACTER CONTEXT (HIERARCHICAL)
            # ====================================================================
            'arc_characters': char_context['arc_characters'],           # All characters (short)
            'episode_characters': char_context['episode_characters'],   # Updated states (full)
            'segment_character_changes': char_context['segment_character_changes'],  # Running changes
            'character_changes_this_episode': accumulated_changes,
            'character_relationships': self._get_character_relationships(episode_chain),
            'relationship_changes': self._get_relationship_changes(episode_chain),
            'character_importance_tiers': self._get_character_importance_tiers(),
            
            # ====================================================================
            # FACTION CONTEXT (NEW)
            # ====================================================================
            'factions': self._get_faction_context(),
            'faction_dynamics': self._get_faction_dynamics(episode_chain),
            'character_faction_alignment': self._get_character_faction_alignment(),
            
            # ====================================================================
            # MAGIC/TECH SYSTEM CONTEXT (NEW)
            # ====================================================================
            'magic_system': self._get_magic_system_context(),
            
            # ====================================================================
            # EPISODE CONTEXT (all episodes in current arc)
            # ====================================================================
            'current_episode': self._get_current_episode_info(current_seg),
            'episodes_in_arc': self._get_previous_episodes_context(
                full_parent_chain,
                current_seg.episode_number,
                current_seg.arc_id
            ),
            'recent_episode_recaps': self._get_recent_episode_recaps(
                current_seg.episode_number,
                current_seg.arc_id,
                count=3
            ),
            
            # ====================================================================
            # ARC CONTEXT
            # ====================================================================
            'current_arc': self._get_current_arc_info(current_seg.arc_id),
            'previous_arcs': self._get_previous_arcs_context(
                current_seg.arc_id,
                count=10
            ),
            'recent_arc_recaps': self._get_recent_arc_recaps(count=10),
            
            # ====================================================================
            # SEGMENT CONTEXT
            # ====================================================================
            'recent_segments_full': self._get_recent_segments_full(
                episode_chain[-3:]
            ),
            'segment_recaps': self._get_segment_recaps_with_context(
                full_parent_chain,
                count=10
            ),
            
            # ====================================================================
            # WORLD STATE & LOCATIONS
            # ====================================================================
            'location_states': self._get_location_states(episode_chain),
            'world_state_changes': self._get_world_state_changes(episode_chain),
            
            # ====================================================================
            # THEME & MYSTERY TRACKING
            # ====================================================================
            'themes_explored': self._get_themes_explored(episode_chain),
            'theme_depth': self._get_theme_depth(episode_chain),
            'mysteries_tracking': self._get_mysteries_tracking(current_seg.arc_id),
            'new_mysteries_introduced': self._get_new_mysteries_introduced(episode_chain),
            
            # ====================================================================
            # STORY MOMENTUM METRICS
            # ====================================================================
            'story_momentum': self._calculate_story_momentum(episode_chain),
            'tension_level': self._calculate_tension_level(episode_chain),
            'pacing_trend': self._calculate_pacing_trend(episode_chain),
            
            # ====================================================================
            # NAVIGATION & SIGNALS
            # ====================================================================
            'should_transition_episode': should_transition,
            'pacing_weight': pacing,
            'episode_number': current_seg.episode_number,
            'segment_number_in_episode': current_seg.segment_number_in_episode,
            'user_choice': user_choice,
            
            # ====================================================================
            # BACKWARD COMPATIBILITY: Top-level episode fields
            # ====================================================================
            'episode_tone': current_seg.episode_tone,
            'episode_end_condition': current_seg.episode_end_condition,
            'protagonist_id': current_seg.protagonist_id,
            'character_states': current_seg.character_states,
            'accumulated_changes': accumulated_changes,
            'previous_segments': [
                self.story.get_segment(seg_id).get_short_overview()
                for seg_id in episode_chain[-5:]  # Last 5 scenes
                if self.story.get_segment(seg_id)
            ],
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
        """Walk backward from segment to episode start (within same episode only)."""
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
    
    def _walk_full_parent_chain(self, segment_id: str, max_depth: int = 100) -> List[str]:
        """Walk backward through ALL parent segments across episode boundaries.
        
        This creates a full genealogy of the story, walking up the parent chain
        from the current segment all the way to the story root, crossing episode
        boundaries. Useful for getting full story context across episodes.
        
        Args:
            segment_id: The segment to start walking from
            max_depth: Maximum segments to traverse (prevents infinite loops)
            
        Returns:
            List of all parent segment IDs in chronological order (oldest first)
        """
        chain = []
        current = self.story.get_segment(segment_id)
        if not current:
            return chain
        
        visited = set()
        depth = 0
        
        while current and depth < max_depth:
            if current.id in visited:
                logger.warning(f"Circular reference detected at segment {current.id}")
                break
            visited.add(current.id)
            
            chain.insert(0, current.id)
            
            if not current.parent_segment_id:
                # Reached the root
                logger.debug(f"Reached root segment {current.id}")
                break
            
            current = self.story.get_segment(current.parent_segment_id)
            depth += 1
        
        if depth >= max_depth:
            logger.warning(f"Reached max depth {max_depth} walking parent chain")
        
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
    
    def _get_previous_episodes_context(self, full_parent_chain: List[str], current_episode: int, current_arc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract context for all episodes from current arc start to current (including previous episodes).
        
        Walks through the full parent chain and identifies all segments that belong
        to the current arc, organizing them by episode. Includes all episodes from
        the arc start up to and including the current episode.
        
        Args:
            full_parent_chain: Full list of parent segment IDs (from root to current)
            current_episode: The current episode number
            current_arc_id: The current arc ID (to filter episodes)
            
        Returns:
            List of dicts with episode information and episode recaps
        """
        episodes_by_number = {}
        
        # Group segments by episode
        for seg_id in full_parent_chain:
            seg = self.story.get_segment(seg_id)
            if not seg:
                continue
            
            # Only include segments from the current arc
            if current_arc_id and seg.arc_id != current_arc_id:
                continue
            
            # Include all episodes in this arc
            if seg.episode_number <= current_episode:
                if seg.episode_number not in episodes_by_number:
                    episodes_by_number[seg.episode_number] = {
                        'episode_number': seg.episode_number,
                        'tone': seg.episode_tone,
                        'end_condition': seg.episode_end_condition,
                        'protagonist_id': seg.protagonist_id,
                        'segments': []
                    }
                
                episodes_by_number[seg.episode_number]['segments'].append({
                    'segment_id': seg.id,
                    'description': seg.short_description,
                    'segment_number': seg.segment_number_in_episode,
                })
        
        # Build result with episode recaps
        result = []
        for ep_num in sorted(episodes_by_number.keys()):
            ep_info = episodes_by_number[ep_num]
            
            # Try to load episode recap
            try:
                from app.models.episode_recap import EpisodeRecap
                recap_id = f"episode_recap_{ep_num}_{current_arc_id}" if current_arc_id else f"episode_recap_{ep_num}"
                recap = EpisodeRecap.load(self.story.id, recap_id)
                if recap:
                    ep_info['recap'] = {
                        'key_events': recap.key_events,
                        'character_developments': recap.character_developments,
                        'plot_progression': recap.plot_progression,
                    }
            except:
                pass
            
            result.append(ep_info)
        
        logger.debug(f"Extracted {len(result)} episodes from current arc")
        return result
    
    def _get_previous_arcs_context(self, current_arc_id: Optional[str] = None, count: int = 10) -> List[Dict[str, Any]]:
        """Get context for previous arcs (up to N).
        
        Loads recaps for previous arcs to provide long-form story context.
        
        Args:
            current_arc_id: The current arc ID (to exclude from results)
            count: Maximum number of previous arcs to include
            
        Returns:
            List of previous arc information with recaps
        """
        from app.models.arc_recap import ArcRecap
        
        arcs = []
        all_arcs = self.story.get_all_arcs() if hasattr(self.story, 'get_all_arcs') else []
        
        # Get previous arcs (before current)
        for arc in all_arcs:
            if current_arc_id and arc.id == current_arc_id:
                continue
            
            try:
                recap = ArcRecap.load(self.story.id, f"arc_recap_{arc.id}")
                if recap:
                    arcs.append({
                        'arc_id': arc.id,
                        'name': arc.name if hasattr(arc, 'name') else arc.id,
                        'premise': recap.arc_premise if hasattr(recap, 'arc_premise') else '',
                        'resolution': recap.resolution if hasattr(recap, 'resolution') else '',
                        'major_events': recap.major_events if hasattr(recap, 'major_events') else [],
                        'character_arcs': recap.character_arcs if hasattr(recap, 'character_arcs') else {},
                    })
                    if len(arcs) >= count:
                        break
            except:
                pass
        
        logger.debug(f"Extracted {len(arcs)} previous arcs")
        return arcs
    
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
    
    def _get_structured_character_context(
        self,
        current_seg: StorySegment,
        episode_chain: List[str]
    ) -> Dict[str, Any]:
        """Build comprehensive, hierarchical character context for LLM.
        
        Hierarchy:
        1. ALL CHARACTERS (from arc): short description only
        2. Episode characters (updated states): full context + all fields
        3. Segment running changes: current state overrides
        
        Returns:
            {
                'arc_characters': {...},           # All characters in arc (short)
                'episode_characters': {...},       # Updated in episode (full context)
                'segment_character_changes': {...} # Running changes this segment
            }
        """
        from app.models.story_arc import StoryArc
        from app.models.episode_meta import EpisodeMeta
        
        arc_characters = {}
        episode_characters = {}
        segment_changes = {}
        
        try:
            # Load arc to get all characters
            if current_seg.arc_id:
                arc = StoryArc.load(self.story.id, current_seg.arc_id)
                if arc:
                    # Get all characters from story and provide short descriptions
                    for character in self.story.get_all_characters():
                        try:
                            arc_characters[character.id] = {
                                'name': character.name,
                                'short_description': character.description,
                                'importance': character.importance_tier if hasattr(character, 'importance_tier') else 'minor',
                            }
                        except Exception as e:
                            logger.debug(f"Failed to get arc character {character.id}: {e}")
            
            # Load episode metadata to get updated character states
            if current_seg.arc_id and current_seg.episode_number:
                episode_meta_id = f"episode_meta_{current_seg.episode_number}_{current_seg.arc_id}"
                episode_meta = EpisodeMeta.load(self.story.id, episode_meta_id)
                
                if episode_meta and episode_meta.character_state_snapshot:
                    # Pack episode character states with full context
                    for char_id, state_snapshot in episode_meta.character_state_snapshot.items():
                        try:
                            character = self.story.get_character(char_id)
                            episode_characters[char_id] = {
                                'name': character.name if character else f"Character {char_id}",
                                'description': state_snapshot.description,
                                'health_status': state_snapshot.health_status,
                                'emotional_status': state_snapshot.emotional_status,
                                'relationship_notes': state_snapshot.relationship_notes,
                                'inventory': state_snapshot.inventory,
                                'character_arc_goal': state_snapshot.character_arc_goal,
                                'goal_progress': state_snapshot.goal_progress,
                                'goal_notes': state_snapshot.goal_notes,
                                'is_active': char_id in (episode_meta.active_characters or []),
                            }
                        except Exception as e:
                            logger.debug(f"Failed to get episode character {char_id}: {e}")
            
            # Get segment-level running changes
            for seg_id in episode_chain[-1:]:  # Last segment
                seg = self.story.get_segment(seg_id)
                if seg and seg.character_states:
                    for char_id, state_dict in seg.character_states.items():
                        if isinstance(state_dict, dict):
                            segment_changes[char_id] = {
                                'emotion': state_dict.get('emotion'),
                                'status': state_dict.get('status'),
                                'notes': state_dict.get('notes'),
                            }
        
        except Exception as e:
            logger.warning(f"Failed to build structured character context: {e}")
        
        return {
            'arc_characters': arc_characters,
            'episode_characters': episode_characters,
            'segment_character_changes': segment_changes,
        }
    
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
    
    def _get_segment_recaps_with_context(self, full_parent_chain: List[str], count: int = 10) -> List[Dict[str, Any]]:
        """Get recaps for recent segments from full parent chain, with recap details.
        
        Walks the full parent chain and gets the N most recent segments with their
        full recap information if available.
        
        Args:
            full_parent_chain: Full list of parent segment IDs
            count: Number of recaps to include
            
        Returns:
            List of segment recaps with details
        """
        from app.models.segment_recap import SegmentRecap
        
        recaps = []
        
        # Get last N segments from full chain
        for seg_id in full_parent_chain[-count:]:
            try:
                recap = SegmentRecap.load(self.story.id, f"segment_recap_{seg_id}")
                if recap:
                    recaps.append({
                        'segment_id': recap.segment_id,
                        'episode_number': recap.episode_number if hasattr(recap, 'episode_number') else None,
                        'segment_number': recap.segment_number if hasattr(recap, 'segment_number') else None,
                        'description': recap.short_description,
                        'key_events': recap.key_events if hasattr(recap, 'key_events') else [],
                        'characters': recap.characters_present if hasattr(recap, 'characters_present') else [],
                        'changes': recap.character_changes if hasattr(recap, 'character_changes') else [],
                    })
                else:
                    # Fallback: create basic recap from segment
                    seg = self.story.get_segment(seg_id)
                    if seg:
                        recaps.append({
                            'segment_id': seg.id,
                            'episode_number': seg.episode_number,
                            'segment_number': seg.segment_number_in_episode,
                            'description': seg.short_description,
                            'characters': seg.characters_present,
                            'changes': seg.change_notes,
                        })
            except:
                # Fallback: create basic recap from segment
                seg = self.story.get_segment(seg_id)
                if seg:
                    recaps.append({
                        'segment_id': seg.id,
                        'episode_number': seg.episode_number,
                        'segment_number': seg.segment_number_in_episode,
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
    
    # =========================================================================
    # NEW: CHARACTER RELATIONSHIP TRACKING
    # =========================================================================
    
    def _get_character_relationships(self, segment_chain: List[str]) -> Dict[str, Dict[str, str]]:
        """Get current character relationships and their status.
        
        Returns mapping of character pairs and their relationship type.
        """
        relationships = {}
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and seg.character_states:
                # Extract relationship info from character states if available
                for char_id, state in seg.character_states.items():
                    if isinstance(state, dict) and 'relationships' in state:
                        if char_id not in relationships:
                            relationships[char_id] = {}
                        relationships[char_id].update(state['relationships'])
        
        return relationships
    
    def _get_relationship_changes(self, segment_chain: List[str]) -> List[Dict[str, str]]:
        """Track how character relationships have changed during episode.
        
        Returns list of relationship changes extracted from change_notes.
        """
        changes = []
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and seg.change_notes:
                # Look for relationship-related change notes
                for note in seg.change_notes:
                    if any(keyword in note.lower() for keyword in ['relationship', 'trust', 'betrayed', 'allied', 'enemy']):
                        changes.append({
                            'segment_id': seg_id,
                            'change': note
                        })
        
        return changes
    
    # =========================================================================
    # NEW: LOCATION & WORLD STATE TRACKING
    # =========================================================================
    
    def _get_location_states(self, segment_chain: List[str]) -> Dict[str, Dict[str, str]]:
        """Get current state of all locations mentioned in episode.
        
        Returns mapping of location_id -> {status, last_seen, description}.
        """
        locations = {}
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg:
                # Add locations from segment
                for loc_id in seg.locations_present if hasattr(seg, 'locations_present') else []:
                    loc = self.story.get_location(loc_id)
                    if loc:
                        locations[loc_id] = {
                            'name': loc.name,
                            'description': loc.description if hasattr(loc, 'description') else '',
                            'last_seen_segment': seg_id,
                            'status': 'accessible'  # Could be expanded with more states
                        }
        
        return locations
    
    def _get_world_state_changes(self, segment_chain: List[str]) -> List[str]:
        """Get changes to world state (locations, environment, objects).
        
        Extracted from segment change_notes.
        """
        changes = []
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and seg.change_notes:
                # Look for world-state related changes
                for note in seg.change_notes:
                    if any(keyword in note.lower() for keyword in ['location', 'environment', 'destroyed', 'built', 'changed', 'fire', 'door', 'wall']):
                        changes.append(f"[Seg {seg_id}] {note}")
        
        return changes
    
    # =========================================================================
    # NEW: THEME & MYSTERY TRACKING
    # =========================================================================
    
    def _get_themes_explored(self, segment_chain: List[str]) -> Dict[str, int]:
        """Get count of how many times each theme appeared.
        
        Returns mapping of theme -> count.
        """
        theme_counts = {}
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and hasattr(seg, 'episode_selected_themes'):
                for theme in seg.episode_selected_themes:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        return theme_counts
    
    def _get_theme_depth(self, segment_chain: List[str]) -> Dict[str, str]:
        """Get depth of exploration for each theme.
        
        Maps theme -> exploration level (introduced/developing/resolved/returning).
        """
        theme_depth = {}
        first_appearance = {}
        theme_segments = {}
        
        for i, seg_id in enumerate(segment_chain):
            seg = self.story.get_segment(seg_id)
            if seg and hasattr(seg, 'episode_selected_themes'):
                for theme in seg.episode_selected_themes:
                    if theme not in first_appearance:
                        first_appearance[theme] = i
                    theme_segments[theme] = theme_segments.get(theme, 0) + 1
        
        # Determine depth based on appearance frequency and position
        for theme, count in theme_segments.items():
            if count == 1:
                theme_depth[theme] = 'introduced'
            elif count <= 3:
                theme_depth[theme] = 'developing'
            elif count > 3:
                theme_depth[theme] = 'deeply_explored'
        
        return theme_depth
    
    def _get_mysteries_tracking(self, arc_id: Optional[str]) -> Dict[str, str]:
        """Get current status of arc mysteries.
        
        Returns mapping of mystery -> status (unresolved/being_investigated/resolved).
        """
        mysteries = {}
        
        if arc_id:
            try:
                from app.models.story_arc import StoryArc
                arc = StoryArc.load(self.story.id, arc_id)
                if arc and arc.unresolved_mysteries:
                    for mystery in arc.unresolved_mysteries:
                        mysteries[mystery] = 'unresolved'
            except:
                pass
        
        return mysteries
    
    def _get_new_mysteries_introduced(self, segment_chain: List[str]) -> List[str]:
        """Get new mysteries/questions introduced in this episode.
        
        Extracted from segment change_notes and episode text.
        """
        new_mysteries = []
        mystery_keywords = ['mystery', 'question', 'unknown', 'puzzle', 'secret', 'hidden', 'discover', 'revealed']
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and seg.change_notes:
                for note in seg.change_notes:
                    if any(keyword in note.lower() for keyword in mystery_keywords):
                        new_mysteries.append(note)
        
        return new_mysteries
    
    # =========================================================================
    # NEW: STORY MOMENTUM METRICS
    # =========================================================================
    
    def _calculate_story_momentum(self, segment_chain: List[str]) -> Dict[str, Any]:
        """Calculate story momentum metrics.
        
        Returns: {
            'direction': 'escalating'/'stable'/'declining',
            'intensity': 0.0-1.0,
            'segment_count': int,
            'average_change_rate': float
        }
        """
        if not segment_chain:
            return {'direction': 'stable', 'intensity': 0.0, 'segment_count': 0, 'average_change_rate': 0.0}
        
        change_rates = []
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and seg.change_notes:
                change_rates.append(len(seg.change_notes))
        
        avg_rate = sum(change_rates) / len(change_rates) if change_rates else 0
        
        # Determine direction based on trend
        if len(change_rates) > 1:
            recent_rate = sum(change_rates[-3:]) / min(3, len(change_rates))
            early_rate = sum(change_rates[:3]) / min(3, len(change_rates))
            if recent_rate > early_rate * 1.2:
                direction = 'escalating'
            elif recent_rate < early_rate * 0.8:
                direction = 'declining'
            else:
                direction = 'stable'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'intensity': min(1.0, avg_rate / 5.0),  # Normalize to 0-1
            'segment_count': len(segment_chain),
            'average_change_rate': avg_rate
        }
    
    def _calculate_tension_level(self, segment_chain: List[str]) -> Dict[str, Any]:
        """Calculate current tension/conflict level in story.
        
        Returns: {
            'level': 'low'/'medium'/'high'/'critical',
            'score': 0.0-1.0,
            'conflict_count': int,
            'resolution_count': int
        }
        """
        conflict_keywords = ['conflict', 'battle', 'danger', 'threat', 'attack', 'death', 'betrayal', 'fear', 'anger']
        resolution_keywords = ['resolve', 'peace', 'victory', 'reconcile', 'trust', 'calm', 'safe', 'relief']
        
        conflicts = 0
        resolutions = 0
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg and seg.change_notes:
                for note in seg.change_notes:
                    note_lower = note.lower()
                    if any(keyword in note_lower for keyword in conflict_keywords):
                        conflicts += 1
                    if any(keyword in note_lower for keyword in resolution_keywords):
                        resolutions += 1
        
        # Calculate tension score
        net_tension = conflicts - resolutions
        tension_score = min(1.0, max(0.0, net_tension / 10.0))
        
        if tension_score < 0.2:
            level = 'low'
        elif tension_score < 0.5:
            level = 'medium'
        elif tension_score < 0.8:
            level = 'high'
        else:
            level = 'critical'
        
        return {
            'level': level,
            'score': tension_score,
            'conflict_count': conflicts,
            'resolution_count': resolutions
        }
    
    def _calculate_pacing_trend(self, segment_chain: List[str]) -> Dict[str, Any]:
        """Calculate pacing trend (accelerating/steady/decelerating).
        
        Returns: {
            'trend': 'accelerating'/'steady'/'decelerating',
            'score': 0.0-1.0,
            'recent_pace': float,
            'early_pace': float
        }
        """
        segment_lengths = []
        
        for seg_id in segment_chain:
            seg = self.story.get_segment(seg_id)
            if seg:
                text_length = len(seg.short_description or '')
                segment_lengths.append(text_length)
        
        if len(segment_lengths) < 2:
            return {
                'trend': 'steady',
                'score': 0.5,
                'recent_pace': 0.0,
                'early_pace': 0.0
            }
        
        early_pace = sum(segment_lengths[:3]) / min(3, len(segment_lengths))
        recent_pace = sum(segment_lengths[-3:]) / min(3, len(segment_lengths))
        
        if recent_pace > early_pace * 1.2:
            trend = 'accelerating'
        elif recent_pace < early_pace * 0.8:
            trend = 'decelerating'
        else:
            trend = 'steady'
        
        # Normalize score
        max_pace = max(early_pace, recent_pace)
        score = recent_pace / max_pace if max_pace > 0 else 0.5
        
        return {
            'trend': trend,
            'score': min(1.0, score),
            'recent_pace': recent_pace,
            'early_pace': early_pace
        }
    
    # ========================================================================
    # NEW METHODS FOR FACTION, MAGIC SYSTEM, AND CHARACTER TIERS
    # ========================================================================
    
    def _get_character_importance_tiers(self) -> Dict[str, List[str]]:
        """Get characters grouped by importance tier.
        
        Returns: {
            'protagonist': [char_names],
            'major': [char_names],
            'minor': [char_names]
        }
        """
        tiers = {'protagonist': [], 'major': [], 'minor': []}
        
        for char in self.story._characters.values():
            tier = getattr(char, 'importance_tier', 'minor')
            name = getattr(char, 'name', 'Unknown')
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(name)
        
        return tiers
    
    def _get_faction_context(self) -> Dict[str, Any]:
        """Get all factions with their details.
        
        Returns: {
            'count': int,
            'factions': [
                {
                    'id': str,
                    'name': str,
                    'description': str,
                    'goals': [str],
                    'leader': str,
                    'resources': str,
                    'alignment': str
                }
            ]
        }
        """
        factions_list = []
        
        # Get factions from story if stored
        if hasattr(self.story, '_factions') and self.story._factions:
            for faction in self.story._factions.values():
                factions_list.append({
                    'id': getattr(faction, 'id', 'unknown'),
                    'name': getattr(faction, 'name', 'Unknown'),
                    'description': getattr(faction, 'description', ''),
                    'goals': getattr(faction, 'goals', []),
                    'leader': getattr(faction, 'leader', 'Unknown'),
                    'resources': getattr(faction, 'resources', ''),
                    'alignment': getattr(faction, 'alignment', 'Neutral')
                })
        
        return {
            'count': len(factions_list),
            'factions': factions_list
        }
    
    def _get_faction_dynamics(self, segment_chain: List[str]) -> Dict[str, Any]:
        """Track faction appearances and conflicts in recent episodes.
        
        Returns: {
            'faction_mentions': {'faction_name': count, ...},
            'faction_conflicts': [{'faction1': str, 'faction2': str, 'description': str}],
            'faction_alliances': [{'faction1': str, 'faction2': str, 'status': str}]
        }
        """
        # This is a simplified version - could be expanded to parse segment text for faction mentions
        return {
            'faction_mentions': {},
            'faction_conflicts': [],
            'faction_alliances': []
        }
    
    def _get_character_faction_alignment(self) -> Dict[str, str]:
        """Get faction alignment for each major character.
        
        Returns: {
            'character_name': 'faction_name',
            ...
        }
        """
        alignments = {}
        
        for char in self.story._characters.values():
            if getattr(char, 'importance_tier', 'minor') in ('protagonist', 'major'):
                char_name = getattr(char, 'name', 'Unknown')
                faction_id = getattr(char, 'faction_id', None)
                
                if faction_id and hasattr(self.story, '_factions'):
                    # Find faction by ID
                    for faction in self.story._factions.values():
                        if getattr(faction, 'id', None) == faction_id:
                            alignments[char_name] = getattr(faction, 'name', 'Unknown Faction')
                            break
        
        return alignments
    
    def _get_magic_system_context(self) -> Dict[str, Any]:
        """Get magic/tech system rules and constraints.
        
        Returns: {
            'name': str,
            'description': str,
            'capabilities': [str],
            'limitations': [str],
            'costs': [str],
            'technology_level': str
        }
        """
        # Try to find magic system in story data
        if hasattr(self.story, '_magic_system') and self.story._magic_system:
            magic_sys = self.story._magic_system
            return {
                'name': getattr(magic_sys, 'name', 'Unknown System'),
                'description': getattr(magic_sys, 'description', ''),
                'capabilities': getattr(magic_sys, 'capabilities', [])[:3],
                'limitations': getattr(magic_sys, 'limitations', [])[:3],
                'costs': getattr(magic_sys, 'costs', [])[:3],
                'technology_level': getattr(magic_sys, 'technology_level', '')
            }
        
        return {
            'name': 'Unknown',
            'description': '',
            'capabilities': [],
            'limitations': [],
            'costs': [],
            'technology_level': ''
        }
