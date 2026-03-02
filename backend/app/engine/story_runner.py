from typing import Dict, List, Optional, Set, Any
import json
import logging
import uuid
from pathlib import Path
from ..models.story import Story
from ..models.story_segment import StorySegment, SegmentStatus
from ..models.story_character import StoryCharacter
from ..models.story_location import StoryLocation
from ..models.story_choice import StoryChoice
from ..models.story_context import StoryContext
from ..models.story_base import LOCAL_DATA_DIR
from ..models.episode_recap import EpisodeRecap
from ..engine.segment_context_builder import SegmentContextBuilder
from ..engine.episode_recap_generator import EpisodeRecapGenerator

logger = logging.getLogger("infinite_story.engine.story_runner")

class StoryRunner:
    """Manages the runtime state of a story and handles the game loop."""

    def __init__(self, story: Story, generator=None):
        self.story = story
        self.current_segment: Optional[StorySegment] = None
        self.visited_segments: Set[str] = set()  # Set of segment IDs we've visited
        self.generator = generator  # Optional TextGenerator for AI-based generation
        self.current_arc_id: Optional[str] = None  # Track current arc for new segments
    
    @property
    def is_running(self) -> bool:
        """Check if the story is still running (has current segment and choices available)."""
        return self.current_segment is not None and len(self.get_available_choices()) > 0
        
    def start(self) -> None:
        """Start the story from the beginning."""
        logger.info(f"Starting story '{self.story.id}' from segment '{self.story.start_segment_id}'")
        if not self.story.start_segment_id:
            raise ValueError("Story has no start segment")
        self.load_all_components(self.story)

        self.current_segment = self.story.get_segment(self.story.start_segment_id)
        if not self.current_segment:
            raise ValueError(f"Start segment '{self.story.start_segment_id}' not found after loading")

        logger.debug(f"Current segment set to '{self.current_segment.id}': {self.current_segment.short_description}")
        # Mark the start segment as visited
        self.visited_segments.add(self.story.start_segment_id)
        
        # Initialize current arc from the start segment (E2-5)
        if self.current_segment.arc_id:
            self.current_arc_id = self.current_segment.arc_id
            logger.debug(f"Set current arc to {self.current_arc_id}")
        
    def get_available_choices(self) -> List[StoryChoice]:
        """Get the choices available in the current segment, sorted by logged clicks then click count."""
        if not self.current_segment:
            return []
            
        # Get choices and sort by logged clicks first, then click count
        choices = list(self.current_segment.outgoing_choices.values())
        # Limit to top 100 choices by click count
        
        # Runtime sort is not a great idea, but here we are
        # Sort by logged clicks first if available
        choices.sort(key=lambda x: (
            x.logged_clicks if hasattr(x, 'logged_clicks') else 0,
            x.click_count if hasattr(x, 'click_count') else 0
        ), reverse=True)
        
        # If all choices have same counts, randomize order
        if all(
            getattr(x, 'logged_clicks', 0) == getattr(choices[0], 'logged_clicks', 0) and
            getattr(x, 'click_count', 0) == getattr(choices[0], 'click_count', 0)
            for x in choices
        ):
            from random import shuffle
            shuffle(choices)
            
        return choices[:100]
        
    def make_choice(self, choice_id: str) -> None:
        """Make a choice and progress the story."""
        if not self.current_segment:
            raise ValueError("No current segment")
            
        # Load the choice
        choice = self.story.get_choice(choice_id)
        if not choice:
            raise ValueError(f"Choice {choice_id} not found")
            
        if choice.from_segment_id != self.current_segment.id:
            raise ValueError(f"Choice {choice_id} is not available in the current segment")
            
        # Load the next segment
        next_segment = self.story.get_segment(choice.to_segment_id)
        if not next_segment:
            raise ValueError(f"Next segment {choice.to_segment_id} not found")
            
        # Move to the next segment
        self.current_segment = next_segment
        self.visited_segments.add(choice.to_segment_id)

    def get_current_state(self) -> dict:
        """Get the current state of the story."""
        return {
            "current_segment": self.current_segment,
            "visited_segments": list(self.visited_segments)
        }
    
    def load_all_components(self, story) -> None:
        """Load all story components (characters, locations, segments, choices, context).

        This method loads all components directly from their storage directories
        and adds them to the story's internal caches.
        """
        logger.info(f"Loading all components for story '{story.id}'")

        # Load all characters
        char_dir = StoryCharacter.get_storage_dir(story.id)
        logger.debug(f"Loading characters from {char_dir}")
        char_count = 0
        for char_file in char_dir.glob("*.json"):
            char_id = char_file.stem
            logger.debug(f"  Loading character: {char_id}")
            character = StoryCharacter.load(story.id, char_id, story)
            if not character:
                raise ValueError(f"Failed to load character {char_id}")
            story.add_character(character)
            char_count += 1
        logger.info(f"Loaded {char_count} characters")

        # Load all locations
        loc_dir = StoryLocation.get_storage_dir(story.id)
        logger.debug(f"Loading locations from {loc_dir}")
        loc_count = 0
        for loc_file in loc_dir.glob("*.json"):
            loc_id = loc_file.stem
            logger.debug(f"  Loading location: {loc_id}")
            location = StoryLocation.load(story.id, loc_id, story)
            if not location:
                raise ValueError(f"Failed to load location {loc_id}")
            story.add_location(location)
            loc_count += 1
        logger.info(f"Loaded {loc_count} locations")

        # Load all segments
        segment_dir = StorySegment.get_storage_dir(story.id)
        logger.debug(f"Loading segments from {segment_dir}")
        seg_count = 0
        for segment_file in segment_dir.glob("*.json"):
            segment_id = segment_file.stem
            logger.debug(f"  Loading segment: {segment_id}")
            segment = StorySegment.load(story.id, segment_id, story)
            if not segment:
                raise ValueError(f"Failed to load segment {segment_id}")
            story.add_segment(segment)
            seg_count += 1
        logger.info(f"Loaded {seg_count} segments")

        # Load all choices
        choice_dir = StoryChoice.get_storage_dir(story.id)
        logger.debug(f"Loading choices from {choice_dir}")
        choice_count = 0
        for choice_file in choice_dir.glob("*.json"):
            choice_id = choice_file.stem
            logger.debug(f"  Loading choice: {choice_id}")
            choice = StoryChoice.load(story.id, choice_id, story)
            if not choice:
                raise ValueError(f"Failed to load choice {choice_id}")
            story.add_choice(choice)
            choice_count += 1
        logger.info(f"Loaded {choice_count} choices")

        # Connect choices to segments
        logger.debug("Connecting choices to segments")
        connected_count = 0
        for choice in story._choices.values():
            # Add choice to source segment's outgoing choices
            if choice.from_segment_id in story._segments:
                story._segments[choice.from_segment_id].add_outgoing_choice(choice)
                logger.debug(f"  Connected choice '{choice.id}' as outgoing from segment '{choice.from_segment_id}'")
                connected_count += 1

            # Add choice to destination segment's incoming choices
            if choice.to_segment_id in story._segments:
                story._segments[choice.to_segment_id].add_incoming_choice(choice)
                logger.debug(f"  Connected choice '{choice.id}' as incoming to segment '{choice.to_segment_id}'")
        logger.info(f"Connected {connected_count} choice-segment relationships")

        context_dir = StoryContext.get_storage_dir(story.id)
        logger.debug(f"Loading context from {context_dir}")
        ctx_count = 0
        for context_file in context_dir.glob("*.json"):
            context_id = context_file.stem
            logger.debug(f"  Loading context: {context_id}")
            context = StoryContext.load(story.id, context_id, story)
            if not context:
                raise ValueError(f"Failed to load context {context_id}")
            story.add_context(context)
            ctx_count += 1
        logger.info(f"Loaded {ctx_count} contexts")
        logger.info(f"Finished loading all components for story '{story.id}'")

    def save_all_components(self, story) -> None:
        """Save all story components (characters, locations, segments, choices, context).
        
        This method saves all components in the story's internal caches to their
        respective storage directories.
        """
        # Save all characters
        for character in story._characters.values():
            character.save()
                
        # Save all locations
        for location in story._locations.values():
            location.save()

        # Save all segments
        for segment in story._segments.values():
            segment.save()

        # Save all choices
        for choice in story._choices.values():
            choice.save()

        # Save story context
        if story._context:
            story._context.save()

    def get_state_file_path(self) -> Path:
        """Get the path to the state file for this story.

        Returns:
            Path to the runner state JSON file
        """
        state_dir = LOCAL_DATA_DIR / self.story.id
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "runner_state.json"

    def save_state(self) -> None:
        """Save the current runner state to disk.

        This saves the current segment ID and visited segments,
        allowing the session to be resumed later.
        """
        state = {
            "current_segment_id": self.current_segment.id if self.current_segment else None,
            "visited_segments": list(self.visited_segments)
        }

        state_file = self.get_state_file_path()
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self) -> bool:
        """Load a previously saved runner state.

        Returns:
            True if state was loaded successfully, False if no saved state exists
        """
        state_file = self.get_state_file_path()

        if not state_file.exists():
            return False

        try:
            with open(state_file, "r") as f:
                state = json.load(f)

            # Restore current segment
            if state.get("current_segment_id"):
                self.current_segment = self.story.get_segment(state["current_segment_id"])

            # Restore visited segments
            self.visited_segments = set(state.get("visited_segments", []))

            return True
        except Exception as e:
            # If loading fails, return False (will start from beginning)
            print(f"Warning: Failed to load state: {e}")
            return False

    def clear_state(self) -> None:
        """Clear the saved state file."""
        state_file = self.get_state_file_path()
        if state_file.exists():
            state_file.unlink()

    def start_from_segment(self, segment_id: str) -> None:
        """Start the story from a specific segment.

        Args:
            segment_id: The ID of the segment to start from

        Raises:
            ValueError: If the segment doesn't exist
        """
        self.load_all_components(self.story)

        segment = self.story.get_segment(segment_id)
        if not segment:
            raise ValueError(f"Segment {segment_id} not found")

        self.current_segment = segment
        self.visited_segments.add(segment_id)
        
        # Initialize current arc from the segment (E2-5)
        if segment.arc_id:
            self.current_arc_id = segment.arc_id
            logger.debug(f"Set current arc to {self.current_arc_id}")
    
    # ========================================================================
    # E1-2: Generation Pipeline
    # ========================================================================
    
    async def traverse_or_generate(
        self,
        choice: StoryChoice
    ) -> StorySegment:
        """Main pipeline decision: traverse existing segment or generate new one.
        
        When a user makes a choice, this decides whether to:
        1. Traverse to an existing segment (if to_segment_id is set)
        2. Generate a new segment (if to_segment_id is null)
        
        Uses choice locking to prevent race conditions during generation.
        
        Args:
            choice: The choice the user made
            
        Returns:
            The destination segment (either existing or newly generated)
            
        Raises:
            ValueError: If destination segment not found or generation fails
        """
        # Case 1: Choice already has a destination
        if choice.to_segment_id:
            dest = self.story.get_segment(choice.to_segment_id)
            if not dest:
                raise ValueError(f"Destination segment {choice.to_segment_id} not found")
            logger.debug(f"Traversing to existing segment {choice.to_segment_id}")
            return dest
        
        # Case 2: Choice needs generation
        # Lock the choice to prevent duplicate generation by other requests
        choice.lock()
        logger.debug(f"Locked choice {choice.id} for generation")
        
        try:
            # Build rich context for generation
            builder = SegmentContextBuilder(self.story)
            context = builder.build_context(
                self.current_segment.id,
                choice.text
            )
            logger.debug(f"Built generation context for choice from segment {self.current_segment.id}")
            
            # Generate new segment using context
            new_segment = await self._generate_segment(context)
            logger.info(f"Generated new segment {new_segment.id}")
            
            # Link choice to new segment
            choice.to_segment_id = new_segment.id
            choice.save()
            logger.debug(f"Linked choice {choice.id} to segment {new_segment.id}")
            
            return new_segment
        
        except Exception as e:
            # Unlock on failure so retry is possible
            logger.error(f"Generation failed: {str(e)}", exc_info=True)
            choice.unlock()
            raise e
        
        finally:
            # Always unlock at the end
            choice.unlock()
            logger.debug(f"Unlocked choice {choice.id}")
    
    async def _generate_segment(self, context: Dict[str, Any]) -> StorySegment:
        """Generate a new story segment using AI and context.
        
        Creates a complete segment with all fields, generates 2 outgoing choices,
        and saves everything to disk.
        
        Args:
            context: Generation context dict from SegmentContextBuilder
            
        Returns:
            The newly created StorySegment
            
        Raises:
            ValueError: If generation fails or segment creation fails
        """
        if not self.current_segment:
            raise ValueError("No current segment set")
        
        try:
            # Build detailed prompt for generation
            prompt = self._build_generation_prompt(context)
            logger.debug(f"Built generation prompt ({len(prompt)} chars)")
            
            # Call AI generator (would need generator initialized in __init__)
            # For now, this creates a placeholder segment
            # In real implementation, would call: response = await self.generator.generate(...)
            
            # Check if this segment transitions to a new episode
            should_transition = context['should_transition_episode']
            
            # Determine episode number and context for new episode
            next_episode_number = context['episode_number']
            next_episode_tone = context['episode_tone']
            next_episode_end_condition = context['episode_end_condition']
            next_segment_number = context['segment_number_in_episode'] + 1
            
            # If transitioning to new episode, generate new episode context via E2-2
            if should_transition and self.generator and self.current_arc_id:
                try:
                    recap_generator = EpisodeRecapGenerator(self.story, self.generator)
                    # Get previous episode recap for continuity
                    prev_recap = EpisodeRecap.load(
                        self.story.id, 
                        f"recap_{self.story.id}_ep{context['episode_number']}_{self.current_arc_id}"
                    ) if context['episode_number'] > 0 else None
                    
                    # Generate new episode context (E2-2)
                    new_ep_context = await recap_generator.generate_new_episode_context(
                        self.current_arc_id,
                        prev_recap
                    )
                    
                    next_episode_number = context['episode_number'] + 1
                    next_episode_tone = new_ep_context.get('tone_tags', [context['episode_tone']])[0]
                    next_episode_end_condition = new_ep_context.get('end_condition', '')
                    next_segment_number = 1  # Reset segment counter for new episode
                    logger.info(f"Generated new episode context for episode {next_episode_number}")
                except Exception as e:
                    logger.warning(f"Failed to generate new episode context: {e}, using defaults")
            
            # Create segment with all fields from context
            segment_id = f"seg_{uuid.uuid4().hex[:12]}"
            new_segment = StorySegment(
                story=self.story,
                id=segment_id,
                short_description="A scene in the story",  # Would come from AI response
                text_blocks=[],  # Would come from AI response
                arc_id=self.current_arc_id,  # Pass arc_id to child segment (E2-5)
                episode_number=next_episode_number,
                episode_tone=next_episode_tone,
                episode_end_condition=next_episode_end_condition,
                segment_number_in_episode=next_segment_number,
                pacing_weight=context['pacing_weight'],
                protagonist_id=context['protagonist_id'],
                parent_segment_id=self.current_segment.id,
                character_states=context.get('character_states', {}),
                change_notes=context.get('accumulated_changes', []),
                end_condition_proximity=0.0,  # Would come from AI response
                triggers_episode_transition=False,  # New segment doesn't trigger transition yet
                status=SegmentStatus.GENERATED,
            )
            logger.debug(f"Created segment {segment_id}")
            
            # Create 2 outgoing choices
            choice_texts = ["Continue forward", "Take a different approach"]  # Would come from AI response
            for i, choice_text in enumerate(choice_texts):
                choice_id = f"choice_{uuid.uuid4().hex[:12]}"
                choice = StoryChoice(
                    story=self.story,
                    id=choice_id,
                    from_segment_id=new_segment.id,
                    to_segment_id=None,
                    text=choice_text,
                )
                choice.save()
                logger.debug(f"Created choice {choice_id}")
            
            # Save segment
            new_segment.save()
            logger.info(f"Saved segment {segment_id} and choices")
            
            return new_segment
        
        except Exception as e:
            logger.error(f"Error in _generate_segment: {str(e)}", exc_info=True)
            raise ValueError(f"Segment generation failed: {str(e)}")
    
    def _build_generation_prompt(self, context: Dict[str, Any]) -> str:
        """Build a detailed prompt for AI generation.
        
        Combines context information into a structured prompt that guides the AI
        to generate a coherent, paced, and consistent story segment.
        
        Args:
            context: Generation context dict from SegmentContextBuilder
            
        Returns:
            A formatted prompt string for the AI
        """
        prev_scenes = "\n".join(context['previous_segments']) if context['previous_segments'] else "(none)"
        changes_str = "\n".join(context['accumulated_changes']) if context['accumulated_changes'] else "(none)"
        
        prompt = f"""You are a creative storyteller continuing a narrative.

EPISODE CONTEXT:
- Episode: {context['episode_number']}
- Tone: {context['episode_tone']}
- End Condition: {context['episode_end_condition']}
- Scene {context['segment_number_in_episode']} of ~20
- Pacing: {context['pacing_weight']:.1%} toward episode end

PREVIOUS SCENES:
{prev_scenes}

CHARACTER STATES:
{json.dumps(context.get('character_states', {}), indent=2)}

ACCUMULATED CHANGES THIS EPISODE:
{changes_str}

USER CHOSE: "{context['user_choice']}"

Generate the next scene that:
1. Follows naturally from the choice
2. Respects character states and changes
3. Maintains the episode tone
4. Advances toward the end condition
5. Leaves room for {20 - context['segment_number_in_episode']} more scenes

Respond with a brief scene description (2-3 sentences).
"""
        return prompt
