"""Debug and logging utilities for the infinite story engine.

This module provides tools for debugging story generation, tracking state changes,
and monitoring performance of the story engine.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime


logger = logging.getLogger("infinite_story.utils.debug")


class PerformanceMonitor:
    """Monitor and log performance metrics for story operations."""
    
    def __init__(self, name: str):
        """Initialize the performance monitor.
        
        Args:
            name: Name of the operation being monitored
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        """Start timing the operation."""
        self.start_time = time.time()
        logger.debug(f"[PERF] Starting: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log the duration."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            logger.info(f"[PERF] Completed '{self.name}': {duration:.2f}s")
        else:
            logger.error(f"[PERF] Failed '{self.name}' after {duration:.2f}s: {exc_type.__name__}")
        
        return False
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0
        end = self.end_time or time.time()
        return end - self.start_time


def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance.
    
    Args:
        func: The function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with PerformanceMonitor(f"{func.__module__}.{func.__name__}") as monitor:
            result = func(*args, **kwargs)
            logger.debug(f"  Args: {args[:2]}")  # Log first 2 args for context
            logger.debug(f"  Kwargs: {kwargs}")
            return result
    
    return wrapper


class StateTracker:
    """Track state changes throughout story execution."""
    
    def __init__(self):
        """Initialize the state tracker."""
        self.events: list[dict] = []
    
    def log_state_change(
        self,
        component_type: str,
        component_id: str,
        change_type: str,
        details: Optional[dict] = None
    ) -> None:
        """Log a state change event.
        
        Args:
            component_type: Type of component (e.g., 'segment', 'character', 'choice')
            component_id: ID of the component that changed
            change_type: Type of change (e.g., 'created', 'modified', 'deleted')
            details: Additional details about the change
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "component_type": component_type,
            "component_id": component_id,
            "change_type": change_type,
            "details": details or {}
        }
        self.events.append(event)
        logger.debug(f"[STATE] {component_type}/{component_id}: {change_type}")
    
    def log_generation(
        self,
        segment_id: str,
        choice_text: str,
        prompt_length: int,
        response_tokens: Optional[int] = None,
        success: bool = True
    ) -> None:
        """Log AI generation event.
        
        Args:
            segment_id: ID of the segment being generated
            choice_text: The player's choice text
            prompt_length: Length of the prompt sent to AI
            response_tokens: Number of tokens in the response
            success: Whether generation was successful
        """
        logger.info(
            f"[GEN] Segment '{segment_id}' generated from choice: '{choice_text[:50]}...'\n"
            f"      Prompt: {prompt_length} chars | Response: {response_tokens or '?'} tokens | "
            f"Status: {'✓' if success else '✗'}"
        )
    
    def get_summary(self) -> str:
        """Get a summary of all tracked events.
        
        Returns:
            Formatted summary of events
        """
        if not self.events:
            return "No events tracked"
        
        summary = f"Total events: {len(self.events)}\n"
        
        # Group by component type
        by_type = {}
        for event in self.events:
            comp_type = event['component_type']
            if comp_type not in by_type:
                by_type[comp_type] = []
            by_type[comp_type].append(event)
        
        for comp_type, events in by_type.items():
            summary += f"  {comp_type}: {len(events)} events\n"
        
        return summary


class DebugHelper:
    """Helper utilities for debugging the story engine."""
    
    @staticmethod
    def format_segment_info(segment: Any) -> str:
        """Format segment information for debugging.
        
        Args:
            segment: The story segment to format
            
        Returns:
            Formatted string with segment details
        """
        info = f"""
=== Segment: {segment.id} ===
Description: {segment.short_description}
Atmosphere: {segment.atmosphere or 'None'}
Time: {segment.time_of_day or 'Unknown'}
Weather: {segment.weather or 'Unknown'}
Text Blocks: {len(segment.text_blocks)}
Characters Present: {', '.join(segment.characters_present) or 'None'}
Locations Present: {', '.join(segment.locations_present) or 'None'}
Outgoing Choices: {len(segment.outgoing_choices)}
Incoming Choices: {len(segment.incoming_choices)}
"""
        return info
    
    @staticmethod
    def format_prompt_info(prompt: str, max_length: int = 500) -> str:
        """Format prompt information for debugging.
        
        Args:
            prompt: The prompt text
            max_length: Maximum length of preview
            
        Returns:
            Formatted prompt information
        """
        preview = prompt[:max_length] + ("..." if len(prompt) > max_length else "")
        approx_tokens = len(prompt) // 4
        
        return f"""
=== Prompt Info ===
Length: {len(prompt)} characters (~{approx_tokens} tokens)
Preview:
{preview}
"""
    
    @staticmethod
    def format_response_info(response: Any) -> str:
        """Format generation response for debugging.
        
        Args:
            response: The generation response object
            
        Returns:
            Formatted response information
        """
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else vars(response)
        
        info = f"""
=== Generation Response ===
Status: {'✓ Success' if not response_dict.get('error') else '✗ Error'}
Error: {response_dict.get('error') or 'None'}
Short Description: {response_dict.get('short_description', 'N/A')[:100]}
Text Blocks: {len(response_dict.get('text_blocks', []))}
Choices Generated: 2
Atmosphere: {response_dict.get('atmosphere', 'N/A')}
Time: {response_dict.get('time_of_day', 'N/A')}
"""
        return info


def enable_debug_logging(level: int = logging.DEBUG) -> None:
    """Enable debug logging for the entire story engine.
    
    Args:
        level: The logging level to set (default: DEBUG)
    """
    # Set root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set specific loggers
    for logger_name in [
        'infinite_story',
        'infinite_story.models',
        'infinite_story.engine',
        'infinite_story.utils',
        'infinite_story.cli'
    ]:
        logging.getLogger(logger_name).setLevel(level)
    
    logger.info(f"Debug logging enabled at level {logging.getLevelName(level)}")


def disable_debug_logging() -> None:
    """Disable debug logging and reset to normal level."""
    logging.basicConfig(level=logging.INFO)
    
    for logger_name in [
        'infinite_story',
        'infinite_story.models',
        'infinite_story.engine',
        'infinite_story.utils',
        'infinite_story.cli'
    ]:
        logging.getLogger(logger_name).setLevel(logging.INFO)
    
    logger.info("Debug logging disabled")
