"""Character state updater service for updating character states after episodes (E2-3 Enhanced)."""

import logging
from typing import Dict, List, Optional, Set
import json

from app.models.story import Story
from app.models.character_state import CharacterStateSnapshot
from app.models.episode_recap import EpisodeRecap
from app.models.story_segment import StorySegment
from app.models.story_character import StoryCharacter

logger = logging.getLogger("infinite_story.engine.character_state_updater")


class CharacterStateUpdater:
    """Update character states after episode completion (E2-3 Enhanced).
    
    This service handles updating character metadata (description, health, emotional status,
    relationships, inventory, character arc goal progress) based on what happened during
    an episode.
    
    Process:
    1. Collect all character mentions from segments in the episode
    2. Extract changes from change_notes (health, emotional, relationships, inventory)
    3. For each character involved, use AI to generate natural language updates
    4. Update goal progress toward character_arc_goals
    5. Save updated CharacterStateSnapshot and update StoryCharacter
    """
    
    def __init__(self, story: Story, generator=None):
        """Initialize the character state updater.
        
        Args:
            story: The Story instance to update characters for
            generator: Optional AI generator for AI-powered updates
        """
        self.story = story
        self.generator = generator
    
    async def update_character_states(
        self,
        episode_number: int,
        arc_id: str,
        segment_ids: List[str],
        prev_recap: Optional[EpisodeRecap] = None
    ) -> Dict[str, CharacterStateSnapshot]:
        """Update all character states after episode completion (E2-3 Enhanced).
        
        Walks through all segments in the episode, collects character mentions and changes,
        then updates character metadata with AI-generated descriptions and state changes.
        
        Args:
            episode_number: Episode number that just completed
            arc_id: Arc ID
            segment_ids: List of segment IDs in the episode
            prev_recap: Previous episode recap for context
            
        Returns:
            Dict[character_id] -> CharacterStateSnapshot with updated states
        """
        logger.info(
            f"Updating character states for episode {episode_number}, "
            f"arc {arc_id} with {len(segment_ids)} segments"
        )
        
        try:
            # Step 1: Collect all character mentions and changes from segments
            characters_involved = self._collect_characters_from_segments(segment_ids)
            all_changes = self._collect_all_changes(segment_ids)
            
            logger.debug(f"Found {len(characters_involved)} characters involved in episode")
            logger.debug(f"Collected {len(all_changes)} total changes across episode")
            
            # Step 2: Update each character involved
            updated_states: Dict[str, CharacterStateSnapshot] = {}
            
            for char_id in characters_involved:
                try:
                    # Get the character
                    char = self.story.get_character(char_id)
                    if not char:
                        logger.warning(f"Character {char_id} not found, skipping")
                        continue
                    
                    # Extract changes specific to this character
                    char_changes = [c for c in all_changes if char_id in c.lower()]
                    
                    # Build new state snapshot
                    snapshot = self._build_character_state_snapshot(
                        char=char,
                        char_id=char_id,
                        arc_id=arc_id,
                        changes=char_changes,
                        prev_recap=prev_recap
                    )
                    
                    # If we have AI generator, enhance with AI-generated updates
                    if self.generator:
                        snapshot = await self._enhance_with_ai(
                            char=char,
                            snapshot=snapshot,
                            episode_number=episode_number,
                            all_changes=all_changes,
                            arc_id=arc_id
                        )
                    
                    # Save the updated snapshot
                    snapshot.save()
                    updated_states[char_id] = snapshot
                    
                    # Update character's permanent description with new narrative
                    self._update_character_description(char, snapshot)
                    char.save()
                    
                    logger.debug(f"Updated character {char_id}")
                    
                except Exception as e:
                    logger.warning(f"Failed to update character {char_id}: {e}")
                    continue
            
            logger.info(f"Successfully updated {len(updated_states)} characters")
            return updated_states
        
        except Exception as e:
            logger.error(f"Error updating character states: {e}", exc_info=True)
            return {}
    
    def _collect_characters_from_segments(self, segment_ids: List[str]) -> Set[str]:
        """Collect all character IDs mentioned in segments.
        
        Args:
            segment_ids: List of segment IDs in the episode
            
        Returns:
            Set of unique character IDs involved
        """
        characters: Set[str] = set()
        
        for seg_id in segment_ids:
            segment = self.story.get_segment(seg_id)
            if not segment:
                continue
            
            # Add characters from character_states
            if segment.character_states:
                characters.update(segment.character_states.keys())
        
        return characters
    
    def _collect_all_changes(self, segment_ids: List[str]) -> List[str]:
        """Collect all change notes from segments.
        
        Args:
            segment_ids: List of segment IDs in the episode
            
        Returns:
            List of all change_notes from all segments
        """
        all_changes: List[str] = []
        
        for seg_id in segment_ids:
            segment = self.story.get_segment(seg_id)
            if segment and segment.change_notes:
                all_changes.extend(segment.change_notes)
        
        return all_changes
    
    def _build_character_state_snapshot(
        self,
        char: StoryCharacter,
        char_id: str,
        arc_id: str,
        changes: List[str],
        prev_recap: Optional[EpisodeRecap] = None
    ) -> CharacterStateSnapshot:
        """Build a character state snapshot from current info.
        
        Args:
            char: The StoryCharacter instance
            char_id: Character ID
            arc_id: Arc ID
            changes: Changes specific to this character
            prev_recap: Previous episode recap for context
            
        Returns:
            CharacterStateSnapshot with extracted state
        """
        # Extract emotion/health from changes
        health_status = self._extract_health_status(changes)
        emotional_status = self._extract_emotional_status(changes)
        relationships = self._extract_relationships(changes, char_id)
        inventory = self._extract_inventory(changes)
        
        # Get arc goal for this character
        arc = self.story.get_arc(arc_id)
        char_arc_goal = ""
        goal_progress = 0.0
        if arc and arc.character_arc_goals:
            char_arc_goal = arc.character_arc_goals.get(char_id, "")
        
        return CharacterStateSnapshot(
            character_id=char_id,
            description=char.description,
            health_status=health_status,
            emotional_status=emotional_status,
            relationship_notes=relationships,
            inventory=inventory,
            character_arc_goal=char_arc_goal,
            goal_progress=goal_progress,
            goal_notes="\n".join(changes[:2]) if changes else ""
        )
    
    async def _enhance_with_ai(
        self,
        char: StoryCharacter,
        snapshot: CharacterStateSnapshot,
        episode_number: int,
        all_changes: List[str],
        arc_id: str
    ) -> CharacterStateSnapshot:
        """Enhance character state with AI-generated updates (TODO - placeholder).
        
        This would call AI to:
        1. Generate natural language description updates
        2. Enhance emotional status based on episode events
        3. Update relationship narratives
        4. Track goal progress
        
        For now, returns snapshot as-is.
        
        Args:
            char: The StoryCharacter
            snapshot: The current CharacterStateSnapshot
            episode_number: Episode number completed
            all_changes: All changes in the episode
            arc_id: Arc ID
            
        Returns:
            Enhanced CharacterStateSnapshot (or unchanged if no AI)
        """
        # TODO: Implement AI enhancement
        # Would prompt AI with:
        # "Based on these episode events for {char.name}, update their state:
        #  Events: {all_changes}
        #  Current state: {snapshot}
        #  Arc goal: {snapshot.character_arc_goal}
        #  Generate: new description, updated emotional status, goal progress"
        
        return snapshot
    
    async def generate_new_character_for_theme(
        self,
        theme: str,
        arc_id: str,
        episode_number: int
    ) -> Optional[StoryCharacter]:
        """Generate a new character when a theme event triggers (E2-4 Enhanced).
        
        Some themes naturally trigger the introduction of new characters:
        - 'mystery' might introduce a detective/investigator
        - 'romance' might introduce a love interest
        - 'rebellion' might introduce a rebel leader
        - 'betrayal' might introduce a former ally
        
        Args:
            theme: The theme that triggered character creation
            arc_id: The arc ID
            episode_number: Current episode number
            
        Returns:
            A new StoryCharacter, or None if theme doesn't trigger new character
        """
        # Themes that naturally trigger new character introduction
        theme_character_hooks = {
            "mystery": "an investigator or detective",
            "romance": "a romantic interest or love interest",
            "betrayal": "a former trusted ally",
            "family": "a long-lost family member",
            "rebellion": "a rebel leader or revolutionary",
            "adventure": "a fellow adventurer or guide",
            "loss": "someone mourning the same loss",
            "redemption": "a mentor or guide toward redemption",
            "darkness": "a mysterious stranger from shadows",
            "revelation": "a messenger with shocking news",
        }
        
        if theme.lower() not in theme_character_hooks:
            logger.debug(f"Theme '{theme}' doesn't trigger new character creation")
            return None
        
        try:
            if not self.generator:
                logger.warning("No generator available for new character creation")
                return None
            
            character_hint = theme_character_hooks[theme.lower()]
            
            # TODO: AI Generate new character based on theme
            # Prompt AI with:
            # f"For theme '{theme}', create a new character who is {character_hint}.
            #  This character should fit the current arc and episode context.
            #  Generate: name, description, background, personality_traits, goals, fears"
            
            # For now, log that this would happen
            logger.info(
                f"[TODO] Would generate new character for theme '{theme}': {character_hint}"
            )
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to generate new character for theme '{theme}': {e}")
            return None
    
    def _update_character_description(
        self,
        char: StoryCharacter,
        snapshot: CharacterStateSnapshot
    ) -> None:
        """Update character's permanent description with new narrative.
        
        Args:
            char: The StoryCharacter to update
            snapshot: The CharacterStateSnapshot with new info
        """
        # Build an updated description incorporating new state
        updates = []
        
        if snapshot.emotional_status:
            updates.append(f"Currently {snapshot.emotional_status}")
        
        if snapshot.health_status and snapshot.health_status != "healthy":
            updates.append(f"Health: {snapshot.health_status}")
        
        if snapshot.relationship_notes:
            rel_summary = ", ".join(
                f"{rel}" for rel in list(snapshot.relationship_notes.values())[:2]
            )
            updates.append(f"Relations: {rel_summary}")
        
        if updates:
            char.description = "\n".join([char.description] + updates)
    
    def _extract_health_status(self, changes: List[str]) -> str:
        """Extract health status from change notes.
        
        Args:
            changes: List of change notes
            
        Returns:
            Health status string (healthy, wounded, etc.)
        """
        health_keywords = {
            'wound': 'wounded',
            'heal': 'healed',
            'sick': 'ill',
            'poison': 'poisoned',
            'death': 'dead',
            'dying': 'dying',
        }
        
        for change in changes:
            change_lower = change.lower()
            for keyword, status in health_keywords.items():
                if keyword in change_lower:
                    return status
        
        return "healthy"
    
    def _extract_emotional_status(self, changes: List[str]) -> str:
        """Extract emotional status from change notes.
        
        Args:
            changes: List of change notes
            
        Returns:
            Emotional status string
        """
        emotion_keywords = {
            'anger': 'angry',
            'betray': 'betrayed',
            'hopeful': 'hopeful',
            'fear': 'fearful',
            'trust': 'trusting',
            'doubt': 'doubtful',
            'resolve': 'resolute',
            'confuse': 'confused',
        }
        
        emotions = []
        for change in changes:
            change_lower = change.lower()
            for keyword, emotion in emotion_keywords.items():
                if keyword in change_lower and emotion not in emotions:
                    emotions.append(emotion)
        
        return ", ".join(emotions) if emotions else "neutral"
    
    def _extract_relationships(self, changes: List[str], char_id: str) -> Dict[str, str]:
        """Extract relationship changes from change notes.
        
        Args:
            changes: List of change notes
            char_id: Character ID to find relationships for
            
        Returns:
            Dict of character_id -> relationship description
        """
        # Look for mentions of other characters in changes
        relationships = {}
        
        # Extract other character mentions
        for change in changes:
            # Simple heuristic: look for "char_" patterns
            import re
            char_ids = re.findall(r'char_\w+', change)
            for other_id in char_ids:
                if other_id != char_id and other_id not in relationships:
                    relationships[other_id] = change
        
        return relationships
    
    def _extract_inventory(self, changes: List[str]) -> Dict[str, str]:
        """Extract inventory changes from change notes.
        
        Args:
            changes: List of change notes
            
        Returns:
            Dict of item_name -> description
        """
        inventory = {}
        
        # Look for keywords like "gained", "lost", "item", "sword", etc.
        item_keywords = ['sword', 'shield', 'item', 'potion', 'letter', 'ring', 'book', 'key']
        
        for change in changes:
            change_lower = change.lower()
            for keyword in item_keywords:
                if keyword in change_lower:
                    inventory[keyword] = change
        
        return inventory
