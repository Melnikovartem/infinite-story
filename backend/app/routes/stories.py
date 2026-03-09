"""Story and segment management endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

from app.utils.story_loader import StoryLoader
from app.utils.response_formatter import success_response, error_response

logger = logging.getLogger("infinite_story.routes.stories")

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


def _build_segment_response(segment, choices: list, story=None) -> Dict[str, Any]:
    """Build a standardized segment response with episode/arc metadata.
    
    Args:
        segment: StorySegment instance
        choices: List of StoryChoice instances
        story: Optional Story instance (for arc title lookup)
    """
    choice_responses = [
        {
            "id": c.id,
            "from_segment_id": c.from_segment_id,
            "to_segment_id": c.to_segment_id,
            "choice_text": c.text if hasattr(c, 'text') else c.get('choice_text', ''),
            "generated": True,
        }
        for c in choices
    ]
    
    result = {
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
            "top": choice_responses[:2],
            "all": choice_responses,
        },
        "episode": {
            "number": segment.episode_number,
            "segment_in_episode": segment.segment_number_in_episode,
            "tone": segment.episode_tone,
            "arc_id": segment.arc_id,
            "triggers_transition": segment.triggers_episode_transition,
        },
    }
    
    # Add arc info if available
    if story and segment.arc_id:
        arc = story.get_arc(segment.arc_id)
        if arc:
            result["episode"]["arc_title"] = arc.title if hasattr(arc, 'title') else None
    
    return result


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
        
        return success_response(_build_segment_response(segment, choices))
    except Exception as e:
        return error_response(str(e))


@router.post("/segments/{segment_id}/choice/{choice_id}")
async def navigate_to_choice(
    segment_id: str,
    choice_id: str,
    story_id: str = Query(...)
) -> Dict[str, Any]:
    """
    Navigate to an existing choice's destination segment.
    
    If the choice has a to_segment_id, loads that segment and its choices.
    If the choice has no destination (to_segment_id is None), triggers AI
    generation to create the next scene.
    
    Args:
        segment_id: The current segment ID
        choice_id: The choice ID to navigate
        story_id: The story ID (query parameter)
        
    Returns:
        Dictionary with the destination segment and its choices
    """
    try:
        # Load the story with all components for full graph traversal
        story = StoryLoader.load_full_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        # Find the choice
        choice = story.get_choice(choice_id)
        if not choice:
            return error_response(f"Choice '{choice_id}' not found")
        
        # Verify the choice belongs to the requested segment
        if choice.from_segment_id != segment_id:
            return error_response(
                f"Choice '{choice_id}' does not belong to segment '{segment_id}'"
            )
        
        # If choice already has a destination, load it
        if choice.to_segment_id:
            dest_segment = story.get_segment(choice.to_segment_id)
            if not dest_segment:
                return error_response(
                    f"Destination segment '{choice.to_segment_id}' not found"
                )
        else:
            # No destination — need AI generation
            logger.info(f"Choice '{choice_id}' has no destination, generating next scene...")
            
            # Lock the choice to prevent concurrent generation
            if choice.locked:
                return error_response(
                    "This choice is currently being generated. Please wait."
                )
            choice.lock()
            
            try:
                # Create generator from config
                from app.config import Config
                from app.engine.openrouter_generator import OpenRouterGenerator
                
                config = Config.load()
                generator = OpenRouterGenerator(
                    api_key=config.generator.api_key,
                    model=config.generator.model,
                    temperature=config.generator.temperature,
                    max_tokens=config.generator.max_tokens,
                    site_url=config.generator.site_url,
                    site_name=config.generator.site_name,
                    auto_fallback=True,
                )
                
                # Get the source segment for generation
                source_segment = story.get_segment(segment_id)
                if not source_segment:
                    return error_response(f"Source segment '{segment_id}' not found")
                
                # Generate next scene
                dest_segment = await source_segment.generate_next_scene(
                    connecting_choice=choice,
                    generator=generator,
                )
            except Exception as gen_err:
                logger.error(f"Generation failed: {gen_err}", exc_info=True)
                choice.unlock()
                return error_response(f"Scene generation failed: {str(gen_err)}")
            finally:
                # Unlock choice (it now has a to_segment_id if generation succeeded)
                if choice.locked:
                    choice.unlock()
        
        # Load outgoing choices for the destination segment
        dest_choices = list(dest_segment.outgoing_choices.values())
        # If no outgoing choices in memory, try loading from disk
        if not dest_choices:
            dest_choices = StoryLoader.load_choices_for_segment(story_id, dest_segment.id)
        
        return success_response(_build_segment_response(dest_segment, dest_choices, story))
    except Exception as e:
        logger.error(f"navigate_to_choice error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/segments/{segment_id}/next")
async def generate_next_scene(
    segment_id: str,
    request: GenerateSceneRequest,
    story_id: str = Query(...)
) -> Dict[str, Any]:
    """
    Generate next scene from a custom choice text (AI generation endpoint).
    
    Creates a new StoryChoice from the custom text, then generates the
    next scene via AI.
    
    Args:
        segment_id: The current segment ID
        request: The generation request with choice text
        story_id: The story ID (query parameter)
        
    Returns:
        Dictionary with new segment and its choices
    """
    try:
        import uuid
        from app.models.story_choice import StoryChoice
        
        # Load the full story with all components
        story = StoryLoader.load_full_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        source_segment = story.get_segment(segment_id)
        if not source_segment:
            return error_response(f"Segment '{segment_id}' not found")
        
        # Create a custom choice from the player's text
        choice_count = len(story.get_all_choices())
        custom_choice_id = f"custom_choice_{choice_count + 1}_{uuid.uuid4().hex[:8]}"
        
        custom_choice = StoryChoice(
            story=story,
            id=custom_choice_id,
            from_segment_id=segment_id,
            to_segment_id=None,
            text=request.choice_text,
        )
        custom_choice.save()
        
        # Create generator from config
        from app.config import Config
        from app.engine.openrouter_generator import OpenRouterGenerator
        
        config = Config.load()
        generator = OpenRouterGenerator(
            api_key=config.generator.api_key,
            model=config.generator.model,
            temperature=config.generator.temperature,
            max_tokens=config.generator.max_tokens,
            site_url=config.generator.site_url,
            site_name=config.generator.site_name,
            auto_fallback=True,
        )
        
        # Generate next scene
        new_segment = await source_segment.generate_next_scene(
            connecting_choice=custom_choice,
            generator=generator,
        )
        
        # Load outgoing choices for the new segment
        new_choices = list(new_segment.outgoing_choices.values())
        if not new_choices:
            new_choices = StoryLoader.load_choices_for_segment(story_id, new_segment.id)
        
        return success_response(_build_segment_response(new_segment, new_choices, story))
    except Exception as e:
        logger.error(f"generate_next_scene error: {e}", exc_info=True)
        return error_response(f"Scene generation failed: {str(e)}")
