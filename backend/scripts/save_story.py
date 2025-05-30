#!/usr/bin/env python3
import sys
import os

# Add the parent directory to the Python path so we can import the models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.story import Story
from app.models.story_segment import StorySegment, CharacterStatus, LocationStatus, StoryChoice
from app.models.story_character import StoryCharacter
from app.models.story_location import StoryLocation
from app.models.story_context import StoryContext
from app.models.text_types import TextType, TextBlock

def create_story():
    """Create the story components."""
    # Create the main story
    story_obj = Story(
        id="veil_of_thornreach",
        title="The Veil of Thornreach",
        description="A dark fantasy adventure set in a mystical forest realm slowly being consumed by a sentient fog called The Veil. As civilization clings to the edge of Thornreach, the last untouched grove, a group of unlikely allies must uncover the origin of The Veil and decide its fate.",
        genre="Dark Fantasy",
        user_id="test_user_1",
        start_segment_id="opening_scene"
    )
    
    # Create the story context with expanded worldbuilding
    context_obj = StoryContext(
        id="veil_context_1",
        story=story_obj,
        fundamental_truths=[
            "The Veil is a living entity that erases memories and reshapes reality",
            "Thornreach Grove is the last sanctuary of the old gods, protected by fading wards",
            "Memory is a resource that can be traded for power or survival",
            "The Withered Court, a lost royal bloodline, rules from inside The Veil",
            "Mystic relics scattered throughout the realm reveal fragments of the world's lost past",
            "The old gods' power is tied to the natural cycles of the forest",
            "The Veil's corruption spreads faster during the waning moon",
            "Ancient prophecies speak of a 'Memory Weaver' who can control The Veil",
            "The forest's heart beats in rhythm with the protective wards",
            "Time flows differently within The Veil's embrace"
        ],
        worldbuilding={
            "setting": "A mystical forest realm on the brink of being consumed by The Veil",
            "magic_system": {
                "druidic_magic": "Nature-based magic that draws power from the forest's life force",
                "fae_enchantments": "Ancient magic of the fae, tied to the realm's natural cycles",
                "veil_magic": "Forbidden arts that manipulate The Veil's power",
                "memory_magic": "Rare ability to manipulate and preserve memories",
                "ward_magic": "Protective magic passed down from the old gods"
            },
            "political_system": {
                "withered_court": "Corrupted rulers who maintain their power through The Veil",
                "druid_circle": "Guardians of Thornreach Grove's ancient traditions",
                "memory_keepers": "Secret society preserving the realm's history",
                "fae_courts": "Ancient powers maintaining neutrality in the conflict",
                "refugee_camps": "Scattered settlements of those who escaped The Veil"
            },
            "major_locations": {
                "thornreach_grove": "The last untouched sanctuary, protected by ancient wards",
                "the_veil": "A sentient fog that consumes and transforms everything it touches",
                "withered_court": "The corrupted seat of power within The Veil",
                "mystic_ruins": "Scattered remnants of the old world containing powerful relics",
                "memory_pools": "Sacred springs where memories crystallize into physical form",
                "fae_crossroads": "Ancient meeting place of the fae courts",
                "warden's_watch": "High vantage point where the druids monitor The Veil's spread",
                "forgotten_archive": "Library of preserved memories and ancient knowledge",
                "heartwood_sanctuary": "The oldest tree in Thornreach, source of the wards' power",
                "twilight_market": "Trading post where memories are bartered for supplies"
            }
        }
    )
    
    # Create expanded character list
    characters = [
        StoryCharacter(
            id="eira",
            story=story_obj,
            name="Eira",
            description="A novice druid with forbidden magic, bound to the forest's spirit. Her connection to nature gives her unique insights into The Veil's corruption.",
            background="Born in Thornreach Grove, Eira showed an early affinity for druidic magic. However, her curiosity led her to experiment with forbidden arts, creating a dangerous bond between her and the forest's spirit."
        ),
        StoryCharacter(
            id="thorne",
            story=story_obj,
            name="Thorne",
            description="A cursed knight exiled from the Veil-corrupted kingdom. His armor bears the scars of The Veil's touch, but also grants him resistance to its effects.",
            background="Once a loyal knight of the Withered Court, Thorne was cursed when he discovered the truth about The Veil's origin. His exile has made him both bitter and determined to find a way to end the corruption."
        ),
        StoryCharacter(
            id="nyx",
            story=story_obj,
            name="Nyx",
            description="A trickster fae whose motives are as mysterious as The Veil itself. They seem to know more than they let on about the realm's fate.",
            background="Nyx has existed in the realm since before The Veil's appearance. Their true nature and allegiance remain unclear, but their knowledge of ancient magic and the old ways makes them a valuable, if untrustworthy, ally."
        ),
        StoryCharacter(
            id="brother_cellen",
            story=story_obj,
            name="Brother Cellen",
            description="A blind monk who can 'see' truth in the fog through song. His unique perception makes him immune to The Veil's memory-erasing effects.",
            background="Once a scholar of the old ways, Brother Cellen lost his sight in a ritual to understand The Veil's nature. His blindness became a gift, allowing him to perceive the true nature of things through song and sound."
        ),
        StoryCharacter(
            id="elder_marrow",
            story=story_obj,
            name="Elder Marrow",
            description="The ancient guardian of the Heartwood Sanctuary, a massive tree that serves as the source of Thornreach's protective wards.",
            background="Having lived for centuries, Elder Marrow has witnessed the gradual spread of The Veil. Their bark-like skin and leaf-veined eyes speak of their deep connection to the forest's heart."
        ),
        StoryCharacter(
            id="memory_weaver",
            story=story_obj,
            name="The Memory Weaver",
            description="A mysterious figure who can manipulate and preserve memories, said to be the key to understanding The Veil's true nature.",
            background="Their true identity is unknown, but they are said to have been the first to discover how to extract and preserve memories from The Veil's grasp."
        ),
        StoryCharacter(
            id="veil_whisperer",
            story=story_obj,
            name="The Veil Whisperer",
            description="A shadowy figure who claims to communicate with The Veil itself, offering insights into its desires and intentions.",
            background="Some believe they are a prophet, others a charlatan. Their true connection to The Veil remains a mystery, but their predictions have proven eerily accurate."
        )
    ]
    
    # Create expanded locations list
    locations = [
        StoryLocation(
            id="thornreach_grove",
            story=story_obj,
            name="Thornreach Grove",
            description="The last untouched sanctuary in the realm, protected by ancient wards. Ancient trees tower overhead, their leaves glowing with protective magic. The air is thick with the scent of herbs and the sound of running water."
        ),
        StoryLocation(
            id="the_veil",
            story=story_obj,
            name="The Veil",
            description="A sentient fog that consumes and transforms everything it touches. Its shifting forms create illusions of familiar places, while erasing memories and reshaping reality. The air is thick with whispers of forgotten things."
        ),
        StoryLocation(
            id="withered_court",
            story=story_obj,
            name="The Withered Court",
            description="The corrupted seat of power within The Veil. Once a magnificent palace, now a twisted reflection of its former glory. The architecture seems to shift and change, as if the building itself is alive and corrupted."
        ),
        StoryLocation(
            id="mystic_ruins",
            story=story_obj,
            name="Mystic Ruins",
            description="Scattered remnants of the old world containing powerful relics. The ruins are partially protected from The Veil's influence, making them safe havens for those seeking knowledge and power."
        ),
        StoryLocation(
            id="memory_pools",
            story=story_obj,
            name="Memory Pools",
            description="Sacred springs where memories crystallize into physical form. The water shimmers with the colors of forgotten moments, and those who drink from it may glimpse fragments of lost memories."
        ),
        StoryLocation(
            id="fae_crossroads",
            story=story_obj,
            name="Fae Crossroads",
            description="An ancient meeting place of the fae courts, marked by a circle of standing stones. The air here is thick with magic, and time flows differently than in the rest of the realm."
        ),
        StoryLocation(
            id="warden_watch",
            story=story_obj,
            name="Warden's Watch",
            description="A high vantage point where the druids monitor The Veil's spread. The view offers a clear sight of the boundary between Thornreach and The Veil's domain."
        ),
        StoryLocation(
            id="heartwood_sanctuary",
            story=story_obj,
            name="Heartwood Sanctuary",
            description="The oldest tree in Thornreach, source of the wards' power. Its massive trunk pulses with ancient magic, and its roots extend deep into the realm's memory."
        )
    ]
    
    # Create the story segment (keeping only the opening scene)
    segment_obj = StorySegment(
        id="opening_scene",
        story=story_obj,
        short_description="The Gathering at Thornreach Grove",
        atmosphere="tense and foreboding",
        text_blocks=[
            TextBlock(
                type=TextType.SCENE_TITLE,
                content="The Last Sanctuary"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The ancient trees of Thornreach Grove sway gently in the evening breeze, their leaves casting dappled shadows on the moss-covered ground. The protective wards hum softly, a constant reminder of the danger that lurks beyond.",
                emotion="foreboding"
            ),
            TextBlock(
                type=TextType.SFX,
                content="The distant sound of The Veil's whispers carries on the wind, like forgotten memories trying to be remembered."
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="The wards are weakening. I can feel it in the roots, in the very soil beneath us.",
                character="eira",
                emotion="concerned"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="Then we must act quickly. The Withered Court grows stronger with each passing day.",
                character="thorne",
                emotion="determined"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="*A melodic laugh echoes through the grove* Oh, but isn't it fascinating how The Veil changes everything it touches? Perhaps it's not something to be feared, but understood...",
                character="nyx",
                emotion="mysterious"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="*singing softly* The truth lies in the patterns, in the spaces between the notes. The Veil... it's not just consuming memories. It's collecting them.",
                character="brother_cellen",
                emotion="enlightened"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The group falls silent as The Veil's whispers grow louder. A decision must be made, and soon. The fate of Thornreach, and perhaps the entire realm, hangs in the balance.",
                emotion="tense"
            )
        ],
        characters=[
            CharacterStatus(
                character_id="eira",
                current_status="active"
            ),
            CharacterStatus(
                character_id="thorne",
                current_status="active"
            ),
            CharacterStatus(
                character_id="nyx",
                current_status="active"
            ),
            CharacterStatus(
                character_id="brother_cellen",
                current_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id="thornreach_grove",
                current_status="active"
            )
        ]
    )
    
    # Create choices for the opening scene
    choices = [
        StoryChoice(
            id="choice_investigate_wards",
            story=story_obj,
            from_segment_id="opening_scene",
            to_segment_id=None,
            text="Investigate the weakening wards with Eira and Brother Cellen"
        ),
        StoryChoice(
            id="choice_enter_veil",
            story=story_obj,
            from_segment_id="opening_scene",
            to_segment_id=None,
            text="Venture into The Veil to understand its nature"
        ),
        StoryChoice(
            id="choice_seek_court",
            story=story_obj,
            from_segment_id="opening_scene",
            to_segment_id=None,
            text="Seek out the Withered Court for answers"
        )
    ]

    # Connect choices with segment
    for choice in choices:
        segment_obj.add_outgoing_choice(choice)
        segment_obj.add_incoming_choice(choice)

    return story_obj, context_obj, characters, locations, [segment_obj], choices

