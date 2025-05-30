from typing import List, Union, Dict
from .story_block import StoryBlock

class StoryContext(StoryBlock):
    """Context for a story.
    
    This represents the fundamental truths and worldbuilding elements
    that provide context for the story.
    """
    fundamental_truths: List[str]
    worldbuilding: Union[str, Dict]

    def __init__(self, **data):
        """Initialize a StoryContext instance.
        
        Args:
            story: Optional Story instance to add this context to
            **data: Context data fields
        """
        super().__init__(**data)
        self.story.add_context(self)

    def get_short_overview(self) -> str:
        """Get a short descriptor of this story context.
        
        Returns:
            A string describing the key aspects of the world
        """
        # Get first few fundamental truths
        truths_preview = ", ".join(self.fundamental_truths[:2])
        if len(self.fundamental_truths) > 2:
            truths_preview += "..."
            
        return f"World Context: {truths_preview}"

    def get_full_overview(self) -> str:
        """Get detailed information about this story context.
        
        Returns:
            A string containing comprehensive world information
        """
        # Format worldbuilding information
        worldbuilding_info = ""
        if isinstance(self.worldbuilding, dict):
            for key, value in self.worldbuilding.items():
                worldbuilding_info += f"\n{key.title()}:\n{value}\n"
        else:
            worldbuilding_info = str(self.worldbuilding)

        # Format the full context information
        info = f"""Story Context

Fundamental Truths:
{chr(10).join(f"- {truth}" for truth in self.fundamental_truths)}

Worldbuilding:
{worldbuilding_info}"""

        return info
