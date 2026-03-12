"""Visual asset API endpoints.

Serves generated visual assets (character sprites, location backgrounds)
and provides endpoints for querying visual metadata.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.models.story_base import LOCAL_DATA_DIR
from app.models.visuals import SpriteSheet, LocationVisual, SegmentVisual

logger = logging.getLogger("infinite_story.routes.visuals")

router = APIRouter(tags=["visuals"])


# ── Serve visual asset files ─────────────────────────────────────────────────

@router.get("/visuals/{story_id}/characters/{character_id}/{filename}")
async def get_character_sprite(
    story_id: str,
    character_id: str,
    filename: str,
) -> FileResponse:
    """Serve a character sprite image file.
    
    Path: /api/visuals/{story_id}/characters/{character_id}/{emotion}.png
    """
    file_path = LOCAL_DATA_DIR / story_id / "visuals" / "characters" / character_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Sprite not found: {filename}")
    return FileResponse(file_path, media_type="image/png")


@router.get("/visuals/{story_id}/locations/{location_id}/{filename}")
async def get_location_background(
    story_id: str,
    location_id: str,
    filename: str,
) -> FileResponse:
    """Serve a location background image file.
    
    Path: /api/visuals/{story_id}/locations/{location_id}/background.png
    """
    file_path = LOCAL_DATA_DIR / story_id / "visuals" / "locations" / location_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Background not found: {filename}")
    return FileResponse(file_path, media_type="image/png")


@router.get("/visuals/{story_id}/segments/{segment_id}/{filename}")
async def get_segment_scene(
    story_id: str,
    segment_id: str,
    filename: str,
) -> FileResponse:
    """Serve a composed scene image file.
    
    Path: /api/visuals/{story_id}/segments/{segment_id}/scene.png
    """
    file_path = LOCAL_DATA_DIR / story_id / "visuals" / "segments" / segment_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Scene image not found: {filename}")
    return FileResponse(file_path, media_type="image/png")


# ── Metadata endpoints ───────────────────────────────────────────────────────

@router.get("/visuals/{story_id}/characters/{character_id}/manifest")
async def get_sprite_manifest(
    story_id: str,
    character_id: str,
) -> Dict[str, Any]:
    """Get the sprite sheet manifest for a character.
    
    Returns all emotion variants and their generation status.
    """
    sheet = SpriteSheet.load(story_id, character_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="No sprites found for this character")
    
    return {
        "character_id": sheet.character_id,
        "is_priority": sheet.is_priority,
        "visual_description": sheet.visual_description[:200],
        "sprites": [
            {
                "emotion": s.emotion.value,
                "status": s.status.value,
                "filename": s.filename,
                "path": f"/api/visuals/{story_id}/characters/{character_id}/{s.filename}" if s.filename else None,
            }
            for s in sheet.sprites
        ],
        "completed_count": len(sheet.get_completed_sprites()),
        "total_count": len(sheet.sprites),
    }


@router.get("/visuals/{story_id}/locations/{location_id}/manifest")
async def get_location_manifest(
    story_id: str,
    location_id: str,
) -> Dict[str, Any]:
    """Get the visual manifest for a location."""
    visual = LocationVisual.load(story_id, location_id)
    if not visual:
        raise HTTPException(status_code=404, detail="No background found for this location")
    
    return {
        "location_id": visual.location_id,
        "status": visual.status.value,
        "visual_description": visual.visual_description[:200],
        "filename": visual.filename,
        "path": f"/api/visuals/{story_id}/locations/{location_id}/{visual.filename}" if visual.filename else None,
    }


@router.get("/visuals/{story_id}/segments/{segment_id}/manifest")
async def get_segment_visual_manifest(
    story_id: str,
    segment_id: str,
) -> Dict[str, Any]:
    """Get the visual composition manifest for a segment.
    
    Returns background and character sprite assignments for the scene.
    """
    visual = SegmentVisual.load(story_id, segment_id)
    if not visual:
        raise HTTPException(status_code=404, detail="No visual data for this segment")
    
    # Resolve asset paths
    background_path = None
    if visual.location_id:
        loc_visual = LocationVisual.load(story_id, visual.location_id)
        if loc_visual and loc_visual.status.value == "completed" and loc_visual.filename:
            background_path = f"/api/visuals/{story_id}/locations/{visual.location_id}/{loc_visual.filename}"
    
    character_visuals = []
    for char_id, emotion in visual.character_sprites.items():
        sheet = SpriteSheet.load(story_id, char_id)
        sprite_path = None
        if sheet:
            entry = sheet.get_best_sprite(emotion)
            if entry and entry.filename:
                sprite_path = f"/api/visuals/{story_id}/characters/{char_id}/{entry.filename}"
        
        character_visuals.append({
            "character_id": char_id,
            "emotion": emotion,
            "sprite_path": sprite_path,
            "has_sprite": sprite_path is not None,
        })
    
    return {
        "segment_id": visual.segment_id,
        "background": background_path,
        "characters": character_visuals,
        "scene_description": visual.scene_description,
    }


@router.get("/visuals/{story_id}/summary")
async def get_story_visual_summary(
    story_id: str,
) -> Dict[str, Any]:
    """Get a summary of all visual assets for a story."""
    visuals_dir = LOCAL_DATA_DIR / story_id / "visuals"
    
    if not visuals_dir.exists():
        return {
            "story_id": story_id,
            "has_visuals": False,
            "characters_with_sprites": 0,
            "locations_with_backgrounds": 0,
            "segments_with_visuals": 0,
        }
    
    # Count character sprites
    chars_dir = visuals_dir / "characters"
    char_count = 0
    if chars_dir.exists():
        for char_dir in chars_dir.iterdir():
            if char_dir.is_dir() and (char_dir / "_manifest.json").exists():
                char_count += 1
    
    # Count location backgrounds
    locs_dir = visuals_dir / "locations"
    loc_count = 0
    if locs_dir.exists():
        for loc_dir in locs_dir.iterdir():
            if loc_dir.is_dir() and (loc_dir / "_manifest.json").exists():
                loc_count += 1
    
    # Count segment visuals
    segs_dir = visuals_dir / "segments"
    seg_count = 0
    if segs_dir.exists():
        for seg_dir in segs_dir.iterdir():
            if seg_dir.is_dir() and (seg_dir / "_manifest.json").exists():
                seg_count += 1
    
    return {
        "story_id": story_id,
        "has_visuals": char_count > 0 or loc_count > 0,
        "characters_with_sprites": char_count,
        "locations_with_backgrounds": loc_count,
        "segments_with_visuals": seg_count,
    }
