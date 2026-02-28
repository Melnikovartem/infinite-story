"""Story and segment endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC
from pathlib import Path
import json
import logging

from app.models.story import Story
from app.models.story_segment import StorySegment

logger = logging.getLogger("infinite_story.routes.stories")

router = APIRouter()

# Response models
class StoryListItem(BaseModel):
    """Story list item in stories list."""
    id: str = Field(..., description="Unique story ID")
    title: str = Field(..., description="Story title")
    description: str = Field(..., description="Story description")
    genre: Optional[str] = Field(None, description="Genre classification")
    start_segment_id: Optional[str] = Field(None, description="ID of the first segment")


class StoryDetail(BaseModel):
    """Detailed story information."""
    id: str = Field(..., description="Unique story ID")
    title: str = Field(..., description="Story title")
    description: str = Field(..., description="Story description")
    genre: Optional[str] = Field(None, description="Genre classification")
    start_segment_id: Optional[str] = Field(None, description="ID of the first segment")
    created_at: Optional[datetime] = Field(None, description="When story was created")


class TextBlockItem(BaseModel):
    """A text block within a segment."""
    type: str = Field(..., description="Type of text block (e.g., NARRATOR_DESCRIBING, CHARACTER_SPEECH)")
    content: str = Field(..., description="The text content")
    character: Optional[str] = Field(None, description="Character ID if applicable")
    emotion: Optional[str] = Field(None, description="Character emotion if applicable")


class CharacterState(BaseModel):
    """Character state in a segment."""
    character_id: str = Field(..., description="Character ID")
    name: str = Field(..., description="Character name")
    emotion: Optional[str] = Field(None, description="Character's emotional state")
    status: str = Field(..., description="Character status (present, absent, mentioned)")


class LocationState(BaseModel):
    """Location state in a segment."""
    location_id: str = Field(..., description="Location ID")
    name: str = Field(..., description="Location name")
    description: Optional[str] = Field(None, description="Location description")


class StoryChoice(BaseModel):
    """A choice available to the player."""
    id: str = Field(..., description="Unique choice ID")
    choice_text: str = Field(..., description="Text of the choice")
    to_segment_id: str = Field(..., description="ID of segment this choice leads to")
    is_custom: bool = Field(default=False, description="Whether this is a custom player choice")
    popularity_score: Optional[int] = Field(None, description="Popularity rating of this choice")


class SegmentResponse(BaseModel):
    """Complete segment response."""
    id: str = Field(..., description="Unique segment ID")
    story_id: str = Field(..., description="ID of the story this segment belongs to")
    short_description: str = Field(..., description="Brief description of the segment")
    content: str = Field(..., description="Full segment content/narrative")
    text_blocks: List[TextBlockItem] = Field(default_factory=list, description="Structured text blocks")
    characters: List[CharacterState] = Field(default_factory=list, description="Characters present in segment")
    locations: List[LocationState] = Field(default_factory=list, description="Locations present in segment")
    is_generated: bool = Field(default=False, description="Whether segment was AI-generated")
    created_at: Optional[datetime] = Field(None, description="When segment was created")
    word_count: int = Field(default=0, description="Number of words in segment")


class ChoicesResponse(BaseModel):
    """Response containing choices for a segment."""
    top_2: List[StoryChoice] = Field(default_factory=list, description="Top 2 most popular choices")
    all: List[StoryChoice] = Field(default_factory=list, description="All available choices")


# Helper functions
def load_story_metadata(story_id: str) -> Optional[Dict[str, Any]]:
    """Load story metadata from disk."""
    story_dir = Path(".infinite_story_data") / story_id
    story_file = story_dir / "story" / f"{story_id}.json"
    
    if not story_file.exists():
        return None
    
    try:
        with open(story_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading story metadata for {story_id}: {e}")
        return None


def load_segment_with_choices(story_id: str, segment_id: str) -> Optional[Dict[str, Any]]:
    """Load segment with its choices."""
    segment_dir = Path(".infinite_story_data") / story_id / "storysegment"
    segment_files = list(segment_dir.glob(f"{segment_id}_*.json"))
    
    if not segment_files:
        return None
    
    try:
        with open(segment_files[0], "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading segment {segment_id}: {e}")
        return None


def get_segment_choices(story_id: str, segment_id: str) -> Dict[str, List[StoryChoice]]:
    """Get all choices for a segment."""
    choices_dir = Path(".infinite_story_data") / story_id / "storychoice"
    
    if not choices_dir.exists():
        return {"top_2": [], "all": []}
    
    choices = []
    
    try:
        # Load all choice files and filter by from_segment_id
        for choice_file in choices_dir.glob("*.json"):
            with open(choice_file, "r") as f:
                choice_data = json.load(f)
                if choice_data.get("from_segment_id") == segment_id:
                    choice = StoryChoice(
                        id=choice_data.get("id", ""),
                        choice_text=choice_data.get("choice_text", ""),
                        to_segment_id=choice_data.get("to_segment_id", ""),
                        is_custom=choice_data.get("is_custom", False),
                        popularity_score=choice_data.get("popularity_score")
                    )
                    choices.append(choice)
        
        # Sort by popularity and split top 2
        choices.sort(key=lambda c: c.popularity_score or 0, reverse=True)
        top_2 = choices[:2]
        
        return {
            "top_2": top_2,
            "all": choices
        }
    except Exception as e:
        logger.error(f"Error loading choices for segment {segment_id}: {e}")
        return {"top_2": [], "all": []}


# Endpoints

@router.get("/stories", response_model=List[StoryListItem])
async def list_stories():
    """
    List all available stories.
    
    Returns:
        List of stories with basic information
    """
    try:
        data_dir = Path(".infinite_story_data")
        
        if not data_dir.exists():
            return []
        
        stories = []
        
        # List all story directories
        for story_dir in data_dir.iterdir():
            if story_dir.is_dir():
                story_id = story_dir.name
                metadata = load_story_metadata(story_id)
                
                if metadata:
                    story = StoryListItem(
                        id=metadata.get("id", story_id),
                        title=metadata.get("title", story_id),
                        description=metadata.get("description", ""),
                        genre=metadata.get("genre"),
                        start_segment_id=metadata.get("start_segment_id")
                    )
                    stories.append(story)
        
        return stories
    
    except Exception as e:
        logger.error(f"Error listing stories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list stories: {str(e)}"
        )


@router.get("/stories/{story_id}", response_model=StoryDetail)
async def get_story_detail(story_id: str):
    """
    Get detailed information about a specific story.
    
    Args:
        story_id: ID of the story to retrieve
        
    Returns:
        Story details
    """
    try:
        metadata = load_story_metadata(story_id)
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story '{story_id}' not found"
            )
        
        return StoryDetail(
            id=metadata.get("id", story_id),
            title=metadata.get("title", story_id),
            description=metadata.get("description", ""),
            genre=metadata.get("genre"),
            start_segment_id=metadata.get("start_segment_id"),
            created_at=metadata.get("created_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving story {story_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve story: {str(e)}"
        )


@router.get("/segments/{segment_id}", response_model=Dict[str, Any])
async def get_segment(segment_id: str, story_id: Optional[str] = None):
    """
    Get a specific story segment.
    
    Args:
        segment_id: ID of the segment
        story_id: Optional story ID for context
        
    Returns:
        Segment details with choices
    """
    try:
        if not story_id:
            # Try to find the story_id from the segment
            data_dir = Path(".infinite_story_data")
            story_id = None
            
            for story_dir in data_dir.iterdir():
                if story_dir.is_dir():
                    segment_files = list((story_dir / "storysegment").glob(f"{segment_id}_*.json"))
                    if segment_files:
                        story_id = story_dir.name
                        break
            
            if not story_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Segment '{segment_id}' not found"
                )
        
        segment_data = load_segment_with_choices(story_id, segment_id)
        
        if not segment_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Segment '{segment_id}' not found in story '{story_id}'"
            )
        
        # Format text blocks
        text_blocks = []
        if "text_blocks" in segment_data and segment_data["text_blocks"]:
            for block in segment_data["text_blocks"]:
                text_blocks.append(TextBlockItem(
                    type=block.get("type", "NARRATOR_DESCRIBING"),
                    content=block.get("content", ""),
                    character=block.get("character"),
                    emotion=block.get("emotion")
                ))
        
        # Format characters
        characters = []
        if "characters" in segment_data and segment_data["characters"]:
            for char in segment_data["characters"]:
                characters.append(CharacterState(
                    character_id=char.get("character_id", ""),
                    name=char.get("name", ""),
                    emotion=char.get("emotion"),
                    status=char.get("current_status", "present")
                ))
        
        # Get choices
        choices_data = get_segment_choices(story_id, segment_id)
        
        # Build response
        segment_response = SegmentResponse(
            id=segment_data.get("id", segment_id),
            story_id=segment_data.get("story_id", story_id),
            short_description=segment_data.get("short_description", ""),
            content=segment_data.get("content", ""),
            text_blocks=text_blocks,
            characters=characters,
            is_generated=segment_data.get("is_generated", True),
            created_at=segment_data.get("created_at"),
            word_count=segment_data.get("word_count", 0)
        )
        
        return {
            "segment": segment_response.model_dump(),
            "choices": choices_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving segment {segment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve segment: {str(e)}"
        )
