"""Theme selector utility for weighted random theme selection."""

import random
import logging
from typing import List, Optional, Dict

from app.models.story_arc import StoryArc
from app.models.story_episode import StoryEpisode as EpisodeRecap

logger = logging.getLogger("infinite_story.utils.theme_selector")


class ThemeSelector:
    """Select themes for episodes using weighted random selection.
    
    Provides intelligent theme selection that:
    1. Uses hardcoded default weights for all possible themes
    2. Allows arc-specific weight overrides
    3. Reduces weight of previously explored themes
    4. Returns weighted random selection of themes
    """
    
    # Hardcoded default theme weights
    # Covers universal story themes that can apply to any narrative
    DEFAULT_THEME_WEIGHTS: Dict[str, float] = {
        # Core emotional & moral themes
        "betrayal": 0.8,
        "redemption": 0.7,
        "power": 0.8,
        "loss": 0.6,
        "trust": 0.7,
        "sacrifice": 0.6,
        "vengeance": 0.7,
        "hope": 0.6,
        "despair": 0.5,
        "corruption": 0.6,
        "innocence": 0.5,
        
        # Relationship themes
        "love": 0.5,
        "friendship": 0.5,
        "loyalty": 0.7,
        "family": 0.6,
        "brotherhood": 0.5,
        "sisterhood": 0.5,
        "romance": 0.4,
        
        # Character & personal themes
        "identity": 0.6,
        "growth": 0.7,
        "self_discovery": 0.6,
        "wisdom": 0.5,
        "courage": 0.6,
        "cowardice": 0.4,
        "ambition": 0.6,
        
        # Story & narrative themes
        "mystery": 0.6,
        "revelation": 0.7,
        "conflict": 0.8,
        "resolution": 0.5,
        "journey": 0.6,
        "quest": 0.5,
        "struggle": 0.6,
        
        # Tone & atmosphere themes
        "darkness": 0.5,
        "light": 0.4,
        "tension": 0.7,
        "calm": 0.3,
        "chaos": 0.6,
        "order": 0.4,
        "adventure": 0.5,
        
        # Social & political themes
        "justice": 0.6,
        "injustice": 0.5,
        "freedom": 0.6,
        "oppression": 0.5,
        "revolution": 0.5,
        "tradition": 0.4,
    }
    
    @staticmethod
    def select_themes(
        arc: StoryArc,
        prev_recap: Optional[EpisodeRecap] = None,
        episode_number: int = 1,
        count: int = 2
    ) -> List[str]:
        """
        Select themes for this episode using weighted random selection.
        
        Algorithm:
        1. Start with DEFAULT_THEME_WEIGHTS as base
        2. If arc has custom theme_weights, use those (override defaults)
        3. If previous episode exists, reduce weight of explored themes by 70%
        4. Random selection proportional to weights
        5. Return selected themes
        
        Args:
            arc: StoryArc with optional custom theme preferences
            prev_recap: Previous episode recap (to avoid repeating themes)
            episode_number: Current episode number
            count: How many themes to select (default 2-3)
            
        Returns:
            List of selected theme strings
            
        Example:
            arc = StoryArc(title="Arc 1", theme_weights={"betrayal": 0.9})
            themes = ThemeSelector.select_themes(arc, prev_recap=None, count=2)
            # Returns: ["betrayal", "trust"]
        """
        logger.debug(
            f"Selecting {count} themes for episode {episode_number} "
            f"from arc {arc.id if hasattr(arc, 'id') else 'unknown'}"
        )
        
        # Step 1: Start with defaults
        weights = ThemeSelector.DEFAULT_THEME_WEIGHTS.copy()
        logger.debug(f"Starting with {len(weights)} default themes")
        
        # Step 2: Override with arc's custom weights if provided
        if arc.theme_weights:
            logger.debug(f"Arc has custom weights, overriding for {len(arc.theme_weights)} themes")
            weights.update(arc.theme_weights)
        
        # Step 3: Reduce weight of previously explored themes
        if prev_recap and prev_recap.themes_explored:
            logger.debug(
                f"Previous episode explored {len(prev_recap.themes_explored)} themes, "
                f"reducing their weights by 70%"
            )
            for explored_theme in prev_recap.themes_explored:
                if explored_theme in weights:
                    original_weight = weights[explored_theme]
                    weights[explored_theme] *= 0.3  # 70% reduction
                    logger.debug(
                        f"  {explored_theme}: {original_weight} → {weights[explored_theme]:.2f}"
                    )
        
        # Step 4: Random selection via weighted choice
        available_themes = list(weights.keys())
        available_weights = list(weights.values())
        
        logger.debug(f"Selecting from {len(available_themes)} available themes")
        
        # Ensure we don't try to select more themes than available
        select_count = min(count, len(available_themes))
        
        # Perform weighted random selection
        try:
            selected = random.choices(
                available_themes,
                weights=available_weights,
                k=select_count
            )
            logger.info(f"Selected themes for episode {episode_number}: {selected}")
            return selected
        except ValueError as e:
            logger.error(f"Failed to select themes: {e}, returning defaults")
            return available_themes[:select_count]
