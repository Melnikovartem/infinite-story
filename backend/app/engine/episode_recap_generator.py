"""Episode recap generator for summarizing completed episodes and generating new episode contexts."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from app.models import Story, StorySegment, StoryArc
from app.models.story_episode import StoryEpisode as EpisodeRecap, CharacterState
from app.models.story_segment import SegmentStatus
from app.engine.generator import TextGenerator
from app.engine.character_state_updater import CharacterStateUpdater
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.episode_recap_generator")


# Schema for episode recap parsing
RECAP_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("title", type="str", required=True, aliases=["episode_title", "name"]),
        FieldSpec("summary", type="str", required=True, aliases=["recap", "description", "overview"]),
        FieldSpec("key_themes", type="list", aliases=["themes", "major_themes"]),
        FieldSpec("themes_explored", type="list", aliases=["explored_themes", "themes_covered"]),
        FieldSpec("hook_for_next", type="str", aliases=["hook", "next_episode_hook", "bridge", "cliffhanger"]),
        FieldSpec("unresolved_new", type="list", aliases=["unresolved", "new_mysteries", "questions", "mysteries"]),
    ],
    expect_array=False,
)


class EpisodeRecapGenerator:
    """Generate episode summaries and character state snapshots."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        self.story = story
        self.generator = generator
    
    async def generate_recap(
        self,
        episode_number: int,
        arc_id: Optional[str] = None,
        triggering_segment_id: Optional[str] = None
    ) -> EpisodeRecap:
        """
        Generate a recap for a completed episode by updating its existing StoryEpisode.
        
        The recap is stored ON the existing episode meta (single object per episode).
        The recap text will later be copied into the NEXT episode's
        previous_episode_recap field for LLM context continuity.
        
        Steps:
        1. Walk episode backward to collect all segments
        2. Extract all character changes
        3. Load existing EpisodeMeta (created at episode start)
        4. Build enhanced recap prompt
        5. Call AI to generate title, summary, themes_explored, hook, mysteries
        6. Reconcile character states
        7. Update the existing EpisodeMeta with recap fields
        8. Update character states via CharacterStateUpdater
        9. Save
        
        Args:
            episode_number: The episode number to recap
            arc_id: Optional arc ID to scope the recap
            triggering_segment_id: Segment that triggered the transition (for ID lookup)
            
        Returns:
            The updated EpisodeRecap (same object as the meta)
            
        Raises:
            ValueError: If no segments found for the episode
        """
        from app.models.story_episode import StoryEpisode as EpisodeMeta
        
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
        
        # 3. Try to load existing EpisodeMeta (created when this episode started)
        episode_meta = None
        selected_themes = []
        
        # Try to find by various ID patterns (transition-based or sequential)
        meta_id_candidates = []
        if triggering_segment_id and arc_id:
            meta_id_candidates.append(f"episode_{arc_id}_{triggering_segment_id}")
        if arc_id:
            meta_id_candidates.append(f"episode_meta_{episode_number}_{arc_id}")
        
        for meta_id in meta_id_candidates:
            try:
                episode_meta = EpisodeMeta.load(self.story.id, meta_id)
                if episode_meta:
                    selected_themes = episode_meta.selected_themes
                    logger.debug(f"Loaded EpisodeMeta '{meta_id}', selected themes: {selected_themes}")
                    break
            except Exception as e:
                logger.debug(f"EpisodeMeta '{meta_id}' not found: {e}")
        
        # 4. Build enhanced recap prompt with theme extraction
        recap_prompt = self._build_recap_prompt(
            episode_segments,
            all_changes,
            episode_number,
            arc_id
        )
        
        # Add theme extraction request to prompt
        recap_prompt += f"""

SELECTED THEMES FOR THIS EPISODE:
{', '.join(selected_themes)}

Additionally, extract:
- THEMES_EXPLORED: Which of the selected themes were actually explored?
- HOOK_FOR_NEXT: A bridging sentence to the next episode
- UNRESOLVED_NEW: Any NEW mysteries/questions raised this episode
"""
        
        # 5. Call AI via generate_structured
        logger.debug(f"Calling AI for episode {episode_number} recap generation")
        fallback = {
            "title": f"Episode {episode_number}",
            "summary": "Episode summary unavailable",
            "key_themes": [],
            "themes_explored": [],
            "hook_for_next": "",
            "unresolved_new": [],
        }
        recap_data = await self.generator.generate_structured(
            system_prompt="",
            user_prompt=recap_prompt,
            schema=RECAP_SCHEMA,
            fallback_defaults=[fallback],
        )
        
        ai_title = recap_data.get('title', fallback['title'])
        ai_summary = recap_data.get('summary', fallback['summary'])
        ai_themes = recap_data.get('key_themes', fallback['key_themes'])
        ai_themes_explored = recap_data.get('themes_explored', fallback['themes_explored'])
        ai_hook_for_next = recap_data.get('hook_for_next', fallback['hook_for_next'])
        ai_unresolved_new = recap_data.get('unresolved_new', fallback['unresolved_new'])
        
        # 6. Reconcile character states
        ending_states = self._reconcile_character_states(
            starting_states,
            all_changes
        )
        
        # 7. Update existing EpisodeMeta with recap fields (or create if not found)
        recap_short = f"{ai_title}: {ai_summary[:200]}" if ai_summary else ai_title
        
        if episode_meta:
            # Update existing meta with recap data
            episode_meta.recap = recap_short
            episode_meta.title = ai_title
            episode_meta.summary = ai_summary
            episode_meta.key_themes = selected_themes if selected_themes else (ai_themes if isinstance(ai_themes, list) else [])
            episode_meta.tone = episode_segments[0].episode_tone or "neutral"
            episode_meta.segment_ids = [seg.id for seg in episode_segments]
            episode_meta.start_segment_id = episode_segments[0].id
            episode_meta.end_segment_id = episode_segments[-1].id
            episode_meta.starting_character_states = starting_states
            episode_meta.ending_character_states = ending_states
            episode_meta.themes_explored = ai_themes_explored if isinstance(ai_themes_explored, list) else []
            episode_meta.hook_for_next = ai_hook_for_next
            episode_meta.unresolved_new = ai_unresolved_new if isinstance(ai_unresolved_new, list) else []
            episode_meta.episode_complete = True
            episode_meta.segment_count = len(episode_segments)
            recap = episode_meta
        else:
            # No existing meta found — create one (backward compatibility)
            recap_id = f"episode_{arc_id or 'main'}_{episode_segments[-1].id}"
            recap = EpisodeRecap(
                story=self.story,
                id=recap_id,
                story_id=self.story.id,
                episode_number=episode_number,
                arc_id=arc_id or "main",
                recap=recap_short,
                title=ai_title,
                summary=ai_summary,
                key_themes=selected_themes if selected_themes else (ai_themes if isinstance(ai_themes, list) else []),
                tone=episode_segments[0].episode_tone or "neutral",
                segment_ids=[seg.id for seg in episode_segments],
                start_segment_id=episode_segments[0].id,
                end_segment_id=episode_segments[-1].id,
                starting_character_states=starting_states,
                ending_character_states=ending_states,
                themes_explored=ai_themes_explored if isinstance(ai_themes_explored, list) else [],
                hook_for_next=ai_hook_for_next,
                unresolved_new=ai_unresolved_new if isinstance(ai_unresolved_new, list) else [],
                episode_complete=True,
                segment_count=len(episode_segments),
            )
        
        # 8. Update character states based on episode events
        try:
            updater = CharacterStateUpdater(self.story, self.generator)
            character_updates = await updater.update_character_states(
                episode_number=episode_number,
                arc_id=arc_id,
                segment_ids=episode_segments,
                prev_recap=recap
            )
            logger.info(f"Updated states for {len(character_updates)} characters after episode {episode_number}")
        except Exception as e:
            logger.warning(f"Failed to update character states: {e}")
        
        # 9. Check themes and generate new characters if needed
        try:
            updater = CharacterStateUpdater(self.story, self.generator)
            for theme in recap.themes_explored:
                new_char = await updater.generate_new_character_for_theme(
                    theme=theme,
                    arc_id=arc_id,
                    episode_number=episode_number
                )
                if new_char:
                    new_char.save()
                    logger.info(f"Generated new character '{new_char.name}' for theme '{theme}'")
        except Exception as e:
            logger.warning(f"Failed to generate new characters: {e}")
        
        # 10. Save
        recap.save()
        logger.info(f"Generated recap for episode {episode_number}: {ai_title}")
        
        return recap
    
    async def generate_new_episode_context(
        self,
        arc_id: str,
        previous_recap: Optional[EpisodeRecap] = None
    ) -> Dict[str, Any]:
        """
        Generate context for a new episode (E2-2 Enhanced).
        
        Steps:
        1. Load arc
        2. Select themes via ThemeSelector (weighted random)
        3. Generate episode tone/end_condition/direction via AI
        4. Create and save EpisodeMeta
        5. Return context dict
        
        Args:
            arc_id: The arc ID for the new episode
            previous_recap: Optional recap from the previous episode
            
        Returns:
            Dictionary with episode context (tone_tags, end_condition, narrative_direction,
            selected_themes, episode_focus, story_hooks)
            
        Raises:
            ValueError: If arc not found
        """
        from app.utils.theme_selector import ThemeSelector
        from app.models.story_episode import StoryEpisode as EpisodeMeta
        
        # Step 1: Get arc
        arc = StoryArc.load(self.story.id, arc_id)
        if not arc:
            raise ValueError(f"Arc {arc_id} not found")
        
        logger.info(f"Generating episode context for arc {arc_id}")
        
        # Step 2: Select themes for this episode
        # episode_count is already incremented by the caller (generate_next_scene)
        # so we use it directly as the next episode number
        next_episode_num = arc.episode_count if arc.episode_count > 0 else 1
        selected_themes = ThemeSelector.select_themes(
            arc,
            previous_recap,
            next_episode_num,
            count=2
        )
        logger.debug(f"Selected themes: {selected_themes}")
        
        # Step 3: Build enhanced prompt with arc context
        prompt = self._build_episode_generation_prompt(
            arc,
            previous_recap,
            selected_themes
        )
        
        # Step 4: Call AI via generate_structured
        logger.debug(f"Calling AI for episode {next_episode_num} context generation")
        ep_ctx_schema = ResponseSchema(
            fields=[
                FieldSpec("tone_tags", type="list", aliases=["tone", "tones"]),
                FieldSpec("end_condition", type="str", aliases=["ending", "resolution"]),
                FieldSpec("narrative_direction", type="str", aliases=["direction", "narrative"]),
                FieldSpec("episode_focus", type="str", aliases=["focus"]),
                FieldSpec("story_hooks", type="list", aliases=["hooks", "plot_hooks"]),
            ],
            expect_array=False,
        )
        ep_fallback = {
            "tone_tags": ["neutral"],
            "end_condition": "Episode completion",
            "narrative_direction": "Story progresses forward",
            "episode_focus": "",
            "story_hooks": [],
        }
        ep_data = await self.generator.generate_structured(
            system_prompt="",
            user_prompt=prompt,
            schema=ep_ctx_schema,
            fallback_defaults=[ep_fallback],
        )
        
        # Ensure tone_tags is a list
        tone_tags = ep_data.get('tone_tags', ['neutral'])
        if isinstance(tone_tags, str):
            tone_tags = [tone_tags]
        
        context = {
            'tone_tags': tone_tags,
            'end_condition': ep_data.get('end_condition', 'Episode completion'),
            'narrative_direction': ep_data.get('narrative_direction', 'Story progresses'),
            'selected_themes': selected_themes,
            'episode_focus': ep_data.get('episode_focus', ''),
            'story_hooks': ep_data.get('story_hooks', []),
        }
        
        logger.info(f"Generated episode {next_episode_num} context: {context}")
        
        # Step 5: Select active characters for this episode
        active_characters = []
        try:
            active_characters = await self._select_active_characters_for_episode(
                next_episode_num,
                arc_id,
                selected_themes,
                context
            )
            logger.info(f"Selected {len(active_characters)} active characters for episode {next_episode_num}")
        except Exception as e:
            logger.debug(f"Failed to select active characters: {e}")
        
        # Step 6: Update story objects and collect running state from previous episode
        running_state = {}
        if next_episode_num > 1:
            try:
                # First, update the story's character and location objects with final state
                self.update_story_objects_with_running_state(
                    next_episode_num - 1,
                    arc_id
                )
                logger.debug(f"Updated story objects with episode {next_episode_num - 1} end state")
                
                # Then collect the running state for EpisodeMeta
                running_state = self.collect_running_state_from_episode(
                    next_episode_num - 1,
                    arc_id
                )
                logger.debug(f"Collected running state from episode {next_episode_num - 1}")
            except Exception as e:
                logger.debug(f"Failed to update story objects/collect running state: {e}")
        
        # Step 7: Create EpisodeMeta and save it
        try:
            episode_meta = EpisodeMeta(
                story=self.story,
                id=f"episode_meta_{next_episode_num}_{arc_id}",
                story_id=self.story.id,
                episode_number=next_episode_num,
                arc_id=arc_id,
                episode_tone=context['tone_tags'][0] if context['tone_tags'] else 'neutral',
                episode_end_condition=context['end_condition'],
                narrative_direction=context['narrative_direction'],
                selected_themes=selected_themes,
                episode_focus=context.get('episode_focus', ''),
                story_hooks=context.get('story_hooks', []),
                active_characters=active_characters,
            )
            
            # Apply running state from previous episode to new episode
            if running_state:
                episode_meta = self.apply_running_state_to_episode_meta(episode_meta, running_state)
            
            episode_meta.save()
            logger.info(f"Created and saved EpisodeMeta for episode {next_episode_num}")
        except Exception as e:
            logger.error(f"Failed to create/save EpisodeMeta: {e}")
        
        return context
    
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
        
        # Sort by segment_number_in_episode (numeric), falling back to id length then id
        return max(matching, key=lambda s: (s.segment_number_in_episode or 0, len(s.id), s.id)) if matching else None
    
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
        previous_recap: Optional[EpisodeRecap],
        selected_themes: Optional[List[str]] = None
    ) -> str:
        """
        Build prompt for new episode context.
        
        Args:
            arc: The story arc for the new episode
            previous_recap: Optional recap from the previous episode
            selected_themes: Optional list of themes selected for this episode
            
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
        
        themes_context = ""
        if selected_themes:
            themes_context = f"\nSELECTED THEMES FOR THIS EPISODE: {', '.join(selected_themes)}\n"
        
        prompt = f"""
