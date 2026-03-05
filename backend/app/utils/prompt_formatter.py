"""Format structured context into natural, lenient prompts for AI.

Instead of rigid structured formats, creates human-readable prompts
that are easier for AI to understand and generate responses for.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("infinite_story.utils.prompt_formatter")


class PromptFormatter:
    """Format context into natural language prompts."""
    
    @staticmethod
    def format_scene_context(context: Dict[str, Any], choice_text: str = None) -> str:
        """Format scene generation context into natural prompt.
        
        Args:
            context: Generation context dict from SegmentContextBuilder
            choice_text: Optional override for user choice text (uses context['user_choice'] if not provided)
            
        Returns:
            Natural language prompt for scene generation
        """
        # Allow choice_text override
        if choice_text and 'user_choice' not in context:
            context['user_choice'] = choice_text
        parts = []
        
        # Story context
        parts.append("=== STORY CONTEXT ===")
        if context.get('user_choice'):
            parts.append(f"The player chose: {context['user_choice']}")
        
        # Episode info
        ep_num = context.get('episode_number', 1)
        seg_num = context.get('segment_number_in_episode', 1)
        parts.append(f"\nEpisode {ep_num}, Scene {seg_num}")
        
        if context.get('episode_tone'):
            parts.append(f"Tone: {context['episode_tone']}")
        if context.get('episode_end_condition'):
            parts.append(f"Episode goal: {context['episode_end_condition']}")
        
        # Recent story
        if context.get('previous_segments'):
            parts.append("\n=== RECENT STORY ===")
            for seg in context['previous_segments'][-3:]:
                parts.append(f"• {seg}")
        
        # All episodes in arc
        if context.get('episodes_in_arc'):
            parts.append("\n=== EPISODES IN THIS ARC ===")
            for ep in context['episodes_in_arc']:
                ep_line = f"Episode {ep.get('episode_number')}: {ep.get('tone', 'Unknown tone')}"
                if ep.get('segments'):
                    ep_line += f" ({len(ep['segments'])} scenes)"
                parts.append(f"• {ep_line}")
        
        # Previous arcs for context
        if context.get('previous_arcs'):
            parts.append("\n=== PREVIOUS STORY ARCS ===")
            for arc in context['previous_arcs'][:3]:  # Show last 3 arcs
                arc_line = f"{arc.get('name', arc.get('arc_id'))}"
                if arc.get('resolution'):
                    arc_line += f": {arc['resolution']}"
                parts.append(f"• {arc_line}")
        
        # Character context
        if context.get('all_characters'):
            parts.append("\n=== CHARACTER REFERENCE ===")
            for char_id, char_info in list(context['all_characters'].items())[:5]:
                char_line = f"{char_info.get('name', char_id)}"
                if char_info.get('status'):
                    char_line += f" ({char_info['status']})"
                parts.append(f"• {char_line}")
        
        # Pacing signal
        pacing = context.get('pacing_weight', 0)
        parts.append(f"\n=== PACING ===")
        pacing_desc = "Just starting" if pacing < 0.25 else \
                     "Mid-episode" if pacing < 0.6 else \
                     "Approaching climax" if pacing < 0.85 else \
                     "Near the end"
        parts.append(f"Progress through episode: {pacing_desc} ({pacing:.0%})")
        
        # Instructions
        parts.append("\n=== GENERATION INSTRUCTIONS ===")
        parts.append("Write the next scene that:")
        parts.append("1. Follows naturally from the player's choice")
        parts.append("2. Maintains the episode tone and goals")
        parts.append("3. Respects character states and relationships")
        parts.append("4. Advances the story forward")
        parts.append("5. Provides meaningful next choices")
        
        parts.append("\nRespond with JSON containing: short_description, text, atmosphere, ")
        parts.append("time_of_day, weather, characters_present, locations_present, choice_1, choice_2")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_world_context(world_info: Dict[str, Any]) -> str:
        """Format world/setting context into natural prompt.
        
        Args:
            world_info: World information dict
            
        Returns:
            Natural language prompt for world generation
        """
        parts = []
        
        parts.append("=== WORLD GENERATION REQUEST ===\n")
        
        if world_info.get('context'):
            parts.append(f"Context: {world_info['context']}\n")
        
        if world_info.get('themes'):
            parts.append(f"Key themes: {', '.join(world_info['themes'])}\n")
        
        if world_info.get('tone'):
            parts.append(f"Tone: {world_info['tone']}\n")
        
        parts.append("Create a detailed world with:")
        parts.append("• Name and premise")
        parts.append("• Overall themes and tone")
        parts.append("• Key locations")
        parts.append("• History and current state")
        
        parts.append("\nRespond with JSON containing: name, premise, themes, ")
        parts.append("key_locations, history, current_state")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_character_context(char_info: Dict[str, Any]) -> str:
        """Format character context into natural prompt.
        
        Args:
            char_info: Character information dict
            
        Returns:
            Natural language prompt for character generation
        """
        parts = []
        
        parts.append("=== CHARACTER GENERATION REQUEST ===\n")
        
        if char_info.get('context'):
            parts.append(f"Context: {char_info['context']}\n")
        
        if char_info.get('role'):
            parts.append(f"Role in story: {char_info['role']}\n")
        
        if char_info.get('story_tone'):
            parts.append(f"Story tone: {char_info['story_tone']}\n")
        
        parts.append("Create a compelling character with:")
        parts.append("• Distinct name and appearance")
        parts.append("• Clear personality and motivations")
        parts.append("• Interesting background")
        parts.append("• Relationships to other characters")
        parts.append("• Current emotional state")
        
        parts.append("\nRespond with JSON containing: name, description, personality, ")
        parts.append("motivation, background, current_status")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_location_context(location_info: Dict[str, Any]) -> str:
        """Format location context into natural prompt.
        
        Args:
            location_info: Location information dict
            
        Returns:
            Natural language prompt for location generation
        """
        parts = []
        
        parts.append("=== LOCATION GENERATION REQUEST ===\n")
        
        if location_info.get('context'):
            parts.append(f"Context: {location_info['context']}\n")
        
        if location_info.get('world_details'):
            parts.append(f"World: {location_info['world_details']}\n")
        
        if location_info.get('purpose'):
            parts.append(f"Purpose: {location_info['purpose']}\n")
        
        parts.append("Describe this location with:")
        parts.append("• Evocative name")
        parts.append("• Detailed description and atmosphere")
        parts.append("• Key features and geography")
        parts.append("• Inhabitants or notable presences")
        parts.append("• Historical significance")
        
        parts.append("\nRespond with JSON containing: name, description, atmosphere, ")
        parts.append("features, inhabitants, history")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_choice_context(choice_context: Dict[str, Any]) -> str:
        """Format choice generation context into natural prompt.
        
        Args:
            choice_context: Choice context information
            
        Returns:
            Natural language prompt for choice generation
        """
        parts = []
        
        parts.append("=== CHOICE GENERATION REQUEST ===\n")
        
        if choice_context.get('current_scene'):
            parts.append(f"Current scene: {choice_context['current_scene']}\n")
        
        if choice_context.get('character_state'):
            parts.append(f"Character situation: {choice_context['character_state']}\n")
        
        if choice_context.get('stakes'):
            parts.append(f"What's at stake: {choice_context['stakes']}\n")
        
        parts.append("Generate 2-3 meaningful choices that:")
        parts.append("• Are distinct from each other")
        parts.append("• Fit the character's situation")
        parts.append("• Lead to different story outcomes")
        parts.append("• Feel natural and not forced")
        
        parts.append("\nRespond with JSON containing: choice_1, choice_2, and optionally choice_3")
        
        return "\n".join(parts)
    
    @staticmethod
    def format_recap_context(recap_context: Dict[str, Any]) -> str:
        """Format recap/summary context into natural prompt.
        
        Args:
            recap_context: Recap context information
            
        Returns:
            Natural language prompt for recap generation
        """
        parts = []
        
        parts.append("=== EPISODE RECAP REQUEST ===\n")
        
        if recap_context.get('episode_number'):
            parts.append(f"Episode {recap_context['episode_number']}\n")
        
        if recap_context.get('events'):
            parts.append("Key events:")
            for event in recap_context['events']:
                parts.append(f"• {event}")
            parts.append()
        
        if recap_context.get('character_changes'):
            parts.append("Character developments:")
            for char, change in recap_context['character_changes'].items():
                parts.append(f"• {char}: {change}")
            parts.append()
        
        parts.append("Write a concise recap (2-3 paragraphs) summarizing:")
        parts.append("• Major events and turning points")
        parts.append("• Character emotional arcs")
        parts.append("• Progress toward episode goals")
        parts.append("• Setup for upcoming challenges")
        
        parts.append("\nRespond with JSON containing: key_events, character_developments, plot_progression")
        
        return "\n".join(parts)


def format_generation_prompt(context: Dict[str, Any], content_type: str = "scene") -> str:
    """Format generation context based on content type.
    
    Args:
        context: Full generation context
        content_type: Type of content to generate
        
    Returns:
        Formatted prompt for AI
    """
    if content_type == "scene":
        return PromptFormatter.format_scene_context(context)
    elif content_type == "world":
        return PromptFormatter.format_world_context(context)
    elif content_type == "character":
        return PromptFormatter.format_character_context(context)
    elif content_type == "location":
        return PromptFormatter.format_location_context(context)
    elif content_type == "choice":
        return PromptFormatter.format_choice_context(context)
    elif content_type == "recap":
        return PromptFormatter.format_recap_context(context)
    else:
        logger.warning(f"Unknown content type: {content_type}")
        return str(context)

