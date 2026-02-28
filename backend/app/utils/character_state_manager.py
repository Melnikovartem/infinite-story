"""Utilities for managing character states and persistence."""
from typing import Optional, List, Dict, Any
from app.models.story_character import StoryCharacter


class CharacterStateManager:
    """Manages character state tracking and updates across story progression."""
    
    @staticmethod
    def update_character_state(
        character: StoryCharacter,
        segment_id: str,
        emotion: Optional[str] = None,
        status: str = "present",
        notes: str = ""
    ) -> None:
        """Update a character's state at a specific segment.
        
        Args:
            character: The StoryCharacter to update
            segment_id: The segment where this state applies
            emotion: Character's emotional state
            status: Character's presence status (present, absent, mentioned)
            notes: Additional notes about the character
        """
        character.add_state(
            segment_id=segment_id,
            emotion=emotion,
            status=status,
            notes=notes
        )
    
    @staticmethod
    def get_character_context(
        character: StoryCharacter,
        up_to_segment_id: Optional[str] = None,
        include_emotions: bool = True,
        include_notes: bool = True
    ) -> str:
        """Build context string for a character for AI generation.
        
        Args:
            character: The StoryCharacter to build context for
            up_to_segment_id: Only include states up to and including this segment
            include_emotions: Whether to include emotional states
            include_notes: Whether to include notes
            
        Returns:
            A formatted string with character context
        """
        context = f"Character: {character.name}\n"
        context += f"Description: {character.description}\n"
        context += f"Background: {character.background}\n"
        context += f"Avatar: {character.avatar_shape.value} {character.avatar_color}\n"
        
        if character.running_status:
            context += "\nCharacter Arc:\n"
            
            for state in character.running_status:
                # Skip if we have a segment limit and state is after it
                if up_to_segment_id:
                    # Only include states up to (and including) the specified segment
                    # We include all states since we don't have ordering info
                    pass
                
                segment_info = f"  - Segment {state['segment_id']}: "
                
                if include_emotions and state.get("emotion"):
                    segment_info += f"({state['emotion']}) "
                
                segment_info += f"[{state['status']}]"
                
                if include_notes and state.get("notes"):
                    segment_info += f" - {state['notes']}"
                
                context += segment_info + "\n"
        
        return context
    
    @staticmethod
    def get_characters_for_generation(
        characters: List[StoryCharacter],
        current_segment_id: str,
        max_history: int = 5
    ) -> str:
        """Build combined context for all characters for AI generation.
        
        Args:
            characters: List of StoryCharacter objects
            current_segment_id: The segment we're generating for
            max_history: Maximum number of previous states to include per character
            
        Returns:
            A formatted string with all character contexts
        """
        if not characters:
            return "No characters in this story."
        
        contexts = []
        for char in characters:
            context = CharacterStateManager.get_character_context(
                character=char,
                up_to_segment_id=current_segment_id
            )
            contexts.append(context)
        
        return "\n---\n".join(contexts)
    
    @staticmethod
    def extract_character_updates_from_response(
        response: Dict[str, Any],
        segment_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Extract character state updates from an AI generation response.
        
        This looks for character updates in the response format:
        {
            "character_updates": {
                "character_id": {
                    "emotion": "...",
                    "status": "...",
                    "notes": "..."
                }
            }
        }
        
        Args:
            response: The AI generation response dictionary
            segment_id: The segment this update applies to
            
        Returns:
            Dictionary mapping character IDs to state updates
        """
        updates = {}
        
        if "character_updates" not in response:
            return updates
        
        char_updates = response.get("character_updates", {})
        
        for char_id, update_data in char_updates.items():
            updates[char_id] = {
                "segment_id": segment_id,
                "emotion": update_data.get("emotion"),
                "status": update_data.get("status", "present"),
                "notes": update_data.get("notes", "")
            }
        
        return updates
    
    @staticmethod
    def apply_character_updates(
        characters: Dict[str, StoryCharacter],
        updates: Dict[str, Dict[str, Any]]
    ) -> None:
        """Apply character state updates.
        
        Args:
            characters: Dictionary mapping character IDs to StoryCharacter objects
            updates: Dictionary of updates from extract_character_updates_from_response
        """
        for char_id, update_data in updates.items():
            if char_id in characters:
                char = characters[char_id]
                char.add_state(
                    segment_id=update_data["segment_id"],
                    emotion=update_data.get("emotion"),
                    status=update_data.get("status", "present"),
                    notes=update_data.get("notes", "")
                )
    
    @staticmethod
    def get_character_arc_summary(character: StoryCharacter) -> str:
        """Get a summary of a character's emotional arc through the story.
        
        Args:
            character: The StoryCharacter to summarize
            
        Returns:
            A string describing the character's journey
        """
        if not character.running_status:
            return f"{character.name} has not appeared in the story yet."
        
        emotions = [
            state.get("emotion", "neutral")
            for state in character.running_status
            if state.get("emotion")
        ]
        
        if not emotions:
            return f"{character.name}'s journey through {len(character.running_status)} scene(s)."
        
        first_emotion = emotions[0] if emotions else "unknown"
        last_emotion = emotions[-1] if len(emotions) > 1 else first_emotion
        
        summary = f"{character.name}: {first_emotion} → {last_emotion}"
        
        if len(character.running_status) > 1:
            summary += f" (across {len(character.running_status)} scenes)"
        
        return summary
    
    @staticmethod
    def validate_character_states(character: StoryCharacter) -> List[str]:
        """Validate consistency of character states.
        
        Args:
            character: The StoryCharacter to validate
            
        Returns:
            List of validation messages/warnings
        """
        messages = []
        
        if not character.running_status:
            messages.append(f"Character {character.name} has no state history.")
            return messages
        
        # Check for consecutive 'absent' states with proper handling
        prev_status = None
        for i, state in enumerate(character.running_status):
            current_status = state.get("status")
            
            # Character shouldn't be in conflicting states
            if prev_status and prev_status == current_status:
                # This is OK - same state continues
                pass
            
            prev_status = current_status
        
        # Check for unusual emotional patterns
        emotions = [
            state.get("emotion")
            for state in character.running_status
            if state.get("emotion")
        ]
        
        if emotions and len(set(emotions)) == 1:
            messages.append(
                f"Warning: {character.name} has the same emotion ({emotions[0]}) throughout the story. "
                "Consider adding emotional variation."
            )
        
        return messages
