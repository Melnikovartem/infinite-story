#!/usr/bin/env python3
"""Debug script to check story loading."""

from app.models.story import Story
from app.engine.story_runner import StoryRunner

# Load the story
story = Story.load("veil_of_thornreach", "veil_of_thornreach")
print(f"Story loaded: {story.title}")
print(f"Start segment: {story.start_segment_id}")

# Check segments BEFORE runner.start()
print(f"\nSegments in story BEFORE start(): {len(story.get_all_segments())}")
for seg in story.get_all_segments():
    print(f"  - {seg.id}: {seg.short_description}")

# Create runner
runner = StoryRunner(story)

# Check segments AFTER creating runner
print(f"\nSegments in story AFTER creating runner: {len(story.get_all_segments())}")

runner.start()

# Check segments AFTER runner.start()
print(f"\nSegments in story AFTER start(): {len(story.get_all_segments())}")
for seg in story.get_all_segments():
    print(f"  - {seg.id}: {seg.short_description}")

# Check current segment
if runner.current_segment:
    print(f"\nCurrent segment: {runner.current_segment.id}")
    print(f"Current segment description: {runner.current_segment.short_description}")

    # Check outgoing choices
    print(f"\nOutgoing choices: {len(runner.current_segment.outgoing_choices)}")
    for choice_id, choice in runner.current_segment.outgoing_choices.items():
        print(f"  - {choice_id}: {choice.text}")
else:
    print("\nERROR: current_segment is None!")

# Check all choices in story
print(f"\nAll choices in story: {len(story.get_all_choices())}")
for choice in story.get_all_choices():
    print(f"  - {choice.id}: from={choice.from_segment_id}, to={choice.to_segment_id}")
