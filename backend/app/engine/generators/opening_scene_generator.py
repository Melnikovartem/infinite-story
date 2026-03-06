"""Generator for the opening scene of a story."""

import logging
from typing import List
import uuid

from app.engine.generator import TextGenerator
from app.models.story import Story
from app.models.story_context import StoryContext
from app.models.story_segment import StorySegment
from app.models.story_choice import StoryChoice
from app.models.text_types import TextBlock

logger = logging.getLogger("infinite_story.generators.opening_scene")


class OpeningSceneGenerator(TextGenerator):
    """Generate opening scene and choices for a story."""

    async def generate_opening_scene(
        self,
        story: Story,
        world_context: StoryContext
    ) -> StorySegment:
        """Generate the opening scene for the story.
        
        Args:
            story: The story object
            world_context: World context with description and plot
            
        Returns:
            The opening story segment
        """
        logger.info(f"Generating opening scene for story: {story.title}")
        
        # Build world summary for the prompt
        world_description = ""
        if hasattr(world_context, 'world_description') and world_context.world_description:
            world_description = world_context.world_description
        
        plot_summary = ""
        if hasattr(world_context, 'plot_description') and world_context.plot_description:
            plot_summary = world_context.plot_description
        
        # Get factions context
        factions_context = ""
        factions = story.get_all_factions()
        if factions:
            factions_context = "\n\nKey Factions:\n"
            for fac in factions[:3]:  # Limit to 3 for context
                fac_desc = fac.to_context_short()
                factions_context += f"- {fac_desc}\n"
        
        # Get locations context
        locations_context = ""
        locations = story.get_all_locations()
        if locations:
            locations_context = "\n\nKey Locations:\n"
            for loc in locations[:3]:  # Limit to 3 for context
                loc_name = loc.name if hasattr(loc, 'name') else str(loc)
                loc_desc = loc.description if hasattr(loc, 'description') else ""
                locations_context += f"- {loc_name}: {loc_desc[:100]}\n"
        
        prompt = f"""Create a CAPTIVATING opening scene for this story:

Title: {story.title}
Genre: {story.genre}
Description: {story.description}

WORLD:
{world_description}

PLOT:
{plot_summary}
{factions_context}
{locations_context}

Write an opening scene that:
- Immediately draws the reader into this world
- Establishes the atmosphere and mood
- Shows the world as a living, breathing character
- Hints at the core conflicts or central story
- Creates compelling hooks that make readers want to continue
- Is vivid, atmospheric, and 2-3 paragraphs long
- Sets the stage for player choices

Focus on sensory details, mood, and atmosphere.
Return ONLY the narrative text, no JSON, no formatting."""
        
        system_prompt = """You are a master storyteller creating immersive opening scenes.
Write with vivid sensory details that make the reader feel present in this world.
Your opening scenes hook readers immediately and establish mood, setting, and story potential."""
        
        # Call _generate_content directly — we want raw narrative text,
        # not a structured JSON response (avoids scene-schema injection).
        try:
            opening_text = await self._generate_content(system_prompt, prompt)
            opening_text = opening_text.strip() if opening_text else ""
        except Exception as e:
            logger.warning(f"Opening scene generation failed: {e}")
            opening_text = ""
        
        # If extraction failed, create a sensible fallback
        if not opening_text or len(opening_text) < 50:
            opening_text = self._create_fallback_scene(story, world_context)
        
        # Create opening segment
        opening_segment = StorySegment(
            id="opening",
            story_id=story.id,
            story=story,
            short_description="The Story Begins",
            atmosphere="atmospheric",
            episode_number=1
        )
        
        # Add text block
        text_block = TextBlock(
            type="narrator_describing",
            content=opening_text,
            emotion="mysterious"
        )
        opening_segment.text_blocks = [text_block]
        
        logger.info("Opening scene generated successfully")
        return opening_segment

    async def generate_opening_choices(
        self,
        story: Story,
        world_context: StoryContext,
        opening_segment: StorySegment
    ) -> List[StoryChoice]:
        """Generate opening choices for the story.
        
        Args:
            story: The story object
            world_context: World context
            opening_segment: The opening segment
            
        Returns:
            List of story choices
        """
        logger.info("Generating opening choices")
        
        opening_text = ""
        if opening_segment.text_blocks:
            opening_text = opening_segment.text_blocks[0].content if hasattr(opening_segment.text_blocks[0], 'content') else str(opening_segment.text_blocks[0])
        
        # Get factions for context
        factions_context = ""
        factions = story.get_all_factions()
        if factions:
            factions_context = "\nFactions present: "
            factions_context += ", ".join([f.name if hasattr(f, 'name') else str(f) for f in factions[:3]])
        
        prompt = f"""Generate 2-3 compelling opening choices for this story:

Story: {story.title}
Genre: {story.genre}
Description: {story.description}{factions_context}

Opening Scene (first 200 chars):
{opening_text[:200]}...

Create realistic story choices that:
- Branch the narrative in different directions
- Let the player engage meaningfully with the world
- Create meaningful consequences
- Move the story forward
- Each should be 1-2 sentences

Format as a numbered list (1. choice text, 2. choice text, 3. choice text)
ONLY output the choices, no explanations."""
        
        system_prompt = """You are a narrative designer creating compelling story choices.
The choices should feel natural, consequential, and offer meaningful branching paths."""
        
        # Call _generate_content directly — we want a numbered list of choices,
        # not structured JSON.
        try:
            choices_text = await self._generate_content(system_prompt, prompt)
            choices_text = choices_text.strip() if choices_text else ""
        except Exception as e:
            logger.warning(f"Opening choices generation failed: {e}")
            choices_text = ""
        
        # Parse choices from response
        choice_lines = []
        for line in choices_text.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 4)):
                # Remove the number prefix
                choice_text = line.split('.', 1)[1].strip() if '.' in line else line
                if choice_text and len(choice_text) > 5:  # Ensure meaningful text
                    choice_lines.append(choice_text)
        
        # If no choices parsed, create fallback choices
        if not choice_lines:
            choice_lines = self._create_fallback_choices(story)
        
        # Create choice objects
        choices_list = []
        for i, choice_text in enumerate(choice_lines[:3]):  # Max 3 choices
            choice_id = f"choice_{uuid.uuid4().hex[:8]}"
            follow_segment_id = f"segment_{uuid.uuid4().hex[:8]}"
            
            choice = StoryChoice(
                id=choice_id,
                story_id=story.id,
                story=story,
                from_segment_id=opening_segment.id,
                to_segment_id=follow_segment_id,
                text=choice_text
            )
            choices_list.append(choice)
        
        logger.info(f"Generated {len(choices_list)} opening choices")
        return choices_list
    
    def _create_fallback_scene(self, story: Story, world_context: StoryContext) -> str:
        """Create a sensible fallback opening scene if generation fails.
        
        Args:
            story: The story
            world_context: World context
            
        Returns:
            Fallback narrative text
        """
        world_desc = "a mysterious world" 
        if hasattr(world_context, 'worldbuilding') and isinstance(world_context.worldbuilding, dict):
            world_desc = world_context.worldbuilding.get('world_description', world_desc)
        
        return f"""You find yourself standing at the threshold of an extraordinary moment. Around you lies {world_desc}. The air crackles with possibility and tension. 

Your journey is about to begin, and with it comes a weight of consequence—the choices you make here will ripple through everything that follows. You can feel it, deep in your bones. This is not just another moment. This is the moment that changes everything.

The path ahead splits in several directions, each promising a different adventure, a different story waiting to unfold. What will you do?"""
    
    def _create_fallback_choices(self, story: Story) -> List[str]:
        """Create sensible fallback choices if generation fails.
        
        Args:
            story: The story
            
        Returns:
            List of fallback choice texts
        """
        factions = story.get_all_factions()
        locations = story.get_all_locations()
        
        choices = [
            "Venture forward cautiously, ready for whatever awaits.",
            "Seek out more information before committing to action.",
            "Trust your instincts and follow the path that calls to you."
        ]
        
        # Customize based on available context
        if factions:
            choices[0] = f"Join forces with the {factions[0].name if hasattr(factions[0], 'name') else 'first faction'}."
        
        if locations:
            choices[1] = f"Make your way toward {locations[0].name if hasattr(locations[0], 'name') else 'the unknown location'}."
        
        return choices
