"""Episode flush generator - consolidates running changes into evolved descriptions.

At episode-end, takes all the running_changes accumulated during an episode
and uses AI to generate evolved character/location descriptions that reflect
what happened during the episode.

These evolved descriptions become the base for the next episode's characters/locations.
"""

import logging
from typing import Dict, List, Optional, Any
from app.models import Story, StorySegment, StoryCharacter, StoryLocation
from app.models.story_segment import EntityChange
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.episode_flush_generator")


class EpisodeFlushGenerator:
    """Flush episode changes into character/location model updates."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize episode flush generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for description evolution
        """
        self.story = story
        self.generator = generator
    
    async def flush_episode_changes(
        self,
        episode_segments: List[StorySegment],
        episode_number: int,
        arc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Flush all running changes from episode into character/location descriptions.
        
        Steps:
        1. Collect all running_changes from all episode segments
        2. Group by entity (character/location)
        3. For each entity: call AI to evolve description based on changes
        4. Update character/location model with new descriptions
        5. Reset character/location current_state for next episode
        
        Args:
            episode_segments: All segments in the completed episode
            episode_number: The episode number being flushed
            arc_id: Optional arc ID for logging
            
        Returns:
            Dict with flushed_characters, flushed_locations, changes_summary
        """
        try:
            logger.info(f"Flushing episode {episode_number} changes to character/location models")
            
            # 1. Collect all running changes
            all_changes = self._collect_all_running_changes(episode_segments)
            if not all_changes:
                logger.info(f"No running changes found for episode {episode_number}")
                return {
                    'flushed_characters': {},
                    'flushed_locations': {},
                    'changes_summary': 'No changes recorded'
                }
            
            logger.debug(f"Collected {len(all_changes)} running changes from episode")
            
            # 2. Group by entity
            character_changes = self._group_changes_by_entity(
                all_changes,
                entity_type='character'
            )
            location_changes = self._group_changes_by_entity(
                all_changes,
                entity_type='location'
            )
            
            logger.debug(f"Grouped into {len(character_changes)} characters, {len(location_changes)} locations")
            
            # 3. Evolve character descriptions
            flushed_characters = await self._evolve_character_descriptions(
                character_changes,
                episode_number
            )
            
            # 4. Evolve location descriptions
            flushed_locations = await self._evolve_location_descriptions(
                location_changes,
                episode_number
            )
            
            # 5. Build summary
            changes_summary = self._build_changes_summary(
                character_changes,
                location_changes
            )
            
            logger.info(
                f"Episode {episode_number} flush complete: "
                f"{len(flushed_characters)} characters, "
                f"{len(flushed_locations)} locations updated"
            )
            
            return {
                'flushed_characters': flushed_characters,
                'flushed_locations': flushed_locations,
                'changes_summary': changes_summary,
            }
        
        except Exception as e:
            logger.error(f"Failed to flush episode {episode_number} changes: {e}", exc_info=True)
            raise ValueError(f"Episode flush failed: {str(e)}")
    
    def _collect_all_running_changes(
        self,
        episode_segments: List[StorySegment]
    ) -> List[Dict[str, Any]]:
        """Collect all running_changes from all episode segments.
        
        Args:
            episode_segments: All segments in the episode
            
        Returns:
            List of change dicts
        """
        all_changes = []
        
        for seg in episode_segments:
            if hasattr(seg, 'running_changes') and seg.running_changes:
                for change in seg.running_changes:
                    if isinstance(change, EntityChange):
                        all_changes.append(change.to_dict())
                    elif isinstance(change, dict):
                        all_changes.append(change)
        
        return all_changes
    
    def _group_changes_by_entity(
        self,
        changes: List[Dict[str, Any]],
        entity_type: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group changes by entity ID for a specific entity type.
        
        Args:
            changes: All changes
            entity_type: "character" or "location"
            
        Returns:
            Dict mapping entity_id to list of changes for that entity
        """
        grouped = {}
        
        for change in changes:
            if change.get('entity_type') != entity_type:
                continue
            
            entity_id = change.get('entity_id')
            if entity_id not in grouped:
                grouped[entity_id] = []
            
            grouped[entity_id].append(change)
        
        return grouped
    
    async def _evolve_character_descriptions(
        self,
        character_changes: Dict[str, List[Dict[str, Any]]],
        episode_number: int
    ) -> Dict[str, str]:
        """Evolve character descriptions based on accumulated changes.
        
        Uses AI to synthesize changes into evolved descriptions.
        
        Args:
            character_changes: Dict mapping char_id to list of changes
            episode_number: Episode number for context
            
        Returns:
            Dict mapping char_id to evolved description
        """
        flushed = {}
        
        for char_id, changes in character_changes.items():
            char = self.story.get_character(char_id)
            if not char:
                logger.warning(f"Character {char_id} not found for flushing")
                continue
            
            try:
                # Build prompt to evolve description
                prompt = self._build_character_evolution_prompt(
                    char,
                    changes,
                    episode_number
                )
                
                # Call AI
                logger.debug(f"Calling AI to evolve description for {char.name}")
                response = await self.generator.generate(
                    system_prompt="You are a narrative writer evolving character descriptions.",
                    user_prompt=prompt,
                    context_type="scene"
                )
                
                if response.error:
                    logger.warning(f"AI error evolving {char.name}: {response.error}")
                    evolved_desc = char.description  # Fall back to original
                else:
                    # Extract evolved description from response
                    evolved_desc = self._extract_evolved_description(response)
                    if not evolved_desc:
                        evolved_desc = char.description
                
                # Update character model
                char.description = evolved_desc
                char.current_state = {}  # Reset for next episode
                char.save()
                
                flushed[char_id] = evolved_desc
                logger.debug(f"Updated {char.name} description")
            
            except Exception as e:
                logger.error(f"Failed to evolve {char_id} description: {e}")
                flushed[char_id] = char.description
        
        return flushed
    
    async def _evolve_location_descriptions(
        self,
        location_changes: Dict[str, List[Dict[str, Any]]],
        episode_number: int
    ) -> Dict[str, str]:
        """Evolve location descriptions based on accumulated changes.
        
        Uses AI to synthesize changes into evolved descriptions.
        
        Args:
            location_changes: Dict mapping loc_id to list of changes
            episode_number: Episode number for context
            
        Returns:
            Dict mapping loc_id to evolved description
        """
        flushed = {}
        
        for loc_id, changes in location_changes.items():
            loc = self.story.get_location(loc_id)
            if not loc:
                logger.warning(f"Location {loc_id} not found for flushing")
                continue
            
            try:
                # Build prompt to evolve description
                prompt = self._build_location_evolution_prompt(
                    loc,
                    changes,
                    episode_number
                )
                
                # Call AI
                logger.debug(f"Calling AI to evolve description for {loc.name}")
                response = await self.generator.generate(
                    system_prompt="You are a narrative writer evolving location descriptions.",
                    user_prompt=prompt,
                    context_type="scene"
                )
                
                if response.error:
                    logger.warning(f"AI error evolving {loc.name}: {response.error}")
                    evolved_desc = loc.description  # Fall back to original
                else:
                    # Extract evolved description from response
                    evolved_desc = self._extract_evolved_description(response)
                    if not evolved_desc:
                        evolved_desc = loc.description
                
                # Update location model
                loc.description = evolved_desc
                loc.current_state = {}  # Reset for next episode
                loc.save()
                
                flushed[loc_id] = evolved_desc
                logger.debug(f"Updated {loc.name} description")
            
            except Exception as e:
                logger.error(f"Failed to evolve {loc_id} description: {e}")
                flushed[loc_id] = loc.description
        
        return flushed
    
    def _build_character_evolution_prompt(
        self,
        char: StoryCharacter,
        changes: List[Dict[str, Any]],
        episode_number: int
    ) -> str:
        """Build prompt for AI to evolve character description.
        
        Args:
            char: The character object
            changes: List of changes that happened to this character
            episode_number: Episode number
            
        Returns:
            Prompt text for AI
        """
        changes_text_lines = []
        for change in changes:
            desc = change.get('description', f"{change.get('property')} changed")
            changes_text_lines.append(f"- {desc}")
        changes_text = "\n".join(changes_text_lines)
        
        return f"""Based on the following changes to a character, write an evolved description.

ORIGINAL DESCRIPTION:
{char.description}

BACKGROUND:
{char.background}

CHANGES DURING EPISODE {episode_number}:
{changes_text}

TASK:
Write a concise evolved description (2-3 sentences) that:
1. Incorporates the character's original traits
2. Reflects the changes that occurred during this episode
3. Maintains continuity with their background
4. Shows how they have grown or changed

EVOLVED DESCRIPTION:
(Write only the description, no preamble)"""
    
    def _build_location_evolution_prompt(
        self,
        loc: StoryLocation,
        changes: List[Dict[str, Any]],
        episode_number: int
    ) -> str:
        """Build prompt for AI to evolve location description.
        
        Args:
            loc: The location object
            changes: List of changes that happened to this location
            episode_number: Episode number
            
        Returns:
            Prompt text for AI
        """
        changes_text_lines = []
        for change in changes:
            desc = change.get('description', f"{change.get('property')} changed")
            changes_text_lines.append(f"- {desc}")
        changes_text = "\n".join(changes_text_lines)
        
        return f"""Based on the following changes to a location, write an evolved description.

ORIGINAL DESCRIPTION:
{loc.description}

FULL DESCRIPTION:
{loc.full_description or loc.description}

CHANGES DURING EPISODE {episode_number}:
{changes_text}

TASK:
Write a concise evolved description (2-3 sentences) that:
1. Incorporates the location's original features
2. Reflects the changes that occurred during this episode
3. Maintains geographical consistency
4. Shows how the location has been affected by events

EVOLVED DESCRIPTION:
(Write only the description, no preamble)"""
    
    def _extract_evolved_description(self, response: Any) -> str:
        """Extract evolved description from AI response.
        
        Args:
            response: Response from generator
            
        Returns:
            Evolved description string
        """
        # Extract from raw_response — the typed response models don't have
        # evolved_description/description/content fields
        if hasattr(response, 'raw_response') and response.raw_response:
            return response.raw_response
        
        return ""
    
    def _build_changes_summary(
        self,
        character_changes: Dict[str, List[Dict[str, Any]]],
        location_changes: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Build a human-readable summary of changes.
        
        Args:
            character_changes: Character changes by entity_id
            location_changes: Location changes by entity_id
            
        Returns:
            Summary string
        """
        summaries = []
        
        for char_id, changes in character_changes.items():
            char = self.story.get_character(char_id)
            if char:
                summaries.append(f"- {char.name}: {len(changes)} changes")
        
        for loc_id, changes in location_changes.items():
            loc = self.story.get_location(loc_id)
            if loc:
                summaries.append(f"- {loc.name}: {len(changes)} changes")
        
        return "\n".join(summaries) if summaries else "No changes recorded"
