"""Prompt building utilities for AI scene generation.

This module handles constructing contextual prompts for the AI text generator,
intelligently filtering and prioritizing information to stay within token limits.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.story_segment import StorySegment

logger = logging.getLogger("infinite_story.utils.prompt_builder")


class ScenePromptBuilder:
    """Builds comprehensive prompts for AI scene generation.
    
    This class takes a story segment and context information and constructs
    a well-structured prompt that provides the AI with relevant information
    while staying mindful of token limits.
    """
    
    def __init__(self, current_segment: 'StorySegment'):
        """Initialize the prompt builder.
        
        Args:
            current_segment: The story segment to build context around
        """
        self.segment = current_segment
        self.story = current_segment.story
    
    def _get_relevant_entity_ids(self, choice_text: str, lookback: int = 3) -> tuple[set[str], set[str]]:
        """Extract relevant character and location IDs based on recent context and choice.

        Args:
            choice_text: The text of the player's choice
            lookback: Number of previous segments to check for mentions

        Returns:
            Tuple of (relevant_character_ids, relevant_location_ids)
        """
        logger.debug("Starting _get_relevant_entity_ids")
        relevant_chars = set()
        relevant_locs = set()

        # Get all character and location names for matching
        logger.debug("Fetching all characters and locations")
        all_chars = {char.id: char.name.lower() for char in self.story.get_all_characters()}
        all_locs = {loc.id: loc.name.lower() for loc in self.story.get_all_locations()}
        logger.debug(f"Found {len(all_chars)} characters and {len(all_locs)} locations")

        # Check choice text for mentions
        logger.debug("Checking choice text for entity mentions")
        choice_lower = choice_text.lower()
        for char_id, char_name in all_chars.items():
            if char_name in choice_lower:
                relevant_chars.add(char_id)
        for loc_id, loc_name in all_locs.items():
            if loc_name in choice_lower:
                relevant_locs.add(loc_id)
        logger.debug(f"Found {len(relevant_chars)} relevant characters and {len(relevant_locs)} relevant locations in choice")

        # Check recent segments for mentions
        logger.debug(f"Checking {lookback} previous segments for mentions")
        segments_to_check = []
        current_segment = self.segment
        for i in range(lookback):
            logger.debug(f"Lookback iteration {i+1}/{lookback}")
            if not current_segment.incoming_choices:
                logger.debug("No incoming choices, stopping lookback")
                break
            first_choice = next(iter(current_segment.incoming_choices.values()))
            if not first_choice.from_segment_id:
                logger.debug("No from_segment_id, stopping lookback")
                break
            prev_segment = self.story.get_segment(first_choice.from_segment_id)
            if not prev_segment:
                logger.debug(f"Could not find segment {first_choice.from_segment_id}, stopping lookback")
                break
            segments_to_check.append(prev_segment)
            current_segment = prev_segment
        logger.debug(f"Will check {len(segments_to_check)} previous segments")

        # Add characters/locations mentioned in recent segments
        logger.debug("Processing previous segments")
        for i, segment in enumerate(segments_to_check):
            logger.debug(f"Processing segment {i+1}/{len(segments_to_check)}: {segment.id}")
            # Add characters present in segment
            relevant_chars.update(segment.characters_present)
            # Add locations present in segment
            relevant_locs.update(segment.locations_present)

            # Check segment text for additional mentions
            logger.debug(f"Getting plain text script for segment {segment.id}")
            segment_text = segment.get_plain_text_script().lower()
            logger.debug(f"Searching through {len(segment_text)} characters of text")
            for char_id, char_name in all_chars.items():
                if char_name in segment_text:
                    relevant_chars.add(char_id)
            for loc_id, loc_name in all_locs.items():
                if loc_name in segment_text:
                    relevant_locs.add(loc_id)
            logger.debug(f"Finished processing segment {segment.id}")

        logger.debug(f"_get_relevant_entity_ids completed: {len(relevant_chars)} chars, {len(relevant_locs)} locs")
        return relevant_chars, relevant_locs

    def build_prompt(self, choice_text: str) -> str:
        """Generate a comprehensive prompt for scene generation.

        This method combines all available context to create a rich prompt for the AI model,
        intelligently filtering to only include relevant characters and locations.

        Args:
            choice_text: The text of the choice that led to this new scene

        Returns:
            A formatted prompt string containing all relevant context
        """
        logger.debug("Starting build_prompt")
        # Get relevant entity IDs based on recent context and choice
        logger.debug("Getting relevant entity IDs")
        relevant_char_ids, relevant_loc_ids = self._get_relevant_entity_ids(choice_text, lookback=3)
        logger.debug(f"Got relevant entities")

        logger.debug(f"Context analysis: {len(relevant_char_ids)} relevant characters, {len(relevant_loc_ids)} relevant locations")
        logger.debug(f"Relevant character IDs: {relevant_char_ids}")
        logger.debug(f"Relevant location IDs: {relevant_loc_ids}")

        # Get story context (condensed)
        logger.debug("Getting story context")
        story_context = self.story._context
        story_context_overview = story_context.get_short_overview() if story_context else ""
        logger.debug("Got story context")

        # Get current story state (last 5 segments instead of 10)
        logger.debug("Getting previous segments")
        prev_segments = self.segment.get_story_segments_before(max_depth=5)
        logger.debug("Getting plain text script")
        content = self.segment.get_plain_text_script()
        logger.debug("Got plain text script")

        # Get character information for those present
        logger.debug("Getting character info for present characters")
        character_info = []
        for char_status in self.segment.characters:
            character = self.story.get_character(char_status.character_id)
            if character:
                character_info.append(f"- {character.name}: {character.description} (Status: {char_status.current_status})")
        logger.debug(f"Got {len(character_info)} character info entries")

        # Get ONLY relevant characters not present
        logger.debug("Getting relevant characters not present")
        relevant_chars_not_present = []
        all_chars = self.story.get_all_characters()
        for char in all_chars:
            if char.id in relevant_char_ids and char.id not in [c.character_id for c in self.segment.characters]:
                relevant_chars_not_present.append(f"- {char.get_short_overview()}")
        logger.debug(f"Got {len(relevant_chars_not_present)} relevant characters not present")

        # Get ONLY relevant locations not present
        logger.debug("Getting relevant locations not present")
        relevant_locs_not_present = []
        all_locs = self.story.get_all_locations()
        for loc in all_locs:
            if loc.id in relevant_loc_ids and loc.id not in self.segment.locations_present:
                relevant_locs_not_present.append(f"- {loc.get_short_overview()}")
        logger.debug(f"Got {len(relevant_locs_not_present)} relevant locations not present")

        # Build prompt with prioritized structure
        prompt = "Generate the next scene based on the player's choice.\n\n"

        # Section 1: Immediate Context (highest priority)
        prompt += "=== CURRENT SCENE ===\n"
        prompt += f"Scene: {self.segment.short_description}\n"
        if self.segment.atmosphere:
            prompt += f"Atmosphere: {self.segment.atmosphere}\n"
        if character_info:
            prompt += f"\nCharacters Present:\n" + "\n".join(character_info) + "\n"
        prompt += f"\nScene Content:\n{content}\n\n"

        # Section 2: Player's Choice (what drives the next scene)
        prompt += "=== PLAYER'S CHOICE ===\n"
        prompt += f"{choice_text}\n\n"

        # Section 3: Recent Story Context
        if prev_segments:
            prompt += "=== RECENT STORY ===\n"
            prompt += f"{prev_segments}\n\n"

        # Section 4: World Context (condensed)
        if story_context_overview:
            prompt += "=== WORLD CONTEXT ===\n"
            prompt += f"{story_context_overview}\n\n"

        # Section 5: Relevant Additional Context (only if relevant entities found)
        if relevant_chars_not_present:
            prompt += "=== RELEVANT CHARACTERS (Available) ===\n"
            prompt += "\n".join(relevant_chars_not_present[:5]) + "\n\n"  # Max 5

        if relevant_locs_not_present:
            prompt += "=== RELEVANT LOCATIONS (Available) ===\n"
            prompt += "\n".join(relevant_locs_not_present[:5]) + "\n\n"  # Max 5

        # Log prompt statistics
        self._log_prompt_stats(prompt, prev_segments, relevant_chars_not_present, relevant_locs_not_present)

        return prompt
    
    def _log_prompt_stats(self, prompt: str, prev_segments: str, relevant_chars: list, relevant_locs: list) -> None:
        """Log statistics about the generated prompt.
        
        Args:
            prompt: The generated prompt string
            prev_segments: The previous segments section
            relevant_chars: List of relevant characters
            relevant_locs: List of relevant locations
        """
        prompt_length = len(prompt)
        approx_tokens = prompt_length // 4  # Rough estimate: 1 token ≈ 4 characters
        logger.info(f"Generated prompt: {prompt_length} chars (~{approx_tokens} tokens)")
        logger.debug(f"Prompt sections: Current scene, Choice, {len(prev_segments.split('-'))-1 if prev_segments else 0} previous segments, " +
                    f"{len(relevant_chars)} relevant chars, {len(relevant_locs)} relevant locs")
