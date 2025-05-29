from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Dict, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class Generator(Generic[T], ABC):
    """Abstract base class for story generators.
    
    This class defines the interface for all story generators in the system.
    Each concrete implementation must provide a way to generate content based on prompts
    and return a validated Pydantic model.
    """
    
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> T:
        """Generate content based on the given prompts.
        
        Args:
            system_prompt: The system-level prompt that defines the behavior and constraints
            user_prompt: The user-level prompt that specifies what to generate
            context: Optional additional context for the generation
            
        Returns:
            A validated Pydantic model instance of type T
            
        Raises:
            NotImplementedError: If the concrete class doesn't implement this method
        """
        raise NotImplementedError("Concrete generator must implement generate method")
