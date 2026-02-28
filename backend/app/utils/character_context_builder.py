"""Character context integration for scene generation.

This module extends the prompt building system to include rich character
state information and emotional arcs.
"""

import logging
from typing import Optional, List, Dict, Any
from app.models.story_character import StoryCharacter
from app.utils.character_state_manager import CharacterStateManager

logger = logging.getLogger("infinite_story.utils.character_context_builder")


class CharacterContextBuilder:
    """Builds rich character context for scene generation."""
    
    @staticmethod
    def build_character_section(
        characters: List[StoryCharacter],
        current_segment_id: str,
        include_arcs: bool = True,
        max_chars: Optional[int] = None
    ) -> str:
        """Build a formatted character section for prompts.
        
        Args:
            characters: List of StoryCharacter objects
            current_segment_id: The current segment ID for context
            include_arcs: Whether to include emotional arc information
            max_chars: Maximum number of characters to include (None = all)
            
        Returns:
            A formatted string with character information
        """
        if not characters:
            return ""
        
        # Limit number of characters if requested
        chars_to_include = characters[:max_chars] if max_chars else characters
        
        section = "=== CHARACTER INFORMATION ===\n"
        
        for char in chars_to_include:
            section += f"\n{char.name}\n"
            section += f"  Description: {char.description}\n"
            section += f"  Avatar: {char.avatar_shape.value} {char.avatar_color}\n"
            
            # Get current state if available
            current_state = char.get_state_at_segment(current_segment_id)
            if current_state:
                section += f"  Status: {current_state.get('status', 'unknown')}\n"
                if current_state.get("emotion"):
                    section += f"  Emotion: {current_state['emotion']}\n"
                if current_state.get("notes"):
                    section += f"  Notes: {current_state['notes']}\n"
            
            # Include emotional arc if requested
            if include_arcs and char.running_status:
                arc_summary = CharacterStateManager.get_character_arc_summary(char)
                section += f"  Arc: {arc_summary}\n"
        
        return section + "\n"
    
    @staticmethod
    def build_character_instructions(characters: List[StoryCharacter]) -> str:
        """Build AI instructions for character consistency.
        
        Args:
            characters: List of StoryCharacter objects
            
        Returns:
            A string with instructions for the AI model
        """
        if not characters:
            return ""
        
        instructions = "=== CHARACTER CONSISTENCY INSTRUCTIONS ===\n"
        instructions += "When generating the next scene, maintain consistency with:\n"
        
        # List character names and key traits
        char_names = [char.name for char in characters]
        instructions += f"- Character names: {', '.join(char_names)}\n"
        
        # Add emotional consistency warnings
        emotional_chars = [
            char for char in characters
            if char.running_status and any(s.get("emotion") for s in char.running_status)
        ]
        
        if emotional_chars:
            instructions += "- Emotional consistency for: "
            instructions += ", ".join([c.name for c in emotional_chars]) + "\n"
        
        instructions += "- Character descriptions and relationships\n"
        instructions += "- Previously established story details\n\n"
        
        return instructions
    
    @staticmethod
    def extract_character_updates_from_text(
        generated_text: str,
        characters: Dict[str, StoryCharacter],
        segment_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Extract character emotion/status updates from generated text.
        
        This attempts to infer character state changes from the generated narrative.
        
        Args:
            generated_text: The AI-generated scene text
            characters: Dictionary mapping character IDs to StoryCharacter objects
            segment_id: The segment being generated
            
        Returns:
            Dictionary of character updates
        """
        updates = {}
        
        # Map character names to IDs for quick lookup
        name_to_id = {char.name.lower(): char_id for char_id, char in characters.items()}
        
        # Simple heuristic: look for emotion words near character names
        emotion_keywords = {
            "happy": "happy",
            "sad": "sad",
            "angry": "angry",
            "afraid": "afraid",
            "scared": "afraid",
            "excited": "excited",
            "determined": "determined",
            "confused": "confused",
            "worried": "worried",
            "triumphant": "triumphant",
            "defeated": "defeated",
        }
        
        text_lower = generated_text.lower()
        
        for char_name, char_id in name_to_id.items():
            # Find all occurrences of character name
            char_positions = []
            start = 0
            while True:
                pos = text_lower.find(char_name, start)
                if pos == -1:
                    break
                char_positions.append(pos)
                start = pos + 1
            
            if not char_positions:
                continue
            
            # Check around the first occurrence
            char_pos = char_positions[0]
            # Look in a window around the character mention
            window_start = max(0, char_pos - 100)
            window_end = min(len(text_lower), char_pos + 100)
            context_window = text_lower[window_start:window_end]
            
            found_emotion = None
            for keyword, emotion in emotion_keywords.items():
                if keyword in context_window:
                    found_emotion = emotion
                    break
            
            # Always add character if mentioned
            updates[char_id] = {
                "segment_id": segment_id,
                "status": "present",
                "emotion": found_emotion,
                "notes": ""
            }
        
        return updates
    
    @staticmethod
    def integrate_character_context_into_prompt(
        prompt: str,
        characters: List[StoryCharacter],
        current_segment_id: str,
        include_instructions: bool = True
    ) -> str:
        """Integrate character context into an existing prompt.
        
        Args:
            prompt: The base prompt string
            characters: List of StoryCharacter objects
            current_segment_id: Current segment ID
            include_instructions: Whether to include consistency instructions
            
        Returns:
            Enhanced prompt with character information
        """
        # Build character sections
        char_section = CharacterContextBuilder.build_character_section(
            characters,
            current_segment_id,
            include_arcs=True,
            max_chars=10
        )
        
        # Add character section to prompt
        enhanced_prompt = prompt + "\n" + char_section
        
        # Add instructions if requested
        if include_instructions:
            instructions = CharacterContextBuilder.build_character_instructions(characters)
            enhanced_prompt += instructions
        
        return enhanced_prompt
    
    @staticmethod
    def validate_and_apply_character_updates(
        characters: Dict[str, StoryCharacter],
        updates: Dict[str, Dict[str, Any]],
        max_emotional_change: int = 3
    ) -> List[str]:
        """Validate and apply character updates, returning any warnings.
        
        Args:
            characters: Dictionary mapping character IDs to StoryCharacter objects
            updates: Dictionary of character updates to apply
            max_emotional_change: Maximum number of emotions to change per segment
            
        Returns:
            List of validation warnings/messages
        """
        warnings = []
        changes_made = 0
        
        for char_id, update in updates.items():
            if char_id not in characters:
                warnings.append(f"Unknown character ID: {char_id}")
                continue
            
            char = characters[char_id]
            
            # Apply the update
            char.add_state(
                segment_id=update.get("segment_id"),
                emotion=update.get("emotion"),
                status=update.get("status", "present"),
                notes=update.get("notes", "")
            )
            changes_made += 1
        
        # Warn if too many changes
        if changes_made > max_emotional_change:
            warnings.append(
                f"High character volatility: {changes_made} characters changed in one segment. "
                f"Consider narrative pacing."
            )
        
        return warnings
