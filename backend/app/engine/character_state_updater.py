"""Character state updater service for updating character states after episodes (E2-3 Enhanced)."""

import logging
import uuid
from typing import Dict, List, Optional, Set

from app.models.story import Story
from app.models.story_arc import StoryArc
from app.models.story_episode import CharacterStateSnapshot, StoryEpisode as EpisodeRecap
from app.models.story_segment import StorySegment
from app.models.story_character import StoryCharacter, CharacterRole
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.character_state_updater")


# Schema for AI-enhanced character state updates
_ENHANCE_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("description", type="str", aliases=["updated_description", "new_description"]),
        FieldSpec("emotional_status", type="str", aliases=["emotion", "mood", "emotional_state"]),
        FieldSpec("health_status", type="str", aliases=["health", "physical_status"]),
        FieldSpec("goal_progress", type="float", aliases=["progress"]),
        FieldSpec("goal_notes", type="str", aliases=["progress_notes", "arc_progress"]),
        FieldSpec("relationship_notes", type="list", aliases=["relationships", "relationship_changes"]),
        FieldSpec("recap", type="str", aliases=["character_recap", "summary", "current_recap"]),
    ],
    expect_array=False,
)

# Schema for new character generation
_NEW_CHAR_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", type="str", required=True, aliases=["character_name"]),
        FieldSpec("description", type="str", required=True, aliases=["appearance", "desc"]),
        FieldSpec("background", type="str", required=True, aliases=["backstory"]),
        FieldSpec("personality_traits", type="list", aliases=["personality", "traits"]),
        FieldSpec("goals", type="str", aliases=["goal", "motivation"]),
        FieldSpec("role_in_theme", type="str", aliases=["role", "thematic_role"]),
    ],
    expect_array=False,
)


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
                    # Match on character name (case-insensitive) since change_notes
                    # use display names like "Knight received order", not IDs
                    char_name_lower = char.name.lower()
                    # Also try matching individual name parts (e.g., "Kael" from "Kael Ashford")
                    name_parts = [p.lower() for p in char.name.split() if len(p) > 2]
                    char_changes = [
                        c for c in all_changes
                        if char_name_lower in c.lower()
                        or any(part in c.lower() for part in name_parts)
                    ]
                    
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
                    
                    # Store the updated snapshot (CharacterStateSnapshot is a BaseModel,
                    # not a StoryBase, so it doesn't have save() — it's stored as part
                    # of the EpisodeRecap's ending_character_states)
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
    
    def _collect_characters_from_segments(self, segment_ids) -> Set[str]:
        """Collect all character IDs mentioned in segments.
        
        Args:
            segment_ids: List of segment IDs (str) or StorySegment objects
            
        Returns:
            Set of unique character IDs involved
        """
        characters: Set[str] = set()
        
        for seg_or_id in segment_ids:
            # Accept both StorySegment objects and string IDs
            if isinstance(seg_or_id, StorySegment):
                segment = seg_or_id
            else:
                segment = self.story.get_segment(seg_or_id)
            if not segment:
                continue
            
            # Add characters from character_states
            if segment.character_states:
                characters.update(segment.character_states.keys())
            # Also check characters_present
            if hasattr(segment, 'characters_present') and segment.characters_present:
                characters.update(segment.characters_present)
        
        return characters
    
    def _collect_all_changes(self, segment_ids) -> List[str]:
        """Collect all change notes from segments.
        
        Args:
            segment_ids: List of segment IDs (str) or StorySegment objects
            
        Returns:
            List of all change_notes from all segments
        """
        all_changes: List[str] = []
        
        for seg_or_id in segment_ids:
            # Accept both StorySegment objects and string IDs
            if isinstance(seg_or_id, StorySegment):
                segment = seg_or_id
            else:
                segment = self.story.get_segment(seg_or_id)
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
        arc = None
        try:
            arc = StoryArc.load(self.story.id, arc_id)
        except Exception:
            pass
        char_arc_goal = ""
        goal_progress = 0.0
        if arc and hasattr(arc, 'character_arc_goals') and arc.character_arc_goals:
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
        """Enhance character state with AI-generated updates.
        
        Calls AI to update character description, emotional status,
        relationship narratives, and goal progress based on episode events.
        
        Falls back to the unmodified snapshot if AI call fails.
        
        Args:
            char: The StoryCharacter
            snapshot: The current CharacterStateSnapshot
            episode_number: Episode number completed
            all_changes: All changes in the episode
            arc_id: Arc ID
            
        Returns:
            Enhanced CharacterStateSnapshot
        """
        if not self.generator:
            return snapshot
        
        try:
            # Filter changes relevant to this character
            char_name_lower = char.name.lower()
            name_parts = [p.lower() for p in char.name.split() if len(p) > 2]
            relevant_changes = [
                c for c in all_changes
                if char_name_lower in c.lower()
                or any(part in c.lower() for part in name_parts)
            ]
            
            if not relevant_changes:
                return snapshot
            
            changes_text = "\n".join(f"- {c}" for c in relevant_changes[:10])
            
            format_instruction = AIResponseParser.get_prompt_instruction(
                _ENHANCE_SCHEMA, OutputFormat.JSON,
                example={
                    "description": "A weathered knight now bearing fresh scars from the ambush, her confidence visibly shaken",
                    "emotional_status": "shaken but resolute",
                    "health_status": "wounded",
                    "goal_progress": 0.4,
                    "goal_notes": "Closer to uncovering the conspiracy but at great personal cost",
                    "relationship_notes": ["Trust in the captain deepened after the rescue", "Growing suspicion of the merchant guild"],
                    "recap": "Survived the ambush but was wounded. Discovered the captain's true loyalty. Growing suspicious of the merchant guild's motives.",
                }
            )
            
            prompt = f"""Update this character's state based on what happened this episode:

CHARACTER: {char.name}
Current Description: {char.description}
Current Emotional Status: {snapshot.emotional_status}
Current Health: {snapshot.health_status}
Arc Goal: {snapshot.character_arc_goal or 'None set'}
Current Goal Progress: {snapshot.goal_progress:.0%}

EPISODE {episode_number} EVENTS INVOLVING {char.name.upper()}:
{changes_text}

Based on these events, provide updated character state. Only change fields that the events actually affected.
For goal_progress, use a value from 0.0 (no progress) to 1.0 (goal achieved).
For recap, write 1-2 sentences summarizing what happened to this character THIS episode
  (e.g. "Survived the ambush but was wounded. Discovered the captain's true loyalty.").

{format_instruction}"""

            data = await self.generator.generate_structured(
                system_prompt="You are a character analyst tracking how story events affect a character's state, emotions, and arc progress.",
                user_prompt=prompt,
                schema=_ENHANCE_SCHEMA,
                fallback_defaults=[{}],
            )
            
            if not data:
                return snapshot
            
            # Only update fields the AI actually returned (non-empty)
            if data.get('description'):
                snapshot.description = data['description']
            if data.get('emotional_status'):
                snapshot.emotional_status = data['emotional_status']
            if data.get('health_status'):
                snapshot.health_status = data['health_status']
            if data.get('goal_progress') is not None:
                try:
                    progress = float(data['goal_progress'])
                    # LLMs sometimes return percentages (e.g., 65.0 instead of 0.65)
                    if progress > 1.0:
                        progress = progress / 100.0
                    snapshot.goal_progress = max(0.0, min(1.0, progress))
                except (ValueError, TypeError):
                    pass
            if data.get('goal_notes'):
                snapshot.goal_notes = data['goal_notes']
            if data.get('relationship_notes') and isinstance(data['relationship_notes'], list):
                # Convert list → Dict[str, str] to match CharacterStateSnapshot.relationship_notes type.
                # The AI returns a list of relationship notes like ["Trust with Kael deepened", ...].
                # We key them as "rel_0", "rel_1", ... since we don't have character IDs here.
                snapshot.relationship_notes = {
                    f"rel_{i}": str(note) for i, note in enumerate(data['relationship_notes'])
                }
            
            # Store the recap on the snapshot so _update_character_description can use it
            if data.get('recap'):
                snapshot._recap_text = data['recap']
            
            logger.debug(f"AI-enhanced state for {char.name}: emotion={snapshot.emotional_status}, health={snapshot.health_status}")
            return snapshot
            
        except Exception as e:
            logger.warning(f"AI enhancement failed for {char.name}: {e}")
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
            
            # Gather world context for the AI
            arc = None
            try:
                arc = StoryArc.load(self.story.id, arc_id)
            except Exception:
                pass
            
            arc_context = ""
            if arc:
                arc_context = f"\nArc: {arc.title}\nPremise: {arc.premise}"
            
            format_instruction = AIResponseParser.get_prompt_instruction(
                _NEW_CHAR_SCHEMA, OutputFormat.JSON,
                example={
                    "name": "Sera Nighthollow",
                    "description": "A gaunt woman in a threadbare cloak, her eyes carrying the weight of too many secrets",
                    "background": "Once a court archivist, she vanished the night the royal library burned. Now she trades in whispered truths from the shadows.",
                    "personality_traits": ["secretive", "perceptive", "haunted", "fiercely loyal to the truth"],
                    "goals": "Expose the conspiracy behind the library fire before the evidence disappears forever",
                    "role_in_theme": "She represents the cost of seeking truth — knowledge gained at the price of safety",
                }
            )
            
            prompt = f"""Create a new character for this story. The theme "{theme}" has naturally called for {character_hint}.

Story: {self.story.title}
{arc_context}
Episode: {episode_number}

The character should:
- Fit naturally into the current story and arc
- Embody the theme of "{theme}" in their role and backstory
- Be {character_hint}
- Have clear motivations tied to the theme
- Feel like they belong in this world, not forced

{format_instruction}"""
            
            data = await self.generator.generate_structured(
                system_prompt="You are a character designer creating a new character that emerges naturally from story themes.",
                user_prompt=prompt,
                schema=_NEW_CHAR_SCHEMA,
                fallback_defaults=[{
                    "name": f"The {theme.title()} Stranger",
                    "description": f"A mysterious figure who is {character_hint}",
                    "background": "Origins unknown",
                    "personality_traits": ["mysterious"],
                    "goals": "",
                    "role_in_theme": "",
                }],
            )
            
            if not data:
                return None
            
            char = StoryCharacter(
                story=self.story,
                id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                story_id=self.story.id,
                name=data.get('name', f"The {theme.title()} Stranger"),
                description=data.get('description', f"A mysterious figure who is {character_hint}"),
                background=data.get('background', 'Origins unknown'),
                personality=data.get('personality_traits', []),
                goals=data.get('goals', ''),
                role=CharacterRole.MINOR,
            )
            char.save()
            logger.info(f"Generated new character for theme '{theme}': {char.name}")
            return char
            
        except Exception as e:
            logger.warning(f"Failed to generate new character for theme '{theme}': {e}")
            return None
    
    def _update_character_description(
        self,
        char: StoryCharacter,
        snapshot: CharacterStateSnapshot
    ) -> None:
        """Update character's permanent description and recap with new narrative.
        
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
            # relationship_notes is Dict[str, str] but handle list defensively
            if isinstance(snapshot.relationship_notes, dict):
                rel_items = list(snapshot.relationship_notes.values())[:2]
            elif isinstance(snapshot.relationship_notes, list):
                rel_items = [str(r) for r in snapshot.relationship_notes[:2]]
            else:
                rel_items = []
            if rel_items:
                rel_summary = ", ".join(rel_items)
                updates.append(f"Relations: {rel_summary}")
        
        if updates:
            char.description = "\n".join([char.description] + updates)
        
        # Update the character recap field — this is the concise "what happened last"
        recap_text = getattr(snapshot, '_recap_text', None)
        if recap_text:
            char.recap = recap_text
        elif updates:
            # Fallback: build a recap from state info
            char.recap = ". ".join(updates)
    
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
