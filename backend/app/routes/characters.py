"""Character data endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import json
from pathlib import Path
from app.config import Settings

settings = Settings()
from app.models.story_character import StoryCharacter, AvatarShape

router = APIRouter()
logger = logging.getLogger("infinite_story.routes.characters")


class CharacterStateResponse(BaseModel):
    """Response model for character state."""
    segment_id: str = Field(..., description="Segment ID where this state applies")
    emotion: Optional[str] = Field(None, description="Character's emotional state")
    status: str = Field(default="present", description="Character presence (present, absent, mentioned)")
    notes: str = Field(default="", description="Additional notes about the character")


class CharacterResponse(BaseModel):
    """Response model for character data."""
    id: str = Field(..., description="Character ID")
    name: str = Field(..., description="Character name")
    description: str = Field(..., description="Character description")
    background: str = Field(..., description="Character background")
    avatar_shape: str = Field(..., description="Avatar shape (square, circle, triangle, diamond, star, pentagon)")
    avatar_color: str = Field(..., description="Avatar color in hex format (#XXXXXX)")
    running_status: List[CharacterStateResponse] = Field(
        default_factory=list,
        description="Character state history through story"
    )


class CharacterListItemResponse(BaseModel):
    """Simplified response for listing characters."""
    id: str = Field(..., description="Character ID")
    name: str = Field(..., description="Character name")
    description: str = Field(..., description="Character description")
    avatar_shape: str = Field(..., description="Avatar shape")
    avatar_color: str = Field(..., description="Avatar color")


class CharacterListResponse(BaseModel):
    """Response for listing story characters."""
    characters: List[CharacterListItemResponse] = Field(
        ...,
        description="List of characters in the story"
    )


def _load_story_file(story_id: str) -> dict:
    """Load a story file from disk.
    
    Args:
        story_id: The story ID to load
        
    Returns:
        The story data as a dictionary
        
    Raises:
        HTTPException: If story not found or cannot be loaded
    """
    data_dir = Path(settings.data_dir)
    story_file = data_dir / f"{story_id}.json"
    
    if not story_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story '{story_id}' not found"
        )
    
    try:
        with open(story_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse story file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load story: {str(e)}"
        )


def _get_character_from_story(story_data: dict, character_id: str) -> dict:
    """Extract character data from story JSON.
    
    Args:
        story_data: The loaded story data
        character_id: The character ID to find
        
    Returns:
        The character data
        
    Raises:
        HTTPException: If character not found
    """
    # Characters are typically stored in story["characters"]
    characters = story_data.get("_characters", {})
    
    if character_id not in characters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character '{character_id}' not found in story"
        )
    
    return characters[character_id]


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    story_id: str
) -> CharacterResponse:
    """Get character details including state history.
    
    Args:
        character_id: ID of the character
        story_id: ID of the story the character belongs to
        
    Returns:
        Character data with full state history
    """
    try:
        # Load the story file
        story_data = _load_story_file(story_id)
        
        # Get the character from the story
        char_data = _get_character_from_story(story_data, character_id)
        
        # Build response
        running_status = []
        for state in char_data.get("running_status", []):
            running_status.append(CharacterStateResponse(**state))
        
        return CharacterResponse(
            id=char_data.get("id", character_id),
            name=char_data.get("name", ""),
            description=char_data.get("description", ""),
            background=char_data.get("background", ""),
            avatar_shape=char_data.get("avatar_shape", "circle"),
            avatar_color=char_data.get("avatar_color", "#FF6B6B"),
            running_status=running_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting character {character_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get character: {str(e)}"
        )


@router.get("/stories/{story_id}/characters", response_model=CharacterListResponse)
async def list_story_characters(story_id: str) -> CharacterListResponse:
    """Get all characters for a story.
    
    Args:
        story_id: ID of the story
        
    Returns:
        List of characters in the story
    """
    try:
        # Load the story file
        story_data = _load_story_file(story_id)
        
        # Get all characters
        characters_data = story_data.get("_characters", {})
        characters_list = []
        
        for char_id, char_data in characters_data.items():
            characters_list.append(CharacterListItemResponse(
                id=char_data.get("id", char_id),
                name=char_data.get("name", ""),
                description=char_data.get("description", ""),
                avatar_shape=char_data.get("avatar_shape", "circle"),
                avatar_color=char_data.get("avatar_color", "#FF6B6B")
            ))
        
        return CharacterListResponse(characters=characters_list)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing characters for story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list characters: {str(e)}"
        )
