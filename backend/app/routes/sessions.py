"""Session management endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, UTC
from app.models.session_state import SessionState
from app.utils.scene_counter import SceneCounter

router = APIRouter()


class SessionStateRequest(BaseModel):
    """Request body for saving session state."""
    id: str = Field(..., description="Session ID (unique identifier)")
    story_id: str = Field(..., description="ID of the story")
    user_id: str = Field(..., description="ID of the user")
    current_segment_id: str = Field(..., description="Current segment ID")
    visited_segments: list[str] = Field(
        default_factory=list,
        description="List of visited segment IDs"
    )
    visited_choices: list[str] = Field(
        default_factory=list,
        description="List of visited choice IDs"
    )


class SessionStateResponse(BaseModel):
    """Response for session state operations."""
    found: bool = Field(..., description="Whether session was found")
    session: Optional[dict] = Field(None, description="Session state data")


class SessionSaveResponse(BaseModel):
    """Response for session save operation."""
    success: bool = Field(..., description="Whether save was successful")
    message: str = Field(..., description="Response message")
    saved_at: datetime = Field(..., description="When the session was saved")


class SessionDeleteResponse(BaseModel):
    """Response for session delete operation."""
    success: bool = Field(..., description="Whether delete was successful")
    message: str = Field(..., description="Response message")


@router.post("/sessions/save", response_model=SessionSaveResponse)
async def save_session(request: SessionStateRequest) -> SessionSaveResponse:
    """Save current game session.
    
    Args:
        request: Session state to save
        
    Returns:
        Success response with save timestamp
    """
    try:
        # Create SessionState from request
        session = SessionState(
            id=request.id,
            story_id=request.story_id,
            user_id=request.user_id,
            current_segment_id=request.current_segment_id,
            visited_segments=request.visited_segments,
            visited_choices=request.visited_choices
        )
        
        # Save to disk using StoryBase.save()
        session.save()
        
        return SessionSaveResponse(
            success=True,
            message="Session saved successfully",
            saved_at=datetime.now(UTC)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save session: {str(e)}"
        )


@router.get("/sessions/{story_id}/{session_id}", response_model=SessionStateResponse)
async def load_session(story_id: str, session_id: str) -> SessionStateResponse:
    """Load saved session for a story.
    
    Args:
        story_id: ID of the story
        session_id: ID of the session to load
        
    Returns:
        Loaded session state if found, otherwise found=False
    """
    try:
        session = SessionState.load(story_id, session_id)
        
        if session is None:
            return SessionStateResponse(
                found=False,
                session=None
            )
        
        return SessionStateResponse(
            found=True,
            session=session.to_dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load session: {str(e)}"
        )


@router.delete("/sessions/{story_id}/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(story_id: str, session_id: str) -> SessionDeleteResponse:
    """Delete saved session for a story.
    
    Args:
        story_id: ID of the story
        session_id: ID of the session to delete
        
    Returns:
        Success response
    """
    try:
        session = SessionState.load(story_id, session_id)
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No session found for story {story_id} with id {session_id}"
            )
        
        session.delete()
        
        return SessionDeleteResponse(
            success=True,
            message="Session deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
