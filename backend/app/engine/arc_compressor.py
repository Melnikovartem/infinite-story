"""Arc compressor for selecting mainline branch and archiving alternatives (E2-4)."""

from typing import List, Dict, Set, Optional
import logging
import random
from app.models import Story, StorySegment, StoryArc, ArcCompressionResult
from app.models.story_segment import SegmentStatus
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.arc_compressor")


class ArcCompressor:
    """Compress arc after 15+ episodes by selecting mainline and archiving alternatives."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """
        Initialize the arc compressor.
        
        Args:
            story: The story to compress
            generator: TextGenerator for AI-based selection
        """
        self.story = story
        self.generator = generator
    
    async def compress_arc(self, arc_id: str) -> Optional[ArcCompressionResult]:
        """
        Compress arc by selecting mainline and archiving alternatives.
        
        Steps:
        1. Find all branches in this arc (from user sessions)
        2. Select candidates (top N by popularity, random M)
        3. Summarize each branch
        4. Call AI to pick best (most coherent, thematic)
        5. Archive non-mainline segments
        6. Save compression result
        7. Return result
        
        Args:
            arc_id: The arc ID to compress
            
        Returns:
            ArcCompressionResult if successful, None if compression not needed
            
        Raises:
            ValueError: If arc not found
        """
        arc = StoryArc.load(self.story.id, arc_id)
        if not arc:
            raise ValueError(f"Arc {arc_id} not found")
        
        # 1. Find branches
        branches = self._find_branches_in_arc(arc_id)
        
        if len(branches) <= 1:
            # No compression needed
            logger.info(f"Arc {arc_id} has {len(branches)} branches, no compression needed")
            return None
        
        # 2. Select candidates (top 3 + random 2)
        candidates = self._select_candidates(branches)
        
        # 3. Summarize branches
        branch_summaries = []
        for branch in candidates:
            summary = await self._summarize_branch(branch)
            branch_summaries.append(summary)
        
        # 4. AI selection
        mainline_branch_idx = await self._ai_select_mainline(
            arc,
            branch_summaries
        )
        
        # 5. Archive non-mainline
        mainline_segments = set(candidates[mainline_branch_idx])
        archived_segments = []
        
        for i, candidate in enumerate(candidates):
            if i != mainline_branch_idx:
                # Archive these segments
                for seg_id in candidate:
                    seg = self.story.get_segment(seg_id, include_archived=True)
                    if seg:
                        seg.status = SegmentStatus.ARCHIVED
                        seg.save()
                        archived_segments.append(seg_id)
                        logger.debug(f"Archived segment {seg_id}")
        
        # 6. Save compression result
        result = ArcCompressionResult(
            arc_id=arc_id,
            mainline_branch_segments=list(mainline_segments),
            archived_segments=archived_segments,
            selection_rationale="Branch selected by AI analysis for narrative coherence and thematic consistency"
        )
        
        # 7. Mark arc as compressed
        arc.is_compressed = True
        arc.compression_result = result
        arc.save()
        
        logger.info(f"Compressed arc {arc_id}: archived {len(archived_segments)} segments")
        return result
    
    def _find_branches_in_arc(self, arc_id: str) -> List[List[str]]:
        """
        Find divergent branches from user sessions.
        
        For each episode in arc, find all different paths users took.
        
        Args:
            arc_id: The arc ID to find branches in
            
        Returns:
            List of branches, each branch is a list of segment IDs
        """
        all_segments = self.story.get_all_segments()
        arc_segments = [
            seg for seg in all_segments
            if seg.arc_id == arc_id
        ]
        
        if not arc_segments:
            return []
        
        # Find all root segments (no parent in this arc)
        root_segments = [
            seg for seg in arc_segments
            if not seg.parent_segment_id or self.story.get_segment(seg.parent_segment_id) is None
        ]
        
        if not root_segments:
            # If no roots, use oldest segments
            root_segments = sorted(arc_segments, key=lambda s: s.id)[:1]
        
        # Walk forward from each root to find branches
        branches = []
        for root_seg in root_segments:
            chain = self._walk_forward_from(root_seg.id)
            if chain:
                branches.append(chain)
        
        return branches if branches else [segment_id for segment_id in [seg.id for seg in arc_segments[:1]]]
    
    def _walk_forward_from(self, segment_id: str) -> List[str]:
        """
        Walk forward from segment through descendants to find branch.
        
        Args:
            segment_id: Starting segment ID
            
        Returns:
            List of segment IDs in the forward path
        """
        chain = [segment_id]
        seg = self.story.get_segment(segment_id, include_archived=True)
        
        if not seg:
            return chain
        
        # For simplicity: follow first outgoing choice if available
        if hasattr(seg, 'outgoing_choices') and seg.outgoing_choices:
            # Get first choice
            first_choice_id = next(iter(seg.outgoing_choices.keys()), None)
            if first_choice_id:
                first_choice = seg.outgoing_choices[first_choice_id]
                if first_choice.to_segment_id:
                    # Recursively walk forward
                    next_chain = self._walk_forward_from(first_choice.to_segment_id)
                    chain.extend(next_chain)
        
        return chain
    
    def _select_candidates(
        self,
        branches: List[List[str]]
    ) -> List[List[str]]:
        """
        Select top N branches by length + random M.
        
        Select the longest branches (most developed) plus some random ones
        for diversity.
        
        Args:
            branches: All branches in the arc
            
        Returns:
            Selected candidate branches
        """
        if len(branches) <= 3:
            return branches
        
        # Top 3 longest
        sorted_branches = sorted(
            branches,
            key=len,
            reverse=True
        )
        candidates = sorted_branches[:3]
        
        # Add random 2 from the rest
        others = sorted_branches[3:]
        if others:
            num_random = min(2, len(others))
            candidates.extend(random.sample(others, num_random))
        
        return candidates
    
    async def _summarize_branch(self, branch: List[str]) -> str:
        """
        Create text summary of a branch.
        
        Args:
            branch: List of segment IDs in the branch
            
        Returns:
            Text summary of the branch
        """
        segments = []
        for seg_id in branch:
            seg = self.story.get_segment(seg_id, include_archived=True)
            if seg:
                segments.append(seg)
        
        summaries = []
        for seg in segments[:5]:  # First 5 scenes
            overview = seg.short_description if hasattr(seg, 'short_description') else f"Segment {seg.id}"
            summaries.append(overview)
        
        summary = f"""
