"""Enhanced character generator for creating fraction-based and independent characters."""

import logging
import json
import uuid
import random
from typing import List, Dict, Any
from app.models.story import Story
from app.models.story_character import StoryCharacter, CharacterRole
from app.models.story_fraction import StoryFraction
from app.models.story_location import StoryLocation
from app.models.story_context import StoryContext
from app.engine.generator import TextGenerator
from app.models.text_types import StoryShapeResponse

logger = logging.getLogger("infinite_story.engine.generators.character_generator_new")


class CharacterGeneratorNew:
    """Generate characters for fractions and as independent entities."""
    
    def __init__(self, story: Story, generator: TextGenerator):
        """Initialize character generator.
        
        Args:
            story: The Story instance
            generator: AI text generator for content generation
        """
        self.story = story
        self.generator = generator
    
    async def generate_fraction_characters(
        self,
        world_context: StoryContext,
        fractions: List[StoryFraction],
        locations: List[StoryLocation],
        story_shape: StoryShapeResponse
    ) -> List[StoryCharacter]:
        """Generate characters assigned to specific fractions.
        
        Args:
            world_context: StoryContext with world data
            fractions: List of StoryFraction objects
            locations: List of StoryLocation objects
            story_shape: StoryShapeResponse with character counts
            
        Returns:
            List of StoryCharacter objects assigned to fractions
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating fraction-based characters for story '{self.story.id}'")
            
            all_characters = []
            
            # Generate characters for each fraction
            for fraction in fractions:
                # Randomly select count from range
                char_count = random.randint(
                    story_shape.characters_per_fraction.get('min', 2),
                    story_shape.characters_per_fraction.get('max', 4)
                )
                
                logger.debug(f"Generating {char_count} characters for fraction '{fraction.title}'")
                
                # Build prompt for this fraction
                prompt = self._build_fraction_character_prompt(
                    self.story.title,
                    self.story.genre,
                    world_context,
                    fraction,
                    locations,
                    char_count
                )
                
                # Generate via AI
                response_text = await self.generator.generate(
                    system_prompt="""You are a character creator specializing in vivid, compelling characters.
