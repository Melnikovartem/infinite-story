"""Theme selector utility for weighted random theme selection.

Provides a rich palette of narrative themes organized by category,
with micro-directives that give the AI specific creative angles
for each theme. This ensures episodes feel distinct even when
revisiting similar thematic territory.
"""

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
    4. Boosts themes related to the arc's declared themes
    5. Returns weighted random selection (no duplicates)
    6. Provides micro-directives for each theme to guide scene generation
    """
    
    # ======================================================================
    # DEFAULT THEME WEIGHTS
    # Weight = how dramatically the theme shifts a scene (higher = more likely).
    # ======================================================================
    DEFAULT_THEME_WEIGHTS: Dict[str, float] = {
        # === Core emotional & moral ===
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
        "guilt": 0.6,
        "shame": 0.5,
        "forgiveness": 0.5,
        "mercy": 0.5,
        "cruelty": 0.6,
        "compassion": 0.5,
        "regret": 0.5,
        "pride": 0.6,
        "humility": 0.4,
        "envy": 0.5,
        "greed": 0.6,
        "wrath": 0.6,
        "patience": 0.3,
        
        # === Relationship ===
        "love": 0.5,
        "friendship": 0.5,
        "loyalty": 0.7,
        "family": 0.6,
        "brotherhood": 0.5,
        "sisterhood": 0.5,
        "romance": 0.4,
        "rivalry": 0.7,
        "mentorship": 0.5,
        "betrayed_trust": 0.7,
        "unrequited_love": 0.5,
        "forbidden_bond": 0.6,
        "estrangement": 0.5,
        "reconciliation": 0.5,
        "codependence": 0.4,
        "isolation": 0.5,
        
        # === Character & personal ===
        "identity": 0.6,
        "growth": 0.7,
        "self_discovery": 0.6,
        "wisdom": 0.5,
        "courage": 0.6,
        "cowardice": 0.4,
        "ambition": 0.6,
        "obsession": 0.7,
        "madness": 0.6,
        "temptation": 0.7,
        "transformation": 0.6,
        "disillusionment": 0.6,
        "resilience": 0.5,
        "vulnerability": 0.5,
        "mask_and_identity": 0.6,
        "inner_conflict": 0.7,
        "coming_of_age": 0.5,
        "legacy": 0.5,
        "mortality": 0.6,
        
        # === Story & narrative ===
        "mystery": 0.6,
        "revelation": 0.7,
        "conflict": 0.8,
        "resolution": 0.5,
        "journey": 0.6,
        "quest": 0.5,
        "struggle": 0.6,
        "deception": 0.7,
        "conspiracy": 0.7,
        "prophecy": 0.5,
        "fate_vs_choice": 0.7,
        "unintended_consequences": 0.7,
        "the_price_of_knowledge": 0.6,
        "forbidden_knowledge": 0.6,
        "the_lesser_evil": 0.7,
        "pyrrhic_victory": 0.6,
        "the_ticking_clock": 0.7,
        "the_hidden_enemy": 0.7,
        "the_reluctant_hero": 0.6,
        "the_fall_from_grace": 0.7,
        
        # === Tone & atmosphere ===
        "darkness": 0.5,
        "light": 0.4,
        "tension": 0.7,
        "calm": 0.3,
        "chaos": 0.6,
        "order": 0.4,
        "adventure": 0.5,
        "dread": 0.6,
        "wonder": 0.5,
        "melancholy": 0.5,
        "euphoria": 0.4,
        "claustrophobia": 0.5,
        "paranoia": 0.7,
        "serenity": 0.3,
        "decay": 0.5,
        "renewal": 0.5,
        "nostalgia": 0.4,
        "the_uncanny": 0.6,
        "sublime_terror": 0.6,
        
        # === Social & political ===
        "justice": 0.6,
        "injustice": 0.5,
        "freedom": 0.6,
        "oppression": 0.5,
        "revolution": 0.5,
        "tradition": 0.4,
        "class_conflict": 0.6,
        "duty_vs_desire": 0.7,
        "collective_vs_individual": 0.6,
        "propaganda": 0.5,
        "exile": 0.5,
        "belonging": 0.5,
        "xenophobia": 0.5,
        "cultural_clash": 0.6,
        "colonialism": 0.5,
        "resistance": 0.6,
        "diplomacy": 0.4,
        "succession": 0.6,
        "civil_war": 0.7,
        
        # === Survival & stakes ===
        "survival": 0.7,
        "scarcity": 0.6,
        "plague": 0.6,
        "famine": 0.5,
        "siege": 0.7,
        "hunt": 0.6,
        "escape": 0.7,
        "captivity": 0.6,
        "exile_and_return": 0.6,
        "last_stand": 0.8,
        "desperate_alliance": 0.7,
        "the_heist": 0.6,
        "the_trial": 0.6,
        
        # === Supernatural & cosmic ===
        "the_beyond": 0.5,
        "cosmic_horror": 0.6,
        "divine_intervention": 0.5,
        "the_curse": 0.6,
        "the_bargain": 0.7,
        "resurrection": 0.5,
        "the_underworld": 0.5,
        "shapeshifting": 0.5,
        "possession": 0.6,
        "the_veil_between_worlds": 0.5,
        
        # === Knowledge & truth ===
        "truth_vs_lies": 0.7,
        "the_unreliable_narrator": 0.6,
        "hidden_history": 0.6,
        "the_map_and_territory": 0.4,
        "memory_and_forgetting": 0.5,
        "the_cost_of_truth": 0.6,
        "willful_ignorance": 0.5,
    }
    
    # ======================================================================
    # THEME MICRO-DIRECTIVES
    # Each theme has 3-5 directives. One is randomly selected per episode
    # to give the AI a specific creative angle.
    # ======================================================================
    THEME_DIRECTIVES: Dict[str, List[str]] = {
        # --- Core emotional ---
        "betrayal": [
            "Show a character discovering they've been used as a pawn.",
            "Have an ally's true motives slip through a careless word or gesture.",
            "Let the protagonist face a choice where betraying someone serves the greater good.",
            "Reveal that a past betrayal is the hidden cause of present events.",
            "Show betrayal from the betrayer's perspective - they believe they're doing right.",
        ],
        "redemption": [
            "Give a villain a moment of genuine vulnerability that hints at change.",
            "Let a character's past mistakes create an unexpected opportunity to help.",
            "Show the cost of redemption - what must be given up to earn forgiveness.",
            "Have a redeemed character face distrust even after proving themselves.",
        ],
        "power": [
            "Show how power changes the way others behave around the powerful.",
            "Reveal the hidden cost someone pays to maintain their authority.",
            "Let a powerless character find leverage through wit or knowledge.",
            "Demonstrate that the most powerful person in the room isn't who everyone thinks.",
        ],
        "loss": [
            "Let a character stumble upon a reminder of what they've lost.",
            "Show how different characters cope with the same loss in opposite ways.",
            "Reveal that what was lost was never really what it seemed.",
            "Have a character choose between holding on and letting go.",
        ],
        "trust": [
            "Force characters to rely on someone they have every reason to doubt.",
            "Show trust being earned through a small, unexpected act of honesty.",
            "Let a character's trust be tested by contradictory evidence.",
            "Have someone prove trustworthy in the worst possible circumstances.",
        ],
        "sacrifice": [
            "Present a choice where every option requires giving something up.",
            "Show a quiet sacrifice that no one else notices or acknowledges.",
            "Reveal the long-term consequences of a past sacrifice.",
            "Let a character refuse to sacrifice, and show what that costs instead.",
        ],
        "vengeance": [
            "Show vengeance consuming the one who pursues it.",
            "Let a character get their revenge and feel nothing.",
            "Have the target of vengeance be sympathetic when finally confronted.",
            "Reveal that vengeance has been misdirected at the wrong person.",
        ],
        "hope": [
            "Let hope emerge from an unlikely source at the darkest moment.",
            "Show how clinging to hope can be both strength and delusion.",
            "Have a cynical character encounter something genuinely beautiful.",
            "Let hope be contagious - one character's optimism shifts the group.",
        ],
        "despair": [
            "Show a character reaching their breaking point through accumulation of small defeats.",
            "Let despair manifest as numbness rather than dramatic grief.",
            "Have a character's despair lead to reckless action with unexpected results.",
            "Show the moment when despair begins to crack and something else seeps through.",
        ],
        "corruption": [
            "Show corruption through gradual moral compromise, each step seemingly reasonable.",
            "Reveal that a trusted institution has been corrupted from within.",
            "Let a character justify their corruption with genuinely compelling logic.",
            "Show corruption's physical manifestation in the environment or a character's appearance.",
        ],
        "guilt": [
            "Have a character overcompensate to hide their guilt from others.",
            "Let guilt surface at an inconvenient moment, disrupting plans.",
            "Show two characters carrying guilt about the same event but blaming themselves for different reasons.",
        ],
        "forgiveness": [
            "Show forgiveness as difficult, messy, and incomplete rather than clean.",
            "Have a character forgive someone who hasn't asked for it.",
            "Let forgiveness come with conditions that reveal the forgiver's own needs.",
        ],
        
        # --- Relationship ---
        "rivalry": [
            "Show rivals forced to cooperate, their competitive instincts creating friction.",
            "Let a rival show unexpected respect after witnessing true skill.",
            "Reveal that a rivalry masks deeper feelings of admiration or fear.",
            "Have the rivalry escalate in a way that threatens bystanders.",
        ],
        "mentorship": [
            "Let the student surpass the teacher in one specific area, straining the relationship.",
            "Show a mentor's flawed advice creating real problems.",
            "Have a mentor reveal their own past failures as a teaching moment.",
        ],
        "isolation": [
            "Show the psychological effects of being the only one who knows the truth.",
            "Let isolation be self-imposed as protection, then show it backfire.",
            "Have an isolated character find unexpected connection in an unlikely place.",
        ],
        "forbidden_bond": [
            "Show a secret alliance forming across enemy lines.",
            "Let characters communicate through coded signals that others miss.",
            "Reveal the consequences if the forbidden bond is discovered.",
        ],
        "loyalty": [
            "Force a character to choose between two people they're loyal to.",
            "Show loyalty tested by new information that changes everything.",
            "Let blind loyalty lead to complicity in something wrong.",
        ],
        
        # --- Character & personal ---
        "obsession": [
            "Show obsession narrowing a character's world until nothing else matters.",
            "Let an obsessed character be brilliant and terrifying in equal measure.",
            "Have obsession lead to a breakthrough that proves the obsessed person right - but at terrible cost.",
        ],
        "temptation": [
            "Present temptation as genuinely appealing, not obviously wrong.",
            "Show a character resisting temptation but being changed by the encounter.",
            "Let temptation come from an unexpected direction - not desire but compassion.",
        ],
        "transformation": [
            "Show transformation through small behavioral changes others notice first.",
            "Let a character resist their own transformation.",
            "Reveal that transformation has made someone unrecognizable to those who knew them.",
        ],
        "inner_conflict": [
            "Externalize inner conflict through a choice that has no good answer.",
            "Show a character arguing with themselves through interactions with others.",
            "Let inner conflict paralyze a character at a critical moment.",
        ],
        "mortality": [
            "Introduce a brush with death that reorders a character's priorities.",
            "Show characters dealing with mortality differently - denial, acceptance, rage.",
            "Let mortality give urgency to relationships and unfinished business.",
        ],
        "identity": [
            "Force a character to act against their self-image and deal with the dissonance.",
            "Have someone challenge the protagonist's understanding of who they are.",
            "Show identity as performance - a character adjusting their persona for different audiences.",
        ],
        "mask_and_identity": [
            "Let a character's mask slip at the worst possible moment.",
            "Show someone who has worn a mask so long they've forgotten who's underneath.",
            "Have a character encounter someone who sees through their mask effortlessly.",
        ],
        
        # --- Narrative & plot ---
        "deception": [
            "Let the reader discover a deception at the same time as the protagonist.",
            "Show a web of lies growing too complex for its creator to maintain.",
            "Have an honest character forced to deceive for the first time.",
        ],
        "conspiracy": [
            "Drop a clue that reframes previous events in a sinister light.",
            "Show a minor character who knows too much acting strangely.",
            "Let paranoia spread through a group as conspiracy becomes plausible.",
        ],
        "fate_vs_choice": [
            "Present a prophecy or prediction and let characters wrestle with whether to fight it.",
            "Show a character making a choice that unknowingly fulfills the very fate they resist.",
            "Let two characters disagree about whether their situation is destiny or coincidence.",
        ],
        "unintended_consequences": [
            "Let a previous good deed create an unexpected problem.",
            "Show the ripple effects of a small decision made episodes ago.",
            "Have a character face the consequences of someone else's well-intentioned actions.",
        ],
        "the_lesser_evil": [
            "Present two terrible options and force a choice with no moral high ground.",
            "Show different characters disagreeing about which evil is lesser.",
            "Let the chosen 'lesser evil' prove worse than expected.",
        ],
        "the_ticking_clock": [
            "Introduce a deadline that forces hasty, imperfect decisions.",
            "Show time pressure revealing characters' true priorities.",
            "Let the ticking clock be a lie - but the urgency it created was real.",
        ],
        "the_hidden_enemy": [
            "Let suspicion fall on the wrong person while the real threat watches.",
            "Show a hidden enemy helping the protagonist for their own reasons.",
            "Reveal the hidden enemy through a detail only the observant would catch.",
        ],
        "the_fall_from_grace": [
            "Show a respected figure making a choice that shatters their reputation.",
            "Let the fall begin with a single compromise that seems harmless.",
            "Have witnesses to the fall react with denial, anger, or satisfaction.",
        ],
        "pyrrhic_victory": [
            "Let a character win a battle but realize what they've lost in the process.",
            "Show a victory celebration undermined by unspoken grief.",
            "Have the fruits of victory turn to ash as the true cost reveals itself.",
        ],
        
        # --- Tone & atmosphere ---
        "dread": [
            "Build dread through small wrong details rather than obvious threats.",
            "Let a character sense danger before they can articulate why.",
            "Show normalcy with one element subtly, deeply wrong.",
        ],
        "wonder": [
            "Reveal something beautiful or awe-inspiring in an otherwise dark moment.",
            "Let a jaded character experience genuine wonder for the first time in years.",
            "Show wonder tinged with fear - something magnificent and dangerous.",
        ],
        "paranoia": [
            "Let the protagonist question whether their perception of events is accurate.",
            "Show evidence that supports contradictory conclusions.",
            "Have paranoia prove partially justified - they're right, but not about everything.",
        ],
        "decay": [
            "Show physical decay reflecting moral or social deterioration.",
            "Let a once-great place or institution be seen in its diminished state.",
            "Have characters disagree about whether decay is natural or caused.",
        ],
        "the_uncanny": [
            "Introduce something familiar that behaves slightly wrong.",
            "Show a place that looks right but feels deeply off.",
            "Let a character encounter a distorted version of something they know well.",
        ],
        "melancholy": [
            "Let a moment of beauty be tinged with awareness that it won't last.",
            "Show a character quietly grieving something they never had.",
            "Create a scene where characters share silence that says more than words.",
        ],
        "chaos": [
            "Show established order crumbling, with different characters reacting to the vacuum.",
            "Let chaos reveal who people really are when structure disappears.",
            "Have chaos create an unlikely alliance between former enemies.",
        ],
        "tension": [
            "Build tension through a conversation where both parties know something the other doesn't.",
            "Show physical details (clenched fists, held breath) to convey unspoken tension.",
            "Let tension break not with a bang but with a quiet, devastating word.",
        ],
        
        # --- Social & political ---
        "duty_vs_desire": [
            "Show a character torn between what they must do and what they want.",
            "Let duty and desire align briefly, then pull apart again.",
            "Have different characters represent opposite sides of the duty/desire spectrum.",
        ],
        "class_conflict": [
            "Show class disparity through small everyday details rather than speeches.",
            "Let a character cross class boundaries and feel the friction.",
            "Reveal shared humanity between characters separated by status.",
        ],
        "exile": [
            "Show exile as both punishment and freedom.",
            "Let an exiled character encounter someone from their former life.",
            "Have exile create unexpected skills or perspectives that prove valuable.",
        ],
        "succession": [
            "Show multiple claimants maneuvering against each other while appearing loyal.",
            "Let the succession question divide previously united allies.",
            "Reveal an unexpected contender who changes the political calculus.",
        ],
        "resistance": [
            "Show resistance through small acts of defiance rather than grand gestures.",
            "Let a character join the resistance for personal reasons, not ideology.",
            "Have the cost of resistance fall on someone other than the resistor.",
        ],
        "civil_war": [
            "Show former friends on opposite sides of the conflict.",
            "Let the 'right side' do something morally questionable.",
            "Reveal that the war's original cause has been forgotten by those fighting it.",
        ],
        "revolution": [
            "Show the gap between revolutionary ideals and revolutionary reality.",
            "Let a revolutionary question whether the new order will be better.",
            "Have the revolution threaten someone the protagonist cares about.",
        ],
        
        # --- Survival & stakes ---
        "survival": [
            "Force a moral choice between surviving and helping others survive.",
            "Show survival instincts overriding civilized behavior.",
            "Let survival depend on an unlikely skill or piece of knowledge.",
        ],
        "scarcity": [
            "Show how scarcity changes relationships and hierarchies.",
            "Let rationing decisions reveal power dynamics.",
            "Have characters disagree about sharing limited resources with outsiders.",
        ],
        "siege": [
            "Build claustrophobia through dwindling supplies and rising tension inside.",
            "Show the psychological toll of waiting for an attack.",
            "Let the siege force unlikely people to depend on each other.",
        ],
        "escape": [
            "Show escape planning as a way to maintain hope and agency.",
            "Let the escape attempt go wrong in an unexpected way.",
            "Have freedom feel different than the character expected.",
        ],
        "last_stand": [
            "Show characters making peace with their situation before the fight.",
            "Let a last stand become unnecessary through an unexpected turn.",
            "Have the last stand inspire others who witness it.",
        ],
        "desperate_alliance": [
            "Force enemies to work together against a greater threat.",
            "Show old grudges complicating cooperation at the worst moments.",
            "Let the alliance succeed but create new problems.",
        ],
        "the_trial": [
            "Show a trial where the legal truth and the moral truth diverge.",
            "Let evidence be ambiguous, making the audience question the verdict.",
            "Have the trial reveal secrets that damage the accuser as much as the accused.",
        ],
        
        # --- Supernatural & cosmic ---
        "the_bargain": [
            "Present a deal where the cost seems acceptable until the fine print emerges.",
            "Show a character trying to outwit a supernatural bargainer.",
            "Let the bargain's true cost be something the character didn't know they valued.",
        ],
        "the_curse": [
            "Show a curse's effects manifesting gradually and insidiously.",
            "Let the curse have an ironic relationship to its victim's greatest strength.",
            "Have the path to breaking the curse require something the cursed cannot bring themselves to do.",
        ],
        "cosmic_horror": [
            "Hint at something vast and indifferent beyond mortal comprehension.",
            "Let a character glimpse the true nature of reality and struggle to function afterward.",
            "Show cosmic forces treating human concerns as irrelevant noise.",
        ],
        "possession": [
            "Show possession through subtle personality shifts noticed by close friends.",
            "Let the possessed character fight for control in brief, lucid moments.",
            "Have possession blur the line between the entity and the original personality.",
        ],
        
        # --- Knowledge & truth ---
        "truth_vs_lies": [
            "Show a truth that's more destructive than the lie it replaces.",
            "Let a character discover they've been living a comfortable lie.",
            "Have two characters present contradictory truths, both supported by evidence.",
        ],
        "hidden_history": [
            "Reveal a piece of history that recontextualizes current conflicts.",
            "Let a character discover their personal history has been falsified.",
            "Show how hidden history is actively suppressed and by whom.",
        ],
        "the_cost_of_truth": [
            "Let knowing the truth isolate a character from those who prefer ignorance.",
            "Show truth destroying a relationship built on comfortable assumptions.",
            "Have the truth arrive too late to prevent what it could have stopped.",
        ],
        "memory_and_forgetting": [
            "Show a character's memory contradicting physical evidence.",
            "Let a forgotten memory resurface and change everything.",
            "Have different characters remember the same event in contradictory ways.",
        ],
        "willful_ignorance": [
            "Show a character choosing not to look at evidence sitting right in front of them.",
            "Let willful ignorance protect someone's sanity but endanger others.",
            "Have willful ignorance finally become impossible to maintain.",
        ],
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
        2. If arc has custom theme_weights, override defaults
        3. Boost themes related to arc's declared themes (affinity system)
        4. Reduce weight of previously explored themes by 70%
        5. Weighted random selection without duplicates
        
        Args:
            arc: StoryArc with optional custom theme preferences
            prev_recap: Previous episode recap (to avoid repeating themes)
            episode_number: Current episode number
            count: How many themes to select (default 2-3)
            
        Returns:
            List of selected theme strings
        """
        logger.debug(
            f"Selecting {count} themes for episode {episode_number} "
            f"from arc {arc.id if hasattr(arc, 'id') else 'unknown'}"
        )
        
        # Step 1: Start with defaults
        weights = ThemeSelector.DEFAULT_THEME_WEIGHTS.copy()
        logger.debug(f"Starting with {len(weights)} default themes")
        
        # Step 2: Override with arc's custom weights
        if arc.theme_weights:
            logger.debug(f"Arc has custom weights for {len(arc.theme_weights)} themes")
            weights.update(arc.theme_weights)
        
        # Step 3: Boost themes related to the arc's declared themes
        if arc.themes:
            related = ThemeSelector._get_related_themes(arc.themes)
            for theme in related:
                if theme in weights:
                    weights[theme] *= 1.4  # 40% boost
        
        # Step 4: Reduce weight of previously explored themes
        if prev_recap and prev_recap.themes_explored:
            logger.debug(
                f"Previous episode explored {len(prev_recap.themes_explored)} themes, "
                f"reducing weights by 70%"
            )
            for explored_theme in prev_recap.themes_explored:
                if explored_theme in weights:
                    original_weight = weights[explored_theme]
                    weights[explored_theme] *= 0.3
                    logger.debug(
                        f"  {explored_theme}: {original_weight} -> {weights[explored_theme]:.2f}"
                    )
        
        # Step 5: Weighted random selection (no duplicates)
        available_themes = list(weights.keys())
        available_weights = list(weights.values())
        select_count = min(count, len(available_themes))
        
        logger.debug(f"Selecting from {len(available_themes)} available themes")
        
        try:
            selected: List[str] = []
            remaining_themes = list(available_themes)
            remaining_weights = list(available_weights)
            
            for _ in range(select_count):
                if not remaining_themes:
                    break
                choice = random.choices(
                    remaining_themes,
                    weights=remaining_weights,
                    k=1
                )[0]
                selected.append(choice)
                idx = remaining_themes.index(choice)
                remaining_themes.pop(idx)
                remaining_weights.pop(idx)
            
            logger.info(f"Selected themes for episode {episode_number}: {selected}")
            return selected
        except ValueError as e:
            logger.error(f"Failed to select themes: {e}, returning defaults")
            return available_themes[:select_count]
    
    @staticmethod
    def get_theme_directive(theme: str) -> str:
        """Get a random micro-directive for a specific theme.
        
        Micro-directives give the AI a specific creative angle to explore,
        ensuring variety even when the same theme recurs across episodes.
        
        Args:
            theme: Theme name (key in THEME_DIRECTIVES)
            
        Returns:
            A specific creative directive string, or generic fallback
        """
        directives = ThemeSelector.THEME_DIRECTIVES.get(theme, [])
        if not directives:
            readable = theme.replace('_', ' ')
            return f"Explore the theme of {readable} through character actions and consequences."
        return random.choice(directives)
    
    @staticmethod
    def _get_related_themes(arc_themes: List[str]) -> List[str]:
        """Given arc themes, return thematically related themes to boost.
        
        Creates thematic coherence by boosting themes that naturally
        pair with the arc's declared themes.
        """
        AFFINITIES: Dict[str, List[str]] = {
            "betrayal": ["trust", "deception", "loyalty", "vengeance", "paranoia", "betrayed_trust"],
            "redemption": ["guilt", "sacrifice", "forgiveness", "growth", "hope", "transformation"],
            "power": ["corruption", "ambition", "succession", "class_conflict", "oppression", "greed"],
            "loss": ["despair", "memory_and_forgetting", "melancholy", "resilience"],
            "trust": ["betrayal", "loyalty", "deception", "truth_vs_lies", "forbidden_bond"],
            "sacrifice": ["duty_vs_desire", "loss", "hope", "the_lesser_evil", "last_stand"],
            "vengeance": ["wrath", "justice", "obsession", "the_fall_from_grace", "betrayal"],
            "hope": ["resilience", "wonder", "redemption", "desperate_alliance", "renewal"],
            "corruption": ["power", "decay", "the_fall_from_grace", "greed", "temptation"],
            "identity": ["mask_and_identity", "transformation", "self_discovery", "inner_conflict"],
            "mystery": ["revelation", "conspiracy", "hidden_history", "the_hidden_enemy", "deception"],
            "revolution": ["resistance", "freedom", "civil_war", "class_conflict", "oppression"],
            "survival": ["scarcity", "siege", "desperate_alliance", "last_stand", "escape"],
            "love": ["forbidden_bond", "unrequited_love", "sacrifice", "loss", "reconciliation"],
            "conflict": ["rivalry", "civil_war", "inner_conflict", "tension", "the_lesser_evil"],
            "justice": ["injustice", "the_trial", "truth_vs_lies", "duty_vs_desire", "mercy"],
            "freedom": ["captivity", "escape", "exile", "oppression", "resistance"],
            "darkness": ["dread", "cosmic_horror", "corruption", "despair", "the_uncanny"],
        }
        
        related: List[str] = []
        for theme in arc_themes:
            theme_lower = theme.lower().replace(' ', '_')
            if theme_lower in AFFINITIES:
                related.extend(AFFINITIES[theme_lower])
        
        return list(set(related))
