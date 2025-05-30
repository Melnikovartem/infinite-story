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
from app.models.types import TextType, TextBlock

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
    
    # Create the story context
    context_obj = StoryContext(
        id="veil_context_1",
        story_id=story_obj.id,
        fundamental_truths=[
            "The Veil is a living entity that erases memories and reshapes reality",
            "Thornreach Grove is the last sanctuary of the old gods, protected by fading wards",
            "Memory is a resource that can be traded for power or survival",
            "The Withered Court, a lost royal bloodline, rules from inside The Veil",
            "Mystic relics scattered throughout the realm reveal fragments of the world's lost past"
        ],
        worldbuilding={
            "setting": "A mystical forest realm on the brink of being consumed by The Veil",
            "magic_system": "A blend of druidic magic, fae enchantments, and forbidden arts tied to The Veil",
            "political_system": "A fractured society with the Withered Court ruling from within The Veil and scattered settlements clinging to Thornreach",
            "major_locations": {
                "thornreach_grove": "The last untouched sanctuary, protected by ancient wards",
                "the_veil": "A sentient fog that consumes and transforms everything it touches",
                "withered_court": "The corrupted seat of power within The Veil",
                "mystic_ruins": "Scattered remnants of the old world containing powerful relics"
            }
        }
    )
    
    # Create the characters
    characters = [
        StoryCharacter(
            id="eira",
            story_id=story_obj.id,
            name="Eira",
            description="A novice druid with forbidden magic, bound to the forest's spirit. Her connection to nature gives her unique insights into The Veil's corruption.",
            background="Born in Thornreach Grove, Eira showed an early affinity for druidic magic. However, her curiosity led her to experiment with forbidden arts, creating a dangerous bond between her and the forest's spirit."
        ),
        StoryCharacter(
            id="thorne",
            story_id=story_obj.id,
            name="Thorne",
            description="A cursed knight exiled from the Veil-corrupted kingdom. His armor bears the scars of The Veil's touch, but also grants him resistance to its effects.",
            background="Once a loyal knight of the Withered Court, Thorne was cursed when he discovered the truth about The Veil's origin. His exile has made him both bitter and determined to find a way to end the corruption."
        ),
        StoryCharacter(
            id="nyx",
            story_id=story_obj.id,
            name="Nyx",
            description="A trickster fae whose motives are as mysterious as The Veil itself. They seem to know more than they let on about the realm's fate.",
            background="Nyx has existed in the realm since before The Veil's appearance. Their true nature and allegiance remain unclear, but their knowledge of ancient magic and the old ways makes them a valuable, if untrustworthy, ally."
        ),
        StoryCharacter(
            id="brother_cellen",
            story_id=story_obj.id,
            name="Brother Cellen",
            description="A blind monk who can 'see' truth in the fog through song. His unique perception makes him immune to The Veil's memory-erasing effects.",
            background="Once a scholar of the old ways, Brother Cellen lost his sight in a ritual to understand The Veil's nature. His blindness became a gift, allowing him to perceive the true nature of things through song and sound."
        )
    ]
    
    # Create the locations
    locations = [
        StoryLocation(
            id="thornreach_grove",
            story_id=story_obj.id,
            name="Thornreach Grove",
            description="The last untouched sanctuary in the realm, protected by ancient wards. Ancient trees tower overhead, their leaves glowing with protective magic. The air is thick with the scent of herbs and the sound of running water."
        ),
        StoryLocation(
            id="the_veil",
            story_id=story_obj.id,
            name="The Veil",
            description="A sentient fog that consumes and transforms everything it touches. Its shifting forms create illusions of familiar places, while erasing memories and reshaping reality. The air is thick with whispers of forgotten things."
        ),
        StoryLocation(
            id="withered_court",
            story_id=story_obj.id,
            name="The Withered Court",
            description="The corrupted seat of power within The Veil. Once a magnificent palace, now a twisted reflection of its former glory. The architecture seems to shift and change, as if the building itself is alive and corrupted."
        ),
        StoryLocation(
            id="mystic_ruins",
            story_id=story_obj.id,
            name="Mystic Ruins",
            description="Scattered remnants of the old world containing powerful relics. The ruins are partially protected from The Veil's influence, making them safe havens for those seeking knowledge and power."
        )
    ]
    
    # Create the story segment
    segment_obj = StorySegment(
        id="opening_scene",
        story_id=story_obj.id,
        short_description="The Gathering at Thornreach Grove",
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
                ai_status="active"
            ),
            CharacterStatus(
                character_id="thorne",
                ai_status="active"
            ),
            CharacterStatus(
                character_id="nyx",
                ai_status="active"
            ),
            CharacterStatus(
                character_id="brother_cellen",
                ai_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id="thornreach_grove",
                ai_status="active"
            )
        ]
    )
    
    # Create additional segments and choices
    segments = [segment_obj]
    choices = []

    # Segment 2: Investigate the Wards
    investigate_wards = StorySegment(
        id="investigate_wards",
        story_id=story_obj.id,
        short_description="Investigating the Weakening Wards",
        text_blocks=[
            TextBlock(
                type=TextType.SCENE_TITLE,
                content="The Wards of Thornreach"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="Eira leads the group to the edge of the grove, where the protective wards shimmer like a curtain of light. The magic here is ancient, woven by the old gods themselves.",
                emotion="awe"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="The wards are like a song, but the melody is changing. Becoming... darker.",
                character="brother_cellen",
                emotion="concerned"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="I can strengthen them, but it will require a great deal of energy. And there's a risk...",
                character="eira",
                emotion="hesitant"
            )
        ],
        characters=[
            CharacterStatus(
                character_id="eira",
                ai_status="active"
            ),
            CharacterStatus(
                character_id="brother_cellen",
                ai_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id="thornreach_grove",
                ai_status="active"
            )
        ]
    )
    segments.append(investigate_wards)

    # Segment 3: Enter the Veil
    enter_veil = StorySegment(
        id="enter_veil",
        story_id=story_obj.id,
        short_description="Venturing into The Veil",
        text_blocks=[
            TextBlock(
                type=TextType.SCENE_TITLE,
                content="Beyond the Wards"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The group steps beyond the protective barrier of Thornreach Grove. The Veil swirls around them, its whispers growing clearer, more distinct.",
                emotion="tense"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="Stay close. The Veil will try to separate us, to make us forget why we're here.",
                character="thorne",
                emotion="warning"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="*laughing* Oh, but isn't it beautiful? Look how it dances!",
                character="nyx",
                emotion="delighted"
            )
        ],
        characters=[
            CharacterStatus(
                character_id="thorne",
                ai_status="active"
            ),
            CharacterStatus(
                character_id="nyx",
                ai_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id="the_veil",
                ai_status="active"
            )
        ]
    )
    segments.append(enter_veil)

    # Segment 4: Seek the Withered Court
    seek_court = StorySegment(
        id="seek_court",
        story_id=story_obj.id,
        short_description="Journey to the Withered Court",
        text_blocks=[
            TextBlock(
                type=TextType.SCENE_TITLE,
                content="The Path to Power"
            ),
            TextBlock(
                type=TextType.NARRATOR_DESCRIBING,
                content="The group decides to seek out the Withered Court, hoping to find answers about The Veil's origin. The path ahead is treacherous, but the promise of knowledge drives them forward.",
                emotion="determined"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="The Court will be expecting us. They always do.",
                character="thorne",
                emotion="grim"
            ),
            TextBlock(
                type=TextType.CHARACTER_SPEECH,
                content="Then we must be ready for whatever they have planned.",
                character="eira",
                emotion="resolute"
            )
        ],
        characters=[
            CharacterStatus(
                character_id="thorne",
                ai_status="active"
            ),
            CharacterStatus(
                character_id="eira",
                ai_status="active"
            )
        ],
        locations=[
            LocationStatus(
                location_id="withered_court",
                ai_status="active"
            )
        ]
    )
    segments.append(seek_court)

    # Create choices for the opening scene
    opening_choices = [
        StoryChoice(
            id="choice_investigate_wards",
            story_id=story_obj.id,
            from_segment_id="opening_scene",
            to_segment_id="investigate_wards",
            text="Investigate the weakening wards with Eira and Brother Cellen"
        ),
        StoryChoice(
            id="choice_enter_veil",
            story_id=story_obj.id,
            from_segment_id="opening_scene",
            to_segment_id="enter_veil",
            text="Venture into The Veil to understand its nature"
        ),
        StoryChoice(
            id="choice_seek_court",
            story_id=story_obj.id,
            from_segment_id="opening_scene",
            to_segment_id="seek_court",
            text="Seek out the Withered Court for answers"
        )
    ]
    choices.extend(opening_choices)

    # Create choices for the investigate_wards segment
    investigate_choices = [
        StoryChoice(
            id="choice_strengthen_wards",
            story_id=story_obj.id,
            from_segment_id="investigate_wards",
            to_segment_id="opening_scene",
            text="Attempt to strengthen the wards, despite the risks"
        ),
        StoryChoice(
            id="choice_study_wards",
            story_id=story_obj.id,
            from_segment_id="investigate_wards",
            to_segment_id="opening_scene",
            text="Study the wards' patterns to understand their weakness"
        )
    ]
    choices.extend(investigate_choices)

    # Create choices for the enter_veil segment
    veil_choices = [
        StoryChoice(
            id="choice_deeper_veil",
            story_id=story_obj.id,
            from_segment_id="enter_veil",
            to_segment_id="opening_scene",
            text="Venture deeper into The Veil"
        ),
        StoryChoice(
            id="choice_return_grove",
            story_id=story_obj.id,
            from_segment_id="enter_veil",
            to_segment_id="opening_scene",
            text="Return to Thornreach Grove"
        )
    ]
    choices.extend(veil_choices)

    # Create choices for the seek_court segment
    court_choices = [
        StoryChoice(
            id="choice_approach_court",
            story_id=story_obj.id,
            from_segment_id="seek_court",
            to_segment_id="opening_scene",
            text="Approach the Court directly"
        ),
        StoryChoice(
            id="choice_observe_court",
            story_id=story_obj.id,
            from_segment_id="seek_court",
            to_segment_id="opening_scene",
            text="Observe the Court from a distance"
        )
    ]
    choices.extend(court_choices)

    # Connect choices with segments
    for segment in segments:
        # Add outgoing choices
        for choice in choices:
            if choice.from_segment_id == segment.id:
                segment.add_outgoing_choice(choice)
        
        # Add incoming choices
        for choice in choices:
            if choice.to_segment_id == segment.id:
                segment.add_incoming_choice(choice)

    return story_obj, context_obj, characters, locations, segments, choices

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