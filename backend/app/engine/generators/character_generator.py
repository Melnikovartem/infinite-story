"""Character generator for creating and parsing characters."""

import logging
import uuid
from typing import List, Optional, Dict, Any

from app.models.story import Story
from app.models.story_character import StoryCharacter
from app.models.story_segment import StorySegment
from app.engine.generator import TextGenerator
from app.utils.ai_response_parser import AIResponseParser, ResponseSchema, FieldSpec, OutputFormat

logger = logging.getLogger("infinite_story.engine.generators.character_generator")


# Schema for character generation
CHARACTER_SCHEMA = ResponseSchema(
    fields=[
        FieldSpec("name", type="str", required=True, aliases=["character_name", "full_name"]),
        FieldSpec("description", type="str", required=True, aliases=["appearance", "physical", "desc"]),
        FieldSpec("background", type="str", required=True, aliases=["backstory", "history", "life_story"]),
        FieldSpec("personality_traits", type="list", aliases=["personality", "traits", "key_traits"]),
        FieldSpec("goals", type="str", aliases=["goal", "motivation", "desire", "wants"]),
        FieldSpec("fears", type="str", aliases=["fear", "weakness", "vulnerability"]),
        FieldSpec("skills", type="list", aliases=["abilities", "skills_abilities", "talents"]),
    ],
    expect_array=True,
    min_items=1,
    max_items=10,
    item_tag="character",
    root_tag="characters",
)

# Example for prompt instruction
CHARACTER_EXAMPLE = {
    "name": "Kael Ashford",
    "description": "A lean, sharp-eyed woman in her thirties with burn scars trailing up her left arm and silver-streaked hair pulled into a tight braid",
    "background": "Former blacksmith's apprentice who discovered she could sense metal through touch. Fled her village after accidentally collapsing a mine shaft. Now works as a freelance surveyor, mapping underground resources for whoever pays.",
    "personality_traits": ["pragmatic", "self-reliant", "quietly compassionate", "distrustful of authority"],
    "goals": "Find a way to control her ability without destroying what she touches",
    "fears": "Losing control and hurting someone she cares about",
    "skills": ["metalworking", "geological surveying", "hand-to-hand combat", "wilderness survival"],
}

# Fallback defaults
CHARACTER_FALLBACK = {
    "name": "Unnamed Character",
    "description": "A mysterious figure whose nature remains to be discovered",
    "background": "Origins unknown — to be revealed through the story",
    "personality_traits": ["determined", "cautious"],
    "goals": "Survive and find purpose",
    "fears": "The unknown",
    "skills": ["adaptability"],
}


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
            character_mentions: Dict[str, set] = {}  # char_name -> {context snippets}
            
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
        user_input: str = "",
        factions: Optional[List[Any]] = None
    ) -> List[StoryCharacter]:
        """Generate initial characters based on world and arcs.
        
        Args:
            count: Number of characters to generate
            user_input: Optional user guidance for character creation
            factions: Optional list of factions to assign characters to
            
        Returns:
            List of generated StoryCharacter objects
            
        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info(f"Generating {count} initial characters for story")
            
            # Build schema with correct count
            schema = ResponseSchema(
                fields=CHARACTER_SCHEMA.fields,
                expect_array=True,
                min_items=count,
                max_items=count + 2,
                item_tag="character",
                root_tag="characters",
            )
            
            prompt = self._build_character_prompt(count, user_input, schema)
            
            fallback_defaults = [
                {**CHARACTER_FALLBACK, "name": name}
                for name in ["The Protagonist", "The Mentor", "The Rival"][:count]
            ]
            parsed_chars = await self.generator.generate_structured(
                system_prompt="""You are a character creation expert designing compelling, diverse characters 
with clear motivations, backgrounds, and potential for growth. 
Create characters that will drive the story forward and create interesting conflicts.""",
                user_prompt=prompt,
                schema=schema,
                fallback_defaults=fallback_defaults,
            )
            
            logger.debug(f"Parsed {len(parsed_chars)} character outlines")
            
            # Create and save character objects
            created_chars = []
            for i, raw in enumerate(parsed_chars[:count]):
                # Assign faction if available
                faction_id = None
                if factions and i < len(factions):
                    faction_id = factions[i].id
                
                # First character is major, rest are minor initially
                importance_tier = "major" if i == 0 else "minor"
                
                char = StoryCharacter(
                    story=self.story,
                    id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                    story_id=self.story.id,
                    name=raw.get('name', CHARACTER_FALLBACK['name']),
                    description=raw.get('description', CHARACTER_FALLBACK['description']),
                    background=raw.get('background', CHARACTER_FALLBACK['background']),
                    personality=raw.get('personality_traits', []),
                    goals=raw.get('goals', ''),
                    avatar_color=self._select_avatar_color(),
                    faction_id=faction_id,
                    importance_tier=importance_tier,
                )
                char.save()
                created_chars.append(char)
                logger.info(f"Generated character: {char.name} (faction: {faction_id}, tier: {importance_tier})")
            
            return created_chars
            
        except Exception as e:
            logger.error(f"Failed to generate characters: {e}", exc_info=True)
            raise ValueError(f"Character generation failed: {str(e)}")
    
    def _build_character_prompt(self, count: int, user_input: str, schema: ResponseSchema) -> str:
        """Build prompt for character generation."""
        world_context = ""
        if self.story._context:
            truths = self.story._context.fundamental_truths[:3]
            world_context = f"\nWorld Themes: {', '.join(truths)}"
        
        faction_context = ""
        all_factions = self.story.get_all_factions()
        if all_factions:
            faction_lines = [f"- {f.name}: {f.description}" for f in all_factions[:5]]
            faction_context = f"\nFactions:\n" + "\n".join(faction_lines)
        
        user_guidance = f"\n\nUser Character Preferences: {user_input}" if user_input else ""
        
        # Get format-agnostic response instructions
        format_instruction = AIResponseParser.get_prompt_instruction(
            schema, OutputFormat.JSON, example=CHARACTER_EXAMPLE
        )
        
        return f"""Create {count} compelling characters for the story: {self.story.title}

