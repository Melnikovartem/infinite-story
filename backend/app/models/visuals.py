"""Visual system models for the Infinite Story Engine.

Defines the data structures for character sprites, location backgrounds,
and per-segment scene visuals. Visuals are stored as image files on disk
alongside the JSON data, referenced by relative paths.

Storage layout:
    .infinite_story_data/<story_id>/
        visuals/
            characters/<character_id>/
                neutral.png
                happy.png
                sad.png
                ...
                _manifest.json       # SpriteSheet as JSON
            locations/<location_id>/
                background.png
                _manifest.json       # LocationVisual as JSON
            segments/<segment_id>/
                scene.png            # composed scene image (optional)
                _manifest.json       # SegmentVisual as JSON
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from .story_base import LOCAL_DATA_DIR


# ── Emotion enum (the 7 standard sprite emotions) ───────────────────────────

class SpriteEmotion(str, Enum):
    """Standard emotion variants for character sprites."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEARFUL = "fearful"
    THOUGHTFUL = "thoughtful"


ALL_SPRITE_EMOTIONS = list(SpriteEmotion)


# ── Sprite status tracking ───────────────────────────────────────────────────

class SpriteStatus(str, Enum):
    """Generation status for a single sprite."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class SpriteEntry(BaseModel):
    """A single sprite image entry (one emotion variant)."""
    emotion: SpriteEmotion
    status: SpriteStatus = SpriteStatus.PENDING
    filename: Optional[str] = None          # e.g. "happy.png"
    image_prompt: Optional[str] = None      # the DALL-E prompt used
    error: Optional[str] = None             # error message if failed


class SpriteSheet(BaseModel):
    """Full sprite sheet manifest for a character.
    
    Tracks all emotion variants, the visual description used as a base
    prompt, and generation status for each sprite.
    """
    character_id: str
    story_id: str
    
    # The visual description used as base for all sprite prompts.
    # Built from StoryCharacter.description + full_description.
    visual_description: str = ""
    
    # Art style directive baked into all prompts
    art_style: str = "anime visual novel style, clean lineart, cel-shaded, transparent background, character portrait bust shot"
    
    # Whether this character is "important" (gets full sprite set)
    # or minor (gets placeholder / lazy-generated)
    is_priority: bool = False
    
    # Individual sprite entries
    sprites: List[SpriteEntry] = Field(default_factory=list)
    
    def get_sprite(self, emotion: SpriteEmotion) -> Optional[SpriteEntry]:
        """Get sprite entry for a specific emotion."""
        for s in self.sprites:
            if s.emotion == emotion:
                return s
        return None
    
    def get_completed_sprites(self) -> List[SpriteEntry]:
        """Get all completed sprite entries."""
        return [s for s in self.sprites if s.status == SpriteStatus.COMPLETED]
    
    def has_sprite(self, emotion: SpriteEmotion) -> bool:
        """Check if a completed sprite exists for an emotion."""
        s = self.get_sprite(emotion)
        return s is not None and s.status == SpriteStatus.COMPLETED
    
    def get_best_sprite(self, emotion: str) -> Optional[SpriteEntry]:
        """Get the best available sprite for a given emotion string.
        
        Tries exact match first, then falls back to neutral, then any completed.
        """
        # Try exact match
        try:
            target = SpriteEmotion(emotion.lower())
            entry = self.get_sprite(target)
            if entry and entry.status == SpriteStatus.COMPLETED:
                return entry
        except ValueError:
            pass
        
        # Map common emotion strings to sprite emotions
        emotion_map: Dict[str, SpriteEmotion] = {
            "joyful": SpriteEmotion.HAPPY,
            "excited": SpriteEmotion.HAPPY,
            "pleased": SpriteEmotion.HAPPY,
            "content": SpriteEmotion.HAPPY,
            "melancholy": SpriteEmotion.SAD,
            "sorrowful": SpriteEmotion.SAD,
            "depressed": SpriteEmotion.SAD,
            "grieving": SpriteEmotion.SAD,
            "furious": SpriteEmotion.ANGRY,
            "irritated": SpriteEmotion.ANGRY,
            "enraged": SpriteEmotion.ANGRY,
            "frustrated": SpriteEmotion.ANGRY,
            "shocked": SpriteEmotion.SURPRISED,
            "astonished": SpriteEmotion.SURPRISED,
            "stunned": SpriteEmotion.SURPRISED,
            "afraid": SpriteEmotion.FEARFUL,
            "terrified": SpriteEmotion.FEARFUL,
            "anxious": SpriteEmotion.FEARFUL,
            "worried": SpriteEmotion.FEARFUL,
            "nervous": SpriteEmotion.FEARFUL,
            "pensive": SpriteEmotion.THOUGHTFUL,
            "contemplative": SpriteEmotion.THOUGHTFUL,
            "curious": SpriteEmotion.THOUGHTFUL,
            "suspicious": SpriteEmotion.THOUGHTFUL,
            "determined": SpriteEmotion.NEUTRAL,
            "calm": SpriteEmotion.NEUTRAL,
            "stoic": SpriteEmotion.NEUTRAL,
            "resolute": SpriteEmotion.NEUTRAL,
        }
        
        mapped = emotion_map.get(emotion.lower())
        if mapped:
            entry = self.get_sprite(mapped)
            if entry and entry.status == SpriteStatus.COMPLETED:
                return entry
        
        # Fallback: neutral
        neutral = self.get_sprite(SpriteEmotion.NEUTRAL)
        if neutral and neutral.status == SpriteStatus.COMPLETED:
            return neutral
        
        # Last resort: any completed sprite
        completed = self.get_completed_sprites()
        return completed[0] if completed else None

    def init_sprites(self, emotions: Optional[List[SpriteEmotion]] = None) -> None:
        """Initialize sprite entries for the given emotions (defaults to all 7)."""
        target = emotions or ALL_SPRITE_EMOTIONS
        existing = {s.emotion for s in self.sprites}
        for emo in target:
            if emo not in existing:
                self.sprites.append(SpriteEntry(emotion=emo))
    
    # ── Persistence ──────────────────────────────────────────────────────
    
    def get_dir(self) -> Path:
        """Get the directory for this character's sprites."""
        d = LOCAL_DATA_DIR / self.story_id / "visuals" / "characters" / self.character_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self) -> None:
        """Save the sprite manifest to disk."""
        import json
        manifest = self.get_dir() / "_manifest.json"
        with open(manifest, "w") as f:
            json.dump(self.model_dump(), f, default=str, indent=2)

    @classmethod
    def load(cls, story_id: str, character_id: str) -> Optional["SpriteSheet"]:
        """Load sprite manifest from disk."""
        import json
        manifest = LOCAL_DATA_DIR / story_id / "visuals" / "characters" / character_id / "_manifest.json"
        if not manifest.exists():
            return None
        with open(manifest) as f:
            return cls(**json.load(f))

    def get_image_path(self, emotion: SpriteEmotion) -> Path:
        """Get the full file path for a sprite image."""
        return self.get_dir() / f"{emotion.value}.png"
    
    def get_relative_path(self, emotion: SpriteEmotion) -> str:
        """Get the URL-friendly relative path for a sprite."""
        return f"visuals/characters/{self.character_id}/{emotion.value}.png"


