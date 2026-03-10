"""Format structured context into natural, lenient prompts for AI.

Instead of rigid structured formats, creates human-readable prompts
that are easier for AI to understand and generate responses for.
"""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..storytellers import Storyteller

logger = logging.getLogger("infinite_story.utils.prompt_formatter")


class PromptFormatter:
    """Format context into natural language prompts."""
    
    @staticmethod
    def format_scene_context(
        context: Dict[str, Any],
        choice_text: str = None,
        storyteller: Optional['Storyteller'] = None
    ) -> str:
        """Format scene generation context into a comprehensive natural prompt.
        
        Builds a layered prompt from oldest context to most recent:
        1. World foundation (fundamental truths, worldbuilding)
        2. Previous arcs (condensed recaps with outcomes)
        3. Current arc (premise, conflict, themes, mysteries)
        4. All episodes in arc (one-line summaries)
        5. Recent episode recaps (bridging context)
        6. Current episode (tone, themes, focus, hooks + thematic directive)
        7. Earlier segment summaries (condensed chain)
        8. Recent scenes (full text for narrative flow)
        9. Characters (hierarchical: protagonist > major > minor)
        10. Factions & magic system
        11. Locations
        12. Story dynamics (tension, momentum, pacing)
        13. Theme tracking & accumulated changes
        14. Player choice
        15. Generation instructions (context-aware, includes storyteller style if provided)
        
        Args:
            context: Generation context dict from SegmentContextBuilder
            choice_text: Optional override for user choice text
            storyteller: Optional Storyteller instance for narrative style injection
            
        Returns:
            Natural language prompt for scene generation
        """
        if choice_text and 'user_choice' not in context:
            context['user_choice'] = choice_text
        parts: List[str] = []
        
        # ================================================================
        # 1. WORLD FOUNDATION — the bedrock rules of the setting
        # ================================================================
        world_ctx = context.get('world_context', {})
        fundamental_truths = world_ctx.get('fundamental_truths', [])
        worldbuilding = world_ctx.get('worldbuilding', '')
        story_desc = world_ctx.get('story_description', '')
        
        if fundamental_truths or worldbuilding or story_desc:
            parts.append("=== WORLD ===")
            if story_desc:
                parts.append(story_desc[:500])  # Increased from 200 to 500
            if fundamental_truths:
                parts.append("Fundamental truths:")
                for truth in fundamental_truths[:7]:  # Increased from 5 to 7
                    parts.append(f"  - {truth[:200]}")  # Increased from 120 to 200
            if worldbuilding:
                parts.append(f"Setting: {worldbuilding[:600]}")  # Increased from 250 to 600
        
        # ================================================================
        # 2. PREVIOUS ARCS — long-term story memory (condensed)
        # ================================================================
        if context.get('previous_arcs'):
            parts.append("\n=== STORY SO FAR (PREVIOUS ARCS) ===")
            for arc in context['previous_arcs'][:4]:  # Increased from 3 to 4
                arc_name = arc.get('name', arc.get('arc_id', 'Unknown'))
                if arc_name and (arc_name.startswith('{') or arc_name.startswith('"') or len(arc_name) > 100):
                    arc_name = f"Arc ({arc.get('arc_id', 'previous')[:20]})"
                parts.append(f"\n--- {arc_name} ---")
                if arc.get('premise'):
                    parts.append(f"Premise: {arc['premise'][:250]}")  # Increased from 150 to 250
                if arc.get('recap'):
                    recap_text = arc['recap']
                    if len(recap_text) > 1000:  # Increased from 500 to 1000
                        recap_text = recap_text[:1000] + "..."
                    parts.append(f"What happened: {recap_text}")
                if arc.get('resolution'):
                    parts.append(f"Outcome: {arc['resolution'][:250]}")  # Increased from 150 to 250
                if arc.get('unresolved'):
                    unresolved_list = ', '.join(arc['unresolved'][:8])  # Increased from 5 to 8
                    if len(unresolved_list) > 300:
                        unresolved_list = unresolved_list[:300] + "..."
                    parts.append(f"Unresolved threads: {unresolved_list}")
                if arc.get('character_arcs'):
                    parts.append("Character arcs:")
                    for char_id, resolution in list(arc['character_arcs'].items())[:5]:  # Increased from 3 to 5
                        parts.append(f"  - {char_id}: {resolution[:150]}")  # Increased from 100 to 150
        
        # ================================================================
        # 3. CURRENT ARC — what the story is about right now
        # ================================================================
        current_arc = context.get('current_arc', {})
        arc_conflict = context.get('central_conflict') or current_arc.get('central_conflict', '')
        arc_themes = context.get('arc_themes') or current_arc.get('themes', [])
        
        if current_arc:
            parts.append("\n=== CURRENT ARC ===")
            if current_arc.get('title'):
                parts.append(f"Arc: {current_arc['title']}")
            if current_arc.get('premise'):
                parts.append(f"Premise: {current_arc['premise']}")
            if current_arc.get('narrative_direction'):
                parts.append(f"Direction: {current_arc['narrative_direction']}")
            if arc_conflict:
                parts.append(f"Central conflict: {arc_conflict}")
            if arc_themes:
                parts.append(f"Themes: {', '.join(arc_themes[:5])}")
            if current_arc.get('tone'):
                tone_line = f"Arc tone: {current_arc['tone']}"
                if current_arc.get('mood'):
                    tone_line += f" / mood: {current_arc['mood']}"
                parts.append(tone_line)
            if current_arc.get('previous_arc_summary'):
                parts.append(f"Previous arc context: {current_arc['previous_arc_summary'][:300]}")
            if current_arc.get('unresolved_mysteries'):
                parts.append(f"Open mysteries: {', '.join(current_arc['unresolved_mysteries'][:5])}")
            if current_arc.get('plot_hooks'):
                parts.append(f"Active hooks: {', '.join(current_arc['plot_hooks'][:5])}")
            
            # Character arc goals
            char_goals = context.get('character_arc_goals') or current_arc.get('character_arc_goals', {})
            if char_goals:
                parts.append("Character goals this arc:")
                for char_id, goal in list(char_goals.items())[:5]:
                    parts.append(f"  - {char_id}: {goal[:80]}")
        
        # ================================================================
        # 4. ALL EPISODES IN ARC — one-line summaries for full arc context
        # ================================================================
        episodes_in_arc = context.get('episodes_in_arc', [])
        if episodes_in_arc and len(episodes_in_arc) > 1:
            parts.append("\n=== ARC EPISODES ===")
            for ep in episodes_in_arc:
                ep_num = ep.get('episode_number', '?')
                tone = ep.get('tone', '')
                seg_count = len(ep.get('segments', []))
                recap = ep.get('recap', {})
                
                ep_line = f"Ep {ep_num}"
                if tone:
                    ep_line += f" ({tone})"
                ep_line += f" - {seg_count} scenes"
                
                # Add one-line summary from recap if available
                progression = recap.get('plot_progression', '')
                if progression:
                    ep_line += f": {progression[:100]}"
                
                parts.append(f"  {ep_line}")
        
        # ================================================================
        # 5. RECENT EPISODE RECAPS — bridging context
        # ================================================================
        if context.get('recent_episode_recaps'):
            parts.append("\n=== RECENT EPISODES (DETAILED) ===")
            for recap in context['recent_episode_recaps']:
                ep_line = f"Episode {recap.get('episode', '?')}"
                if recap.get('title'):
                    ep_line += f": {recap['title']}"
                if recap.get('from_previous_arc'):
                    ep_line += f" [from {recap.get('arc_name', 'prev arc')}]"
                parts.append(ep_line)
                if recap.get('summary'):
                    parts.append(f"  {recap['summary'][:200]}")
                if recap.get('hook_for_next'):
                    parts.append(f"  Hook: {recap['hook_for_next'][:100]}")
        
        if context.get('previous_episode_recap'):
            prev_title = context.get('previous_episode_title', 'Last Episode')
            parts.append(f"\n=== PREVIOUSLY ({prev_title}) ===")
            parts.append(context['previous_episode_recap'][:2000])  # Expanded from 500 to 2000
            
            # Also include full previous episode scenes if available
            if context.get('previous_episode_full_text'):
                parts.append("\n--- PREVIOUS EPISODE FULL NARRATIVE ---")
                full_text = context['previous_episode_full_text']
                if len(full_text) > 2500:
                    full_text = full_text[:2500] + "..."
                parts.append(full_text)
        
        # ================================================================
        # 6. CURRENT EPISODE — tone, themes, focus, hooks
        # ================================================================
        parts.append("\n=== CURRENT EPISODE ===")
        ep_num = context.get('episode_number', 1)
        seg_num = context.get('segment_number_in_episode', 1)
        parts.append(f"Episode {ep_num}, Scene {seg_num}")
        
        if context.get('episode_tone'):
            parts.append(f"Tone: {context['episode_tone']}")
        if context.get('episode_end_condition'):
            parts.append(f"Episode goal: {context['episode_end_condition']}")
        
        ep_themes = context.get('episode_selected_themes', [])
        ep_focus = context.get('episode_focus', '')
        ep_hooks = context.get('story_hooks', [])
        
        if ep_themes:
            parts.append(f"Episode themes: {', '.join(ep_themes)}")
            parts.append("  (Weave these themes into events, dialogue, and atmosphere)")
        if ep_focus:
            parts.append(f"Focus: {ep_focus}")
        if ep_hooks:
            parts.append(f"Active hooks: {', '.join(ep_hooks[:3])}")
        
        # Thematic micro-directive
        if ep_themes:
            directive = PromptFormatter._build_theme_directive(ep_themes, context)
            if directive:
                parts.append(f"\nThematic directive: {directive}")
        
        # ================================================================
        # 7. EARLIER SEGMENT SUMMARIES — condensed chain for wider context
        # ================================================================
        seg_recaps = context.get('segment_recaps', [])
        recent_full = context.get('recent_segments_full', [])
        recent_full_ids = {s.get('segment_id') for s in recent_full if isinstance(s, dict)} if recent_full else set()
        
        # Show older segment recaps (not already shown as full text)
        older_recaps = [r for r in seg_recaps if r.get('segment_id') not in recent_full_ids]
        if older_recaps:
            parts.append("\n=== EARLIER SCENES (SUMMARY) ===")
            for recap in older_recaps:
                desc = recap.get('description', '')
                if desc:
                    ep_tag = f"[Ep{recap.get('episode_number', '?')}]" if recap.get('episode_number') else ""
                    changes = recap.get('changes', [])
                    line = f"  {ep_tag} {desc[:100]}"
                    if changes:
                        line += f" ({'; '.join(changes[:2])})"
                    parts.append(line)
        
        # ================================================================
        # 8. RECENT SCENES — full text for narrative flow
        # ================================================================
        if recent_full:
            parts.append("\n=== RECENT SCENES (FULL) ===")
            for seg_info in recent_full[-3:]:  # Show 3 instead of 2
                if isinstance(seg_info, dict):
                    if seg_info.get('description'):
                        parts.append(f"--- {seg_info['description']} ---")
                    if seg_info.get('text'):
                        text = seg_info['text']
                        if len(text) > 1000:  # Increased from 500 to 1000
                            text = text[:1000] + "..."
                        parts.append(text)
                    if seg_info.get('changes'):
                        parts.append(f"  Changes: {'; '.join(seg_info['changes'][:5])}")  # Show 5 changes
                    if seg_info.get('characters_present'):
                        chars = ', '.join(seg_info['characters_present'][:6]) if isinstance(seg_info['characters_present'], list) else seg_info['characters_present']
                        parts.append(f"  Characters: {chars}")
                elif isinstance(seg_info, str):
                    parts.append(seg_info[:600])  # Increased from 400
        elif context.get('previous_segments'):
            parts.append("\n=== RECENT SCENES (SUMMARY) ===")
            for seg in context['previous_segments'][-5:]:  # Show 5 instead of 3
                parts.append(f"  {seg}")
        
        # ================================================================
        # 9. CHARACTERS — hierarchical (protagonist > major > minor)
        # ================================================================
        arc_characters = context.get('arc_characters', {})
        episode_characters = context.get('episode_characters', {})
        segment_changes = context.get('segment_character_changes', {})
        char_goals = context.get('character_arc_goals') or current_arc.get('character_arc_goals', {})
        role_tiers = context.get('character_role_tiers', {})
        protagonist_id = context.get('protagonist_id')
        
        char_sections = []
        
        # Protagonist
        if protagonist_id and protagonist_id in arc_characters:
            char = arc_characters[protagonist_id]
            ep_state = episode_characters.get(protagonist_id, {})
            seg_state = segment_changes.get(protagonist_id, {})
            line = f"PROTAGONIST: {char.get('name', protagonist_id)}"
            desc = char.get('short_description') or char.get('description', '')
            if desc:
                line += f" - {desc[:80]}"
            if ep_state.get('emotional_status'):
                line += f" | Feeling: {ep_state['emotional_status']}"
            if ep_state.get('health_status'):
                line += f" | Health: {ep_state['health_status']}"
            if seg_state.get('status'):
                line += f" | Now: {seg_state['status']}"
            goal = char_goals.get(protagonist_id, '')
            if goal:
                line += f" | Goal: {goal[:60]}"
                progress = ep_state.get('goal_progress', '')
                if progress:
                    line += f" ({progress})"
            char_sections.append(line)
        
        # Major characters
        major_names = role_tiers.get('major', [])
        for char_id, info in arc_characters.items():
            if char_id == protagonist_id:
                continue
            name = info.get('name', char_id) if isinstance(info, dict) else char_id
            importance = info.get('importance', 'minor') if isinstance(info, dict) else 'minor'
            if importance in ('major', 'antagonist', 'ally') or name in major_names:
                ep_state = episode_characters.get(char_id, {})
                seg_state = segment_changes.get(char_id, {})
                desc = info.get('short_description') or info.get('description', '') if isinstance(info, dict) else ''
                line = f"  {name}"
                if desc:
                    line += f" - {desc[:200]}"  # Increased from 60 to 200 for fuller descriptions
                if isinstance(ep_state, dict) and ep_state.get('emotional_status'):
                    line += f" | {ep_state['emotional_status']}"
                if isinstance(ep_state, dict) and ep_state.get('status'):
                    line += f" | {ep_state['status'][:100]}"  # Increased from 60 to 100
                if isinstance(seg_state, dict) and seg_state.get('status'):
                    line += f" | Now: {seg_state['status']}"
                goal = char_goals.get(char_id, '')
                if goal:
                    line += f" | Goal: {goal[:100]}"  # Increased from 50 to 100
                char_sections.append(line)
        
        # Minor characters (compact list)
        minor_chars = []
        for char_id, info in arc_characters.items():
            if char_id == protagonist_id:
                continue
            name = info.get('name', char_id) if isinstance(info, dict) else char_id
            importance = info.get('importance', 'minor') if isinstance(info, dict) else 'minor'
            if importance not in ('major', 'protagonist', 'antagonist', 'ally') and name not in major_names:
                minor_chars.append(name)
        if minor_chars:
            char_sections.append(f"  Minor: {', '.join(minor_chars[:8])}")
        
        # Fallback: old format
        if not char_sections and context.get('all_characters'):
            for char_id, char_info in list(context['all_characters'].items())[:5]:
                name = char_info.get('name', char_id) if isinstance(char_info, dict) else char_id
                status = char_info.get('status', '') if isinstance(char_info, dict) else ''
                line = name
                if status:
                    line += f" ({status})"
                char_sections.append(f"  {line}")
        
        if char_sections:
            parts.append("\n=== CHARACTERS (SUMMARY) ===")
            parts.extend(char_sections)
        
        # Full character profiles for major characters
        major_char_profiles = []
        for char_id, info in arc_characters.items():
            if char_id == protagonist_id:
                continue
            name = info.get('name', char_id) if isinstance(info, dict) else char_id
            importance = info.get('importance', 'minor') if isinstance(info, dict) else 'minor'
            if importance in ('major', 'antagonist', 'ally'):
                full_desc = info.get('description', info.get('short_description', '')) if isinstance(info, dict) else ''
                personality = info.get('personality', '') if isinstance(info, dict) else ''
                goals = info.get('goals', '') if isinstance(info, dict) else ''
                if full_desc or personality or goals:
                    profile = f"\n**{name}** ({importance.upper()})"
                    if full_desc:
                        profile += f"\n  {full_desc[:400]}"  # Full description, 400 chars
                    if personality:
                        profile += f"\n  Personality: {personality[:250]}"
                    if goals:
                        profile += f"\n  Goals: {goals[:200]}"
                    major_char_profiles.append(profile)
        
        if major_char_profiles:
            parts.append("\n=== FULL CHARACTER PROFILES (MAJOR) ===")
            for profile in major_char_profiles[:6]:  # Show up to 6 major characters
                parts.append(profile)
        
        # Character relationships
        relationships = context.get('character_relationships', {})
        rel_changes = context.get('relationship_changes', [])
        if relationships or rel_changes:
            parts.append("\n=== CHARACTER RELATIONSHIPS ===")
            for char_id, rels in list(relationships.items())[:8]:  # Increased from 5 to 8
                char_name = arc_characters.get(char_id, {}).get('name', char_id) if isinstance(arc_characters.get(char_id), dict) else char_id
                for target, rel_type in list(rels.items())[:4]:  # Increased from 3 to 4
                    target_name = arc_characters.get(target, {}).get('name', target) if isinstance(arc_characters.get(target), dict) else target
                    parts.append(f"  {char_name} <-> {target_name}: {rel_type}")
            if rel_changes:
                for change in rel_changes[-3:]:
                    ch = change.get('change', change) if isinstance(change, dict) else str(change)
                    parts.append(f"  (shift) {ch[:80]}")
        
        # ================================================================
        # 10. FACTIONS & MAGIC
        # ================================================================
        if context.get('factions'):
            factions_data = context['factions']
            if isinstance(factions_data, dict) and 'factions' in factions_data:
                factions_list = factions_data['factions']
            elif isinstance(factions_data, list):
                factions_list = factions_data
            elif isinstance(factions_data, dict):
                factions_list = list(factions_data.values())
            else:
                factions_list = []
            
            if factions_list:
                parts.append("\n=== FACTIONS (SUMMARY) ===")
                faction_profiles = []
                for f in factions_list[:7]:  # Show all factions
                    if isinstance(f, dict):
                        name = f.get('name', f.get('id', '?'))
                        desc = f.get('description', f.get('status', ''))
                        goals = f.get('goals', [])
                        alignment = f.get('alignment', '')
                        line = f"  {name}"
                        if alignment:
                            line += f" ({alignment})"
                        if desc:
                            line += f" - {desc[:250]}"  # Increased from 80 to 250
                        if goals and isinstance(goals, list):
                            line += f" | Goals: {', '.join(goals[:3])}"  # Show 3 goals
                        parts.append(line)
                        
                        # Store for full profiles
                        faction_profiles.append(f)
                    else:
                        parts.append(f"  {str(f)[:100]}")
                
                # Full faction profiles
                if faction_profiles:
                    parts.append("\n=== FULL FACTION PROFILES ===")
                    for f in faction_profiles[:5]:  # Full profiles for 5 main factions
                        if isinstance(f, dict):
                            name = f.get('name', f.get('id', '?'))
                            alignment = f.get('alignment', '')
                            desc = f.get('description', '')
                            goals = f.get('goals', [])
                            structure = f.get('structure', '')
                            conflicts = f.get('conflicts', '')
                            
                            profile = f"\n**{name}** ({alignment})"
                            if desc:
                                profile += f"\n  Description: {desc[:400]}"
                            if goals:
                                profile += f"\n  Goals: {', '.join(goals[:5])}"
                            if structure:
                                profile += f"\n  Structure: {structure[:250]}"
                            if conflicts:
                                profile += f"\n  Key Conflicts: {conflicts[:250]}"
                            parts.append(profile)
                
                faction_alignment = context.get('character_faction_alignment', {})
                if faction_alignment:
                    parts.append("\n=== FACTION ALLEGIANCES ===")
                    for char_name, faction_name in list(faction_alignment.items())[:10]:  # Increased from 6 to 10
                        parts.append(f"  {char_name} -> {faction_name}")
        
        magic = context.get('magic_system', {})
        if isinstance(magic, dict) and magic.get('name') and magic['name'] != 'Unknown':
            parts.append(f"\n=== MAGIC/TECH: {magic['name']} ===")
            if magic.get('description'):
                parts.append(f"{magic['description'][:500]}")  # Increased from 200 to 500
            if magic.get('capabilities'):
                parts.append(f"Can do: {', '.join(magic['capabilities'][:5])}")  # Show more capabilities
            if magic.get('limitations'):
                parts.append(f"Limits: {', '.join(magic['limitations'][:5])}")  # Show more limits
            if magic.get('costs'):
                parts.append(f"Costs: {', '.join(magic['costs'][:5])}")  # Show more costs
            parts.append("(Characters must respect these rules)")
        elif isinstance(magic, str) and magic:
            parts.append(f"\n=== MAGIC/TECH SYSTEM ===")
            parts.append(magic[:150])
        
        # ================================================================
        # 11. LOCATIONS
        # ================================================================
        locations = context.get('location_states', {})
        if locations:
            parts.append("\n=== ACTIVE LOCATIONS ===")
            for loc_id, loc_info in list(locations.items())[:5]:
                name = loc_info.get('name', loc_id)
                desc = loc_info.get('description', '')
                status = loc_info.get('status', '')
                line = f"  {name}"
                if desc:
                    line += f" - {desc[:80]}"
                if status:
                    line += f" [{status}]"
                parts.append(line)
        
        # ================================================================
        # 11.5. LOCATIONS (EXPANDED)
        # ================================================================
        locations = context.get('location_states', {})
        if locations:
            parts.append("\n=== KEY LOCATIONS (DETAILED) ===")
            for loc_id, loc_info in list(locations.items())[:8]:  # Increased from 5 to 8
                name = loc_info.get('name', loc_id)
                desc = loc_info.get('description', '')
                status = loc_info.get('status', '')
                significance = loc_info.get('significance', '')
                
                loc_profile = f"\n**{name}**"
                if desc:
                    loc_profile += f"\n  {desc[:300]}"  # Increased detail
                if status:
                    loc_profile += f"\n  Current Status: {status[:200]}"
                if significance:
                    loc_profile += f"\n  Significance: {significance[:200]}"
                parts.append(loc_profile)
        
        # ================================================================
        # 12. MYSTERIES & THEME TRACKING
        # ================================================================
        mysteries = context.get('mysteries_tracking', {})
        if isinstance(mysteries, dict) and mysteries:
            parts.append("\n=== OPEN MYSTERIES ===")
            for mystery, status in list(mysteries.items())[:8]:  # Increased from 5 to 8
                parts.append(f"  - {mystery[:200]} [{status}]")  # Show more details
        elif isinstance(mysteries, list) and mysteries:
            parts.append("\n=== OPEN MYSTERIES ===")
            for m in mysteries[:8]:  # Increased from 5 to 8
                if isinstance(m, dict):
                    parts.append(f"  - {m.get('mystery', m.get('name', str(m)))[:150]}")  # 150 chars
                else:
                    parts.append(f"  - {str(m)[:150]}")
        
        themes_explored = context.get('themes_explored', {})
        theme_depth = context.get('theme_depth', {})
        if theme_depth:
            parts.append("\n=== THEME TRACKING ===")
            for theme, depth in list(theme_depth.items())[:10]:  # Increased from 6 to 10
                count = themes_explored.get(theme, 0)
                parts.append(f"  {theme}: {depth} (appeared {count}x)")
        
        new_mysteries = context.get('new_mysteries_introduced', [])
        if new_mysteries:
            parts.append("  New mysteries this episode:")
            for m in new_mysteries[-5:]:  # Increased from 3 to 5
                parts.append(f"    - {m[:100]}")
        
        # ================================================================
        # 13. STORY DYNAMICS — tension, momentum, pacing
        # ================================================================
        momentum = context.get('story_momentum', {})
        tension = context.get('tension_level', {})
        pacing_trend = context.get('pacing_trend', {})
        pacing = context.get('pacing_weight', 0)
        
        parts.append("\n=== STORY DYNAMICS ===")
        pacing_desc = "Just starting" if pacing < 0.25 else \
                     "Building" if pacing < 0.5 else \
                     "Mid-episode" if pacing < 0.65 else \
                     "Rising action" if pacing < 0.8 else \
                     "Approaching climax" if pacing < 0.9 else \
                     "Climax / resolution"
        parts.append(f"Episode progress: {pacing_desc} ({pacing:.0%})")
        
        if tension and tension.get('level'):
            parts.append(f"Tension: {tension['level']}")
        if momentum and momentum.get('direction'):
            parts.append(f"Momentum: {momentum['direction']} (intensity {momentum.get('intensity', 0):.1f})")
        if pacing_trend and pacing_trend.get('trend'):
            parts.append(f"Pacing trend: {pacing_trend['trend']}")
        
        if context.get('should_transition_episode'):
            parts.append("*** EPISODE ENDING - build toward conclusion/cliffhanger ***")
        
        # Accumulated changes this episode
        accumulated = context.get('character_changes_this_episode') or context.get('accumulated_changes', [])
        if accumulated:
            parts.append("\n=== CHANGES THIS EPISODE ===")
            for change in accumulated[-6:]:
                parts.append(f"  - {change[:100]}")
        
        world_changes = context.get('world_state_changes', [])
        if world_changes:
            parts.append("  World changes:")
            for change in world_changes[-3:]:
                parts.append(f"    - {change[:100]}")
        
        # ================================================================
        # CHARACTER EMOTIONS — how characters feel right now
        # ================================================================
        if context.get('character_emotions'):
            parts.append("\n=== CHARACTER EMOTIONS ===")
            for char_name, emotion in context['character_emotions'].items():
                parts.append(f"  {char_name}: {emotion}")
            parts.append("Track how these emotions EVOLVE based on what happens in this scene.")
        
        # ================================================================
        # STORYLINE TYPE — what kind of scene to generate
        # ================================================================
        if context.get('storyline_type'):
            parts.append(f"\n=== STORYLINE TYPE ===")
            parts.append(f"Previous scene type: {context['storyline_type']}")
            parts.append("Consider if the storyline type should shift based on the player's choice.")
        if context.get('dominant_storylines'):
            parts.append(f"Dominant storylines this episode: {', '.join(context['dominant_storylines'])}")
        
        # ================================================================
        # 14. PLAYER CHOICE
        # ================================================================
        if context.get('user_choice'):
            parts.append(f"\n=== PLAYER'S CHOICE ===")
            parts.append(f"The player chose: \"{context['user_choice']}\"")
        
        # ================================================================
        # 15. GENERATION INSTRUCTIONS (context-aware)
        # ================================================================
        parts.append("\n=== GENERATION INSTRUCTIONS ===")
        
        # Inject storyteller style if provided
        if storyteller:
            parts.append(f"[Narrative Voice: {storyteller.name}]")
            parts.append(storyteller.style_instructions)
            parts.append("")
            if storyteller.examples:
                parts.append("Example of this style:")
                for i, example in enumerate(storyteller.examples[:1], 1):
                    parts.append(f"  \"{example[:150]}...\"")
            parts.append("")
        
        parts.append("Write the next scene. Your scene MUST:")
        parts.append("1. Follow naturally from the player's choice")
        parts.append("2. Maintain continuity with previous arcs, episodes, and established world facts")
        if ep_themes:
            parts.append(f"3. Explore the episode themes ({', '.join(ep_themes)}) through events, dialogue, or subtext")
        else:
            parts.append("3. Explore themes relevant to the arc")
        if arc_conflict:
            parts.append(f"4. Connect to the central conflict: {arc_conflict[:100]}")
        else:
            parts.append("4. Advance the current arc's premise and central conflict")
        parts.append("5. Respect character states, goals, and relationships")
        parts.append("6. Track how each character's EMOTION changes through the scene")
        parts.append("7. Set the storyline_type to match the scene's dominant narrative style")
        parts.append("8. Use varied text block types — mix narration, dialogue, thoughts, sounds, visual cues")
        parts.append("9. Assign a storyline tag to each text block where relevant (action for combat, mystery for clues, etc.)")
        
        instr_num = 10
        has_factions = bool(context.get('factions', {}).get('factions') if isinstance(context.get('factions'), dict) else context.get('factions'))
        if has_factions:
            parts.append(f"{instr_num}. Reflect faction tensions and allegiances where relevant")
            instr_num += 1
        if isinstance(magic, dict) and magic.get('name') and magic['name'] != 'Unknown':
            parts.append(f"{instr_num}. Stay within the rules of the {magic['name']} system")
            instr_num += 1
        parts.append(f"{instr_num}. Provide two meaningful, distinct choices that push the story in different directions")
        
        # Pacing-specific guidance
        if pacing < 0.2:
            parts.append("\nPacing note: Early episode. Establish setting, introduce tensions, plant seeds.")
        elif pacing < 0.5:
            parts.append("\nPacing note: Build complexity. Deepen conflicts, reveal motivations, raise stakes.")
        elif pacing < 0.8:
            parts.append("\nPacing note: Rising action. Accelerate toward the episode's climactic moment.")
        elif context.get('should_transition_episode'):
            parts.append("\nPacing note: CLIMAX. Deliver a powerful conclusion or cliffhanger.")
        else:
            parts.append("\nPacing note: Nearing the climax. Build tension, converge plot threads.")
        
        parts.append("\n=== RESPONSE FORMAT (JSON) ===")
        parts.append("You MUST respond with valid JSON matching this structure:")
        parts.append("""{
  "short_description": "Brief summary of what happens",
  "storyline_type": "action|mystery|romance|political|horror|comedy|drama|exploration",
  "atmosphere": "The emotional/sensory mood",
  "time_of_day": "dawn|morning|afternoon|sunset|night",
  "weather": "Weather or 'clear'",
  "text_blocks": [
    {"type": "narrator_describing", "content": "Scene text...", "emotion": "tense"},
    {"type": "character_speech", "content": "Dialogue", "character": "Name"}
  ],
  "characters_present": ["Name 1", "Name 2"],
  "locations_present": ["Location"],
  "character_emotions": {"Name": "specific emotion"},
  "character_status_change": {"Name": "what changed"},
  "location_status_change": {"Location": "how it changed"},
  "change_notes": ["Key change"],
  "choice_1": "Player choice A",
  "choice_2": "Player choice B"
}""")
        
        return "\n".join(parts)
    
    @staticmethod
    def _build_theme_directive(themes: List[str], context: Dict[str, Any]) -> str:
        """Build a specific creative directive based on the episode's selected themes.
        
        Instead of just listing themes, gives the AI a concrete angle to explore.
        This creates variety between episodes even with similar themes.
        """
        from app.utils.theme_selector import ThemeSelector
        
        directives = []
        for theme in themes[:2]:
            directive = ThemeSelector.get_theme_directive(theme)
            if directive:
                directives.append(directive)
        
        if not directives:
            return ""
        
        tension = context.get('tension_level', {})
        tension_level = tension.get('level', 'medium') if isinstance(tension, dict) else 'medium'
        
        if tension_level in ('high', 'critical'):
            return f"Under high tension: {' Meanwhile, '.join(directives)}"
        else:
            return ' '.join(directives)
    
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

