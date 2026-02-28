"""Error handling and user-friendly error messages for the infinite story engine."""

import logging
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger("infinite_story.utils.error_handler")


class ErrorType(Enum):
    """Enumeration of error types with user-friendly messages."""
    
    # Configuration errors
    MISSING_CONFIG = "missing_config"
    INVALID_API_KEY = "invalid_api_key"
    INVALID_MODEL = "invalid_model"
    
    # Story errors
    STORY_NOT_FOUND = "story_not_found"
    SEGMENT_NOT_FOUND = "segment_not_found"
    INVALID_CHOICE = "invalid_choice"
    
    # Generation errors
    GENERATION_FAILED = "generation_failed"
    INVALID_RESPONSE = "invalid_response"
    API_RATE_LIMIT = "api_rate_limit"
    NETWORK_ERROR = "network_error"
    
    # System errors
    FILE_SYSTEM_ERROR = "file_system_error"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"


class StoryEngineError(Exception):
    """Base exception for story engine errors."""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        suggestion: Optional[str] = None,
        technical_details: Optional[str] = None
    ):
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        self.technical_details = technical_details
        super().__init__(message)


class ErrorHandler:
    """Centralized error handling for the story engine."""
    
    # Error messages and suggestions
    ERROR_MESSAGES = {
        ErrorType.MISSING_CONFIG: (
            "Configuration file is missing or invalid",
            "Please create a .env file in the backend directory based on .env.example:\n"
            "  cp backend/.env.example backend/.env\n"
            "  # Then edit with your OpenAI API key"
        ),
        ErrorType.INVALID_API_KEY: (
            "OpenAI API key is invalid or expired",
            "Please check your API key in the .env file:\n"
            "  - Verify the key is correct and not expired\n"
            "  - Check that the key has appropriate permissions\n"
            "  - Visit https://platform.openai.com/account/api-keys to manage keys"
        ),
        ErrorType.INVALID_MODEL: (
            "The specified OpenAI model is not available",
            "Please check your .env file for a valid model name.\n"
            "Popular choices: gpt-4, gpt-4-turbo-preview, gpt-3.5-turbo"
        ),
        ErrorType.STORY_NOT_FOUND: (
            "The selected story could not be found",
            "Please check that the story exists by running:\n"
            "  list-stories"
        ),
        ErrorType.SEGMENT_NOT_FOUND: (
            "A required story segment is missing",
            "The story data may be corrupted. Try running the story again or recreating it."
        ),
        ErrorType.GENERATION_FAILED: (
            "Failed to generate the next scene",
            "This could be due to:\n"
            "  - API rate limiting (try again in a moment)\n"
            "  - Network issues (check your internet connection)\n"
            "  - API service problems (check https://status.openai.com)\n"
            "Please try a different choice or try again later."
        ),
        ErrorType.INVALID_RESPONSE: (
            "The AI generated an invalid response",
            "The AI's response could not be parsed. Try generating the scene again.\n"
            "If this continues, there may be a problem with your API configuration."
        ),
        ErrorType.API_RATE_LIMIT: (
            "API rate limit exceeded",
            "You're making requests too quickly. Please wait a moment and try again.\n"
            "Consider using a lower temperature setting or fewer concurrent requests."
        ),
        ErrorType.NETWORK_ERROR: (
            "Network connection error",
            "Please check your internet connection and try again.\n"
            "If the problem persists, the API service may be experiencing issues."
        ),
        ErrorType.FILE_SYSTEM_ERROR: (
            "Error accessing story data on disk",
            "This may be a permissions issue or disk space problem.\n"
            "Please check that you have read/write permissions in the .infinite_story_data directory."
        ),
        ErrorType.PERMISSION_ERROR: (
            "Permission denied",
            "You don't have permission to access this resource.\n"
            "Please check your file permissions or contact your system administrator."
        ),
        ErrorType.UNKNOWN_ERROR: (
            "An unexpected error occurred",
            "Please report this issue with the detailed error message below."
        ),
    }
    
    @classmethod
    def get_user_message(cls, error_type: ErrorType) -> Tuple[str, str]:
        """Get user-friendly error message and suggestion for an error type.
        
        Args:
            error_type: The type of error that occurred
            
        Returns:
            Tuple of (message, suggestion)
        """
        if error_type in cls.ERROR_MESSAGES:
            return cls.ERROR_MESSAGES[error_type]
        return (
            "An unknown error occurred",
            "Please try again or report this issue."
        )
    
    @classmethod
    def handle_error(
        cls,
        error_type: ErrorType,
        technical_error: Optional[Exception] = None,
        context: Optional[str] = None
    ) -> Tuple[str, str]:
        """Handle an error and return user-friendly messages.
        
        Args:
            error_type: The type of error
            technical_error: The underlying technical exception
            context: Additional context about what was being done
            
        Returns:
            Tuple of (user_message, suggestion_message)
        """
        message, suggestion = cls.get_user_message(error_type)
        
        # Log technical details for debugging
        if technical_error:
            logger.error(
                f"Error [{error_type.value}] in context '{context}': {str(technical_error)}",
                exc_info=technical_error
            )
        else:
            logger.warning(f"Error [{error_type.value}] in context '{context}': {message}")
        
        return message, suggestion
    
    @classmethod
    def format_error_output(cls, message: str, suggestion: str) -> str:
        """Format error output for display in the CLI.
        
        Args:
            message: The error message
            suggestion: Suggestions for resolving the error
            
        Returns:
            Formatted error string for display
        """
        return f"\n[red]Error: {message}[/red]\n\n[yellow]Suggestion:[/yellow]\n{suggestion}\n"


class APIError(StoryEngineError):
    """Error related to API calls."""
    pass


class GenerationError(StoryEngineError):
    """Error during scene generation."""
    pass


class StorageError(StoryEngineError):
    """Error accessing story storage."""
    pass


class ConfigurationError(StoryEngineError):
    """Error in configuration."""
    pass


def handle_api_error(exception: Exception) -> Tuple[ErrorType, str]:
    """Determine error type from an API exception.
    
    Args:
        exception: The exception that occurred
        
    Returns:
        Tuple of (ErrorType, error_message)
    """
    error_msg = str(exception).lower()
    
    if "api_key" in error_msg or "authentication" in error_msg:
        return ErrorType.INVALID_API_KEY, str(exception)
    elif "rate_limit" in error_msg or "429" in error_msg:
        return ErrorType.API_RATE_LIMIT, str(exception)
    elif "model" in error_msg or "404" in error_msg:
        return ErrorType.INVALID_MODEL, str(exception)
    elif "connection" in error_msg or "timeout" in error_msg:
        return ErrorType.NETWORK_ERROR, str(exception)
    else:
        return ErrorType.GENERATION_FAILED, str(exception)


def handle_storage_error(exception: Exception) -> Tuple[ErrorType, str]:
    """Determine error type from a storage exception.
    
    Args:
        exception: The exception that occurred
        
    Returns:
        Tuple of (ErrorType, error_message)
    """
    error_msg = str(exception).lower()
    
    if "permission" in error_msg:
        return ErrorType.PERMISSION_ERROR, str(exception)
    elif "not found" in error_msg or "no such file" in error_msg:
        return ErrorType.STORY_NOT_FOUND, str(exception)
    else:
        return ErrorType.FILE_SYSTEM_ERROR, str(exception)
