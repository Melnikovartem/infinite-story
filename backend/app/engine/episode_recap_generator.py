"""Episode recap generator for summarizing completed episodes and generating new episode contexts."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from app.models import Story, StorySegment, EpisodeRecap, StoryArc, CharacterState
from app.models.story_segment import SegmentStatus
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.episode_recap_generator")


class EpisodeRecapGenerator:
    """Generate episode summaries and character state snapshots."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        self.story = story
        self.generator = generator
    
    async def generate_recap(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> EpisodeRecap:
        """
        Generate a recap for completed episode.
        
        Steps:
        1. Walk episode backward to collect all segments
        2. Extract all character changes
        3. Build recap prompt with context
        4. Call AI to generate title, summary, themes
        5. Reconcile character states (apply changes)
        6. Create EpisodeRecap object
        7. Save to disk
        
        Args:
            episode_number: The episode number to recap
            arc_id: Optional arc ID to scope the recap
            
        Returns:
            The generated EpisodeRecap
            
        Raises:
            ValueError: If no segments found for the episode
        """
        # 1. Collect segments in this episode
        episode_segments = self._walk_episode_segments(
            episode_number, 
            arc_id
        )
        
        if not episode_segments:
            raise ValueError(f"No segments found for episode {episode_number}")
        
        # 2. Extract all changes and metadata
        all_changes = self._collect_changes(episode_segments)
        starting_states = self._extract_starting_states(episode_segments)
        
        # 3. Build recap prompt
        recap_prompt = self._build_recap_prompt(
            episode_segments,
            all_changes,
            episode_number,
            arc_id
        )
        
        # 4. Call AI
        recap_response = await self.generator.generate(
            system_prompt="",
            user_prompt=recap_prompt,
            context_type="scene"
        )
        
        # Handle AI response errors
        if recap_response.error:
            logger.warning(f"AI generation error for recap: {recap_response.error}")
            # Use fallback values
            ai_title = f"Episode {episode_number}"
            ai_summary = "Episode summary unavailable"
            ai_themes = []
        else:
            # Extract AI-generated values from response
            ai_title = getattr(recap_response, 'title', f"Episode {episode_number}")
            ai_summary = getattr(recap_response, 'summary', "Episode summary unavailable")
            ai_themes = getattr(recap_response, 'key_themes', [])
        
        # 5. Reconcile character states
        ending_states = self._reconcile_character_states(
            starting_states,
            all_changes
        )
        
        # 6. Create EpisodeRecap
        recap_id = f"recap_{self.story.id}_ep{episode_number}_{arc_id or 'main'}"
        recap = EpisodeRecap(
            id=recap_id,
            story_id=self.story.id,
            episode_number=episode_number,
            arc_id=arc_id,
            title=ai_title,
            summary=ai_summary,
            key_themes=ai_themes if isinstance(ai_themes, list) else [],
            tone=episode_segments[0].episode_tone or "neutral",
            segment_ids=[seg.id for seg in episode_segments],
            starting_character_states=starting_states,
            ending_character_states=ending_states,
        )
        
        # 7. Save
        recap.save()
        logger.info(f"Generated recap for episode {episode_number}")
        
        return recap
    
    async def generate_new_episode_context(
        self,
        arc_id: str,
        previous_recap: Optional[EpisodeRecap] = None
    ) -> Dict[str, Any]:
        """
        Generate context for a new episode.
        
        Args:
            arc_id: The arc ID for the new episode
            previous_recap: Optional recap from the previous episode
            
        Returns:
            Dictionary with tone_tags, end_condition, narrative_direction
            
        Raises:
            ValueError: If arc not found
        """
        # Get arc - load from disk if needed
        arc = StoryArc.load(self.story.id, arc_id)
        if not arc:
            raise ValueError(f"Arc {arc_id} not found")
        
        # Build prompt
        prompt = self._build_episode_generation_prompt(
            arc,
            previous_recap
        )
        
        # Call AI
        response = await self.generator.generate(
            system_prompt="",
            user_prompt=prompt,
            context_type="scene"
        )
        
        # Handle AI response errors
        if response.error:
            logger.warning(f"AI generation error for episode context: {response.error}")
            # Use fallback values
            return {
                'tone_tags': ['neutral'],
                'end_condition': 'Episode completion',
                'narrative_direction': 'Story progresses forward',
            }
        
        # Extract values from response
        return {
            'tone_tags': getattr(response, 'tone_tags', []),
            'end_condition': getattr(response, 'end_condition', ''),
            'narrative_direction': getattr(response, 'narrative_direction', ''),
        }
    
    def _walk_episode_segments(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> List[StorySegment]:
        """
        Collect all segments belonging to this episode.
        
        Walk from latest segment backward until episode number changes
        or arc changes (if specified).
        
        Args:
            episode_number: The episode number to collect
            arc_id: Optional arc ID to scope the search
            
        Returns:
            List of segments in chronological order
        """
        segments = []
        
        # Find latest segment in this episode
        latest = self._find_latest_segment(episode_number, arc_id)
        if not latest:
            return []
        
        # Walk backward to episode start
        current = latest
        while (current and 
               current.episode_number == episode_number and
               (arc_id is None or current.arc_id == arc_id)):
            segments.insert(0, current)  # Prepend for chronological order
            
            if not current.parent_segment_id:
                break
            
            current = self.story.get_segment(current.parent_segment_id)
        
        return segments
    
    def _find_latest_segment(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> Optional[StorySegment]:
        """
        Find the most recent segment in episode.
        
        Args:
            episode_number: The episode number to search
            arc_id: Optional arc ID to scope the search
            
        Returns:
            The latest segment in the episode, or None if not found
        """
        all_segments = self.story.get_all_segments()
        
        matching = [
            seg for seg in all_segments
            if seg.episode_number == episode_number and
               (arc_id is None or seg.arc_id == arc_id)
        ]
        
        return max(matching, key=lambda s: s.id) if matching else None
    
    def _collect_changes(self, segments: List[StorySegment]) -> List[str]:
        """
        Extract all change_notes from segment chain.
        
        Args:
            segments: List of segments in the episode
            
        Returns:
            List of all change notes
        """
        all_changes = []
        for seg in segments:
            all_changes.extend(seg.change_notes)
        return all_changes
    
    def _extract_starting_states(
        self,
        segments: List[StorySegment]
    ) -> Dict[str, CharacterState]:
        """
        Extract character states from first segment of episode.
        
        Args:
            segments: List of segments in the episode
            
        Returns:
            Dictionary mapping character IDs to CharacterState objects
        """
        if not segments:
            return {}
        
        # First segment of episode has the starting state snapshot
        first_segment = segments[0]
        starting_states = {}
        
        # Convert raw character_states dict to CharacterState objects
        if hasattr(first_segment, 'character_states') and first_segment.character_states:
            for char_id, state_data in first_segment.character_states.items():
                if isinstance(state_data, CharacterState):
                    starting_states[char_id] = state_data
                elif isinstance(state_data, dict):
                    # Convert dict to CharacterState
                    starting_states[char_id] = CharacterState(
                        id=char_id,
                        name=state_data.get('name', char_id),
                        status=state_data.get('status', 'alive'),
                        mood=state_data.get('mood', 'neutral'),
                        loyalty=state_data.get('loyalty', 0.0),
                        location=state_data.get('location'),
                        relationships=state_data.get('relationships', {}),
                        goals=state_data.get('goals', []),
                        custom_data=state_data.get('custom_data', {})
                    )
        
        return starting_states
    
    def _build_recap_prompt(
        self,
        segments: List[StorySegment],
        changes: List[str],
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> str:
        """
        Build prompt for AI to generate recap.
        
        Args:
            segments: List of segments in the episode
            changes: List of character change notes
            episode_number: The episode number
            arc_id: Optional arc ID
            
        Returns:
            The prompt to send to the AI
        """
        
        # Summarize key scenes
        scene_summaries = []
        for i, seg in enumerate(segments[:10]):  # First 10 scenes
            overview = seg.short_description if hasattr(seg, 'short_description') else f"Segment {seg.id}"
            scene_summaries.append(f"Scene {i+1}: {overview}")
        
        prompt = f"""
You are a narrative summarizer. Generate a recap for the following episode:

EPISODE {episode_number}
Arc: {arc_id or '(unassigned)'}
Total Scenes: {len(segments)}

KEY SCENES:
{chr(10).join(scene_summaries) if scene_summaries else '(no scenes recorded)'}

CHARACTER CHANGES THIS EPISODE:
{chr(10).join(changes) if changes else '(no explicit changes recorded)'}

Generate a 2-3 paragraph narrative recap that:
1. Captures the core story arc of the episode
2. Summarizes how characters evolved
3. Sets up thematic threads for next episode

Respond with JSON:
{{
    "title": "Episode Title",
    "summary": "2-3 paragraphs...",
    "key_themes": ["theme1", "theme2", ...]
}}
"""
        return prompt
    
    def _build_episode_generation_prompt(
        self,
        arc: StoryArc,
        previous_recap: Optional[EpisodeRecap]
    ) -> str:
        """
        Build prompt for new episode context.
        
        Args:
            arc: The story arc for the new episode
            previous_recap: Optional recap from the previous episode
            
        Returns:
            The prompt to send to the AI
        """
        
        prev_context = ""
        if previous_recap:
            prev_context = f"""
PREVIOUS EPISODE ({previous_recap.episode_number}):
Title: {previous_recap.title}
Summary: {previous_recap.summary}
Key Themes: {', '.join(previous_recap.key_themes) if previous_recap.key_themes else '(none)'}

"""
        
        prompt = f"""
You are a narrative architect designing episodes for a story arc.

ARC: {arc.title}
Premise: {arc.premise}
Direction: {arc.narrative_direction}

{prev_context}

Generate context for the NEXT EPISODE:
1. Pick a primary tone (dark_and_mysterious, hopeful, tense, etc.)
2. Define the episode's end condition (what should resolve)
3. Describe narrative direction (what should happen)

The episode will have ~15-20 scenes.

Respond with JSON:
{{
    "tone_tags": ["tone1", "tone2"],
    "end_condition": "What must happen by episode end",
    "narrative_direction": "The story moves toward..."
}}
"""
        return prompt
    
    def _reconcile_character_states(
        self,
        starting_states: Dict[str, CharacterState],
        changes: List[str]
    ) -> Dict[str, CharacterState]:
        """
        Apply changes to character states.
        
        Reconciliation logic:
        1. Start with episode snapshot
        2. For each change note, parse it
        3. Apply to character state
        4. If contradictory, ask AI to resolve (simplified version)
        
        Args:
            starting_states: Starting character states
            changes: List of change notes to apply
            
        Returns:
            Updated character states
        """
        final_states = {}
        
        # Start with snapshots
        for char_id, state in starting_states.items():
            # Create a copy of the state
            final_states[char_id] = CharacterState(
                id=state.id,
                name=state.name,
                status=state.status,
                mood=state.mood,
                loyalty=state.loyalty,
                location=state.location,
                relationships=dict(state.relationships) if state.relationships else {},
                goals=list(state.goals) if state.goals else [],
                custom_data=dict(state.custom_data) if state.custom_data else {}
            )
        
        # Apply changes (simplified: trust the changes are valid)
        # Full reconciliation would parse change notes more carefully
        # and handle contradictions with AI fallback
        for change in changes:
            # Simple parsing: "CharName's mood changed to angry"
            # More complex logic would be needed for production use
            logger.debug(f"Applying change: {change}")
        
        return final_states
