"""Character sprite generation service.

Generates anime-style character portrait sprites with emotion variants.
Priority characters (protagonist, antagonist, major allies) get full
7-emotion sprite sets generated eagerly. Minor characters get sprites
generated lazily on first appearance, or use placeholder images.
"""

import asyncio
import logging
from typing import List, Optional

from app.models.visuals import (
    SpriteSheet,
    SpriteEntry,
    SpriteEmotion,
    SpriteStatus,
    ALL_SPRITE_EMOTIONS,
)
from app.models.story_character import StoryCharacter, CharacterRole
from app.engine.image_generator import ImageGenerator, ImageGenerationError

logger = logging.getLogger("infinite_story.engine.visual.sprite_generator")


# Emotion-specific prompt modifiers
EMOTION_PROMPTS = {
    SpriteEmotion.NEUTRAL: "neutral calm expression, relaxed posture",
    SpriteEmotion.HAPPY: "warm genuine smile, bright eyes, joyful expression",
    SpriteEmotion.SAD: "downcast eyes, sorrowful expression, slight frown, melancholy look",
    SpriteEmotion.ANGRY: "furrowed brows, intense glare, clenched jaw, angry expression",
    SpriteEmotion.SURPRISED: "wide eyes, raised eyebrows, open mouth, shocked expression",
    SpriteEmotion.FEARFUL: "wide frightened eyes, tense posture, fearful expression, slightly trembling",
    SpriteEmotion.THOUGHTFUL: "contemplative gaze, slightly narrowed eyes, hand near chin, pensive expression",
}


