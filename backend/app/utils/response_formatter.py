"""
Response formatting utilities for consistent API responses.
"""

from typing import Any, Optional
from datetime import datetime, UTC
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str


def success_response(data: Any = None) -> dict:
    """
    Create a success response.
    
    Args:
        data: The response data payload
        
    Returns:
        dict: Formatted response
    """
    return {
        "success": True,
        "data": data,
        "error": None,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def error_response(error: str) -> dict:
    """
    Create an error response.
    
    Args:
        error: Error message
        
    Returns:
        dict: Formatted error response
    """
    return {
        "success": False,
        "data": None,
        "error": error,
        "timestamp": datetime.now(UTC).isoformat(),
    }
