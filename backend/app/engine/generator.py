from typing import TypeVar, Generic, Type, Optional, Dict, Any
from pydantic import BaseModel
from ..models.types import GeneratorResponse

T = TypeVar('T', bound=GeneratorResponse)

class Generator(Generic[T]):
    """Base class for AI generators.
    
    This class provides common functionality for generating content using AI models.
    It handles response parsing and error handling.
    """
    
    def __init__(self, response_type: Type[T]):
        """Initialize the generator.
        
        Args:
            response_type: The Pydantic model class to parse responses into
        """
        self.response_type = response_type
        
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[BaseModel] = None
    ) -> T:
        """Generate content based on prompts and context.
        
        Args:
            system_prompt: The system prompt that sets the behavior of the AI
            user_prompt: The user prompt that specifies what to generate
            context: Optional Pydantic model that provides context and validates the generated response
            
        Returns:
            A parsed response of type T
            
        Raises:
            ValueError: If the response cannot be parsed or validated against context
        """
        try:
            # In the future, this will call the AI model with both prompts
            raw_response = "{}"  # Empty JSON for now
            
            # Parse the response into the specified type
            response = self.response_type(
                raw_response=raw_response,
                parsed_data={},
                error=None
            )
            
            # If context is provided, validate the response against it
            if context is not None:
                # TODO: Implement context validation
                # This will depend on the specific context model and response type
                pass
                
            return response
            
        except Exception as e:
            # If parsing fails, return a response with the error
            return self.response_type(
                raw_response="",
                parsed_data={},
                error=str(e)
            )
            
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the raw response from the AI model.
        
        This method should be implemented by subclasses to handle their specific
        response format.
        
        Args:
            response: The raw response from the AI model
            
        Returns:
            A dictionary of parsed data
            
        Raises:
            ValueError: If the response cannot be parsed
        """
        # TODO: Implement actual response parsing
        return {}
