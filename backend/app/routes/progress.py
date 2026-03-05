"""Progress tracking endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.session_state import SessionState
from app.utils.scene_counter import SceneCounter

router = APIRouter()


class ProgressResponse(BaseModel):
    """Response with progress information."""
    story_id: str = Field(..., description="Story ID")
    current_segment_id: str = Field(..., description="Current segment ID")
    scene_number: int = Field(..., description="Current scene number")
    total_visited: int = Field(..., description="Total scenes visited")
    elapsed_seconds: int = Field(..., description="Total elapsed seconds")
    elapsed_formatted: str = Field(..., description="Human-readable elapsed time")
    reading_pace_minutes_per_scene: float = Field(
        ...,
        description="Average minutes spent per scene"
    )
    estimated_remaining_seconds: Optional[int] = Field(
        None,
        description="Estimated remaining time if total scenes is known"
    )
    session_start_time: datetime = Field(..., description="When session started")
    last_updated: datetime = Field(..., description="Last session update time")


@router.get("/progress/{story_id}/{session_id}", response_model=ProgressResponse)
async def get_progress(
    story_id: str,
    session_id: str,
    estimated_total_scenes: Optional[int] = None
) -> ProgressResponse:
    """Get progress data for a story.
    
    Args:
        story_id: ID of the story
        session_id: ID of the session
        estimated_total_scenes: Total scene estimate for completion prediction
        
    Returns:
        Progress information including scene counter and timing data
    
    Note: v2 SessionState no longer tracks time. Progress is based on segment visits.
    """
    try:
        # Load session using new StoryBase pattern
        session = SessionState.load(story_id, session_id)
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No session found for story {story_id} with id {session_id}"
            )
        
        # v2: Calculate progress based on visited segments only
        total_visited = len(session.visited_segments)
        scene_number = total_visited  # Simplified: scene number = number of visited segments
        
        # Create scene counter with basic info from session
        counter = SceneCounter(
            scene_number=scene_number,
            start_time=session.created_at,
            elapsed_seconds=int((session.updated_at - session.created_at).total_seconds()),
            total_visited=total_visited
        )
        
        # Get remaining time estimate if provided
        remaining_seconds = counter.estimate_remaining_time(estimated_total_scenes)
        
        return ProgressResponse(
            story_id=story_id,
            current_segment_id=session.current_segment_id,
            scene_number=counter.scene_number,
            total_visited=counter.total_visited,
            elapsed_seconds=counter.elapsed_seconds,
            elapsed_formatted=counter.get_elapsed_formatted(),
            reading_pace_minutes_per_scene=counter.get_reading_pace(),
            estimated_remaining_seconds=remaining_seconds,
            session_start_time=session.created_at,
            last_updated=session.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )
