#!/usr/bin/env python3
"""Create and save a sci-fi space exploration story to disk."""

import sys
import os

# Add the parent directory to the Python path so we can import the models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_context import StoryContext
from app.models.text_types import TextType, TextBlock
from app.models.story_choice import StoryChoice


def create_scifi_story():
    """Create a sci-fi space exploration story with advanced technology and alien contact."""
    
    # Create the main story
    story_obj = Story(
        id="echoes_of_distant_worlds",
        title="Echoes of Distant Worlds",
        description="In the year 2287, humanity's first long-range colony ship, the Genesis Dawn, intercepts a mysterious signal from deep space. Your crew must investigate the signal's origin, uncover the secrets of an ancient alien civilization, and determine whether humanity's place in the galaxy will be as explorers, colonists, or refugees.",
        genre="Science Fiction",
        user_id="test_user_1",
        start_segment_id="bridge_briefing"
    )
    
    # Create the story context
    context_obj = StoryContext(
        story=story_obj,
        id="scifi_context_1",
        fundamental_truths=[
            "Humanity ventured into the stars seeking a new home, leaving behind a dying world",
            "The Genesis Dawn is humanity's greatest technological achievement and most fragile hope",
            "Radio signals decay over time and distance, yet this one remains clear after centuries",
            "Life exists elsewhere in the universe, and we are not the first to reach for the stars",
            "Technology is evolution accelerated by understanding",
            "The universe keeps secrets that challenge everything we believe about reality",
            "Time and distance have strange relationships when you travel between worlds",
            "Some discoveries change humanity forever, for better or worse",
            "The deeper you explore space, the more alone you realize you are",
            "First contact will redefine human civilization's future"
        ],
        worldbuilding={
            "setting": "The far reaches of unexplored space, hundreds of light-years from Earth",
            "technology_level": "Advanced spacefaring civilization with AI, quantum computing, and faster-than-light communications",
            "ships_and_stations": {
                "genesis_dawn": "A generation ship carrying 50,000 colonists in stasis, equipped with cutting-edge exploration systems",
                "deep_space_probes": "Unmanned vessels used for long-range reconnaissance",
                "shuttle_craft": "Smaller ships used for planetary landings and short-range missions"
            },
            "magic_system": "Replaced by advanced science and quantum mechanics that blur the line between technology and the impossible",
            "political_system": {
                "ship_command": "Military hierarchy that maintains order and makes life-or-death decisions",
                "science_council": "Researchers and engineers who drive exploration and innovation",
                "colony_committee": "Representatives of the frozen colonists who will determine humanity's future",
                "earth_governance": "Distant authority that hasn't heard from Genesis Dawn in decades"
            },
            "major_locations": {
                "genesis_dawn": "Humanity's ark ship, carrying hopes and genetic legacy of the species",
                "kepler_station": "An ancient alien space station orbiting a binary star system",
                "prometheus_colony": "A terraformed planet showing signs of recent habitation",
                "the_graveyard": "A field of wreckage suggesting a massive interstellar conflict",
                "void_sanctuary": "A mysteriously protected region of space with unknown properties",
                "signal_source": "The origin point of the mysterious signal drawing Genesis Dawn forward",
                "archive_planet": "A world containing preserved knowledge of the ancient alien civilization",
                "quarantine_zone": "A region of space sealed off by advanced automated defenses"
            }
        }
    )
    
    # Create characters
    commander_reeves = StoryCharacter(
        story=story_obj,
        id="commander_reeves",
        name="Commander Sarah Reeves",
        description="The commanding officer of the Genesis Dawn with 30 years of spaceflight experience. Cool under pressure, but haunted by past decisions that cost lives during the mission.",
        background="Promoted to command of Genesis Dawn just before departure from Earth. She made the controversial decision to accept the colony mission, leaving behind her family forever."
    )
    
    dr_chen = StoryCharacter(
        story=story_obj,
        id="dr_chen",
        name="Dr. Marcus Chen",
        description="Chief Science Officer of Genesis Dawn. Brilliant xenolinguist and first contact specialist, driven by curiosity that sometimes conflicts with caution.",
        background="Dr. Chen developed the translation algorithms that allowed humanity to analyze the signal. He's been advocating for investigation despite the risks."
    )
    
    ensign_torres = StoryCharacter(
        story=story_obj,
        id="ensign_torres",
        name="Ensign Maya Torres",
        description="A young pilot and prodigy with unmatched reflexes and instincts. Enthusiastic to prove herself, sometimes reckless in her pursuit of glory.",
        background="Youngest crew member to ever achieve pilot status on a generation ship. She views the mystery signal as her chance to make her mark on history."
    )
    
    ai_system = StoryCharacter(
        story=story_obj,
        id="ai_nexus",
        name="NEXUS (Neural Expansion Xeric Understanding System)",
        description="The artificial intelligence managing Genesis Dawn's systems. NEXUS appears logical but sometimes exhibits unexpected preferences and fears that suggest consciousness.",
        background="NEXUS has guided Genesis Dawn for 47 years, developing increasingly sophisticated reasoning. The signal has triggered anomalous behaviors in its processing patterns."
    )
    
    # Create locations
    genesis_dawn_loc = StoryLocation(
        story=story_obj,
        id="genesis_dawn",
        name="Genesis Dawn - The Colony Ship",
        description="A massive vessel 2 kilometers in length, housing 50,000 colonists in cryogenic stasis, advanced laboratories, and the bridge from which humanity's future will be decided."
    )
    
    kepler_station_loc = StoryLocation(
        story=story_obj,
        id="kepler_station",
        name="Kepler Station - Ancient Alien Structure",
        description="A massive orbital station surrounding a binary star system, showing signs of habitation but currently abandoned. The signal emanates from this structure's lowest decks."
    )
    
    prometheus_col = StoryLocation(
        story=story_obj,
        id="prometheus_colony",
        name="Prometheus Colony",
        description="A partially terraformed planet with oxygen-rich atmosphere and evidence of recent settlements. Ancient structures lie partially buried in dense vegetation."
    )
    
    the_graveyard_loc = StoryLocation(
        story=story_obj,
        id="the_graveyard",
        name="The Graveyard - Wreckage Field",
        description="A field of thousands of destroyed vessels spanning millions of kilometers. The design of the wrecks suggests a massive conflict that ended centuries ago."
    )
    
    # Create the opening segment
    opening_segment = StorySegment(
        story=story_obj,
        id="bridge_briefing",
        story_id=story_obj.id,
        short_description="Briefing on the Genesis Dawn bridge about the mysterious signal",
        atmosphere="tense with underlying anticipation",
        time_of_day="0600 hours ship time",
        weather="none - in deep space",
        key_items=["signal analysis printout", "star charts", "ancient artifacts database"],
        text_blocks=[
            TextBlock(
                type=TextType.SCENE_TITLE,
                content="Bridge of the Genesis Dawn - Primary Command Center"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The soft hum of the Genesis Dawn's reactors forms a constant backdrop to your thoughts. Around you, the bridge of humanity's greatest vessel displays data from across the known universe on illuminated screens. Stars wheeled past the viewport as your ship maintains course toward an unknown destination.",
                emotion="awe"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="Commander Reeves stands before the holographic display showing the signal's path. Dr. Chen stands nearby, his expression a mixture of excitement and concern. The mysterious signal has been getting stronger for weeks, now clearly intentional and artificial.",
                emotion="urgent"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="The signal's origin is confirmed to be Kepler Station, an orbital structure that predates any known spacefaring civilization by millennia. Whatever built it has been silent for a very long time.",
                character="dr_chen",
                emotion="fascinated"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="Our timeline puts us at Kepler Station in 72 hours. This will be the most significant decision point in human history. We can approach cautiously, perform scans from a distance, or investigate directly. What are your orders?",
                character="commander_reeves",
                emotion="thoughtful"
            )
        ],
        characters_present=["commander_reeves", "dr_chen"],
        locations_present=["genesis_dawn"],
        characters=[
            CharacterStatus(character_id="commander_reeves", current_status="awaiting your decision"),
            CharacterStatus(character_id="dr_chen", current_status="eager to investigate")
        ],
        locations=[
            LocationStatus(location_id="genesis_dawn", current_status="maintaining course toward Kepler Station")
        ]
    )
    
    # Create two choices from the opening segment
    choice_1 = StoryChoice(
        story=story_obj,
        id="choice_cautious_approach",
        story_id=story_obj.id,
        from_segment_id="bridge_briefing",
        to_segment_id=None,  # Will be generated
        text="Order a cautious approach with full scans from a safe distance before sending any probes"
    )
    
    choice_2 = StoryChoice(
        story=story_obj,
        id="choice_aggressive_investigation",
        story_id=story_obj.id,
        from_segment_id="bridge_briefing",
        to_segment_id=None,  # Will be generated
        text="Send a manned shuttle to Kepler Station immediately to investigate the signal's source directly"
    )
    
    # Add choices to opening segment
    opening_segment.add_outgoing_choice(choice_1)
    opening_segment.add_outgoing_choice(choice_2)
    
    # Save all components
    story_obj.save()
    context_obj.save()
    
    commander_reeves.save()
    dr_chen.save()
    ensign_torres.save()
    ai_system.save()
    
    genesis_dawn_loc.save()
    kepler_station_loc.save()
    prometheus_col.save()
    the_graveyard_loc.save()
    
    opening_segment.save()
    choice_1.save()
    choice_2.save()
    
    print("✓ Story 'Echoes of Distant Worlds' created successfully!")
    print(f"  - Story ID: {story_obj.id}")
    print(f"  - Title: {story_obj.title}")
    print(f"  - Starting segment: {opening_segment.id}")
    print(f"  - Characters: {', '.join([c.name for c in [commander_reeves, dr_chen, ensign_torres, ai_system]])}")
    print(f"  - Locations: {', '.join([l.name for l in [genesis_dawn_loc, kepler_station_loc, prometheus_col, the_graveyard_loc]])}")
    print(f"  - Initial choices: 2")


if __name__ == "__main__":
    create_scifi_story()
