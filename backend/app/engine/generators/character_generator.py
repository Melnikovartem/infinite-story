"""Character generator for creating and parsing characters."""

import logging
from typing import List, Optional, Dict, Set, Any
import re
import uuid

from app.models.story import Story
from app.models.story_character import StoryCharacter
from app.models.story_segment import StorySegment
from app.engine.generator import TextGenerator

logger = logging.getLogger("infinite_story.engine.generators.character_generator")


class CharacterGenerator:
    """Generate and parse characters from story context."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize character generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def parse_characters_from_segments(self) -> List[StoryCharacter]:
        """Parse character mentions from existing segment narrative text.
        
        Looks for character references in segment text blocks and creates
        basic character entries for them.
        
        Returns:
            List of parsed StoryCharacter objects
        """
        try:
            logger.info(f"Parsing characters from existing segments")
            
            # Collect all character mentions from segments
            character_mentions: Dict[str, Set[str]] = {}  # char_name -> {context snippets}
            
            for segment in self.story._segments.values():
                if segment.text_blocks:
                    for block in segment.text_blocks:
                        # Extract potential character mentions
                        if block.character:
                            if block.character not in character_mentions:
                                character_mentions[block.character] = set()
                            character_mentions[block.character].add(block.content[:100])
            
            if not character_mentions:
                logger.info("No character mentions found in segments")
                return []
            
            # Create character objects from mentions
            created_chars = []
            for char_name, contexts in character_mentions.items():
                try:
                    # Check if character already exists
                    existing = [c for c in self.story._characters.values() 
                              if c.name.lower() == char_name.lower()]
                    if existing:
                        logger.debug(f"Character '{char_name}' already exists")
                        continue
                    
                    # Create new character
                    char = StoryCharacter(
                        story=self.story,
                        id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                        story_id=self.story.id,
                        name=char_name,
                        description=f"Character mentioned in story as: {', '.join(list(contexts)[:2])}",
                        background="To be developed through story"
                    )
                    char.save()
                    created_chars.append(char)
                    logger.debug(f"Created parsed character: {char_name}")
                except Exception as e:
                    logger.warning(f"Failed to create character '{char_name}': {e}")
            
            logger.info(f"Parsed {len(created_chars)} characters from segments")
            return created_chars
            
        except Exception as e:
            logger.error(f"Failed to parse characters from segments: {e}", exc_info=True)
            raise ValueError(f"Character parsing failed: {str(e)}")
    
    async def generate_initial_characters(
        self,
        count: int = 3,
        user_input: str = ""
    ) -> List[StoryCharacter]:
        """Generate initial characters based on world and arcs.
        
        Args:
            count: Number of characters to generate
            user_input: Optional user guidance for character creation
            
        Returns:
            List of generated StoryCharacter objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {count} initial characters for story")
            
            # Build prompt
            prompt = self._build_character_prompt(count, user_input)
            
            # Generate via AI
            response = await self.generator.generate(
                system_prompt="""You are a character creation expert designing compelling, diverse characters 
with clear motivations, backgrounds, and potential for growth. 
Create characters that will drive the story forward and create interesting conflicts.""",
                user_prompt=prompt,
                context_type="character"
            )
            
            if response.error:
                raise ValueError(f"Character generation failed: {response.error}")
            
            # Parse character details
            char_details = self._parse_character_details(response, count)
            
            # Create and save character objects
            created_chars = []
            for details in char_details:
                char = StoryCharacter(
                    story=self.story,
                    id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    name=details.get('name', 'Unnamed Character'),
                    description=details.get('description', ''),
                    background=details.get('background', ''),
                    avatar_color=self._select_avatar_color()
                )
                char.save()
                created_chars.append(char)
                logger.info(f"Generated character: {char.name}")
            
            return created_chars
            
        except Exception as e:
            logger.error(f"Failed to generate characters: {e}", exc_info=True)
            raise ValueError(f"Character generation failed: {str(e)}")
    
    def _build_character_prompt(self, count: int, user_input: str) -> str:
        """Build prompt for character generation."""
        world_context = ""
        if self.story._context:
            truths = self.story._context.fundamental_truths[:3]
            world_context = f"\nWorld Themes: {', '.join(truths)}"
        
        arc_context = ""
        if self.story._segments:
            # Get any arc info from segments
            segments = list(self.story._segments.values())[:3]
            if segments and segments[0].arc_id:
                arc_context = f"\nStory is set in an arc-based narrative structure"
        
        user_guidance = f"\n\nUser Character Preferences: {user_input}" if user_input else ""
        
        return f"""Create {count} compelling characters for the story: {self.story.title}

Story Description: {self.story.description}
{world_context}
{arc_context}
{user_guidance}

For EACH character, provide:

NAME: A memorable, fitting name

DESCRIPTION: Physical appearance and immediate impression (2-3 sentences)

BACKGROUND: Life story and how they got here (2-3 sentences)

PERSONALITY TRAITS: 3-4 key traits (e.g., cautious, ambitious, compassionate)

GOALS: What do they want? (primary goal for the story)

FEARS: What do they fear most?

SKILLS/ABILITIES: What are they good at?

RELATIONSHIPS: How might they relate to other characters? (general)

CHARACTER ARC POTENTIAL: What could they learn/discover/overcome?

Make sure the characters:
- Are diverse in personality and background
- Have clear motivations
- Can create interesting conflicts with each other
- Have room for growth and change through the story"""
    
    def _parse_character_details(self, response: Any, count: int) -> List[Dict[str, str]]:
        """Parse character details from AI response."""
        details = []
        
        # Try to extract from response
        if hasattr(response, 'displayed_name') and response.displayed_name:
            details.append({
                'name': response.displayed_name,
                'description': getattr(response, 'short_description', ''),
                'background': getattr(response, 'background', '')
            })
        
        # Create placeholder characters if parsing failed
        if len(details) < count:
            character_archetypes = [
                {'name': 'The Hero', 'desc': 'A brave and determined character'},
                {'name': 'The Mentor', 'desc': 'A wise guide with hidden depths'},
                {'name': 'The Ally', 'desc': 'A loyal companion with their own story'},
                {'name': 'The Rival', 'desc': 'A challenging opponent or antagonist'},
            ]
            
            for i in range(count - len(details)):
                if i < len(character_archetypes):
                    arch = character_archetypes[i]
                    details.append({
                        'name': arch['name'],
                        'description': arch['desc'],
                        'background': 'To be developed'
                    })
        
        return details[:count]
    
    def _select_avatar_color(self) -> str:
        """Select a unique avatar color for the character."""
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#6C5CE7", "#A29BFE", "#74B9FF", "#81ECEC", "#FFD93D",
            "#6C567B", "#FF7675", "#FF8C42", "#90BE6D", "#577590"
        ]
        
        # Get colors already in use
        used_colors = set()
        for char in self.story._characters.values():
            if hasattr(char, 'avatar_color'):
                used_colors.add(char.avatar_color)
        
        # Find first unused color
        for color in colors:
            if color not in used_colors:
                return color
        
        # Fallback to random
        import random
        return random.choice(colors)
