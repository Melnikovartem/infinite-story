"""Arc transition manager for handling arc completion and next arc initialization (E2-5)."""

from typing import List, Dict, Optional, Any
import logging
from app.models import Story, StoryArc, StorySegment
from app.models.story_segment import SegmentStatus
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.arc_transition_manager")

# Number of episodes that trigger arc completion and finalization
ARC_COMPLETION_THRESHOLD = 15


class ArcTransitionManager:
    """Manage arc completion, mainline selection, and next arc initialization."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """
        Initialize the arc transition manager.
        
        Args:
            story: The story being managed
            generator: TextGenerator for AI-based tasks
        """
        self.story = story
        self.generator = generator
    
    async def check_and_handle_arc_completion(
        self,
        arc_id: str,
        episode_number: int
    ) -> Optional[str]:
        """
        Check if arc is complete after episode finalization.
        
        When episode {ARC_COMPLETION_THRESHOLD} completes, this method:
        1. Finalizes the current arc (mark mainline, archive branches)
        2. Determines next arc to use (activate existing or generate new)
        3. Feeds previous arc context to next arc
        4. Returns the next arc ID
        
        Args:
            arc_id: The arc ID that just completed an episode
            episode_number: The episode number that just completed
            
        Returns:
            The next arc ID to use, or None if no next arc available
        """
        arc = StoryArc.load(self.story.id, arc_id)
        if not arc:
            logger.warning(f"Arc {arc_id} not found during completion check")
            return None
        
        logger.info(f"Checking arc completion: arc={arc_id}, episode={episode_number}")
        
        # Check if this episode triggers arc completion
        if episode_number != ARC_COMPLETION_THRESHOLD:
            logger.debug(f"Arc not yet complete (episode {episode_number}/{ARC_COMPLETION_THRESHOLD})")
            return None
        
        logger.info(f"Arc {arc_id} has completed {ARC_COMPLETION_THRESHOLD} episodes, finalizing...")
        
        # Step 1: Finalize current arc (select mainline, archive branches)
        await self._finalize_arc(arc_id)
        
        # Step 2: Determine next arc
        next_arc_id = await self._get_or_create_next_arc(arc_id)
        
        if next_arc_id:
            # Step 3: Feed context from current arc to next arc
            await self._feed_context_to_next_arc(arc_id, next_arc_id)
            logger.info(f"Arc transition complete: {arc_id} -> {next_arc_id}")
        else:
            logger.warning(f"No next arc available for {arc_id}")
        
        return next_arc_id
    
    async def _finalize_arc(self, arc_id: str) -> None:
        """
        Finalize the arc by marking mainline segments and archiving branches.
        
        Steps:
        1. Find all branches in the arc (divergent paths from user choices)
        2. Determine the "mainline" (most followed/canonical path)
        3. Mark all mainline segments with is_mainline=True
        4. Archive alternative branch segments
        5. Mark arc as finalized
        
        Args:
            arc_id: The arc ID to finalize
        """
        try:
            arc = StoryArc.load(self.story.id, arc_id)
            if not arc:
                logger.warning(f"Arc {arc_id} not found for finalization")
                return
            
            logger.debug(f"Finalizing arc {arc_id}")
            
            # 1. Find all branches
            all_segments = self.story.get_all_segments()
            arc_segments = [s for s in all_segments if s.arc_id == arc_id]
            
            if not arc_segments:
                logger.warning(f"No segments found for arc {arc_id}")
                return
            
            # 2. Determine mainline (select primary path)
            # For now: longest path (most segments) = most developed = mainline
            mainline_segments = self._determine_mainline(arc_segments)
            mainline_ids = {seg.id for seg in mainline_segments}
            
            # 3. Mark mainline segments
            for seg in mainline_segments:
                seg.is_mainline = True
                seg.save()
            
            logger.info(f"Marked {len(mainline_ids)} segments as mainline in arc {arc_id}")
            
            # 4. Archive non-mainline segments (alternative branches)
            for seg in arc_segments:
                if seg.id not in mainline_ids:
                    seg.status = SegmentStatus.ARCHIVED
                    seg.save()
            
            archived_count = len(arc_segments) - len(mainline_ids)
            logger.info(f"Archived {archived_count} non-mainline segments in arc {arc_id}")
            
            # 5. Mark arc as finalized
            arc.is_finalized = True
            arc.mainline_segment_count = len(mainline_ids)
            arc.save()
            
            logger.info(f"Arc {arc_id} finalized with {len(mainline_ids)} mainline segments")
        
        except Exception as e:
            logger.error(f"Failed to finalize arc {arc_id}: {e}", exc_info=True)
    
    def _determine_mainline(self, arc_segments: List[StorySegment]) -> List[StorySegment]:
        """
        Determine which segments form the mainline (primary narrative path).
        
        Algorithm:
        1. Build parent-child relationships between segments
        2. Find all leaf nodes (segments with no children in arc)
        3. Walk backward from each leaf to find paths
        4. Return the longest path (most developed = canonical)
        
        Args:
            arc_segments: All segments in the arc
            
        Returns:
            List of segments in the mainline path
        """
        if not arc_segments:
            return []
        
        # Build parent->child mapping
        segment_map = {seg.id: seg for seg in arc_segments}
        parent_to_children = {}
        
        for seg in arc_segments:
            if seg.parent_segment_id:
                if seg.parent_segment_id not in parent_to_children:
                    parent_to_children[seg.parent_segment_id] = []
                parent_to_children[seg.parent_segment_id].append(seg.id)
        
        # Find leaf nodes (segments with no children)
        leaf_segments = [
            seg for seg in arc_segments
            if seg.id not in parent_to_children
        ]
        
        if not leaf_segments:
            # No leaves found, use last segment by ID
            leaf_segments = [max(arc_segments, key=lambda s: s.id)]
        
        # Walk backward from each leaf to find full paths
        paths = []
        for leaf_seg in leaf_segments:
            path = self._walk_backward_to_root(leaf_seg, segment_map)
            paths.append(path)
        
        # Return longest path (most developed)
        mainline = max(paths, key=len) if paths else []
        
        logger.debug(f"Found {len(paths)} paths, selected mainline with {len(mainline)} segments")
        
        return mainline
    
    def _walk_backward_to_root(
        self,
        segment: StorySegment,
        segment_map: Dict[str, StorySegment]
    ) -> List[StorySegment]:
        """
        Walk backward from a segment to the root, building the full path.
        
        Args:
            segment: The segment to start from (leaf)
            segment_map: Map of segment ID -> segment
            
        Returns:
            List of segments from root to leaf
        """
        path = [segment]
        current = segment
        
        while current.parent_segment_id and current.parent_segment_id in segment_map:
            current = segment_map[current.parent_segment_id]
            path.insert(0, current)
        
        return path
    
    async def _get_or_create_next_arc(self, completed_arc_id: str) -> Optional[str]:
        """
        Get the next arc to use, either from future arcs or create new ones.
        
        Steps:
        1. Check if future arcs exist (generated during current arc)
        2. If yes: activate the first one
        3. If no: generate 3 new future arcs
        4. Return the next arc ID
        
        Args:
            completed_arc_id: The arc that just completed
            
        Returns:
            The ID of the next arc to use, or None if generation failed
        """
        # Look for future arcs in story
        all_arcs = self._get_all_arcs()
        future_arcs = [a for a in all_arcs if a.is_future_arc]
        
        if future_arcs:
            # Activate the first future arc
            next_arc = future_arcs[0]
            next_arc.is_future_arc = False
            next_arc.is_active = True
            next_arc.save()
            
            logger.info(f"Activated future arc {next_arc.id} as next arc")
            return next_arc.id
        else:
            # No future arcs, generate 3 new ones
            logger.info(f"No future arcs found, generating 3 new arcs...")
            try:
                next_arc_id = await self._generate_future_arcs(completed_arc_id)
                return next_arc_id
            except Exception as e:
                logger.error(f"Failed to generate future arcs: {e}", exc_info=True)
                return None
    
    async def _feed_context_to_next_arc(
        self,
        completed_arc_id: str,
        next_arc_id: str
    ) -> None:
        """
        Feed context from completed arc to next arc.
        
        Updates the next arc's context with:
        1. Reference to previous arc
        2. Summary of previous arc's mainline
        3. Evolved character descriptions from previous arc
        4. Updated location descriptions
        5. Unresolved mysteries from previous arc (new hooks for next arc)
        
        Args:
            completed_arc_id: The arc that just completed
            next_arc_id: The next arc to update with context
        """
        try:
            completed_arc = StoryArc.load(self.story.id, completed_arc_id)
            next_arc = StoryArc.load(self.story.id, next_arc_id)
            
            if not completed_arc or not next_arc:
                logger.warning(f"Failed to load arcs for context feeding: completed={completed_arc}, next={next_arc}")
                return
            
            logger.debug(f"Feeding context from arc {completed_arc_id} to arc {next_arc_id}")
            
            # 1. Set previous arc reference
            next_arc.previous_arc_id = completed_arc_id
            
            # 2. Create summary of completed arc's narrative (from mainline segments)
            arc_summary = await self._build_arc_summary(completed_arc_id)
            next_arc.previous_arc_summary = arc_summary
            
            # 3. Feed evolved character descriptions
            # Copy character descriptions from completed arc to next arc as baseline
            next_arc.episode_character_descriptions = dict(completed_arc.episode_character_descriptions)
            
            # 4. Feed evolved location descriptions
            next_arc.episode_location_descriptions = dict(completed_arc.episode_location_descriptions)
            
            # 5. Feed unresolved mysteries as new hooks
            # Add completed arc's unresolved mysteries to next arc's plot hooks
            if completed_arc.unresolved_mysteries:
                next_arc.plot_hooks.extend(completed_arc.unresolved_mysteries)
            
            # 6. Save updated next arc
            next_arc.save()
            
            logger.info(f"Successfully fed context from arc {completed_arc_id} to arc {next_arc_id}")
        
        except Exception as e:
            logger.error(f"Failed to feed context to next arc: {e}", exc_info=True)
    
    async def _build_arc_summary(self, arc_id: str) -> str:
        """
        Build a summary of the arc's narrative from mainline segments.
        
        This creates a concise summary of what happened in the arc (mainline path only)
        to provide context for the next arc.
        
        Args:
            arc_id: The arc to summarize
            
        Returns:
            A text summary of the arc
        """
        try:
            all_segments = self.story.get_all_segments()
            arc_segments = [
                s for s in all_segments
                if s.arc_id == arc_id and (s.is_mainline or not s.status == SegmentStatus.ARCHIVED)
            ]
            
            if not arc_segments:
                return f"Arc {arc_id} completed with no recorded narrative."
            
            # Build summary from segment descriptions
            summaries = []
            for seg in sorted(arc_segments, key=lambda s: s.id)[:15]:  # First 15 segments
                if seg.short_description:
                    summaries.append(seg.short_description)
            
            if summaries:
                return " ".join(summaries)
            else:
                return f"Arc {arc_id} completed with {len(arc_segments)} segments."
        
        except Exception as e:
            logger.error(f"Failed to build arc summary: {e}")
            return f"Arc {arc_id} summary unavailable."
    
    async def _generate_future_arcs(self, completed_arc_id: str) -> Optional[str]:
        """
        Generate 3 future arc outlines for the story.
        
        This uses the arc generator to create 3 potential next arcs.
        
        Args:
            completed_arc_id: The arc that just completed (for context)
            
        Returns:
            The ID of the first new arc, or None if generation failed
        """
        try:
            from app.engine.generators.arc_generator import ArcGenerator
            
            completed_arc = StoryArc.load(self.story.id, completed_arc_id)
            if not completed_arc:
                logger.warning(f"Cannot generate arcs: completed arc {completed_arc_id} not found")
                return None
            
            generator = ArcGenerator(self.story, self.generator)
            
            # Generate 3 future arcs with context from completed arc
            new_arcs = await generator.generate_future_arcs(
                previous_arc=completed_arc,
                count=3
            )
            
            if not new_arcs:
                logger.warning("Arc generator returned no new arcs")
                return None
            
            # Save the new arcs and mark as future arcs
            saved_arc_ids = []
            for arc in new_arcs:
                arc.is_future_arc = True
                arc.save()
                saved_arc_ids.append(arc.id)
                logger.debug(f"Generated and saved future arc {arc.id}")
            
            # Return the first one (will be activated as next arc)
            return saved_arc_ids[0] if saved_arc_ids else None
        
        except Exception as e:
            logger.error(f"Failed to generate future arcs: {e}", exc_info=True)
            return None
    
    def _get_all_arcs(self) -> List[StoryArc]:
        """
        Get all arcs in the story.
        
        Returns:
            List of all StoryArc objects
        """
        try:
            arc_dir = StoryArc.get_storage_dir(self.story.id)
            all_arcs = []
            
            for arc_file in arc_dir.glob("*.json"):
                arc_id = arc_file.stem
                arc = StoryArc.load(self.story.id, arc_id)
                if arc:
                    all_arcs.append(arc)
            
            return all_arcs
        except Exception as e:
            logger.error(f"Failed to load all arcs: {e}")
            return []
