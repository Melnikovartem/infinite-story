"""Story and segment management endpoints."""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

from app.utils.story_loader import StoryLoader
from app.utils.response_formatter import success_response, error_response

router = APIRouter()


# Response models
class StoryMetadata(BaseModel):
    """Basic story metadata."""
    id: str = Field(..., description="Story ID")
    title: str = Field(..., description="Story title")
    description: str = Field(..., description="Story description")
    genre: Optional[str] = Field(None, description="Story genre")
    created_at: str = Field(..., description="When story was created")
    updated_at: str = Field(..., description="When story was last updated")


class TextBlock(BaseModel):
    """A text block in a segment."""
    type: str = Field(..., description="Type of text block")
    content: str = Field(..., description="Block content")
    style: Optional[Dict[str, Any]] = Field(None, description="Optional styling")


class Choice(BaseModel):
    """A choice in a segment."""
    id: str = Field(..., description="Choice ID")
    from_segment_id: str = Field(..., description="From segment ID")
    to_segment_id: Optional[str] = Field(None, description="To segment ID")
    choice_text: str = Field(..., description="The choice text")
    generated: bool = Field(default=False, description="Whether choice was AI-generated")


class SegmentResponse(BaseModel):
    """Response containing a segment."""
    id: str = Field(..., description="Segment ID")
    story_id: str = Field(..., description="Story ID")
    short_description: str = Field(..., description="Brief description of the segment")
    atmosphere: Optional[str] = Field(None, description="Scene atmosphere")
    time_of_day: Optional[str] = Field(None, description="Time of day")
    weather: Optional[str] = Field(None, description="Weather conditions")
    text_blocks: List[TextBlock] = Field(default_factory=list, description="Text blocks")
    characters_present: List[str] = Field(default_factory=list, description="Character IDs present")
    locations_present: List[str] = Field(default_factory=list, description="Location IDs present")


class StoryDetailResponse(BaseModel):
    """Response with full story details."""
    id: str = Field(..., description="Story ID")
    title: str = Field(..., description="Story title")
    description: str = Field(..., description="Story description")
    genre: Optional[str] = Field(None, description="Story genre")
    start_segment_id: Optional[str] = Field(None, description="Starting segment ID")
    created_at: str = Field(..., description="When story was created")
    updated_at: str = Field(..., description="When story was last updated")
    characters: List[Dict[str, Any]] = Field(default_factory=list, description="All characters in story")
    locations: List[Dict[str, Any]] = Field(default_factory=list, description="All locations in story")


class ChoicesResponse(BaseModel):
    """Response with segment and choices."""
    segment: SegmentResponse = Field(..., description="The segment")
    choices: List[Choice] = Field(..., description="Available choices")
    scene_number: int = Field(..., description="Scene number in playthrough")


class GenerateSceneRequest(BaseModel):
    """Request to generate next scene."""
    choice_text: str = Field(..., description="Custom choice text for generation")
    character_ids: Optional[List[str]] = Field(None, description="Character IDs to involve")


# Endpoints
@router.get("/stories")
async def list_stories() -> Dict[str, Any]:
    """
    List all available stories.
    
    Returns:
        Dictionary with 'success' flag and list of story metadata
    """
    try:
        stories = StoryLoader.list_all_stories()
        return success_response({
            "stories": stories,
            "count": len(stories)
        })
    except Exception as e:
        return error_response(str(e))


@router.get("/stories/{story_id}")
async def get_story_detail(story_id: str) -> Dict[str, Any]:
    """
    Get story details including all characters and locations.
    
    Args:
        story_id: The ID of the story
        
    Returns:
        Dictionary with story details
    """
    try:
        story = StoryLoader.load_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        # Load characters and locations
        characters = StoryLoader.load_all_characters(story_id)
        locations = StoryLoader.load_all_locations(story_id)
        
        return success_response({
            "id": story.id,
            "title": story.title,
            "description": story.description,
            "genre": story.genre,
            "start_segment_id": story.start_segment_id,
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat(),
            "characters": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "avatar_shape": c.avatar_shape,
                    "avatar_color": c.avatar_color,
                }
                for c in characters
            ],
            "locations": [
                {
                    "id": l.id,
                    "name": l.name,
                    "description": l.description,
                }
                for l in locations
            ]
        })
    except Exception as e:
        return error_response(str(e))


@router.get("/segments/{segment_id}")
async def get_segment(segment_id: str, story_id: str = Query(...)) -> Dict[str, Any]:
    """
    Get a segment with its choices.
    
    Args:
        segment_id: The ID of the segment
        story_id: The story ID (query parameter)
        
    Returns:
        Dictionary with segment and available choices
    """
    try:
        segment = StoryLoader.load_segment(story_id, segment_id)
        if not segment:
            return error_response(
                f"Segment '{segment_id}' not found in story '{story_id}'"
            )
        
        # Load choices for this segment
        choices = StoryLoader.load_choices_for_segment(story_id, segment_id)
        
        # Convert choices to response format
        choice_responses = [
            {
                "id": c.id,
                "from_segment_id": c.from_segment_id,
                "to_segment_id": c.to_segment_id,
                "choice_text": c.text,
                "generated": False,
            }
            for c in choices
        ]
        
        # Split into top 2 and remaining
        top_choices = choice_responses[:2]
        remaining_choices = choice_responses[2:]
        
        # Calculate scene number (1-indexed based on visited segments)
        scene_number = 1  # Default to 1, will be updated from session
        
        return success_response({
            "segment": {
                "id": segment.id,
                "story_id": segment.story_id,
                "short_description": segment.short_description,
                "atmosphere": segment.atmosphere,
                "time_of_day": segment.time_of_day,
                "weather": segment.weather,
                "text_blocks": [
                    {
                        "type": getattr(block, "type", "text"),
                        "content": getattr(block, "content", str(block)),
                    }
                    for block in segment.text_blocks
                ],
                "characters_present": segment.characters_present,
                "locations_present": segment.locations_present,
            },
            "choices": {
                "top": top_choices,
                "all": choice_responses,
            },
            "scene_number": scene_number,
        })
    except Exception as e:
        return error_response(str(e))


@router.post("/segments/{segment_id}/next")
async def generate_next_scene(
    segment_id: str,
    request: GenerateSceneRequest,
    story_id: str = Query(...)
) -> Dict[str, Any]:
    """
    Generate next scene from a custom choice (AI generation endpoint).
    
    This endpoint is reserved for Phase 2.5 when AI generation is integrated.
    
    Args:
        segment_id: The current segment ID
        request: The generation request with choice text
        story_id: The story ID (query parameter)
        
    Returns:
        Error response with 501 Not Implemented
    """
    return error_response(
        "AI generation endpoint coming in Phase 2.5"
    )
