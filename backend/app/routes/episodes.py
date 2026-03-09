"""Episode and arc management endpoints."""

import logging
from fastapi import APIRouter, Query
from typing import Dict, Any

from app.utils.story_loader import StoryLoader
from app.utils.response_formatter import success_response, error_response

logger = logging.getLogger("infinite_story.routes.episodes")

router = APIRouter()


@router.get("/episodes/{story_id}")
async def list_episodes(story_id: str) -> Dict[str, Any]:
    """List all episodes for a story.
    
    Args:
        story_id: The story ID
        
    Returns:
        List of episode summaries
    """
    try:
        story = StoryLoader.load_full_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        episodes = story.get_all_episodes()
        episode_list = []
        for ep in sorted(episodes, key=lambda e: e.episode_number):
            episode_list.append({
                "id": ep.id,
                "episode_number": ep.episode_number,
                "arc_id": ep.arc_id,
                "title": ep.title if hasattr(ep, 'title') else None,
                "summary": ep.summary if hasattr(ep, 'summary') else None,
                "episode_complete": ep.episode_complete if hasattr(ep, 'episode_complete') else False,
                "segment_count": ep.segment_count if hasattr(ep, 'segment_count') else 0,
                "tone": ep.tone if hasattr(ep, 'tone') else None,
            })
        
        return success_response({
            "episodes": episode_list,
            "count": len(episode_list),
        })
    except Exception as e:
        logger.error(f"list_episodes error: {e}", exc_info=True)
        return error_response(str(e))


@router.get("/episodes/{story_id}/{episode_id}")
async def get_episode(story_id: str, episode_id: str) -> Dict[str, Any]:
    """Get full episode details including recap.
    
    Args:
        story_id: The story ID
        episode_id: The episode ID
        
    Returns:
        Full episode data
    """
    try:
        story = StoryLoader.load_full_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        episode = story.get_episode(episode_id)
        if not episode:
            return error_response(f"Episode '{episode_id}' not found")
        
        return success_response({
            "id": episode.id,
            "episode_number": episode.episode_number,
            "arc_id": episode.arc_id,
            "title": getattr(episode, 'title', None),
            "summary": getattr(episode, 'summary', None),
            "recap": getattr(episode, 'recap', None),
            "episode_complete": getattr(episode, 'episode_complete', False),
            "segment_count": getattr(episode, 'segment_count', 0),
            "segment_ids": getattr(episode, 'segment_ids', []),
            "tone": getattr(episode, 'tone', None),
            "themes": getattr(episode, 'themes', []),
            "hook_for_next": getattr(episode, 'hook_for_next', None),
            "selected_themes": getattr(episode, 'selected_themes', []),
            "episode_focus": getattr(episode, 'episode_focus', ''),
            "story_hooks": getattr(episode, 'story_hooks', []),
        })
    except Exception as e:
        logger.error(f"get_episode error: {e}", exc_info=True)
        return error_response(str(e))


@router.get("/arcs/{story_id}")
async def list_arcs(story_id: str) -> Dict[str, Any]:
    """List all arcs for a story.
    
    Args:
        story_id: The story ID
        
    Returns:
        List of arc summaries
    """
    try:
        story = StoryLoader.load_full_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        arcs = story.get_all_arcs()
        arc_list = []
        for arc in arcs:
            arc_list.append({
                "id": arc.id,
                "title": arc.title if hasattr(arc, 'title') else None,
                "description": arc.description if hasattr(arc, 'description') else None,
                "is_active": getattr(arc, 'is_active', False),
                "is_finalized": getattr(arc, 'is_finalized', False),
                "episode_count": getattr(arc, 'episode_count', 0),
                "themes": getattr(arc, 'themes', []),
                "central_conflict": getattr(arc, 'central_conflict', None),
            })
        
        return success_response({
            "arcs": arc_list,
            "count": len(arc_list),
        })
    except Exception as e:
        logger.error(f"list_arcs error: {e}", exc_info=True)
        return error_response(str(e))


@router.get("/arcs/{story_id}/{arc_id}")
async def get_arc(story_id: str, arc_id: str) -> Dict[str, Any]:
    """Get full arc details.
    
    Args:
        story_id: The story ID
        arc_id: The arc ID
        
    Returns:
        Full arc data
    """
    try:
        story = StoryLoader.load_full_story(story_id)
        if not story:
            return error_response(f"Story '{story_id}' not found")
        
        arc = story.get_arc(arc_id)
        if not arc:
            return error_response(f"Arc '{arc_id}' not found")
        
        return success_response({
            "id": arc.id,
            "title": getattr(arc, 'title', None),
            "description": getattr(arc, 'description', None),
            "is_active": getattr(arc, 'is_active', False),
            "is_finalized": getattr(arc, 'is_finalized', False),
            "episode_count": getattr(arc, 'episode_count', 0),
            "themes": getattr(arc, 'themes', []),
            "central_conflict": getattr(arc, 'central_conflict', None),
            "tone_tags": getattr(arc, 'tone_tags', []),
            "mood": getattr(arc, 'mood', None),
            "unresolved_mysteries": getattr(arc, 'unresolved_mysteries', []),
            "plot_hooks": getattr(arc, 'plot_hooks', []),
            "recap_title": getattr(arc, 'recap_title', None),
            "recap_summary": getattr(arc, 'recap_summary', None),
        })
    except Exception as e:
        logger.error(f"get_arc error: {e}", exc_info=True)
        return error_response(str(e))
