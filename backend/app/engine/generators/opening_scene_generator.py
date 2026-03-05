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

Focus on sensory details, mood, and atmosphere."""
        
        system_prompt = """You are a master storyteller creating immersive opening scenes.
Write with vivid sensory details that make the reader feel present in this world.
Your opening scenes hook readers immediately and establish mood, setting, and story potential."""
        
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt=prompt,
            context_type="scene"
        )
        
        opening_text = response.raw_response or ""
        
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
        
        response = await self.generate(
            system_prompt=system_prompt,
            user_prompt=prompt,
            context_type="scene"
        )
        
        choices_text = response.raw_response or ""
        
        # Parse choices from response
        choice_lines = []
        for line in choices_text.split('\n'):
            line = line.strip()
            if line and any(line.startswith(f"{i}.") for i in range(1, 4)):
                # Remove the number prefix
                choice_text = line.split('.', 1)[1].strip() if '.' in line else line
                if choice_text:
                    choice_lines.append(choice_text)
        
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