def save_story_data(story, story_context, characters, locations, story_segments, story_choices):
    """Save all story components to disk."""
    # Save the main story
    story.save()
    
    # Save the story context
    story_context.save()
    
    # Save all characters
    for char in characters:
        char.save()
    
    # Save all locations
    for loc in locations:
        loc.save()
    
    # Save all story segments
    for segment in story_segments:
        segment.save()
    
    # Save all story choices
    for choice in story_choices:
        choice.save()
    
    return {
        "story_id": story.id,
        "context_id": story_context.id,
        "character_ids": [c.id for c in characters],
        "location_ids": [l.id for l in locations],
        "segment_ids": [s.id for s in story_segments],
        "choice_ids": [c.id for c in story_choices]
    }

def main():
    """Save the story data to disk."""
    print("Saving The Veil of Thornreach story data...")
    
    # Create all story components
    story_obj, context_obj, characters, locations, segments, choices = create_story()
    
    # Save all components
    saved_data = save_story_data(
        story_obj,
        context_obj,
        characters,
        locations,
        segments,
        choices
    )
    
    print("\nStory data saved successfully!")
    print("\nSaved components:")
    print(f"Story ID: {saved_data['story_id']}")
    print(f"Context ID: {saved_data['context_id']}")
    print(f"Character IDs: {', '.join(saved_data['character_ids'])}")
    print(f"Location IDs: {', '.join(saved_data['location_ids'])}")
    print(f"Segment IDs: {', '.join(saved_data['segment_ids'])}")
    print(f"Choice IDs: {', '.join(saved_data['choice_ids'])}")
    print("\nThe story data has been saved to the 'data' directory.")

if __name__ == "__main__":
    main()