You are a narrative architect designing episodes for a story arc.

ARC: {arc.title}
Premise: {arc.premise}
Direction: {arc.narrative_direction}
{themes_context}
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
        
        # Apply changes using the simple keyword-based parser
        for change in changes:
            logger.debug(f"Applying change: {change}")
            self._apply_single_change(final_states, change)
        
        return final_states
    
    async def reconcile_character_states_with_ai(
        self,
        starting_states: Dict[str, CharacterState],
        changes: List[str]
    ) -> Dict[str, CharacterState]:
        """
        Advanced reconciliation: if changes contradict, ask AI to resolve.
        
        This method detects contradictions in character changes and uses AI
        to determine the final canonical state when conflicts exist.
        
        Example:
        - Starting: Alice is hopeful
        - Changes: "Alice loses hope", "Alice finds hope again"
        - Result: Ask AI which is final state, why
        
        Args:
            starting_states: Starting character states
            changes: List of change notes to apply
            
        Returns:
            Final character states after contradiction resolution
        """
        
        final_states = dict(starting_states)
        
        # Detect potential contradictions
        contradictions = self._detect_contradictions(changes)
        
        if contradictions:
            # Ask AI to resolve
            logger.info(f"Detected {len(contradictions)} contradictions, requesting AI resolution")
            resolution = await self._resolve_contradictions_with_ai(
                starting_states,
                changes,
                contradictions
            )
            # Apply resolution
            final_states = resolution
        else:
            # Simple: apply all changes in order
            for change in changes:
                self._apply_single_change(final_states, change)
        
        return final_states
    
    def _detect_contradictions(self, changes: List[str]) -> List[tuple]:
        """
        Find contradictory statements in change notes.
        
        Args:
            changes: List of change notes to analyze
            
        Returns:
            List of tuples (change1, change2) that contradict
        """
        contradictions = []
        
        for i, change1 in enumerate(changes):
            for change2 in changes[i+1:]:
                if self._are_contradictory(change1, change2):
                    contradictions.append((change1, change2))
        
        return contradictions
    
    def _are_contradictory(self, change1: str, change2: str) -> bool:
        """
        Simple check: do these changes contradict?
        
        Uses keyword-based detection for common contradictions.
        
        Args:
            change1: First change note
            change2: Second change note
            
        Returns:
            True if changes are contradictory
        """
        # Keyword-based: "dead" vs "alive", "betrays" vs "trusts", etc.
        # Note: order matters - check both directions
        contradictory_pairs = [
            (["dies", "dead"], ["alive", "survives", "lives"]),
            (["alive", "survives", "lives"], ["dies", "dead"]),
            (["betrays"], ["trusts"]),
            (["trusts"], ["betrays"]),
            (["hates"], ["loves"]),
            (["loves"], ["hates"]),
            (["loses hope"], ["gains hope", "finds hope"]),
            (["gains hope", "finds hope"], ["loses hope"]),
        ]
        
        lower1 = change1.lower()
        lower2 = change2.lower()
        
        for group1, group2 in contradictory_pairs:
            has_word1 = any(word in lower1 for word in group1)
            has_word2 = any(word in lower2 for word in group2)
            if has_word1 and has_word2:
                return True
        
        return False
    
    async def _resolve_contradictions_with_ai(
        self,
        starting_states: Dict[str, CharacterState],
        changes: List[str],
        contradictions: List[tuple]
    ) -> Dict[str, CharacterState]:
        """
        Ask AI to resolve character state contradictions.
        
        Args:
            starting_states: Initial character states
            changes: All change notes
            contradictions: List of contradictory change pairs
            
        Returns:
            Final resolved character states
        """
        
        prompt = f"""
You are a narrative reconciler. Resolve character state contradictions.

Starting State:
{str(starting_states)}

Changes recorded:
{chr(10).join(changes)}

Contradictions to resolve:
{chr(10).join([f"- '{c1}' vs '{c2}'" for c1, c2 in contradictions])}

For each contradiction, decide which is the final state
(the one that actually happened in the story). Respond with the final
character states as JSON object mapping character IDs to their final states.

{{
    "char_1": {{"status": "alive", "mood": "determined", ...}},
    ...
}}
"""
        
        # Use generate_structured with a minimal schema — the real structure is dynamic
        # (character IDs as keys), so we just need the raw parsed dict
        reconcile_schema = ResponseSchema(
            fields=[
                FieldSpec("__any__", type="dict"),  # Dynamic keys
            ],
            expect_array=False,
        )
        
        try:
            parsed = await self.generator.generate_structured(
                system_prompt="",
                user_prompt=prompt,
                schema=reconcile_schema,
                fallback_defaults=[{}],
            )
            
            if not parsed:
                logger.warning("Empty AI reconciliation response, using starting states")
                return starting_states
            
            # Convert parsed data back into CharacterState objects
            resolved_states = {}
            for char_id, state_data in parsed.items():
                if isinstance(state_data, dict):
                    base = starting_states.get(char_id)
                    if base:
                        resolved_states[char_id] = CharacterState(
                            id=char_id,
                            name=base.name,
                            status=state_data.get('status', base.status),
                            mood=state_data.get('mood', base.mood),
                            loyalty=state_data.get('loyalty', base.loyalty),
                            location=state_data.get('location', base.location),
                            relationships=state_data.get('relationships', base.relationships),
                            goals=state_data.get('goals', base.goals),
                            custom_data=state_data.get('custom_data', base.custom_data)
                        )
                    else:
                        resolved_states[char_id] = CharacterState(
                            id=char_id,
                            name=state_data.get('name', char_id),
                            status=state_data.get('status', 'alive'),
                            mood=state_data.get('mood', 'neutral'),
                        )
            # Merge: keep starting states for chars not in resolution
            for char_id, state in starting_states.items():
                if char_id not in resolved_states:
                    resolved_states[char_id] = state
            return resolved_states
        except Exception as e:
            logger.error(f"Failed to parse AI reconciliation response: {e}")
            return starting_states
    
    def _apply_single_change(
        self,
        character_states: Dict[str, CharacterState],
        change: str
    ) -> None:
        """
        Apply a single change note to character states.
        
        Simple parsing of change notes to update character state.
        Production version would use NLP for more sophisticated parsing.
        
        Args:
            character_states: Dictionary of character states to update
            change: Change note to apply
        """
        # Simple parsing: "CharName's mood changed to angry"
        # Look for pattern: "<name> <property> <new_value>"
        lower_change = change.lower()
        
        # Try to identify character (very simple heuristic)
        for char_id, state in character_states.items():
            char_name_lower = state.name.lower()
            if char_name_lower in lower_change:
                # Character mentioned in change
                
                # Check for status/death keywords
                status_keywords = {
                    "alive": ["alive", "survives", "survives the"],
                    "dead": ["dies", "dead", "death"],
                    "missing": ["missing", "lost"]
                }
                
                for status, keywords in status_keywords.items():
                    if any(kw in lower_change for kw in keywords):
                        state.status = status
                        logger.debug(f"Updated {state.name}'s status to {status}")
                        break
                
                # Check for mood keywords
                mood_keywords = {
                    "angry": ["angry", "anger", "enraged"],
                    "hopeful": ["hopeful", "hope"],
                    "desperate": ["desperate", "despair"],
                    "determined": ["determined", "determination"],
                    "sad": ["sad", "sadness"],
                    "happy": ["happy", "happiness", "happy"],
                    "neutral": ["neutral"]
                }
                
                for mood, keywords in mood_keywords.items():
                    if any(kw in lower_change for kw in keywords):
                        # Check if it's a positive or negative change
                        if "loses" in lower_change or "no longer" in lower_change:
                            # Opposite of mentioned mood
                            continue
                        state.mood = mood
                        logger.debug(f"Updated {state.name}'s mood to {mood}")
                        break
                
                if "location" in lower_change or "goes to" in lower_change or "moves to" in lower_change:
                    # Simple location extraction (would need NLP for production)
                    logger.debug(f"Location change detected for {state.name}")
                
                break
    
    async def _select_active_characters_for_episode(
        self,
        episode_number: int,
        arc_id: Optional[str],
        selected_themes: List[str],
        episode_context: Dict[str, Any]
    ) -> List[str]:
        """Use LLM to designate most likely active characters for this episode.
        
        Args:
            episode_number: The episode number
            arc_id: The arc ID
            selected_themes: Themes selected for this episode
            episode_context: Episode generation context including tone, focus, hooks
            
        Returns:
            List of character IDs most likely to be active in this episode
        """
        try:
            logger.debug(f"Selecting active characters for episode {episode_number}")
            
            # Load arc to get character arc goals
            arc = None
            arc_goals = {}
            if arc_id:
                try:
                    arc = StoryArc.load(self.story.id, arc_id)
                    if arc:
                        arc_goals = arc.character_arc_goals
                except:
                    pass
            
            # Get all characters
            all_characters = self.story.get_all_characters()
            char_list = "\n".join([
                f"- {char.name} (ID: {char.id}): {char.description}"
                for char in all_characters
            ])
            
            # Build prompt
            prompt = f"""Given this episode context, identify 3-5 characters most likely to be active and prominent.

EPISODE {episode_number} CONTEXT:
Themes: {', '.join(selected_themes)}
Focus: {episode_context.get('episode_focus', 'General progression')}
Tone: {episode_context.get('tone_tags', ['neutral'])[0]}
End Condition: {episode_context.get('end_condition', 'Episode completion')}
Narrative Direction: {episode_context.get('narrative_direction', 'Story progresses')}
Story Hooks: {', '.join(episode_context.get('story_hooks', []))}

CHARACTER ARC GOALS:
{chr(10).join([f"- {char_id}: {goal}" for char_id, goal in arc_goals.items()])}

AVAILABLE CHARACTERS:
{char_list}

Based on the episode's themes, focus, and narrative direction, which 3-5 characters will likely be 
the most active and central to this episode? Consider:
- Which characters have arc goals that align with the episode themes?
- Who would naturally be involved in the end condition?
- Which characters fit the episode's focus and tone?

Respond with a JSON object:
{{
  "active_characters": [
    {{"character_id": "char_xxx", "reason": "brief reason they're active in this episode"}}
  ]
}}

Include exactly the character IDs. Be selective - focus on the most important characters."""
            
            active_char_schema = ResponseSchema(
                fields=[
                    FieldSpec("active_characters", type="list", required=True, aliases=["characters"]),
                ],
                expect_array=False,
            )
            result = await self.generator.generate_structured(
                system_prompt="You are a narrative director selecting which characters will be most prominent in an episode.",
                user_prompt=prompt,
                schema=active_char_schema,
                fallback_defaults=[{"active_characters": []}],
            )
            
            # Extract character IDs from the parsed result
            active_chars = result.get("active_characters", [])
            active_ids = []
            for char in active_chars:
                if isinstance(char, dict):
                    cid = char.get("character_id")
                    if cid:
                        active_ids.append(cid)
                elif isinstance(char, str):
                    active_ids.append(char)
            
            logger.debug(f"Selected {len(active_ids)} active characters for episode {episode_number}: {active_ids}")
            return active_ids
            
        except Exception as e:
            logger.warning(f"Failed to select active characters for episode: {e}")
            return []
    
    def collect_running_state_from_episode(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect all running state changes from segments in a completed episode.
        
        This method walks all segments in an episode and collects:
        - Character running_status updates
        - Location running_status updates
        - All change_notes (narrative events like "Knight lost cursed_sword")
        
        The collected state represents the final state after all segments in the episode.
        This is used to update the next episode's EpisodeMeta with the accumulated state.
        
        Args:
            episode_number: The episode number to collect running state from
            arc_id: Optional arc ID to scope the search
            
        Returns:
            Dict with keys:
            {
                'character_states': {
                    'char_id': {
                        'name': str,
                        'description': str,
                        'emotion': str,
                        'status': str,
                        'notes': str
                    }
                },
                'location_states': {
                    'loc_id': {
                        'name': str,
                        'description': str,
                        'current_state': str
                    }
                },
                'change_notes': [list of narrative changes from all segments]
            }
        """
        character_states = {}
        location_states = {}
        change_notes = []
        
        # Get all segments in this episode
        episode_segments = self._walk_episode_segments(episode_number, arc_id)
        
        if not episode_segments:
            logger.debug(f"No segments found for episode {episode_number}, returning empty running state")
            return {'character_states': {}, 'location_states': {}, 'change_notes': []}
        
        # Collect character running status, location status, and change notes from all segments
        for segment in episode_segments:
            # Character running status (last one wins)
            for char_status in segment.characters_running_status:
                char = self.story.get_character(char_status.character_id)
                if char:
                    character_states[char_status.character_id] = {
                        'name': char.name,
                        'description': char.description,
                        'emotion': char_status.current_status.split('|')[0] if '|' in char_status.current_status else char_status.current_status,
                        'status': 'present',
                        'notes': char_status.current_status
                    }
            
            # Location running status (last one wins)
            for loc_status in segment.locations_running_status:
                loc = self.story.get_location(loc_status.location_id)
                if loc:
                    location_states[loc_status.location_id] = {
                        'name': loc.name,
                        'description': loc.description,
                        'current_state': loc_status.current_status
                    }
            
            # Collect all change_notes (narrative events)
            if segment.change_notes:
                change_notes.extend(segment.change_notes)
        
        # Collect faction state updates (based on faction_id from characters)
        faction_states = self._collect_faction_states_from_episode(episode_number, arc_id)
        
        logger.info(f"Collected running state for episode {episode_number}: "
                   f"{len(character_states)} characters, {len(location_states)} locations, "
                   f"{len(faction_states)} factions, {len(change_notes)} change notes")
        
        return {
            'character_states': character_states,
            'location_states': location_states,
            'faction_states': faction_states,
            'change_notes': change_notes
        }
    
    def apply_running_state_to_episode_meta(
        self,
        episode_meta: "EpisodeMeta",
        running_state: Dict[str, Any]
    ) -> "EpisodeMeta":
        """
        Apply collected running state from previous episode to new episode's metadata.
        
        This updates the EpisodeMeta's character_state_snapshot, location_state_snapshot,
        and previous_episode_changes with the running state from the previous episode.
        
        This ensures:
        1. Characters/locations start with state from end of previous episode
        2. LLM context includes change_notes (e.g., "Knight lost cursed_sword")
        
        Args:
            episode_meta: The EpisodeMeta to update
            running_state: Dict from collect_running_state_from_episode()
            
        Returns:
            Updated EpisodeMeta
        """
        from app.models.story_episode import StoryEpisode as EpisodeMeta
        from app.models.story_episode import CharacterStateSnapshot
        
        # Update character states
        for char_id, char_state in running_state.get('character_states', {}).items():
            if char_id not in episode_meta.character_state_snapshot:
                # Create new snapshot from running state
                try:
                    snapshot = CharacterStateSnapshot(
                        character_id=char_id,
                        health_status=char_state.get('status', ''),
                        emotional_status=char_state.get('emotion', ''),
                        relationship_notes={},
                        inventory={},
                        character_arc_goal='',
                        goal_progress=0.0,
                        goal_notes=char_state.get('notes', '')
                    )
                    episode_meta.character_state_snapshot[char_id] = snapshot
                except Exception as e:
                    logger.warning(f"Failed to create character snapshot for {char_id}: {e}")
        
        # Update location states
        for loc_id, loc_state in running_state.get('location_states', {}).items():
            episode_meta.location_state_snapshot[loc_id] = loc_state
        
        # Preserve narrative changes from previous episode
        change_notes = running_state.get('change_notes', [])
        if change_notes:
            episode_meta.previous_episode_changes = change_notes
            logger.debug(f"Preserved {len(change_notes)} change notes from previous episode")
        
        # Update faction states
        for faction_id, faction_state in running_state.get('faction_states', {}).items():
            episode_meta.faction_state_snapshot[faction_id] = faction_state
        
        logger.info(f"Applied running state to episode {episode_meta.episode_number}: "
                   f"updated {len(running_state.get('character_states', {}))} characters, "
                   f"{len(running_state.get('location_states', {}))} locations, "
                   f"{len(running_state.get('faction_states', {}))} factions, "
                   f"preserved {len(change_notes)} change notes")
        
        return episode_meta
    
    def update_character(
        self,
        character_id: str,
        running_notes: str,
        emotion: Optional[str] = None,
        status: str = "present",
        segment_id: Optional[str] = None,
        world_context: Optional[Dict[str, Any]] = None,
        use_llm_regeneration: bool = False
    ) -> bool:
        """
        Update a character's running_status with new notes.
        
        This is the core function for tracking character state changes.
        Can be called from segments, episodes, or other generators.
        
        If use_llm_regeneration=True and world_context provided, will call LLM
        to regenerate character fields based on running notes.
        
        Args:
            character_id: ID of the character to update
            running_notes: Narrative note about what happened (e.g., "lost cursed_sword")
            emotion: Optional emotional state update
            status: Character presence status (present, absent, mentioned)
            segment_id: Optional segment ID this change occurred in
                       If not provided, uses a marked entry like "episode_X_end"
            world_context: Optional world context for LLM regeneration
            use_llm_regeneration: If True, call LLM to regenerate character fields
            
        Returns:
            True if update succeeded, False otherwise
            
        Example:
            update_character(
                "char_knight",
                "lost cursed_sword - dropped in the river",
                emotion="desperate",
                status="present",
                world_context=world_info,
                use_llm_regeneration=True
            )
        """
        char = self.story.get_character(character_id)
        if not char:
            logger.warning(f"Character {character_id} not found")
            return False
        
        try:
            # Always record the running status update
            char.add_state(
                segment_id=segment_id or "marked_update",
                emotion=emotion,
                status=status,
                notes=running_notes
            )
            char.save()
            logger.info(f"Updated character {char.name}: {running_notes}")
            
            # If LLM regeneration requested, call async method
            if use_llm_regeneration and world_context and self.generator:
                # Note: This is a sync method calling async - should be awaited by caller
                logger.debug(f"Regeneration requested for {char.name}, world context available")
                # Return True here, caller should await regenerate_character_from_running_state separately
            
            return True
        except Exception as e:
            logger.error(f"Failed to update character {character_id}: {e}")
            return False
    
    def _collect_faction_states_from_episode(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Collect faction states affected by characters in the episode.
        
        Factions are identified by characters' faction_id field.
        Tracks faction power/influence based on character involvement.
        
        Args:
            episode_number: The episode number to analyze
            arc_id: Optional arc ID to scope the search
            
        Returns:
            Dict of faction_id -> {name, description, goals, leader, alignment, power_level, member_count}
        """
        faction_states = {}
        
        # Get all segments in this episode
        episode_segments = self._walk_episode_segments(episode_number, arc_id)
        
        if not episode_segments:
            return {}
        
        # Track unique factions from characters in episodes
        faction_members = {}  # faction_id -> list of (char_id, char_name)
        
        for segment in episode_segments:
            # Get characters from this segment and their factions
            for char_status in segment.characters_running_status:
                char = self.story.get_character(char_status.character_id)
                if char and char.faction_id:
                    if char.faction_id not in faction_members:
                        faction_members[char.faction_id] = []
                    faction_members[char.faction_id].append((char.id, char.name))
        
        # Get faction details from story
        for faction in self.story.get_all_factions():
            if faction.id in faction_members:
                faction_states[faction.id] = {
                    'name': faction.name,
                    'description': faction.description,
                    'goals': faction.goals,
                    'leader': faction.leader,
                    'alignment': faction.alignment,
                    'status': faction.status,
                    'power_level': 0.5,  # Default, can be updated by LLM
                    'members': faction_members[faction.id],
                    'member_count': len(faction_members[faction.id])
                }
        
        logger.debug(f"Collected faction states from episode {episode_number}: {len(faction_states)} factions")
        return faction_states
    
    def update_story_objects_with_running_state(
        self,
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> None:
        """
        Update StoryCharacter and StoryLocation objects with their final running state
        from a completed episode.
        
        This ensures the story object itself reflects what happened in the episode,
        so when we query a character's running_status later, we get the up-to-date state.
        
        For example:
        - If Knight had running_status entries for each segment
        - At episode end, we consolidate to the final state
        - StoryCharacter.running_status is updated with marked entries for episode end
        
        Args:
            episode_number: The episode number that just completed
            arc_id: Optional arc ID to scope the search
        """
        running_state = self.collect_running_state_from_episode(episode_number, arc_id)
        
        # Update StoryCharacter running_status with final episode state
        for char_id, char_state in running_state.get('character_states', {}).items():
            self.update_character(
                character_id=char_id,
                running_notes=f"End of Episode {episode_number}: {char_state.get('notes', '')}",
                emotion=char_state.get('emotion', ''),
                status='present',
                segment_id=f"episode_{episode_number}_end"
            )
        
        # Update StoryLocation current_state with final episode state
        for loc_id, loc_state in running_state.get('location_states', {}).items():
            loc = self.story.get_location(loc_id)
            if loc:
                loc.current_state = loc_state.get('current_state', '')
                loc.save()
                logger.debug(f"Updated location {loc.name} current_state with episode {episode_number} end state")
        
        # Update faction states with final episode state
        for faction_id, faction_state in running_state.get('faction_states', {}).items():
            faction = self.story.get_faction(faction_id)
            if faction:
                # Record change and update description if needed
                change = f"Episode {episode_number}: power_level={faction_state.get('power_level', 0.5)}, members={faction_state.get('member_count', 0)}"
                faction.apply_change(change)
                faction.save()
                logger.debug(f"Updated faction {faction.name} with episode {episode_number} end state")
        
        logger.info(f"Updated story objects with running state from episode {episode_number}: "
                   f"{len(running_state.get('character_states', {}))} characters, "
                   f"{len(running_state.get('location_states', {}))} locations, "
                   f"{len(running_state.get('faction_states', {}))} factions")
    
    async def update_story_objects_with_llm_regeneration(
        self,
        episode_number: int,
        arc_id: Optional[str] = None,
        world_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update story objects AND regenerate character fields via LLM where needed.
        
        This is the high-level method that:
        1. Collects running state from completed episode
        2. For each character, checks if regeneration needed
        3. If yes and world_context available, calls LLM to regenerate fields
        4. Updates both StoryCharacter and EpisodeMeta
        
        Args:
            episode_number: The completed episode number
            arc_id: Optional arc ID
            world_context: Optional full story world context
                          If provided, enables LLM regeneration for significant changes
        """
        running_state = self.collect_running_state_from_episode(episode_number, arc_id)
        
        # Update characters
        for char_id, char_state in running_state.get('character_states', {}).items():
            running_notes = char_state.get('notes', '')
            
            # Always update running_status
            self.update_character(
                character_id=char_id,
                running_notes=running_notes,
                emotion=char_state.get('emotion', ''),
                status='present',
                segment_id=f"episode_{episode_number}_end"
            )
            
            # If significant changes and world context available, regenerate via LLM
            if world_context and self._should_regenerate_character(running_notes):
                try:
                    success = await self.update_character_with_llm(
                        character_id=char_id,
                        running_notes=running_notes,
                        world_context=world_context,
                        emotion=char_state.get('emotion', ''),
                        status='present',
                        segment_id=f"episode_{episode_number}_end"
                    )
                    if success:
                        logger.info(f"Successfully regenerated character {char_id} from running state")
                    else:
                        logger.debug(f"LLM regeneration failed for {char_id}, using basic update")
                except Exception as e:
                    logger.debug(f"Could not regenerate character {char_id} via LLM: {e}")
        
        # Update locations
        for loc_id, loc_state in running_state.get('location_states', {}).items():
            loc = self.story.get_location(loc_id)
            if loc:
                loc.current_state = loc_state.get('current_state', '')
                loc.save()
        
        # Update factions
        for faction_id, faction_state in running_state.get('faction_states', {}).items():
            faction = self.story.get_faction(faction_id)
            if faction:
                change = f"LLM update: {faction_state.get('description', '')[:100]}"
                faction.apply_change(change)
                faction.save()
        
        logger.info(f"Updated story objects with running state from episode {episode_number}: "
                   f"{len(running_state.get('character_states', {}))} characters, "
                   f"{len(running_state.get('faction_states', {}))} factions")
    
    def _should_regenerate_character(self, running_notes: str) -> bool:
        """
        Detect if running_notes contain significant changes warranting LLM regeneration.
        
        Heuristic: If running_notes contain state-changing keywords, regenerate.
        Examples that trigger regeneration:
        - "lost X" / "gained X" (inventory changes)
        - "wounded" / "healed" / "dying" (health changes)
        - "angry" / "determined" / "desperate" (emotional shifts)
        - "betrayed by" / "allied with" (relationship changes)
        
        Args:
            running_notes: Arbitrary running state text
            
        Returns:
            True if regeneration likely needed
        """
        significant_keywords = {
            'lost', 'gained', 'obtained', 'dropped', 'destroyed',  # inventory
            'wounded', 'healed', 'injured', 'dying', 'dead', 'poisoned',  # health
            'angry', 'furious', 'calm', 'desperate', 'hopeful', 'betrayed',  # emotion
            'alliance', 'betrayal', 'trust', 'revenge', 'sacrifice',  # relationships
            'discovered', 'learned', 'revealed', 'exposed', 'admitted'  # knowledge
        }
        
        notes_lower = running_notes.lower()
        return any(keyword in notes_lower for keyword in significant_keywords)
    
    async def update_character_with_llm(
        self,
        character_id: str,
        running_notes: str,
        world_context: Dict[str, Any],
        emotion: Optional[str] = None,
        status: str = "present",
        segment_id: Optional[str] = None
    ) -> bool:
        """
        Update character running_status AND regenerate fields via LLM.
        
        This is the async version that:
        1. Records the running_status update
        2. Calls LLM to regenerate character description, health, emotion, inventory
        3. Updates EpisodeMeta character_state_snapshot with new values
        
        Args:
            character_id: ID of character to update
            running_notes: Narrative changes (e.g., "wounded in arm, lost cursed_sword")
            world_context: Full story context (arc, themes, locations, etc.)
            emotion: Optional emotion state (may be overridden by LLM)
            status: Character presence status
            segment_id: Optional segment ID for running_status
            
        Returns:
            True if both update and regeneration succeeded
        """
        # First update the running_status
        if not self.update_character(character_id, running_notes, emotion, status, segment_id):
            return False
        
        # Then regenerate fields via LLM
        return await self.regenerate_character_from_running_state(
            character_id,
            running_notes,
            world_context
        )
    
    async def regenerate_character_from_running_state(
        self,
        character_id: str,
        running_notes: str,
        world_context: Dict[str, Any]
    ) -> bool:
        """
        Use LLM to regenerate character fields based on running state changes.
        
        When a character's running_status contains significant changes (e.g., "lost cursed_sword"),
        we ask the LLM to:
        1. Parse the running notes
        2. Update character description, health_status, emotional_status, inventory
        3. Preserve character core identity
        4. Reflect changes in arc goal progress
        
        Args:
            character_id: ID of character to update
            running_notes: Arbitrary text from running_status (e.g., "wounded, angry, lost cursed_sword")
            world_context: Full story world context (arc, locations, factions, themes, etc.)
            
        Returns:
            True if update succeeded, False otherwise
        """
        char = self.story.get_character(character_id)
        if not char:
            logger.warning(f"Character {character_id} not found")
            return False
        
        # Build LLM prompt
        prompt = f"""You are updating a character's description and state based on what happened to them.

CHARACTER DETAILS:
- Name: {char.name}
- Original Description: {char.description}
- Original Background: {char.background}

WHAT HAPPENED (running notes):
{running_notes}

WORLD CONTEXT:
Arc: {world_context.get('arc', {}).get('name', 'Unknown')}
Current Themes: {', '.join(world_context.get('themes', []))}
Current Location: {world_context.get('location', 'Unknown')}

Please regenerate the character's:
1. description (1-2 sentences, reflecting current state and changes)
2. health_status (e.g., "healthy", "wounded in arm", "dying")
3. emotional_status (e.g., "determined", "angry", "desperate", "hopeful")
4. inventory (key items this character has, formatted as dict with notes)
5. goal_progress (0.0 to 1.0, how much closer/further from their arc goal)
6. goal_notes (what progress was made toward their arc goal)

Return ONLY valid JSON in this format:
{{
  "description": "...",
  "health_status": "...",
  "emotional_status": "...",
  "inventory": {{"item_name": "notes about item", ...}},
  "goal_progress": 0.5,
  "goal_notes": "..."
}}"""
        
        try:
            logger.debug(f"Calling LLM to regenerate character {char.name} from running state")
            
            regen_schema = ResponseSchema(
                fields=[
                    FieldSpec("description", type="str", aliases=["char_description"]),
                    FieldSpec("health_status", type="str", aliases=["health"]),
                    FieldSpec("emotional_status", type="str", aliases=["emotion", "mood"]),
                    FieldSpec("inventory", type="dict", aliases=["items"]),
                    FieldSpec("goal_progress", type="float", aliases=["progress"]),
                    FieldSpec("goal_notes", type="str", aliases=["notes"]),
                ],
                expect_array=False,
            )
            parsed = await self.generator.generate_structured(
                system_prompt="You are a creative writer updating character states based on narrative changes.",
                user_prompt=prompt,
                schema=regen_schema,
                fallback_defaults=[{}],
            )
            
            if not parsed:
                logger.warning(f"Empty result regenerating character {character_id}")
                return False
            
            # Update character fields
            if parsed.get('description'):
                char.description = parsed['description']
            
            # Update CharacterStateSnapshot in EpisodeMeta
            from app.models.story_episode import CharacterStateSnapshot
            from app.models.story_episode import StoryEpisode as EpisodeMeta
            
            # Try to find and update current episode's metadata
            if hasattr(self, 'current_episode_number'):
                episode_num = self.current_episode_number
            else:
                # Default to latest episode
                arc = StoryArc.load(self.story.id, getattr(self, 'current_arc_id', None))
                episode_num = arc.episode_count if arc else 1
            
            # Create/update snapshot with new fields
            snapshot = CharacterStateSnapshot(
                character_id=character_id,
                description=parsed.get('description', char.description),
                health_status=parsed.get('health_status', ''),
                emotional_status=parsed.get('emotional_status', ''),
                relationship_notes={},
                inventory=parsed.get('inventory', {}),
                character_arc_goal=getattr(char, 'character_arc_goal', ''),
                goal_progress=float(parsed.get('goal_progress', 0.0)),
                goal_notes=parsed.get('goal_notes', '')
            )
            
            # Try to update EpisodeMeta if available
            try:
                episode_meta_id = f"episode_meta_{episode_num}_{getattr(self, 'current_arc_id', 'unknown')}"
                episode_meta = EpisodeMeta.load(self.story.id, episode_meta_id)
                if episode_meta:
                    episode_meta.character_state_snapshot[character_id] = snapshot
                    episode_meta.save()
                    logger.debug(f"Updated EpisodeMeta for character {char.name}")
            except Exception as e:
                logger.debug(f"Could not update EpisodeMeta: {e}")
            
            # Save character
            char.save()
            logger.info(f"Regenerated character {char.name} from running state: "
                       f"health={parsed.get('health_status')}, "
                       f"emotion={parsed.get('emotional_status')}, "
                       f"items={len(parsed.get('inventory', {}))}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to regenerate character {character_id}: {e}")
            return False
