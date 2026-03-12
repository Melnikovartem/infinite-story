"""Scene visual generator service.

Creates SegmentVisual manifests during segment generation. This determines
which background and character sprites to display for each segment,
and generates a visual scene description that can be used for additional
composed scene generation if needed.

This service does NOT generate images itself -- it only creates the
composition manifest that tells the UI which existing assets to display.
"""

import logging
from typing import Dict, List, Optional

from app.models.visuals import SegmentVisual
from app.models.story_segment import StorySegment
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation

logger = logging.getLogger("infinite_story.engine.visual.scene_visual_generator")


class SceneVisualGeneratorService:
    """Creates visual composition data for segments.
    
    For each segment, determines:
    - Which location background to show
    - Which character sprites to show and with what emotions
    - A textual scene visual description
    """

    def create_segment_visual(
        self,
        segment: StorySegment,
        characters: Optional[List[StoryCharacter]] = None,
        locations: Optional[List[StoryLocation]] = None,
    ) -> SegmentVisual:
        """Create a SegmentVisual manifest for a segment.
        
        Inspects the segment's characters_present, locations_present,
        and character_emotions to build the visual composition.
        
        Args:
            segment: The segment to create visuals for.
            characters: Available characters (if None, attempts to load).
            locations: Available locations (if None, attempts to load).
            
        Returns:
            The created SegmentVisual, saved to disk.
        """
        # Build character lookup
        char_map: Dict[str, StoryCharacter] = {}
        if characters:
            for c in characters:
                char_map[c.id] = c
                char_map[c.name.lower()] = c

        # Build location lookup
        loc_map: Dict[str, StoryLocation] = {}
        if locations:
            for loc in locations:
                loc_map[loc.id] = loc
                loc_map[loc.name.lower()] = loc

        # Determine the primary location
        location_id = None
        if segment.locations_present:
            for loc_ref in segment.locations_present:
                # Try direct ID match first, then name match
                if loc_ref in loc_map:
                    location_id = loc_map[loc_ref].id
                    break
                lower = loc_ref.lower()
                if lower in loc_map:
                    location_id = loc_map[lower].id
                    break

        # Build character sprite assignments
        character_sprites: Dict[str, str] = {}
        emotions_data = segment.character_emotions or {}
        
        for char_ref in (segment.characters_present or []):
            # Resolve character ID
            char = char_map.get(char_ref) or char_map.get(char_ref.lower())
            if not char:
                continue
            
            # Get emotion for this character
            emotion = "neutral"
            # Check character_emotions dict (character name -> emotion)
            for name_key, emo_val in emotions_data.items():
                if name_key.lower() == char.name.lower() or name_key == char.id:
                    emotion = emo_val
                    break
            
            character_sprites[char.id] = emotion

        # Build scene description from segment metadata
        scene_parts = []
        if segment.atmosphere:
            scene_parts.append(f"Atmosphere: {segment.atmosphere}")
        if segment.time_of_day:
            scene_parts.append(f"Time: {segment.time_of_day}")
        if segment.weather:
            scene_parts.append(f"Weather: {segment.weather}")
        if segment.short_description:
            scene_parts.append(segment.short_description)
        
        scene_description = ". ".join(scene_parts)

        # Create and save the visual manifest
        visual = SegmentVisual(
            segment_id=segment.id,
            story_id=segment.story_id,
            location_id=location_id,
            character_sprites=character_sprites,
            scene_description=scene_description,
        )
        visual.save()

        # Mark segment as having visuals
        segment.has_visuals = True
        segment.scene_visual_description = scene_description

        logger.info(
            f"[SceneVisual] Created visual for segment {segment.id}: "
            f"location={location_id}, "
            f"characters={list(character_sprites.keys())}"
        )

        return visual

    def get_segment_visual_data(
        self,
        segment: StorySegment,
        characters: Optional[List[StoryCharacter]] = None,
        locations: Optional[List[StoryLocation]] = None,
    ) -> Dict:
        """Get the full visual data for a segment as a dict.
        
        Loads or creates the SegmentVisual, then resolves all asset
        paths (background, sprites) into a dict the API can return.
        
        Returns a dict like:
        {
            "background": "visuals/locations/loc_123/background.png" or None,
            "characters": [
                {
                    "character_id": "char_1",
                    "name": "Eira",
                    "emotion": "happy",
                    "sprite_path": "visuals/characters/char_1/happy.png" or None,
                    "has_sprite": True/False
                },
                ...
            ],
            "scene_description": "..."
        }
        """
        # Load or create visual manifest
        visual = SegmentVisual.load(segment.story_id, segment.id)
        if not visual:
            visual = self.create_segment_visual(segment, characters, locations)

        # Build character lookup
        char_map: Dict[str, StoryCharacter] = {}
        if characters:
            for c in characters:
                char_map[c.id] = c

        # Resolve background path
        background_path = None
        if visual.location_id:
            from app.models.visuals import LocationVisual
            loc_visual = LocationVisual.load(segment.story_id, visual.location_id)
            if loc_visual and loc_visual.status.value == "completed":
                background_path = loc_visual.get_relative_path()

        # Resolve character sprite paths
        character_visuals = []
        for char_id, emotion in visual.character_sprites.items():
            char = char_map.get(char_id)
            char_name = char.name if char else char_id
            
            sprite_path = None
            has_sprite = False
            if char:
                sprite_path = char.get_sprite_path(emotion)
                has_sprite = sprite_path is not None

            character_visuals.append({
                "character_id": char_id,
                "name": char_name,
                "emotion": emotion,
                "sprite_path": sprite_path,
                "has_sprite": has_sprite,
            })

        return {
            "background": background_path,
            "characters": character_visuals,
            "scene_description": visual.scene_description,
        }
