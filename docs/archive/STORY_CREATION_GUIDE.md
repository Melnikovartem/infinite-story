# Story Creation Guide

This guide explains how to create new stories using the modern `StoryBuilder` system.

## Quick Start

### Using the CLI (Interactive)

Create a new story interactively:

```bash
python -m app.cli create-story my_story \
  --title "My Story Title" \
  --description "A longer description of the story" \
  --genre "Fantasy"
```

This will prompt you to:
1. Add worldbuilding truths and descriptions
2. Create 2-4 main characters
3. Create 2-3 main locations
4. Write the opening scene
5. Create 2-3 opening choices

Then run your story:

```bash
python -m app.cli run-story my_story
```

### Using the StoryBuilder API (Programmatic)

For more control, use the `StoryBuilder` class in Python:

```python
from app.utils.story_builder import StoryBuilder

# Create a story
builder = StoryBuilder(
    story_id="my_story",
    title="My Story Title",
    description="A longer description",
    genre="Fantasy"
)

# Add worldbuilding
builder.add_worldbuilding(
    fundamental_truths=[
        "The world is ancient and full of magic",
        "Dragons once ruled the sky",
        "Magic flows through all living things"
    ],
    worldbuilding={
        "setting": "A medieval fantasy world",
        "magic_system": "Elemental magic"
    }
)

# Add characters
builder.add_character(
    char_id="protagonist",
    name="Alex",
    description="A young wizard",
    background="Discovered their powers at age 16"
)

# Add locations
builder.add_location(
    loc_id="tower",
    name="The Wizard's Tower",
    description="An ancient tower where magic is studied"
)

# Add opening scene
builder.add_opening_segment(
    segment_id="opening",
    title="A New Beginning",
    content="You stand before the ancient tower..."
)

# Add choices
builder.add_choice(
    choice_id="choice_1",
    from_segment_id="opening",
    text="Enter the tower",
    to_segment_id=None  # None = AI will generate
)

# Save everything
story_id = builder.save()
print(f"Story created: {story_id}")
```

## The StoryBuilder Class

### Constructor

```python
StoryBuilder(story_id: str, title: str, description: str, genre: str = "Unknown")
```

**Parameters:**
- `story_id`: Unique identifier for the story (lowercase, no spaces, e.g., `my_adventure`)
- `title`: Display title (e.g., `My Epic Adventure`)
- `description`: Long description of the story
- `genre`: Genre tag (optional, default: "Unknown")

### Methods

#### `add_worldbuilding(fundamental_truths, worldbuilding)`

Add worldbuilding context to the story.

```python
builder.add_worldbuilding(
    fundamental_truths=[
        "The world is ancient",
        "Magic is everywhere",
        "Dragons are nearly extinct"
    ],
    worldbuilding={
        "setting": "A fantasy world",
        "magic": "Elemental magic system",
        "history": "Dragons ruled for millennia"
    }
)
```

#### `add_character(char_id, name, description, background, avatar_shape, avatar_color)`

Add a character to the story.

```python
builder.add_character(
    char_id="protagonist",
    name="Alex",
    description="A young wizard with untamed power",
    background="Grew up in a small village, discovered magic at age 16",
    avatar_shape="circle",  # circle, square, triangle, diamond, star, pentagon
    avatar_color="#FF6B6B"  # Hex color code
)
```

#### `add_location(loc_id, name, description)`

Add a location to the story.

```python
builder.add_location(
    loc_id="tower",
    name="The Wizard's Tower",
    description="An ancient stone tower where magic is studied and preserved"
)
```

#### `add_opening_segment(segment_id, title, content, atmosphere, episode_number, episode_tone)`

Add the opening segment (first scene).

```python
builder.add_opening_segment(
    segment_id="opening",
    title="A New Beginning",
    content="The narrative text of the scene...",
    atmosphere="mysterious",
    episode_number=1,
    episode_tone="hopeful"
)
```

#### `add_segment(segment_id, title, content, atmosphere, episode_number, episode_tone, parent_segment_id)`

Add a non-opening segment.

```python
builder.add_segment(
    segment_id="tower_entrance",
    title="Inside the Tower",
    content="The narrative text...",
    atmosphere="awe",
    episode_number=1,
    episode_tone="hopeful",
    parent_segment_id="opening"  # Which segment leads here
)
```

