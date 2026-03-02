#!/usr/bin/env python3
"""Setup example stories using the new StoryBuilder system."""

import sys
import os
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.story_builder import StoryBuilder
from app.models.text_types import TextType, TextBlock

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_veil_of_thornreach() -> str:
    """Create the 'Veil of Thornreach' dark fantasy story."""
    logger.info("Creating 'Veil of Thornreach' story...")
    
    builder = StoryBuilder(
        story_id="veil_of_thornreach",
        title="The Veil of Thornreach",
        description="A dark fantasy adventure set in a mystical forest realm slowly being consumed by a sentient fog called The Veil. As civilization clings to the edge of Thornreach, the last untouched grove, a group of unlikely allies must uncover the origin of The Veil and decide its fate.",
        genre="Dark Fantasy"
    )
    
    # Worldbuilding
    builder.add_worldbuilding(
        fundamental_truths=[
            "The Veil is a living entity that erases memories and reshapes reality",
            "Thornreach Grove is the last sanctuary of the old gods",
            "Memory is a resource that can be traded for power",
            "The Withered Court rules from inside The Veil",
            "Ancient prophecies speak of a Memory Weaver who can control The Veil",
            "Time flows differently within The Veil's embrace"
        ],
        worldbuilding={
            "setting": "A mystical forest realm on the brink of being consumed by The Veil",
            "magic_system": {
                "druidic_magic": "Nature-based magic drawing from the forest",
                "memory_magic": "Rare ability to manipulate memories",
                "veil_magic": "Forbidden arts manipulating The Veil's power"
            },
            "factions": [
                "Druid Circle - Guardians of Thornreach Grove",
                "Memory Keepers - Preserving the realm's history",
                "Withered Court - Corrupted rulers within The Veil"
            ]
        }
    )
    
    # Characters
    builder.add_character(
        "eira",
        "Eira",
        "A novice druid with forbidden magic",
        "Born in Thornreach Grove with a unique connection to the forest's spirit",
        avatar_color="#2ECC71"
    )
    builder.add_character(
        "thorne",
        "Thorne",
        "A cursed knight exiled from the Veil-corrupted kingdom",
        "Once loyal to the Withered Court until he discovered its dark truth",
        avatar_color="#E74C3C"
    )
    builder.add_character(
        "nyx",
        "Nyx",
        "A trickster fae with mysterious motives",
        "Has existed in the realm since before The Veil's appearance",
        avatar_color="#9B59B6"
    )
    
    # Locations
    builder.add_location(
        "thornreach_grove",
        "Thornreach Grove",
        "The last untouched sanctuary, protected by ancient wards against The Veil"
    )
    builder.add_location(
        "the_veil_edge",
        "The Veil's Edge",
        "Where the sentient fog meets the mortal realm, a place of twisted reality"
    )
    builder.add_location(
        "memory_pool",
        "The Memory Pool",
        "A sacred spring where memories crystallize into physical form"
    )
    
    # Opening segment
    builder.add_opening_segment(
        segment_id="opening",
        title="Whispers in the Grove",
        content="The ancient trees of Thornreach Grove tower above you, their branches tangled with silver wards that glow faintly in the twilight. You've lived here your whole life, protected by magic older than memory itself. But lately, something has changed. The wards flicker more often, and at night, you hear whispers from beyond their boundary—voices calling from The Veil. Tonight, you've been summoned to the Grove's heart. The circle of druids waits, and their expressions are grave.",
        atmosphere="mysterious",
        episode_number=1,
        episode_tone="dark_and_foreboding"
    )
    
    # Additional segments
    builder.add_segment(
        "druid_meeting",
        "The Druid's Warning",
        "You enter the sacred circle where the elder druids gather around a dying fire. Eira, the most senior druid, steps forward. 'The Veil grows stronger,' she says, her voice heavy with worry. 'Our wards will not hold for much longer. We must make a choice—reinforce the barriers at great cost to ourselves, or send a small group beyond the Grove to find the source of The Veil's power.' The decision falls to you.",
        atmosphere="tense",
        episode_number=1,
        parent_segment_id="opening"
    )
    
    # Choices
    builder.add_choice(
        "choice_investigate_council",
        "opening",
        "Head to the Druid Council meeting immediately",
        "druid_meeting"
    )
    builder.add_choice(
        "choice_seek_nyx",
        "opening",
        "Find Nyx first—the fae might have answers about The Veil",
        to_segment_id=None  # AI will generate
    )
    builder.add_choice(
        "choice_explore_veil_edge",
        "opening",
        "Sneak to The Veil's edge to investigate yourself",
        to_segment_id=None  # AI will generate
    )
    
    builder.add_choice(
        "choice_reinforce_wards",
        "druid_meeting",
        "Volunteer to help strengthen the protective wards",
        to_segment_id=None  # AI will generate
    )
    builder.add_choice(
        "choice_investigate_veil",
        "druid_meeting",
        "Offer to lead a group beyond the Grove to find The Veil's source",
        to_segment_id=None  # AI will generate
    )
    
    return builder.save()