Story Description: {self.story.description}
{world_context}
{faction_context}
{user_guidance}

For EACH character, provide:
- name: A memorable, fitting name
- description: Physical appearance and immediate impression (2-3 sentences)
- background: Life story and how they got here (2-3 sentences)
- personality_traits: 3-4 key traits (e.g., cautious, ambitious, compassionate)
- goals: What do they want? (primary motivation)
- fears: What do they fear most?
- skills: 2-4 skills or abilities

Make sure the characters:
- Are diverse in personality and background
- Have clear motivations that can conflict with each other
- Can create interesting tensions when they interact
- Have room for growth and change through the story

{format_instruction}"""
    
    async def generate_faction_characters(
        self,
        factions: List[Any],
        story_plan: Optional[Dict[str, Any]] = None
    ) -> List[StoryCharacter]:
        """Generate characters assigned to factions.
        
        Args:
            factions: List of faction objects to populate with characters
            story_plan: Optional story scope plan containing character count requirements
            
        Returns:
            List of generated StoryCharacter objects
        """
        try:
            logger.info(f"Generating faction-aligned characters for {len(factions)} factions")
            
            # Determine characters per faction from story plan
            if story_plan:
                chars_per_faction_min = story_plan.get('chars_per_faction_min', 1)
                chars_per_faction_max = story_plan.get('chars_per_faction_max', 3)
            else:
                chars_per_faction_min = 1
                chars_per_faction_max = 3
            
            created_chars = []
            
            for faction in factions:
                num_chars = min(chars_per_faction_max, max(chars_per_faction_min, 2))
                
                # Build schema for this batch
                schema = ResponseSchema(
                    fields=CHARACTER_SCHEMA.fields,
                    expect_array=True,
                    min_items=num_chars,
                    max_items=num_chars + 1,
                    item_tag="character",
                    root_tag="characters",
                )
                
                format_instruction = AIResponseParser.get_prompt_instruction(
                    schema, OutputFormat.JSON, example=CHARACTER_EXAMPLE
                )
                
                faction_goals = ', '.join(faction.goals) if hasattr(faction, 'goals') and faction.goals else 'Unknown'
                faction_resources = faction.resources if hasattr(faction, 'resources') else 'Unknown'
                
                prompt = f"""Create {num_chars} compelling characters for the {faction.name} faction:

Faction Description: {faction.description}
Faction Goals: {faction_goals}
Faction Resources: {faction_resources}

These characters should:
- Be aligned with the faction's values and goals
- Have clear motivations tied to the faction's agenda
- Be distinct personalities within the faction
- Have potential for interesting conflicts

For EACH character, provide:
- name: A fitting name
- description: Physical appearance and impression (1-2 sentences)
- background: How they came to this faction (1-2 sentences)
- personality_traits: 3-4 key traits
- goals: Their personal motivation within the faction
- fears: What they fear most
- skills: 2-4 skills or abilities

{format_instruction}"""
                
                fallback_defaults = [
                    {**CHARACTER_FALLBACK, "name": f"{faction.name} Member {i+1}"}
                    for i in range(num_chars)
                ]
                parsed_chars = await self.generator.generate_structured(
                    system_prompt="You are creating characters aligned with specific factions and organizations.",
                    user_prompt=prompt,
                    schema=schema,
                    fallback_defaults=fallback_defaults,
                )
                
                for i, raw in enumerate(parsed_chars[:num_chars]):
                    importance_tier = "major" if i == 0 else "minor"
                    
                    char = StoryCharacter(
                        story=self.story,
                        id=f"char_{self.story.id}_{uuid.uuid4().hex[:8]}",
                        story_id=self.story.id,
                        name=raw.get('name', CHARACTER_FALLBACK['name']),
                        description=raw.get('description', CHARACTER_FALLBACK['description']),
                        background=raw.get('background', CHARACTER_FALLBACK['background']),
                        personality=raw.get('personality_traits', []),
                        goals=raw.get('goals', ''),
                        avatar_color=self._select_avatar_color(),
                        faction_id=faction.id,
                        importance_tier=importance_tier,
                    )
                    char.save()
                    created_chars.append(char)
                    logger.info(f"Generated {faction.name} character: {char.name}")
            
            logger.info(f"Generated {len(created_chars)} faction-aligned characters")
            return created_chars
            
        except Exception as e:
            logger.error(f"Failed to generate faction characters: {e}", exc_info=True)
            raise ValueError(f"Faction character generation failed: {str(e)}")
    
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
