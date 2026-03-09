"""Story creation endpoints with SSE progress streaming."""

import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.utils.response_formatter import success_response, error_response

logger = logging.getLogger("infinite_story.routes.creation")

router = APIRouter()

# In-memory store for creation jobs (keyed by story_id)
_creation_jobs: Dict[str, Dict[str, Any]] = {}


class CreateStoryRequest(BaseModel):
    """Request body for creating a new story."""
    story_id: str = Field(..., description="Unique identifier (slug) for the story")
    title: str = Field(..., description="Display title")
    description: str = Field(..., description="Story description/premise")
    genre: str = Field(default="Fantasy", description="Genre (Fantasy, Sci-Fi, Mystery, etc.)")
    world_input: str = Field(default="", description="Optional user world vision")
    first_scene_input: str = Field(default="", description="Optional opening scene direction")


def _sanitize_story_id(raw: str) -> str:
    """Convert a raw string into a valid story_id slug."""
    slug = raw.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = slug.strip("_")
    return slug or "untitled_story"


@router.post("/stories/create")
async def create_story(request: CreateStoryRequest) -> Dict[str, Any]:
    """Start story creation (async). Returns immediately with job info.
    
    The actual generation runs in background. Poll /stories/create/{story_id}/status
    or connect to /stories/create/{story_id}/stream for SSE updates.
    """
    story_id = _sanitize_story_id(request.story_id)
    
    # Check if already running
    if story_id in _creation_jobs and _creation_jobs[story_id]["status"] == "running":
        return error_response(f"Creation already in progress for '{story_id}'")
    
    # Check if story already exists on disk
    from app.models.story import Story
    existing = Story.load(story_id, story_id)
    if existing:
        return error_response(f"Story '{story_id}' already exists")
    
    # Initialize job state
    _creation_jobs[story_id] = {
        "status": "running",
        "steps": [],
        "current_step": None,
        "error": None,
        "result": None,
    }
    
    # Start background generation
    asyncio.create_task(_run_creation(
        story_id=story_id,
        title=request.title,
        description=request.description,
        genre=request.genre,
        world_input=request.world_input,
        first_scene_input=request.first_scene_input,
    ))
    
    return success_response({
        "story_id": story_id,
        "status": "running",
        "message": "Story creation started",
        "stream_url": f"/api/stories/create/{story_id}/stream",
        "status_url": f"/api/stories/create/{story_id}/status",
    })


@router.get("/stories/create/{story_id}/status")
async def get_creation_status(story_id: str) -> Dict[str, Any]:
    """Poll creation status for a story."""
    job = _creation_jobs.get(story_id)
    if not job:
        return error_response(f"No creation job found for '{story_id}'")
    
    return success_response({
        "story_id": story_id,
        "status": job["status"],
        "current_step": job["current_step"],
        "steps": job["steps"],
        "error": job["error"],
        "result": job["result"],
    })


@router.get("/stories/create/{story_id}/stream")
async def stream_creation_progress(story_id: str):
    """SSE endpoint for real-time creation progress."""
    
    async def event_generator():
        # If no job, send error and close
        job = _creation_jobs.get(story_id)
        if not job:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No creation job found'})}\n\n"
            return
        
        last_step_count = 0
        while True:
            job = _creation_jobs.get(story_id)
            if not job:
                break
            
            # Send any new step updates
            current_steps = job["steps"]
            if len(current_steps) > last_step_count:
                for step_data in current_steps[last_step_count:]:
                    yield f"data: {json.dumps({'type': 'step', **step_data})}\n\n"
                last_step_count = len(current_steps)
            
            # Check if done
            if job["status"] in ("completed", "failed"):
                final = {
                    "type": "done" if job["status"] == "completed" else "error",
                    "status": job["status"],
                    "result": job["result"],
                    "error": job["error"],
                }
                yield f"data: {json.dumps(final)}\n\n"
                break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/stories/{story_id}")
async def delete_story(story_id: str) -> Dict[str, Any]:
    """Delete a story and all its data from disk."""
    import shutil
    from pathlib import Path
    from app.models.story_base import LOCAL_DATA_DIR
    
    story_dir = LOCAL_DATA_DIR / story_id
    if not story_dir.exists():
        return error_response(f"Story '{story_id}' not found")
    
    try:
        shutil.rmtree(story_dir)
        # Also clean up any creation job state
        _creation_jobs.pop(story_id, None)
        return success_response({"story_id": story_id, "deleted": True})
    except Exception as e:
        logger.error(f"Failed to delete story '{story_id}': {e}")
        return error_response(f"Failed to delete story: {str(e)}")


async def _run_creation(
    story_id: str,
    title: str,
    description: str,
    genre: str,
    world_input: str,
    first_scene_input: str,
):
    """Background task that runs the full creation pipeline."""
    from app.config import Config
    from app.engine.openrouter_generator import OpenRouterGenerator
    from app.engine.story_creation_orchestrator import StoryCreationOrchestrator
    
    job = _creation_jobs[story_id]
    
    try:
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
        
        def on_progress(progress):
            step_data = {
                "step": progress.step,
                "name": progress.name,
                "status": progress.status,
                "message": progress.message,
            }
            job["steps"].append(step_data)
            job["current_step"] = step_data
        
        orchestrator = StoryCreationOrchestrator(
            generator=generator,
            progress_callback=on_progress,
        )
        
        result = await orchestrator.create_story(
            story_id=story_id,
            title=title,
            description=description,
            genre=genre,
            world_input=world_input,
            first_scene_input=first_scene_input,
        )
        
        if result.success:
            job["status"] = "completed"
            job["result"] = orchestrator.get_creation_summary(result)
        else:
            job["status"] = "failed"
            job["error"] = result.error
            
    except Exception as e:
        logger.error(f"Creation background task failed: {e}", exc_info=True)
        job["status"] = "failed"
        job["error"] = str(e)