# ── Location background ──────────────────────────────────────────────────────

class BackgroundStatus(str, Enum):
    """Generation status for a location background."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class LocationVisual(BaseModel):
    """Background image data for a location."""
    location_id: str
    story_id: str
    
    # The visual description used for the background prompt
    visual_description: str = ""
    
    # Art style for backgrounds
    art_style: str = "anime visual novel background, detailed environment art, wide landscape, no characters, painterly style"
    
    status: BackgroundStatus = BackgroundStatus.PENDING
    filename: Optional[str] = None              # e.g. "background.png"
    image_prompt: Optional[str] = None          # the DALL-E prompt used
    error: Optional[str] = None
    
    # ── Persistence ──────────────────────────────────────────────────────
    
    def get_dir(self) -> Path:
        d = LOCAL_DATA_DIR / self.story_id / "visuals" / "locations" / self.location_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self) -> None:
        import json
        manifest = self.get_dir() / "_manifest.json"
        with open(manifest, "w") as f:
            json.dump(self.model_dump(), f, default=str, indent=2)

    @classmethod
    def load(cls, story_id: str, location_id: str) -> Optional["LocationVisual"]:
        import json
        manifest = LOCAL_DATA_DIR / story_id / "visuals" / "locations" / location_id / "_manifest.json"
        if not manifest.exists():
            return None
        with open(manifest) as f:
            return cls(**json.load(f))

    def get_image_path(self) -> Path:
        return self.get_dir() / "background.png"
    
    def get_relative_path(self) -> str:
        return f"visuals/locations/{self.location_id}/background.png"


# ── Segment scene visual ─────────────────────────────────────────────────────

class SegmentVisual(BaseModel):
    """Visual composition data for a specific segment.
    
    This tracks which background and character sprites should be displayed
    for a given segment, plus an optional composed scene image.
    """
    segment_id: str
    story_id: str
    
    # Which location background to use
    location_id: Optional[str] = None
    
    # Characters visible in this scene + their emotions for sprite selection
    character_sprites: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of character_id -> emotion string for sprite selection"
    )
    
    # AI-generated visual description of the scene (for potential scene image generation)
    scene_description: str = ""
    
    # Optional: a fully composed scene image (background + sprites composited)
    has_composed_image: bool = False
    composed_image_prompt: Optional[str] = None
    
    # ── Persistence ──────────────────────────────────────────────────────
    
    def get_dir(self) -> Path:
        d = LOCAL_DATA_DIR / self.story_id / "visuals" / "segments" / self.segment_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self) -> None:
        import json
        manifest = self.get_dir() / "_manifest.json"
        with open(manifest, "w") as f:
            json.dump(self.model_dump(), f, default=str, indent=2)

    @classmethod
    def load(cls, story_id: str, segment_id: str) -> Optional["SegmentVisual"]:
        import json
        manifest = LOCAL_DATA_DIR / story_id / "visuals" / "segments" / segment_id / "_manifest.json"
        if not manifest.exists():
            return None
        with open(manifest) as f:
            return cls(**json.load(f))

    def get_composed_image_path(self) -> Path:
        return self.get_dir() / "scene.png"
    
    def get_relative_path(self) -> str:
        return f"visuals/segments/{self.segment_id}/scene.png"
