"""Location background generation service.

Generates anime-style background images for story locations.
Each location gets one background image that is reused across all
segments set in that location.
"""

import logging
from typing import List, Optional

from app.models.visuals import LocationVisual, BackgroundStatus
from app.models.story_location import StoryLocation
from app.engine.image_generator import ImageGenerator, ImageGenerationError

logger = logging.getLogger("infinite_story.engine.visual.background_generator")


class BackgroundGeneratorService:
    """Generates background images for story locations."""

    def __init__(self, image_generator: ImageGenerator):
        self.image_gen = image_generator

    @staticmethod
    def _truncate_visual_desc(desc: str, max_chars: int = 250) -> str:
        """Truncate visual description for image prompt."""
        if not desc:
            return ""
        truncated = desc[:max_chars]
        for sep in [",", ".", " —", " -"]:
            idx = truncated.rfind(sep)
            if idx > max_chars // 2:
                truncated = truncated[:idx]
                break
        return truncated.strip().rstrip(",.")

    def _build_background_prompt(
        self,
        visual_description: str,
        art_style: str,
        location_name: str = "",
    ) -> str:
        """Build a DALL-E prompt for a location background.
        
        Focuses on environment art: no characters, wide composition,
        painterly anime style.
        """
        clean_desc = self._truncate_visual_desc(visual_description)
        parts = [
            art_style,
            f"scene: {location_name}" if location_name else "",
            clean_desc,
            "no characters, no people, empty scene",
            "no text, no labels, no captions, no UI elements",
            "wide angle view, establishing shot",
            "high quality, detailed environment art",
        ]
        return ", ".join(p for p in parts if p)

    async def generate_background(
        self,
        location: StoryLocation,
    ) -> LocationVisual:
        """Generate a background image for a location.
        
        Creates or loads the LocationVisual manifest, generates the image,
        and updates the manifest + location model.
        
        Args:
            location: The location to generate a background for.
            
        Returns:
            The updated LocationVisual.
        """
        # Load or create manifest
        visual = LocationVisual.load(location.story_id, location.id)
        if not visual:
            visual = LocationVisual(
                location_id=location.id,
                story_id=location.story_id,
                visual_description=location.visual_description or location.description,
            )

        if visual.status == BackgroundStatus.COMPLETED:
            logger.debug(f"[Background] {location.name} already completed, skipping")
            return visual

        prompt = self._build_background_prompt(
            visual.visual_description, visual.art_style, location.name
        )
        visual.image_prompt = prompt
        visual.status = BackgroundStatus.GENERATING
        visual.save()

        logger.info(f"[Background] Generating background for: {location.name}")

        try:
            save_path = visual.get_image_path()
            await self.image_gen.generate_image(
                prompt=prompt,
                save_path=save_path,
                size="1792x1024",  # wide landscape for backgrounds
                quality="standard",
            )
            visual.status = BackgroundStatus.COMPLETED
            visual.filename = "background.png"
            visual.error = None
            
            location.has_background = True
            location.save()
            
            logger.info(f"[Background] Generated background for: {location.name}")
        except ImageGenerationError as e:
            visual.status = BackgroundStatus.FAILED
            visual.error = str(e)[:200]
            logger.error(f"[Background] Failed for {location.name}: {e}")

        visual.save()
        return visual

    async def generate_all_backgrounds(
        self,
        locations: List[StoryLocation],
        max_locations: Optional[int] = None,
    ) -> List[LocationVisual]:
        """Generate backgrounds for multiple locations.
        
        Generates sequentially to avoid rate limits (backgrounds are
        higher resolution and more expensive).
        
        Args:
            locations: List of locations to generate backgrounds for.
            max_locations: Optional limit on how many to generate.
            
        Returns:
            List of LocationVisual results.
        """
        targets = locations[:max_locations] if max_locations else locations
        
        logger.info(
            f"[Background] Generating backgrounds for {len(targets)} locations: "
            + ", ".join(loc.name for loc in targets)
        )

        results = []
        for loc in targets:
            visual = await self.generate_background(loc)
            results.append(visual)

        completed = sum(1 for v in results if v.status == BackgroundStatus.COMPLETED)
        logger.info(f"[Background] Finished: {completed}/{len(targets)} backgrounds completed")
        
        return results