Branch with {len(branch)} segments:
{chr(10).join(summaries)}
{"..." if len(segments) > 5 else ""}
"""
        return summary
    
    async def _ai_select_mainline(
        self,
        arc: StoryArc,
        branch_summaries: List[str]
    ) -> int:
        """
        Ask AI which branch is best for mainline.
        
        Args:
            arc: The story arc being compressed
            branch_summaries: Summaries of candidate branches
            
        Returns:
            Index of the selected mainline branch
        """
        
        prompt = f"""
You are a narrative architect selecting a canonical storyline.

ARC: {arc.title}
Premise: {arc.premise}
Direction: {arc.narrative_direction}

We have {len(branch_summaries)} divergent branches.
Select which should be the mainline (canon) version.

Consider:
1. Narrative coherence with arc premise
2. Character development consistency
3. Thematic resonance
4. Story momentum and pacing

BRANCH OPTIONS:
{chr(10).join([
    f"Branch {i}: {summary}"
    for i, summary in enumerate(branch_summaries)
])}

Respond with JSON:
{{
    "selected_branch": 0,
    "reasoning": "Why this branch is the most coherent mainline..."
}}
"""
        
        response = await self.generator.generate(
            system_prompt="",
            user_prompt=prompt,
            context_type="scene"
        )
        
        if response.error:
            logger.warning(f"AI branch selection failed: {response.error}, selecting longest branch")
            return 0
        
        # Try to extract selected_branch (would be in response fields)
        selected = getattr(response, 'selected_branch', 0)
        if isinstance(selected, int) and 0 <= selected < len(branch_summaries):
            logger.info(f"AI selected branch {selected}")
            return selected
        
        logger.info("AI response unclear, selecting longest branch")
        return 0
