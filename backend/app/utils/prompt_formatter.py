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
        
        # ================================================================
        # PREVIOUS ARCS — long-term story memory (most important for continuity)
        # ================================================================
        if context.get('previous_arcs'):
            parts.append("=== STORY SO FAR (PREVIOUS ARCS) ===")
            for arc in context['previous_arcs'][:3]:
                arc_name = arc.get('name', arc.get('arc_id', 'Unknown'))
                # Guard against raw JSON stored as title (pre-existing data issue)
                if arc_name and (arc_name.startswith('{') or arc_name.startswith('"') or len(arc_name) > 100):
                    arc_name = f"Arc ({arc.get('arc_id', 'previous')[:20]})"
                parts.append(f"\n--- {arc_name} ---")
                if arc.get('premise'):
                    parts.append(f"Premise: {arc['premise']}")
                if arc.get('recap'):
                    # Include the actual recap text (the whole point of this section)
                    recap_text = arc['recap']
                    if len(recap_text) > 500:
                        recap_text = recap_text[:500] + "..."
                    parts.append(f"What happened: {recap_text}")
                if arc.get('resolution'):
                    parts.append(f"Outcome: {arc['resolution']}")
                if arc.get('unresolved'):
                    parts.append(f"Unresolved threads: {', '.join(arc['unresolved'][:5])}")
                if arc.get('character_arcs'):
                    for char_id, resolution in list(arc['character_arcs'].items())[:3]:
                        parts.append(f"  • {char_id}: {resolution}")
        
        # ================================================================
        # CURRENT ARC — what the story is about right now
        # ================================================================
        current_arc = context.get('current_arc', {})
        if current_arc:
            parts.append("\n=== CURRENT ARC ===")
            if current_arc.get('title'):
                parts.append(f"Arc: {current_arc['title']}")
            if current_arc.get('premise'):
                parts.append(f"Premise: {current_arc['premise']}")
            if current_arc.get('narrative_direction'):
                parts.append(f"Direction: {current_arc['narrative_direction']}")
            if current_arc.get('central_conflict'):
                parts.append(f"Central conflict: {current_arc['central_conflict']}")
            if current_arc.get('themes'):
                parts.append(f"Themes: {', '.join(current_arc['themes'][:5])}")
            if current_arc.get('previous_arc_summary'):
                parts.append(f"\nPrevious arc context: {current_arc['previous_arc_summary'][:300]}")
            if current_arc.get('unresolved_mysteries'):
                parts.append(f"Open mysteries: {', '.join(current_arc['unresolved_mysteries'][:5])}")
            if current_arc.get('plot_hooks'):
                parts.append(f"Active hooks: {', '.join(current_arc['plot_hooks'][:5])}")
        
        # ================================================================
        # EPISODE RECAPS — what happened in recent episodes of this arc
        # ================================================================
        if context.get('recent_episode_recaps'):
            parts.append("\n=== RECENT EPISODES ===")
            for recap in context['recent_episode_recaps']:
                ep_line = f"Episode {recap.get('episode', '?')}"
                if recap.get('title'):
                    ep_line += f": {recap['title']}"
                parts.append(ep_line)
                if recap.get('summary'):
                    parts.append(f"  {recap['summary'][:200]}")
                if recap.get('hook_for_next'):
                    parts.append(f"  Hook: {recap['hook_for_next']}")
        
        # ================================================================
        # CURRENT EPISODE & SCENE
        # ================================================================
        parts.append("\n=== CURRENT EPISODE ===")
        ep_num = context.get('episode_number', 1)
        seg_num = context.get('segment_number_in_episode', 1)
        parts.append(f"Episode {ep_num}, Scene {seg_num}")
        
        if context.get('episode_tone'):
            parts.append(f"Tone: {context['episode_tone']}")
        if context.get('episode_end_condition'):
            parts.append(f"Episode goal: {context['episode_end_condition']}")
        if context.get('episode_selected_themes'):
            parts.append(f"Episode themes: {', '.join(context['episode_selected_themes'])}")
        if context.get('episode_focus'):
            parts.append(f"Focus: {context['episode_focus']}")
        if context.get('story_hooks'):
            parts.append(f"Active hooks: {', '.join(context['story_hooks'][:3])}")
        
        # ================================================================
        # RECENT SCENES — what just happened
        # ================================================================
        # Full text of last 1-2 scenes for narrative flow
        if context.get('recent_segments_full'):
            parts.append("\n=== RECENT SCENES (FULL) ===")
            for seg_info in context['recent_segments_full'][-2:]:
                if isinstance(seg_info, dict):
                    if seg_info.get('description'):
                        parts.append(f"[{seg_info.get('segment_id', '?')}] {seg_info['description']}")
                    if seg_info.get('text'):
                        text = seg_info['text']
                        if len(text) > 400:
                            text = text[:400] + "..."
                        parts.append(text)
                elif isinstance(seg_info, str):
                    parts.append(seg_info[:400])
        elif context.get('previous_segments'):
            parts.append("\n=== RECENT SCENES ===")
            for seg in context['previous_segments'][-3:]:
                parts.append(f"• {seg}")
        
        # ================================================================
        # CHARACTERS — who is involved
        # ================================================================
        # Try hierarchical character context first (arc > episode > segment)
        char_sections = []
        if context.get('arc_characters'):
            for char_id, info in list(context['arc_characters'].items())[:8]:
                name = info.get('name', char_id) if isinstance(info, dict) else char_id
                desc = info.get('description', '') if isinstance(info, dict) else str(info)
                status = info.get('status', '') if isinstance(info, dict) else ''
                line = name
                if status:
                    line += f" ({status})"
                if desc:
                    line += f" — {desc[:80]}"
                char_sections.append(f"• {line}")
        
        # Override with episode-level updates
        if context.get('episode_characters'):
            for char_id, info in list(context['episode_characters'].items())[:5]:
                name = info.get('name', char_id) if isinstance(info, dict) else char_id
                status = info.get('status', '') if isinstance(info, dict) else str(info)
                if status:
                    char_sections.append(f"• {name} [updated]: {status[:100]}")
        
        # Fallback: all_characters key (old format)
        if not char_sections and context.get('all_characters'):
            for char_id, char_info in list(context['all_characters'].items())[:5]:
                char_line = char_info.get('name', char_id) if isinstance(char_info, dict) else char_id
                status = char_info.get('status', '') if isinstance(char_info, dict) else ''
                if status:
                    char_line += f" ({status})"
                char_sections.append(f"• {char_line}")
        
        if char_sections:
            parts.append("\n=== CHARACTERS ===")
            parts.extend(char_sections)
        
        # ================================================================
        # FACTIONS & MAGIC — world systems
        # ================================================================
        if context.get('factions'):
            factions_data = context['factions']
            # Unwrap {count: N, factions: [...]} structure if present
            if isinstance(factions_data, dict) and 'factions' in factions_data:
                factions_list = factions_data['factions']
            elif isinstance(factions_data, list):
                factions_list = factions_data
            elif isinstance(factions_data, dict):
                factions_list = list(factions_data.values())
            else:
                factions_list = []
            
            if factions_list:
                parts.append("\n=== FACTIONS ===")
                for f in factions_list[:4]:
                    if isinstance(f, dict):
                        name = f.get('name', f.get('id', '?'))
                        desc = f.get('description', f.get('status', ''))
                        goals = f.get('goals', [])
                        line = f"• {name}: {desc[:80]}"
                        if goals and isinstance(goals, list):
                            line += f" (goals: {', '.join(goals[:2])})"
                        parts.append(line)
                    else:
                        parts.append(f"• {str(f)[:100]}")
        
        if context.get('magic_system'):
            ms = context['magic_system']
            if isinstance(ms, dict) and ms.get('name'):
                parts.append(f"\n=== MAGIC/TECH SYSTEM ===")
                parts.append(f"{ms['name']}: {ms.get('description', ms.get('summary', ''))[:150]}")
            elif isinstance(ms, str) and ms:
                parts.append(f"\n=== MAGIC/TECH SYSTEM ===")
                parts.append(ms[:150])
        
        # ================================================================
        # MYSTERIES & THEMES — narrative tracking
        # ================================================================
        if context.get('mysteries_tracking'):
            mysteries = context['mysteries_tracking']
            if isinstance(mysteries, list) and mysteries:
                parts.append("\n=== OPEN MYSTERIES ===")
                for m in mysteries[:5]:
                    if isinstance(m, dict):
                        parts.append(f"• {m.get('mystery', m.get('name', str(m)))[:100]}")
                    else:
                        parts.append(f"• {str(m)[:100]}")
            elif isinstance(mysteries, dict) and mysteries:
                parts.append("\n=== OPEN MYSTERIES ===")
                for k, v in list(mysteries.items())[:5]:
                    parts.append(f"• {k}: {str(v)[:100]}")
        
        # ================================================================
        # PLAYER CHOICE — what the player decided
        # ================================================================
        if context.get('user_choice'):
            parts.append(f"\n=== PLAYER'S CHOICE ===")
            parts.append(f"The player chose: {context['user_choice']}")
        
        # ================================================================
        # PACING — where we are in the episode
        # ================================================================
        pacing = context.get('pacing_weight', 0)
        pacing_desc = "Just starting" if pacing < 0.25 else \
                     "Mid-episode" if pacing < 0.6 else \
                     "Approaching climax" if pacing < 0.85 else \
                     "Near the end"
        parts.append(f"\n=== PACING ===")
        parts.append(f"Progress through episode: {pacing_desc} ({pacing:.0%})")
        
        # ================================================================
        # INSTRUCTIONS
        # ================================================================
        parts.append("\n=== GENERATION INSTRUCTIONS ===")
        parts.append("Write the next scene that:")
        parts.append("1. Follows naturally from the player's choice")
        parts.append("2. Maintains continuity with previous arcs and episodes")
        parts.append("3. Respects character states, relationships, and established world facts")
        parts.append("4. Advances the current arc's premise and central conflict")
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
            parts.append("")
        
        if recap_context.get('character_changes'):
            parts.append("Character developments:")
            for char, change in recap_context['character_changes'].items():
                parts.append(f"• {char}: {change}")
            parts.append("")
        
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