class SpriteGeneratorService:
    """Generates character sprite images using an ImageGenerator backend.
    
    Handles prompt construction, emotion variants, priority scheduling,
    and manifest management.
    """

    def __init__(self, image_generator: ImageGenerator):
        self.image_gen = image_generator

    @staticmethod
    def _extract_visual_keywords(desc: str, max_chars: int = 120) -> str:
        """Extract visual keywords from a narrative description.
        
        Strips sentences into comma-separated physical traits.
        DALL-E works best with short keyword phrases, not prose.
        """
        if not desc:
            return ""
        import re
        # Remove narrative/action phrases
        cleaned = re.sub(r'\b(who|that|which|whose)\b[^,\.]+', '', desc)
        cleaned = re.sub(r'\b(constantly|rarely|always|never|often)\s+\w+', '', cleaned)
        cleaned = re.sub(r'his \w+ (constantly|rarely)[^,\.]*', '', cleaned)
        # Remove "A/An" at start
        cleaned = re.sub(r'^(A|An)\s+', '', cleaned.strip())
        # Collapse whitespace and double commas
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r',\s*,', ',', cleaned)
        # Truncate at a natural break
        if len(cleaned) > max_chars:
            idx = cleaned.rfind(',', 0, max_chars)
            if idx > max_chars // 3:
                cleaned = cleaned[:idx]
            else:
                cleaned = cleaned[:max_chars]
        return cleaned.strip().rstrip(",. ")

    def _build_sprite_prompt(
        self,
        visual_description: str,
        emotion: SpriteEmotion,
        art_style: str,
        character_name: str = "",
    ) -> str:
        """Build a DALL-E prompt for a single sprite.
        
        DALL-E 3 renders negative instructions ("no text") as actual text.
        The prompt must ONLY describe what we want to see -- nothing else.
        """
        emotion_mod = EMOTION_PROMPTS.get(emotion, "neutral expression")
        clean_desc = self._extract_visual_keywords(visual_description)
        
        # Frame as a screenshot from an existing anime/game to avoid
        # DALL-E's tendency to create character design sheets.
        prompt = (
            f"Screenshot from a Japanese visual novel game. "
            f"Close-up of one person: {clean_desc}. "
            f"They have a {emotion_mod}. "
            f"Soft flat colors, clean anime style. "
            f"Simple gradient background."
        )
        
        return prompt

    async def generate_sprite(
        self,
        sheet: SpriteSheet,
        emotion: SpriteEmotion,
        character_name: str = "",
    ) -> SpriteEntry:
        """Generate a single sprite for one emotion variant.
        
        Updates the SpriteSheet entry in-place and saves the manifest.
        
        Args:
            sheet: The SpriteSheet to update.
            emotion: Which emotion to generate.
            character_name: Character name for the prompt.
            
        Returns:
            The updated SpriteEntry.
        """
        entry = sheet.get_sprite(emotion)
        if not entry:
            entry = SpriteEntry(emotion=emotion)
            sheet.sprites.append(entry)

        if entry.status == SpriteStatus.COMPLETED:
            logger.debug(f"[Sprite] {character_name}/{emotion.value} already completed, skipping")
            return entry

        prompt = self._build_sprite_prompt(
            sheet.visual_description, emotion, sheet.art_style, character_name
        )
        entry.image_prompt = prompt
        entry.status = SpriteStatus.GENERATING
        sheet.save()

        try:
            save_path = sheet.get_image_path(emotion)
            await self.image_gen.generate_image(
                prompt=prompt,
                save_path=save_path,
                size="1024x1024",
                quality="standard",
            )
            entry.status = SpriteStatus.COMPLETED
            entry.filename = f"{emotion.value}.png"
            entry.error = None
            logger.info(f"[Sprite] Generated {character_name}/{emotion.value}")
        except ImageGenerationError as e:
            entry.status = SpriteStatus.FAILED
            entry.error = str(e)[:200]
            logger.error(f"[Sprite] Failed {character_name}/{emotion.value}: {e}")

        sheet.save()
        return entry

    async def generate_full_sprite_set(
        self,
        character: StoryCharacter,
        emotions: Optional[List[SpriteEmotion]] = None,
        concurrent: int = 2,
    ) -> SpriteSheet:
        """Generate a full set of sprites for a character.
        
        Creates or loads the SpriteSheet, then generates all requested
        emotion variants. Uses limited concurrency to avoid rate limits.
        
        Args:
            character: The character to generate sprites for.
            emotions: Which emotions to generate (defaults to all 7).
            concurrent: Max concurrent image generations.
            
        Returns:
            The updated SpriteSheet with all generation results.
        """
        target_emotions = emotions or ALL_SPRITE_EMOTIONS
        
        # Load or create sprite sheet
        sheet = SpriteSheet.load(character.story_id, character.id)
        if not sheet:
            sheet = SpriteSheet(
                character_id=character.id,
                story_id=character.story_id,
                visual_description=character.visual_description or character.description,
                is_priority=character.role in (CharacterRole.PROTAGONIST, CharacterRole.ANTAGONIST),
            )
        
        # Ensure all emotion entries exist
        sheet.init_sprites(target_emotions)
        sheet.save()
        
        logger.info(
            f"[Sprite] Generating {len(target_emotions)} sprites for "
            f"{character.name} (priority={sheet.is_priority})"
        )

        # Generate with limited concurrency using semaphore
        sem = asyncio.Semaphore(concurrent)

        async def gen_one(emo: SpriteEmotion):
            async with sem:
                return await self.generate_sprite(sheet, emo, character.name)

        await asyncio.gather(*[gen_one(emo) for emo in target_emotions])

        # Update character model
        completed = sheet.get_completed_sprites()
        character.has_sprites = len(completed) > 0
        character.save()

        logger.info(
            f"[Sprite] Finished {character.name}: "
            f"{len(completed)}/{len(target_emotions)} sprites completed"
        )
        return sheet

    async def generate_single_lazy(
        self,
        character: StoryCharacter,
        emotion: str = "neutral",
    ) -> Optional[str]:
        """Lazy-generate a single sprite on demand.
        
        Used for minor characters who appear in a scene. Generates just
        the requested emotion (or neutral fallback).
        
        Args:
            character: The character.
            emotion: The desired emotion string.
            
        Returns:
            Relative path to the sprite image, or None if generation fails.
        """
        sheet = SpriteSheet.load(character.story_id, character.id)
        if not sheet:
            sheet = SpriteSheet(
                character_id=character.id,
                story_id=character.story_id,
                visual_description=character.visual_description or character.description,
                is_priority=False,
            )

        # Try to find existing sprite first
        existing = sheet.get_best_sprite(emotion)
        if existing and existing.filename:
            return sheet.get_relative_path(SpriteEmotion(existing.emotion))

        # Generate just this emotion
        try:
            target_emotion = SpriteEmotion(emotion.lower())
        except ValueError:
            target_emotion = SpriteEmotion.NEUTRAL

        sheet.init_sprites([target_emotion])
        entry = await self.generate_sprite(sheet, target_emotion, character.name)

        if entry.status == SpriteStatus.COMPLETED:
            character.has_sprites = True
            character.save()
            return sheet.get_relative_path(target_emotion)
        
        return None

    async def generate_priority_characters(
        self,
        characters: List[StoryCharacter],
        max_priority: int = 4,
    ) -> List[SpriteSheet]:
        """Generate sprites for priority characters in a story.
        
        Selects protagonist, antagonist, and top allies up to max_priority,
        then generates full sprite sets for each.
        
        Args:
            characters: All characters in the story.
            max_priority: Max number of characters to give full sprite sets.
            
        Returns:
            List of SpriteSheets for the priority characters.
        """
        # Sort by role priority
        role_order = {
            CharacterRole.PROTAGONIST: 0,
            CharacterRole.ANTAGONIST: 1,
            CharacterRole.ALLY: 2,
            CharacterRole.MINOR: 3,
        }
        
        sorted_chars = sorted(characters, key=lambda c: role_order.get(c.role, 99))
        priority_chars = sorted_chars[:max_priority]
        
        logger.info(
            f"[Sprite] Generating sprites for {len(priority_chars)} priority characters: "
            + ", ".join(c.name for c in priority_chars)
        )

        results = []
        for char in priority_chars:
            char.sprites_priority = True
            sheet = await self.generate_full_sprite_set(char)
            results.append(sheet)

        return results
