"""Protagonist selector for choosing or developing the main character."""

import logging
from typing import Optional, List
import uuid

from app.models.story import Story
from app.models.story_character import StoryCharacter
from app.models.story_episode import CharacterStateSnapshot
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.protagonist_selector")


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
                    return char
                else:
                    logger.warning(f"User-selected character '{user_choice}' not found")
            
            # 2. Single character
            if len(characters) == 1:
                logger.info(f"Selected protagonist: {characters[0].name} (only character)")
                return characters[0]
            
            # 3. Multiple characters - use AI to select
            if len(characters) > 1:
                selected = await self._select_best_protagonist(characters)
                logger.info(f"Selected protagonist: {selected.name} (AI selection)")
                return selected
            
            # 4. No characters - generate new protagonist
            logger.warning("No characters available, generating new protagonist")
            protag = await self._generate_new_protagonist()
            logger.info(f"Generated new protagonist: {protag.name}")
            return protag
            
        except Exception as e:
            logger.error(f"Failed to select/develop protagonist: {e}", exc_info=True)
            raise ValueError(f"Protagonist selection failed: {str(e)}")
    
    async def _select_best_protagonist(
        self,
        characters: List[StoryCharacter]
    ) -> StoryCharacter:
        """Use AI to analyze characters and select best protagonist.
        
        Args:
            characters: List of available characters
            
        Returns:
            The character best suited as protagonist
        """
        try:
            # Build character descriptions
            char_descriptions = []
            for i, char in enumerate(characters, 1):
                char_descriptions.append(
                    f"{i}. {char.name}\n"
                    f"   Description: {char.description}\n"
                    f"   Background: {char.background}"
                )
            
            # Build prompt
            prompt = f"""Analyze these characters and select the BEST protagonist for the story:

Story: {self.story.title}
Description: {self.story.description}

CHARACTERS:
{chr(10).join(char_descriptions)}

Which character (by number) is the best choice as protagonist and why?

Respond with:
- NUMBER: The character number (1, 2, etc.)
- REASON: Why they make a great protagonist
- DEVELOPMENT: How to develop them further as protagonist"""
            
            # Call AI
            response = await self.generator.generate(
                system_prompt="""You are a story structure expert.
Analyze characters and select the one with the most potential as a protagonist.
Consider growth potential, complexity, and ability to drive the narrative.""",
                user_prompt=prompt,
                context_type="character"
            )
            
            if response.error:
                # Fallback to first character
                logger.warning(f"AI selection failed: {response.error}, using first character")
                return characters[0]
            
            # Try to extract character number from response
            selection_index = self._parse_selection(response.raw_response, len(characters))
            
            selected = characters[selection_index]
            
            # Optionally enhance selected character with AI development ideas
            if hasattr(response, 'raw_response'):
                enhanced = await self._enhance_protagonist_description(selected, response)
                selected = enhanced
            
            return selected
            
        except Exception as e:
            logger.warning(f"AI protagonist selection failed: {e}, using first character")
            return characters[0]
    
    async def _generate_new_protagonist(self) -> StoryCharacter:
        """Generate a brand new protagonist character.
        
        Returns:
            A newly created StoryCharacter as protagonist
        """
        try:
            # Build prompt
            prompt = f"""Create a compelling protagonist for this story:

Title: {self.story.title}
Description: {self.story.description}

The protagonist should:
- Be interesting and relatable
- Have clear goals and motivations
- Have room for growth and change
- Fit the world and story setting
- Drive the narrative forward

Provide a detailed character profile for the protagonist."""
            
            # Generate
            response = await self.generator.generate(
                system_prompt="""You are a character creation expert designing compelling protagonists.
Create a character that will drive the story forward and engage readers.""",
                user_prompt=prompt,
                context_type="character"
            )
            
            if response.error:
                raise ValueError(f"Protagonist generation failed: {response.error}")
            
            # Extract character details
            name = getattr(response, 'displayed_name', 'The Protagonist')
            description = getattr(response, 'short_description', 'A mysterious figure')
            background = getattr(response, 'background', 'To be discovered')
            
            # Create character
            protag = StoryCharacter(
                story=self.story,
                id=f"char_{self.story.id}_protag",
                story_id=self.story.id,
                name=name,
                description=description,
                background=background,
                avatar_color="#4ECDC4"  # Distinctive color for protagonist
            )
            protag.save()
            
            return protag
            
        except Exception as e:
            logger.error(f"Failed to generate new protagonist: {e}", exc_info=True)
            raise ValueError(f"Protagonist generation failed: {str(e)}")
    
    async def _enhance_protagonist_description(
        self,
        character: StoryCharacter,
        ai_response: any
    ) -> StoryCharacter:
        """Enhance protagonist description with AI development ideas.
        
        Args:
            character: The selected protagonist
            ai_response: AI response with development ideas
            
        Returns:
            Updated character with enhanced description
        """
        try:
            # Extract development notes from response
            if hasattr(ai_response, 'raw_response'):
                # Update character description with key traits if available
                if hasattr(ai_response, 'personality_traits'):
                    traits_str = ", ".join(ai_response.personality_traits[:3])
                    character.description += f"\n\nKey Traits: {traits_str}"
                
                if hasattr(ai_response, 'goals'):
                    goal = ai_response.goals[0] if ai_response.goals else ""
                    if goal:
                        character.description += f"\n\nPrimary Goal: {goal}"
            
            character.save()
            return character
            
        except Exception as e:
            logger.debug(f"Failed to enhance protagonist: {e}")
            return character
    
    def _parse_selection(self, response_text: str, char_count: int) -> int:
        """Parse character selection from AI response.
        
        Args:
            response_text: Raw AI response text
            char_count: Number of characters available
            
        Returns:
            Index of selected character (0-based)
        """
        import re
        
        # Look for patterns like "Character 1", "NUMBER: 1", "Option 2", etc.
        patterns = [
            r'[Cc]haracter\s+(\d+)',
            r'[Nn]umber\s*:\s*(\d+)',
            r'[Oo]ption\s+(\d+)',
            r'#(\d+)',
            r'\((\d+)\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text)
            if match:
                try:
                    num = int(match.group(1))
                    if 1 <= num <= char_count:
                        return num - 1  # Convert to 0-based index
                except:
                    pass
        
        # Default to first character if no valid selection found
        return 0