Create characters that drive the story forward.
Return ONLY valid JSON array with no additional text.""",
                    user_prompt=prompt,
                    context_type="character"
                )
                
                if hasattr(response_text, 'error') and response_text.error:
                    logger.warning(f"Character generation failed for fraction: {response_text.error}")
                    continue
                
                # Parse response
                character_data_list = self._parse_characters_response(response_text, char_count)
                
                # Create character objects
                for character_data in character_data_list:
                    character = StoryCharacter(
                        id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                        story_id=self.story.id,
                        story=self.story,
                        name=character_data.get('name', 'Unknown'),
                        description=character_data.get('short_description', ''),
                        full_description=character_data.get('full_description', ''),
                        background=character_data.get('background', ''),
                        fraction_id=fraction.id,
                        associated_locations=character_data.get('associated_locations', []),
                        role=self._parse_role(character_data.get('role', 'minor')),
                        personality=character_data.get('personality', []),
                        goals=character_data.get('goals', ''),
                        relationships=character_data.get('relationships', {})
                    )
                    all_characters.append(character)
                    fraction.character_ids.append(character.id)
                    logger.debug(f"Created character: {character.name} for fraction {fraction.title}")
            
            logger.info(f"Generated {len(all_characters)} fraction-based characters")
            return all_characters
            
        except Exception as e:
            logger.error(f"Failed to generate fraction characters: {e}", exc_info=True)
            raise ValueError(f"Fraction character generation failed: {str(e)}")
    
    async def generate_independent_characters(
        self,
        world_context: StoryContext,
        fractions: List[StoryFraction],
        locations: List[StoryLocation],
        existing_characters: List[StoryCharacter],
        story_shape: StoryShapeResponse
    ) -> List[StoryCharacter]:
        """Generate independent characters not tied to fractions.
        
        Args:
            world_context: StoryContext with world data
            fractions: List of StoryFraction objects
            locations: List of StoryLocation objects
            existing_characters: Already-generated fraction characters
            story_shape: StoryShapeResponse with independent character count
            
        Returns:
            List of independent StoryCharacter objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {story_shape.num_independent_characters} independent characters")
            
            # Build prompt
            prompt = self._build_independent_character_prompt(
                self.story.title,
                self.story.genre,
                world_context,
                fractions,
                locations,
                existing_characters,
                story_shape.num_independent_characters
            )
            
            # Generate via AI
            response_text = await self.generator.generate(
                system_prompt="""You are a character creator specializing in complex, compelling characters.
Create independent characters who operate across the entire story.
Return ONLY valid JSON array with no additional text.""",
                user_prompt=prompt,
                context_type="character"
            )
            
            if hasattr(response_text, 'error') and response_text.error:
                raise ValueError(f"Independent character generation failed: {response_text.error}")
            
            # Parse response
            character_data_list = self._parse_characters_response(
                response_text,
                story_shape.num_independent_characters
            )
            
            # Create character objects
            all_characters = []
            for character_data in character_data_list:
                character = StoryCharacter(
                    id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    story=self.story,
                    name=character_data.get('name', 'Unknown'),
                    description=character_data.get('short_description', ''),
                    full_description=character_data.get('full_description', ''),
                    background=character_data.get('background', ''),
                    fraction_id=None,  # Independent - no fraction
                    associated_locations=character_data.get('associated_locations', []),
                    role=self._parse_role(character_data.get('role', 'minor')),
                    personality=character_data.get('personality', []),
                    goals=character_data.get('goals', ''),
                    relationships=character_data.get('relationships', {})
                )
                all_characters.append(character)
                logger.debug(f"Created independent character: {character.name}")
            
            logger.info(f"Generated {len(all_characters)} independent characters")
            return all_characters
            
        except Exception as e:
            logger.error(f"Failed to generate independent characters: {e}", exc_info=True)
            raise ValueError(f"Independent character generation failed: {str(e)}")
    
    def _build_fraction_character_prompt(
        self,
        title: str,
        genre: str,
        world_context: StoryContext,
        fraction: StoryFraction,
        locations: List[StoryLocation],
        char_count: int
    ) -> str:
        """Build prompt for generating characters for a specific fraction."""
        
        # Build locations text
        locations_text = "\n".join([f"- {loc.name}: {loc.description}" for loc in locations[:5]])
        
        # Build other fractions context
        other_fractions = f"\n\nOther Fractions in the Story:\n- {fraction.title} (current)"
        
        return f"""Create {char_count} compelling characters for this story fraction.

Story: {title}
Genre: {genre}

Fraction: {fraction.title}
Goal: {fraction.main_goal}
{fraction.to_context_full()}

Locations in World:
{locations_text}

Return ONLY a valid JSON array (no markdown, no explanation) like this:
[
  {{
    "name": "Character Name",
    "short_description": "Physical appearance and impression",
    "full_description": "3-5 sentences with backstory",
    "background": "Character's history",
    "role": "protagonist|antagonist|ally|minor",
    "personality": ["trait1", "trait2", "trait3"],
    "goals": "What does this character want?",
    "associated_locations": ["location_name1", "location_name2"],
    "relationships": {{"character_name": "relationship description"}}
  }},
  ...
]

For each character:
- NAME: Character's name
- SHORT_DESCRIPTION: Physical appearance and immediate impression
- FULL_DESCRIPTION: 3-5 sentences with rich background
- BACKGROUND: Their history and how they got here
- ROLE: protagonist, antagonist, ally, or minor
- PERSONALITY: 3-4 key personality traits
- GOALS: What do they want in this fraction?
- ASSOCIATED_LOCATIONS: Which locations are they in?
- RELATIONSHIPS: How do they relate to others in the fraction?

Characters should be tied to this fraction's goal and conflict."""
    
    def _build_independent_character_prompt(
        self,
        title: str,
        genre: str,
        world_context: StoryContext,
        fractions: List[StoryFraction],
        locations: List[StoryLocation],
        existing_characters: List[StoryCharacter],
        char_count: int
    ) -> str:
        """Build prompt for generating independent characters."""
        
        # Build fractions text
        fractions_text = "\n".join([f"{i}. {f.title}: {f.short_description}" for i, f in enumerate(fractions, 1)])
        
        # Build locations text
        locations_text = "\n".join([f"- {loc.name}: {loc.description}" for loc in locations[:5]])
        
        # Build existing characters brief
        existing_chars_text = "\n".join([f"- {c.name}: {c.description}" for c in existing_characters[:5]])
        
        return f"""Create {char_count} independent characters who operate across the entire story.

Story: {title}
Genre: {genre}

Fractions:
{fractions_text}

Locations:
{locations_text}

Existing Characters (for relationship building):
{existing_chars_text}

Return ONLY a valid JSON array (no markdown, no explanation) with same format as before.

These characters:
- Operate independently across all fractions
- May be antagonists, neutrals, or side characters
- Have their own goals/agendas
- Can interact with faction-based characters
- Fill important narrative roles not tied to specific fractions"""
    
    def _parse_characters_response(self, response: Any, num_expected: int) -> List[Dict[str, Any]]:
        """Parse characters response into structured data."""
        
        # Extract content
        content = response
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        else:
            content = str(response)
        
        logger.debug(f"Characters response content: {content[:200]}")
        
        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            json_str = str(content)
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0]
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0]
            
            data = json.loads(json_str.strip())
            
            # Validate it's a list
            if isinstance(data, list) and len(data) > 0:
                return data[:num_expected]
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning(f"JSON parsing failed: {e}")
        
        # Fallback: create default characters
        logger.warning(f"Using default {num_expected} characters")
        defaults = [
            {
                "name": "The Hero",
                "short_description": "A determined figure with purpose",
                "full_description": "A character driven by conviction. They embody the faction's ideals and drive its story forward.",
                "background": "A past that led them to this moment",
                "role": "protagonist",
                "personality": ["determined", "brave", "principled"],
                "goals": "Achieve the fraction's main goal",
                "associated_locations": [],
                "relationships": {}
            },
            {
                "name": "The Conflicted One",
                "short_description": "Someone torn between different sides",
                "full_description": "A character with internal conflict. Their journey becomes central to the fraction's themes.",
                "background": "A history that creates inner turmoil",
                "role": "ally",
                "personality": ["uncertain", "thoughtful", "growing"],
                "goals": "Find their true path",
                "associated_locations": [],
                "relationships": {}
            }
        ]
        
        return defaults[:num_expected]
    
    def _parse_role(self, role_str: str) -> CharacterRole:
        """Parse role string to CharacterRole enum."""
        role_lower = str(role_str).lower()
        if 'protagonist' in role_lower:
            return CharacterRole.PROTAGONIST
        elif 'antagonist' in role_lower:
            return CharacterRole.ANTAGONIST
        elif 'ally' in role_lower:
            return CharacterRole.ALLY
        else:
            return CharacterRole.MINOR