#### `add_choice(choice_id, from_segment_id, text, to_segment_id)`

Add a choice connecting segments.

```python
builder.add_choice(
    choice_id="choice_1",
    from_segment_id="opening",
    text="Enter the tower",
    to_segment_id="tower_entrance"  # None = AI will generate
)

builder.add_choice(
    choice_id="choice_2",
    from_segment_id="opening",
    text="Ask for guidance first",
    to_segment_id=None  # AI will generate what happens next
)
```

#### `save()`

Save all story components to disk.

```python
story_id = builder.save()
print(f"Story saved: {story_id}")
```

Returns: The story ID

Raises: `ValueError` if the story is incomplete (missing opening segment or choices)

## Example Stories

Three example stories are included in `backend/scripts/setup_example_stories.py`:

### 1. Veil of Thornreach (Dark Fantasy)
A dark fantasy adventure with:
- 3 characters: Eira, Thorne, Nyx
- 3 locations: Thornreach Grove, The Veil's Edge, Memory Pool
- 2 segments with interconnected choices

Run with:
```bash
python -m app.cli run-story veil_of_thornreach
```

### 2. Station Aurora (Sci-Fi)
A sci-fi thriller featuring:
- 2 characters: Commander Chen, ARIA (AI)
- 2 locations: Command Bridge, Core Chamber
- 1 opening segment with 3 choice options

Run with:
```bash
python -m app.cli run-story station_aurora
```

### 3. The Midnight Library (Mystery)
A contemporary mystery about:
- 2 characters: Alex Moore, Dr. Helena Ward
- 2 locations: Main Reading Room, Restricted Archives
- 1 opening segment with investigation choices

Run with:
```bash
python -m app.cli run-story midnight_library
```

## Data Structure

Stories created with `StoryBuilder` are stored in:

```
.infinite_story_data/<story_id>/
├── story/
│   └── <story_id>.json          # Story metadata
├── storycontext/
│   └── main_context.json        # Worldbuilding
├── storycharacter/
│   ├── char_1.json
│   ├── char_2.json
│   └── ...
├── storylocation/
│   ├── loc_1.json
│   └── ...
├── storysegment/
│   ├── opening.json
│   ├── segment_2.json
│   └── ...
└── storychoice/
    ├── choice_1.json
    └── ...
```

Each file is a JSON representation of that component.

## Story Requirements

A valid story must have:

1. ✅ **A Story object** with unique `id`, `title`, `description`, and `genre`
2. ✅ **An opening segment** (referenced by `start_segment_id`)
3. ✅ **At least one choice** from the opening segment
4. ✅ **Text content** in segments (for narrative)

Optional but recommended:
- Worldbuilding context
- Multiple characters (2-5)
- Multiple locations (2-3)
- Multiple segments creating a narrative flow

## Avatar Customization

Characters can have custom avatars:

```python
builder.add_character(
    char_id="char_1",
    name="Alice",
    description="...",
    background="...",
    avatar_shape="circle",      # circle, square, triangle, diamond, star, pentagon
    avatar_color="#4ECDC4"      # Any hex color
)
```

Available shapes: `circle`, `square`, `triangle`, `diamond`, `star`, `pentagon`

Colors: Any valid hex color code (e.g., `#FF6B6B`, `#4ECDC4`, `#95E1D3`)

## Advanced: Branching Stories

Create complex branching narratives:

```python
# Segment 1
builder.add_opening_segment(
    segment_id="start",
    title="The Choice",
    content="You face two paths..."
)

# Path A
builder.add_segment(
    segment_id="path_a",
    title="The Left Path",
    content="You chose left...",
    parent_segment_id="start"
)

# Path B
builder.add_segment(
    segment_id="path_b",
    title="The Right Path",
    content="You chose right...",
    parent_segment_id="start"
)

# Converge both paths
builder.add_segment(
    segment_id="convergence",
    title="The Reunion",
    content="Both paths lead here...",
    parent_segment_id="path_a"  # Could also be path_b
)

# Create choices
builder.add_choice("c1", "start", "Take the left path", "path_a")
builder.add_choice("c2", "start", "Take the right path", "path_b")
builder.add_choice("c3", "path_a", "Move forward", "convergence")
builder.add_choice("c4", "path_b", "Move forward", "convergence")
```

