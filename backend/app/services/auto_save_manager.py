"""Auto-save management system for sessions."""

import logging
import asyncio
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Optional, Dict
from app.models.session_state import SessionState

logger = logging.getLogger("infinite_story.auto_save")


class AutoSaveManager:
    """Manages automatic session saving with debouncing and error handling."""
    
    # Debounce time in seconds - don't save twice within this period
    DEBOUNCE_SECONDS = 10
    
    # Cleanup interval - remove old saves
    CLEANUP_OLDER_THAN_DAYS = 30
    
    # Track last save times per story
    _last_saves: Dict[str, datetime] = {}
    
    # Track pending saves
    _pending_saves: Dict[str, asyncio.Task] = {}
    
    @classmethod
    def should_save(cls, story_id: str) -> bool:
        """Check if enough time has passed to save.
        
        Uses debouncing to avoid too-frequent saves.
        
        Args:
            story_id: ID of the story
            
        Returns:
            True if enough time has passed since last save
        """
        now = datetime.now(UTC)
        last_save = cls._last_saves.get(story_id)
        
        if last_save is None:
            return True
        
        elapsed = (now - last_save).total_seconds()
        return elapsed >= cls.DEBOUNCE_SECONDS
    
    @classmethod
    async def auto_save_async(
        cls,
        story_id: str,
        session: SessionState
    ) -> bool:
        """Asynchronously save a session with debouncing.
        
        Args:
            story_id: ID of the story
            session: Session to save
            
        Returns:
            True if save was performed, False if debounced
        """
        # Check debounce
        if not cls.should_save(story_id):
            logger.debug(f"Auto-save for {story_id} debounced (too recent)")
            return False
        
        try:
            # Perform save
            SessionState.save_to_file(story_id, session)
            cls._last_saves[story_id] = datetime.now(UTC)
            logger.info(f"Auto-saved session for story {story_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to auto-save session for {story_id}: {e}")
            return False
    
    @classmethod
    def auto_save_sync(
        cls,
        story_id: str,
        session: SessionState
    ) -> bool:
        """Synchronously save a session with debouncing.
        
        Args:
            story_id: ID of the story
            session: Session to save
            
        Returns:
            True if save was performed, False if debounced
        """
        # Check debounce
        if not cls.should_save(story_id):
            logger.debug(f"Auto-save for {story_id} debounced (too recent)")
            return False
        
        try:
            # Perform save
            SessionState.save_to_file(story_id, session)
            cls._last_saves[story_id] = datetime.now(UTC)
            logger.info(f"Auto-saved session for story {story_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to auto-save session for {story_id}: {e}")
            # Don't raise - log and continue
            return False
    
    @classmethod
    def get_auto_save_info(cls, story_id: str) -> dict:
        """Get information about auto-save status for a story.
        
        Args:
            story_id: ID of the story
            
        Returns:
            Dictionary with auto-save information
        """
        last_save = cls._last_saves.get(story_id)
        next_save_ready = cls.should_save(story_id)
        
        info = {
            "story_id": story_id,
            "last_save": last_save.isoformat() if last_save else None,
            "next_save_ready_in_seconds": 0
        }
        
        if not next_save_ready and last_save:
            now = datetime.now(UTC)
            elapsed = (now - last_save).total_seconds()
            info["next_save_ready_in_seconds"] = max(0, int(cls.DEBOUNCE_SECONDS - elapsed))
        
        return info
    
    @classmethod
    def cleanup_old_saves(cls, days_old: Optional[int] = None) -> dict:
        """Clean up old saved sessions.
        
        Args:
            days_old: Delete saves older than this many days
                      (defaults to CLEANUP_OLDER_THAN_DAYS)
            
        Returns:
            Dictionary with cleanup statistics
        """
        if days_old is None:
            days_old = cls.CLEANUP_OLDER_THAN_DAYS
        
        cutoff_time = datetime.now(UTC) - timedelta(days=days_old)
        cleanup_stats = {
            "total_stories_checked": 0,
            "sessions_deleted": 0,
            "errors": []
        }
        
        try:
            base_dir = Path(".infinite_story_data")
            if not base_dir.exists():
                return cleanup_stats
            
            # Iterate through story directories
            for story_dir in base_dir.iterdir():
                if not story_dir.is_dir():
                    continue
                
                cleanup_stats["total_stories_checked"] += 1
                
                runner_state_file = story_dir / "runner_state.json"
                if not runner_state_file.exists():
                    continue
                
                # Get file modification time
                file_mtime = datetime.fromtimestamp(
                    runner_state_file.stat().st_mtime,
                    tz=UTC
                )
                
                # Delete if older than cutoff
                if file_mtime < cutoff_time:
                    try:
                        runner_state_file.unlink()
                        cleanup_stats["sessions_deleted"] += 1
                        logger.info(f"Deleted old session for {story_dir.name}")
                    except Exception as e:
                        error_msg = f"Failed to delete session for {story_dir.name}: {e}"
                        cleanup_stats["errors"].append(error_msg)
                        logger.error(error_msg)
            
            logger.info(
                f"Auto-save cleanup completed: {cleanup_stats['sessions_deleted']} "
                f"sessions deleted from {cleanup_stats['total_stories_checked']} stories"
            )
            
        except Exception as e:
            error_msg = f"Auto-save cleanup failed: {e}"
            cleanup_stats["errors"].append(error_msg)
            logger.error(error_msg)
        
        return cleanup_stats
    
    @classmethod
    def reset_debounce(cls, story_id: str) -> None:
        """Reset the debounce timer for a story.
        
        Useful for testing or force-save scenarios.
        
        Args:
            story_id: ID of the story
        """
        if story_id in cls._last_saves:
            del cls._last_saves[story_id]
        logger.debug(f"Reset debounce timer for story {story_id}")
    
    @classmethod
    def clear_all_debounce(cls) -> None:
        """Clear all debounce timers.
        
        Useful for testing.
        """
        cls._last_saves.clear()
        logger.debug("Cleared all debounce timers")
