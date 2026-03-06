"""Protagonist selector for choosing or developing the main character."""

import logging
import re
from typing import Optional, List

from app.models.story import Story
from app.models.story_character import StoryCharacter, CharacterRole
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import ResponseSchema, FieldSpec

logger = logging.getLogger("infinite_story.engine.generators.protagonist_selector")


# Schema for protagonist selection (AI picks a number + reasoning)
_SELECTION_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("selected_number", type="int", required=True, aliases=["number", "choice", "character_number", "selection"]),
        FieldSpec("reason", type="str", aliases=["reasoning", "why", "explanation"]),
        FieldSpec("development", type="str", aliases=["development_ideas", "growth"]),
    ],
    expect_array=False,
)

_SELECTION_FALLBACK = {
    "selected_number": 1,
    "reason": "Best fit for the story",
    "development": "",
}

# Schema for new protagonist generation
_PROTAGONIST_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", type="str", required=True, aliases=["character_name", "full_name", "displayed_name"]),
        FieldSpec("description", type="str", required=True, aliases=["short_description", "appearance", "desc"]),
        FieldSpec("background", type="str", required=True, aliases=["backstory", "history"]),
        FieldSpec("personality_traits", type="list", aliases=["personality", "traits"]),
        FieldSpec("goals", type="str", aliases=["goal", "motivation"]),
    ],
    expect_array=False,
)

_PROTAGONIST_FALLBACK = {
    "name": "The Protagonist",
    "description": "A mysterious figure with untapped potential",
    "background": "Origins yet to be discovered",
    "personality_traits": ["determined", "curious"],
    "goals": "Find their purpose",
}


class ProtagonistSelector:
    """Select and develop the protagonist for a story."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize protagonist selector.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def select_or_develop_protagonist(
        self,
        user_choice: Optional[str] = None
    ) -> StoryCharacter:
        """Select protagonist from existing characters or develop new one.
        
        Process:
        1. If user provides character ID, use that
        2. If only one character exists, use that
        3. If multiple characters exist, use AI to select best fit
        4. If no characters exist, generate a new protagonist
        
        Args:
            user_choice: Optional character ID selected by user
            
        Returns:
            The selected or developed StoryCharacter
            
        Raises:
            ValueError: If selection/development fails
        """
        try:
            characters = list(self.story._characters.values())
            
            # 1. User selection
            if user_choice:
                char = self.story.get_character(user_choice)
                if char:
                    logger.info(f"Selected protagonist: {char.name} (user choice)")
                    self._assign_protagonist_role(char)
                    return char
                else:
                    logger.warning(f"User-selected character '{user_choice}' not found")
            
            # 2. Single character
            if len(characters) == 1:
                logger.info(f"Selected protagonist: {characters[0].name} (only character)")
                self._assign_protagonist_role(characters[0])
                return characters[0]
            
            # 3. Multiple characters - use AI to select
            if len(characters) > 1:
                selected = await self._select_best_protagonist(characters)
                logger.info(f"Selected protagonist: {selected.name} (AI selection)")
                self._assign_protagonist_role(selected)
                return selected
            
            # 4. No characters - generate new protagonist
            logger.warning("No characters available, generating new protagonist")
            protag = await self._generate_new_protagonist()
            logger.info(f"Generated new protagonist: {protag.name}")
            self._assign_protagonist_role(protag)
            return protag
            
        except Exception as e:
            logger.error(f"Failed to select/develop protagonist: {e}", exc_info=True)
            raise ValueError(f"Protagonist selection failed: {str(e)}")
    
    def _assign_protagonist_role(self, character: StoryCharacter) -> None:
        """Set the PROTAGONIST role on the selected character and save."""
        character.role = CharacterRole.PROTAGONIST
        character.save()
        logger.debug(f"Assigned PROTAGONIST role to {character.name}")
    
    async def _select_best_protagonist(
        self,
        characters: List[StoryCharacter]
    ) -> StoryCharacter:
        """Use AI to analyze characters and select best protagonist."""
        try:
            # Build character descriptions
            char_descriptions = []
            for i, char in enumerate(characters, 1):
                char_descriptions.append(
                    f"{i}. {char.name}\n"
                    f"   Description: {char.description}\n"
                    f"   Background: {char.background}"
                )
            
            prompt = f"""Analyze these characters and select the BEST protagonist for the story:

Story: {self.story.title}
Description: {self.story.description}

CHARACTERS:
{chr(10).join(char_descriptions)}

Which character (by number) is the best choice as protagonist and why?"""

            data = await self.generator.generate_structured(
                system_prompt="""You are a story structure expert.
Analyze characters and select the one with the most potential as a protagonist.
Consider growth potential, complexity, and ability to drive the narrative.""",
                user_prompt=prompt,
                schema=_SELECTION_SCHEMA,
                fallback_defaults=[_SELECTION_FALLBACK],
            )
            
            # Extract selection number
            selection_num = data.get("selected_number", 1)
            if isinstance(selection_num, str):
                # Try to parse a number from the string
                match = re.search(r'\d+', str(selection_num))
                selection_num = int(match.group()) if match else 1
            
            # Convert to 0-based index, clamp to valid range
            index = max(0, min(int(selection_num) - 1, len(characters) - 1))
            return characters[index]
            
        except Exception as e:
            logger.warning(f"AI protagonist selection failed: {e}, using first character")
            return characters[0]
    
    async def _generate_new_protagonist(self) -> StoryCharacter:
        """Generate a brand new protagonist character."""
        try:
            prompt = f"""Create a compelling protagonist for this story:

Title: {self.story.title}
Description: {self.story.description}

The protagonist should:
- Be interesting and relatable
- Have clear goals and motivations
- Have room for growth and change
- Fit the world and story setting
- Drive the narrative forward"""

            data = await self.generator.generate_structured(
                system_prompt="""You are a character creation expert designing compelling protagonists.
Create a character that will drive the story forward and engage readers.""",
                user_prompt=prompt,
                schema=_PROTAGONIST_SCHEMA,
                fallback_defaults=[_PROTAGONIST_FALLBACK],
            )
            
            protag = StoryCharacter(
                story=self.story,
                id=f"char_{self.story.id}_protag",
                story_id=self.story.id,
                name=data.get("name", "The Protagonist"),
                description=data.get("description", "A mysterious figure"),
                background=data.get("background", "To be discovered"),
                personality=data.get("personality_traits") or [],
                goals=data.get("goals", ""),
                role=CharacterRole.PROTAGONIST,
                avatar_color="#4ECDC4",
            )
            protag.save()
            return protag
            
        except Exception as e:
            logger.error(f"Failed to generate new protagonist: {e}", exc_info=True)
            raise ValueError(f"Protagonist generation failed: {str(e)}")