## AI-Generated Branches

Choices with `to_segment_id=None` will have their next segment generated by AI:

```python
builder.add_choice(
    choice_id="choice_explore",
    from_segment_id="opening",
    text="Explore the unknown",
    to_segment_id=None  # AI will generate what you find
)
```

When the player makes this choice during gameplay, the AI will:
1. Read the current segment and choice context
2. Generate a new segment with narrative content
3. Create 2 new choices for that segment
4. Save everything to disk

This allows stories to grow organically as players explore them.

## Common Patterns

### Pattern 1: Linear Story (A → B → C)

```python
builder.add_opening_segment("seg_a", "Opening", "Text A")
builder.add_segment("seg_b", "Middle", "Text B", parent_segment_id="seg_a")
builder.add_segment("seg_c", "Ending", "Text C", parent_segment_id="seg_b")

builder.add_choice("c1", "seg_a", "Continue", "seg_b")
builder.add_choice("c2", "seg_b", "Continue", "seg_c")
```

### Pattern 2: Multiple Branches (A → B/C, B → D, C → E)

```python
builder.add_opening_segment("a", "Start", "...")
builder.add_segment("b", "Left", "...", parent_segment_id="a")
builder.add_segment("c", "Right", "...", parent_segment_id="a")
builder.add_segment("d", "Left End", "...", parent_segment_id="b")
builder.add_segment("e", "Right End", "...", parent_segment_id="c")

builder.add_choice("c1", "a", "Left", "b")
builder.add_choice("c2", "a", "Right", "c")
builder.add_choice("c3", "b", "Continue", "d")
builder.add_choice("c4", "c", "Continue", "e")
```

### Pattern 3: Hybrid (Some Manual, Some AI-Generated)

```python
# Write the opening yourself
builder.add_opening_segment("a", "Beginning", "...")
builder.add_segment("b", "Continuation", "...", parent_segment_id="a")

# Let AI take over
builder.add_choice("c1", "a", "Follow the map", "b")
builder.add_choice("c2", "a", "Ignore the map", to_segment_id=None)  # AI generates
builder.add_choice("c3", "b", "Enter the cave", to_segment_id=None)  # AI generates
builder.add_choice("c4", "b", "Setup camp", to_segment_id=None)  # AI generates
```

## Tips & Best Practices

1. **Start simple**: Begin with 1-2 segments and 2-3 choices per segment
2. **Use descriptive IDs**: Use names like `protagonist`, `forest_entrance`, not `char_1`, `seg_1`
3. **Write good opening text**: The first segment sets the tone for everything
4. **Create meaningful choices**: Each choice should feel like it matters
5. **Leave room for AI**: Use `to_segment_id=None` for player-driven exploration
6. **Test your story**: Play through your story after creation to verify choices work
7. **Expand gradually**: Start with a core narrative, add branches later

## Troubleshooting

### Story won't save

**Error**: `ValueError: Story must have a starting segment`

**Fix**: Call `add_opening_segment()` before `save()`

### Can't add choice

**Error**: `ValueError: Source segment 'xyz' not found`

**Fix**: Add the segment before creating choices from it

### Choices not appearing

**Cause**: Forgot to add choices to opening segment

**Fix**: Ensure the opening segment has at least 2 choices via `add_choice()`

### Files not found

**Error**: Story files not in `.infinite_story_data/`

**Fix**: Make sure `save()` completed successfully and check the logs

## Migration from Old Data

To convert old story data to the new format:

```python
from app.utils.story_builder import StoryBuilder

def migrate_old_story(old_data):
    builder = StoryBuilder(
        story_id=old_data['id'],
        title=old_data['title'],
        description=old_data['description'],
        genre=old_data.get('genre', 'Unknown')
    )
    
    # Migrate components...
    for char in old_data['characters']:
        builder.add_character(char['id'], char['name'], ...)
    
    # ... etc
    
    return builder.save()
```

## Next Steps

- Create a story with `python -m app.cli create-story`
- Play it with `python -m app.cli run-story <story_id>`
- Watch AI generate new segments as you explore unexplored choices
- Modify the story JSON files in `.infinite_story_data/` for advanced editing