def create_sci_fi_story() -> str:
    """Create a science fiction story."""
    logger.info("Creating 'Station Aurora' sci-fi story...")
    
    builder = StoryBuilder(
        story_id="station_aurora",
        title="Station Aurora",
        description="A sci-fi thriller set on a distant space station where a mysterious signal awakens something that was meant to stay dormant.",
        genre="Science Fiction"
    )
    
    # Worldbuilding
    builder.add_worldbuilding(
        fundamental_truths=[
            "Station Aurora orbits a black hole at the edge of known space",
            "Humanity discovered an alien signal decades ago",
            "The signal was encoded into the station's core",
            "No one has heard from Earth in 15 years",
            "The crew has dwindled to only essential personnel"
        ],
        worldbuilding={
            "setting": "Space station in orbit around a black hole",
            "technology": "Advanced AI, faster-than-light communication (experimental)",
            "threat": "Something awakening in the station's core"
        }
    )
    
    # Characters
    builder.add_character(
        "commander",
        "Commander Sarah Chen",
        "Station Aurora's commanding officer",
        "Led the mission 20 years ago, determined to decode the alien signal",
        avatar_color="#3498DB"
    )
    builder.add_character(
        "ai",
        "ARIA",
        "The station's artificial intelligence",
        "Began showing unexpected behaviors after the signal activation",
        avatar_color="#F39C12"
    )
    
    # Locations
    builder.add_location(
        "command_bridge",
        "Command Bridge",
        "The nerve center of Station Aurora where all major decisions are made"
    )
    builder.add_location(
        "core_chamber",
        "Core Chamber",
        "The station's heart where the alien signal is stored"
    )
    
    # Opening
    builder.add_opening_segment(
        segment_id="opening",
        title="The Signal Awakens",
        content="Red emergency lights flicker across the command bridge. Alarms sound with an urgency you haven't heard in years. Commander Chen's voice crackles over the intercom: 'All hands to stations. The signal is active. The core is powering up by itself.' You rush to your station as screens fill with data—the alien signal, dormant for decades, suddenly pulsing with life. ARIA, the station AI, speaks with an unusual hesitation in her voice: 'I am... experiencing something new. I cannot describe it.'",
        atmosphere="urgent",
        episode_number=1,
        episode_tone="tense_and_mysterious"
    )
    
    # Choices
    builder.add_choice(
        "choice_investigate_core",
        "opening",
        "Head to the Core Chamber to see what's happening",
        to_segment_id=None
    )
    builder.add_choice(
        "choice_question_aria",
        "opening",
        "Ask ARIA what she's experiencing",
        to_segment_id=None
    )
    builder.add_choice(
        "choice_contact_chen",
        "opening",
        "Report to Commander Chen immediately",
        to_segment_id=None
    )
    
    return builder.save()


def create_mystery_story() -> str:
    """Create a mystery story."""
    logger.info("Creating 'The Midnight Library' mystery story...")
    
    builder = StoryBuilder(
        story_id="midnight_library",
        title="The Midnight Library",
        description="A contemporary mystery where a librarian discovers that books are disappearing from the library—and no one remembers they ever existed.",
        genre="Mystery"
    )
    
    # Worldbuilding
    builder.add_worldbuilding(
        fundamental_truths=[
            "Books are disappearing from existence one by one",
            "When a book disappears, all memory of it vanishes from readers' minds",
            "The librarian is immune to the memory loss",
            "There's a pattern to which books disappear",
            "Someone—or something—is deliberately erasing literature from history"
        ],
        worldbuilding={
            "setting": "A grand city library that's been standing for 200 years",
            "mystery": "Why are books being systematically erased?",
            "stakes": "If this continues, entire histories could be forgotten"
        }
    )
    
    # Characters
    builder.add_character(
        "librarian",
        "Alex Moore",
        "A dedicated librarian with an unusual immunity",
        "Has worked at the library for 10 years and noticed the disappearances",
        avatar_color="#34495E"
    )
    builder.add_character(
        "archivist",
        "Dr. Helena Ward",
        "The library's head archivist",
        "Knows secrets about the library's past that might explain what's happening",
        avatar_color="#8E44AD"
    )
    
    # Locations
    builder.add_location(
        "main_reading_room",
        "Main Reading Room",
        "The heart of the library with shelves of books stretching to the ceiling"
    )
    builder.add_location(
        "restricted_archives",
        "Restricted Archives",
        "A locked section containing the library's oldest and most valuable books"
    )
    
    # Opening
    builder.add_opening_segment(
        segment_id="opening",
        title="The First Disappearance",
        content="You're organizing the evening returns when you notice something wrong. The shelf where 'The Midnight Chronicles' should be is empty. You check the system—it shows no record of the book ever existing. You're certain it was here this morning. Your hands shake as you pull up the library camera feeds. There's no footage of anyone checking out the book. It's as if it simply ceased to exist.",
        atmosphere="eerie",
        episode_number=1,
        episode_tone="mysterious"
    )
    
    # Choices
    builder.add_choice(
        "choice_check_archives",
        "opening",
        "Search the archives for any records of the missing book",
        to_segment_id=None
    )
    builder.add_choice(
        "choice_ask_helena",
        "opening",
        "Tell Dr. Ward about the disappearance",
        to_segment_id=None
    )
    builder.add_choice(
        "choice_review_footage",
        "opening",
        "Carefully review all library footage from the past week",
        to_segment_id=None
    )
    
    return builder.save()


def main():
    """Create all example stories."""
    try:
        stories = [
            create_veil_of_thornreach(),
            create_sci_fi_story(),
            create_mystery_story()
        ]
        
        print("\n" + "="*60)
        print("✅ Successfully created example stories:")
        for story_id in stories:
            print(f"   • {story_id}")
        print("="*60)
        print("\nRun stories with:")
        for story_id in stories:
            print(f"   python -m app.cli run-story {story_id}")
        
        return 0
    except Exception as e:
        logger.error(f"Error creating stories: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
