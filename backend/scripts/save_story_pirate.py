#!/usr/bin/env python3
"""Create and save a pirate adventure story to disk."""

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


def create_pirate_story():
    """Create a pirate adventure story with multiple characters and locations."""
    
    # Create the main story
    story_obj = Story(
        id="seas_of_fortune",
        title="Seas of Fortune",
        description="A high-seas adventure where you command a ship and crew, seeking fortune, glory, and dangerous secrets hidden on mysterious islands. Navigate treacherous waters, build alliances with other captains, and uncover the truth behind the legendary Treasure of the Crimson Depths.",
        genre="Adventure Fantasy",
        user_id="test_user_1",
        start_segment_id="dock_encounter"
    )
    
    # Create the story context
    context_obj = StoryContext(
        story=story_obj,
        id="pirate_context_1",
        fundamental_truths=[
            "The sea holds power that cannot be controlled, only navigated",
            "Trust is the most valuable currency among pirates",
            "The Crimson Depths contain an ancient power waiting to be awakened",
            "Every island has secrets that predate current civilization",
            "Loyalty to your crew means more than gold or glory",
            "The old maps tell truths that most believe to be myths",
            "Some treasures are worth more than their weight in gold",
            "The rival pirate lords control the major trade routes",
            "Magic flows through the veins of the oldest sea captains",
            "The horizon always promises something new for those brave enough to seek it"
        ],
        worldbuilding={
            "setting": "A vast archipelago spanning thousands of islands, ruled by rival pirate lords and protected by treacherous currents",
            "magic_system": {
                "sea_magic": "Ancient magic tied to the ocean's currents and tides",
                "navigation_magic": "Magic that reveals hidden routes and safe passages",
                "curse_magic": "Dark spells placed on ships and treasures by desperate souls",
                "tempest_calling": "Rare ability to influence storms and weather patterns"
            },
            "political_system": {
                "pirate_lords": "Five major captains who control different regions of the archipelago",
                "merchant_guild": "Wealthy traders who control legitimate sea routes",
                "navy_fleet": "Government forces trying to eliminate piracy",
                "independent_crews": "Smaller pirate groups seeking freedom from larger factions"
            },
            "major_locations": {
                "port_of_crimson_tides": "The largest pirate haven, built inside an ancient volcano",
                "skull_island": "Traditional meeting ground for pirate councils",
                "treasure_reef": "Graveyard of a thousand ships hiding countless treasures",
                "ghost_straits": "A mysterious passage that appears only during certain moon phases",
                "emerald_jungle_islands": "Uncharted islands rumored to contain ancient ruins",
                "iron_chain_fortress": "An impregnable naval base of the government fleet",
                "the_shallows": "Dangerous waters where many ships have been wrecked",
                "merchant_harbor": "The largest legitimate trading port in the known world",
                "storm_eye_sanctuary": "A safe harbor hidden within permanent storm systems",
                "lost_city_ruins": "Submerged remains of a pre-pirate civilization"
            }
        }
    )
    
    # Create characters
    captain_blackhook = StoryCharacter(
        story=story_obj,
        id="captain_blackhook",
        name="Captain Blackhook",
        description="A legendary pirate captain with a prosthetic hook hand and a reputation for both cruelty and honor among her crew. Her ship, The Obsidian Wave, is feared throughout the archipelago.",
        background="Once a merchant captain, Blackhook turned to piracy after the government seized her trading fleet. She's been hunting for the Crimson Depths treasure for fifteen years."
    )
    
    captain_vex = StoryCharacter(
        story=story_obj,
        id="captain_vex",
        name="Captain Vex",
        description="A charismatic young pirate lord controlling the northern routes. Vex is cunning, ambitious, and views the Crimson Depths as their key to ultimate power.",
        background="Rose through the pirate ranks quickly by making strategic alliances. Vex's rivalry with Blackhook spans a decade of naval skirmishes."
    )
    
    quartermaster_quinn = StoryCharacter(
        story=story_obj,
        id="quartermaster_quinn",
        name="Quinn",
        description="Your loyal quartermaster and closest friend. Quinn has sailed every known sea and knows the temperaments of the islands better than anyone alive.",
        background="Joined your crew years ago when you saved their life during a naval ambush. Quinn is your most trusted advisor on matters of strategy and survival."
    )
    
    witch_morgan = StoryCharacter(
        story=story_obj,
        id="witch_morgan",
        name="Witch Morgan",
        description="A mysterious sea witch who trades in magical artifacts and forbidden knowledge. Her true allegiances remain unknown, but her magic is undeniably powerful.",
        background="Rumored to have lived for over a century, Morgan appears where pirate fortunes change. Many believe she has a stake in who discovers the Crimson Depths."
    )
    
    # Create locations
    port_crimson = StoryLocation(
        story=story_obj,
        id="port_crimson_tides",
        name="Port of Crimson Tides",
        description="A sprawling pirate settlement built inside an ancient volcanic crater. The port is filled with merchant stalls, taverns, and the docks where the most fearsome ships in the archipelago are anchored."
    )
    
    skull_island = StoryLocation(
        story=story_obj,
        id="skull_island",
        name="Skull Island",
        description="A barren, skull-shaped island that serves as the traditional meeting ground for pirate councils. Ancient stone structures mark the gathering places where major decisions affecting all pirates are made."
    )
    
    emerald_jungle = StoryLocation(
        story=story_obj,
        id="emerald_jungle_islands",
        name="Emerald Jungle Islands",
        description="An uncharted region of dense islands covered in ancient vegetation. Local legends speak of ruins belonging to a civilization that predates the pirate era."
    )
    
    ghost_straits_loc = StoryLocation(
        story=story_obj,
        id="ghost_straits",
        name="Ghost Straits",
        description="A mysterious passage between two major islands that only appears during specific lunar phases. Ships that attempt to navigate it at the wrong time vanish without a trace."
    )
    
    # Create the opening segment
    opening_segment = StorySegment(
        story=story_obj,
        id="dock_encounter",
        story_id=story_obj.id,
        short_description="A tense encounter at the docks of Port Crimson Tides",
        atmosphere="tense and mysterious",
        time_of_day="sunset",
        weather="calm with occasional ocean breeze",
        key_items=["treasure map fragment", "captain's medallion", "old weathered journal"],
        text_blocks=[
            TextBlock(
                type=TextType.SCENE_TITLE,
                content="Port of Crimson Tides - The Docks"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The setting sun casts long shadows across the volcanic stone docks of Port Crimson Tides. Your ship, the Swift Fortune, rocks gently at its berth as crew members prepare the final supplies for departure. The air smells of salt, tar, and adventure.",
                emotion="anticipatory"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="As you oversee the loading of supplies, a hooded figure approaches you with hurried steps. Their hand grips something tightly - possibly a map or letter. Quinn appears at your side, hand instinctively moving toward their cutlass.",
                emotion="cautious"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="Captain, stay alert. I don't recognize that figure, and they're moving with purpose.",
                character="quartermaster_quinn",
                emotion="protective"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The hooded figure stops a few paces away, breathing heavily as if they've been running. They glance nervously over their shoulder before speaking in a hushed, urgent tone.",
                emotion="tense"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="Captain, I have information about the location of the Crimson Depths. But it's not safe to discuss here. Your enemy, Captain Vex, has spies watching the docks. What will you do?",
                character="stranger",
                emotion="desperate"
            )
        ],
        characters_present=["quartermaster_quinn"],
        locations_present=["port_crimson_tides"],
        characters=[
            CharacterStatus(character_id="quartermaster_quinn", current_status="alert and protective")
        ],
        locations=[
            LocationStatus(location_id="port_crimson_tides", current_status="bustling with activity at sunset")
        ]
    )
    
    # Create two choices from the opening segment
    choice_1 = StoryChoice(
        story=story_obj,
        id="choice_trust_stranger",
        story_id=story_obj.id,
        from_segment_id="dock_encounter",
        to_segment_id=None,  # Will be generated
        text="Trust the stranger and move to a private location to hear their information about the Crimson Depths"
    )
    
    choice_2 = StoryChoice(
        story=story_obj,
        id="choice_suspicious",
        story_id=story_obj.id,
        from_segment_id="dock_encounter",
        to_segment_id=None,  # Will be generated
        text="View this as a trap set by Captain Vex and have Quinn arrest the stranger for questioning"
    )
    
    # Add choices to opening segment
    opening_segment.add_outgoing_choice(choice_1)
    opening_segment.add_outgoing_choice(choice_2)
    
    # Save all components
    story_obj.save()
    context_obj.save()
    
    captain_blackhook.save()
    captain_vex.save()
    quartermaster_quinn.save()
    witch_morgan.save()
    
    port_crimson.save()
    skull_island.save()
    emerald_jungle.save()
    ghost_straits_loc.save()
    
    opening_segment.save()
    choice_1.save()
    choice_2.save()
    
    print("✓ Story 'Seas of Fortune' created successfully!")
    print(f"  - Story ID: {story_obj.id}")
    print(f"  - Title: {story_obj.title}")
    print(f"  - Starting segment: {opening_segment.id}")
    print(f"  - Characters: {', '.join([c.name for c in [captain_blackhook, captain_vex, quartermaster_quinn, witch_morgan]])}")
    print(f"  - Locations: {', '.join([l.name for l in [port_crimson, skull_island, emerald_jungle, ghost_straits_loc]])}")
    print(f"  - Initial choices: 2")


if __name__ == "__main__":
    create_pirate_story()
