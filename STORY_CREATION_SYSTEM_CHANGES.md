# Story Creation System - What Changed

## Summary of Changes

A modern story creation system has been implemented to replace the old hardcoded scripts. You can now create new stories through:

1. **Interactive CLI command**: `python -m app.cli create-story`
2. **Programmatic API**: `StoryBuilder` class for Python scripts
3. **Setup scripts**: Pre-made example stories

---

## Deleted Files

The following old story creation scripts have been removed:

```
❌ backend/scripts/save_story.py           (Old: Veil of Thornreach hardcoded)
❌ backend/scripts/save_story_scifi.py     (Old: Sci-Fi story hardcoded)
❌ backend/scripts/save_story_pirate.py    (Old: Pirate story hardcoded)
```

These were inflexible, hardcoded story definitions. Now replaced with a modern builder pattern.

---

## New Files

### 1. `backend/app/utils/story_builder.py`

A fluent API for building stories programmatically.

**Key classes:**
- `StoryBuilder`: Main builder class with chainable methods

**Key methods:**
- `add_worldbuilding()` - Add fundamental truths and worldbuilding
- `add_character()` - Add a character with avatar customization
- `add_location()` - Add a location
- `add_opening_segment()` - Add the first scene
- `add_segment()` - Add additional scenes
- `add_choice()` - Connect scenes with player choices
- `save()` - Write everything to disk

**Example:**
```python
from app.utils.story_builder import StoryBuilder

builder = StoryBuilder("my_story", "My Story", "Description", "Fantasy")
builder.add_opening_segment("opening", "Opening Scene", "Text...")
builder.add_choice("c1", "opening", "Do something", to_segment_id=None)
builder.save()
```

### 2. `backend/scripts/setup_example_stories.py`

Pre-configured example stories ready to use.

**Creates three stories:**
- `veil_of_thornreach` - Dark Fantasy (3 characters, 3 locations, 2 segments, 5 choices)
- `station_aurora` - Sci-Fi (2 characters, 2 locations, 1 segment, 3 choices)
- `midnight_library` - Mystery (2 characters, 2 locations, 1 segment, 3 choices)

**Run with:**
```bash
python backend/scripts/setup_example_stories.py
```

### 3. `STORY_CREATION_GUIDE.md`

Comprehensive guide for creating stories with examples and best practices.

---

## Modified Files

### 1. `backend/app/cli.py`

**Added new command:**

```bash
python -m app.cli create-story <story_id> \
  --title "Story Title" \
  --description "Description" \
  --genre "Genre"
```

This guides you through an interactive story creation process:
1. Add worldbuilding truths
2. Create characters
3. Create locations
4. Write opening scene
5. Create opening choices

The command validates the story is complete before saving.

### 2. `run.sh`

Updated the story auto-creation logic:

```bash
# Old behavior:
# If story doesn't exist and is "veil_of_thornreach", run save_story.py

# New behavior:
# If story doesn't exist and is "veil_of_thornreach", run setup_example_stories.py
```

This means:
- `./run.sh` - Creates example stories automatically
- `./run.sh my_story` - Fails with helpful message pointing to `create-story` command

---

## How It Works

### Old System (Deleted)

```
hardcoded Python script
    ↓
Creates Story/Characters/Segments manually
    ↓
Saves to disk
    ↓
Fixed to one story per script
```

**Problems:**
- Can't easily create new stories without writing code
- Each story required its own file
- No validation during creation
- Hard to maintain consistency

### New System (Current)

```
CLI create-story command  OR  StoryBuilder API
    ↓
Interactive prompts / Fluent method calls
    ↓
StoryBuilder validates and builds
    ↓
Saves all components to disk
    ↓
Can create unlimited stories
    ↓
Consistent structure for all stories
```

**Improvements:**
- ✅ No code writing needed (CLI handles it)
- ✅ One system for all stories
- ✅ Built-in validation
- ✅ Reusable API for migrations
- ✅ Easy to extend with new story types

---

## Usage Examples

### Create a Story Interactively

```bash
python -m app.cli create-story adventure \
  --title "Dragon's Lair" \
  --description "Explore a dragon's ancient lair" \
  --genre "Fantasy"

# Follow the prompts to add worldbuilding, characters, locations, and scenes
```

### Create a Story Programmatically

```python
from app.utils.story_builder import StoryBuilder

builder = StoryBuilder("my_epic", "My Epic Journey", "...", "Adventure")

builder.add_worldbuilding(
    fundamental_truths=["The world is ancient", "Dragons rule"],
    worldbuilding={"setting": "A fantasy realm"}
)

builder.add_character("hero", "The Hero", "A brave adventurer", "...")
builder.add_location("tower", "The Tower", "An ancient tower")

builder.add_opening_segment("start", "Beginning", "You stand before a tower...")
builder.add_choice("c1", "start", "Enter", to_segment_id=None)

builder.save()
```

### Setup Example Stories

```bash
python backend/scripts/setup_example_stories.py
```

Creates:
- `veil_of_thornreach` (Dark Fantasy)
- `station_aurora` (Sci-Fi)
- `midnight_library` (Mystery)

### Play Any Story

```bash
python -m app.cli run-story my_story
```

---

## Data Structure

All stories follow the same structure:

```
.infinite_story_data/<story_id>/
├── story/
│   └── <story_id>.json              # Story metadata
├── storycontext/
│   └── main_context.json            # Worldbuilding
├── storycharacter/
│   ├── <char_id>.json
│   └── ...
├── storylocation/
│   ├── <loc_id>.json
│   └── ...
├── storysegment/
│   ├── <segment_id>.json
│   └── ...
└── storychoice/
    ├── <choice_id>.json
    └── ...
```

This is consistent regardless of how the story was created.

---

## CLI Commands Reference

### Story Management

```bash
# Create new story (interactive)
python -m app.cli create-story <story_id> --title "Title" --description "Desc" --genre "Genre"

# List all stories
python -m app.cli list-stories

# Play a story
python -m app.cli run-story <story_id> [--mode immersive|debug] [--resume]

# Delete a story
python -m app.cli delete-story <story_id>

# Reset story to start
python -m app.cli clear-state <story_id>

# Test AI generation
python -m app.cli test-generation <story_id>
```

---

## Validation

Stories must have:

✅ **Required:**
- Unique story ID
- Title and description
- Genre tag
- At least one segment (opening scene)
- At least one choice from the opening

⚠️ **Recommended:**
- Worldbuilding context
- 2-4 characters
- 2-3 locations
- Multiple segments creating narrative flow

The `StoryBuilder.save()` method validates:
- Opening segment exists
- Opening segment has outgoing choices
- Choice references are valid

---

## Migration Path for Old Data

To convert old data to the new format:

```python
from app.utils.story_builder import StoryBuilder

def migrate_old_story(old_dict):
    builder = StoryBuilder(
        story_id=old_dict['id'],
        title=old_dict['title'],
        description=old_dict['description'],
        genre=old_dict.get('genre', 'Unknown')
    )
    
    # Add all old components
    for char in old_dict['characters']:
        builder.add_character(char['id'], char['name'], ...)
    
    for loc in old_dict['locations']:
        builder.add_location(loc['id'], loc['name'], ...)
    
    for seg in old_dict['segments']:
        builder.add_segment(seg['id'], seg['title'], ...)
    
    for choice in old_dict['choices']:
        builder.add_choice(choice['id'], ...)
    
    return builder.save()
```

---

## Benefits of New System

### For Users

- ✅ Easy interactive story creation
- ✅ No coding required
- ✅ Clear guidance at each step
- ✅ Helpful error messages
- ✅ Stories ready to play immediately

### For Developers

- ✅ Reusable, testable API
- ✅ Chainable method calls
- ✅ Built-in validation
- ✅ Easy to extend
- ✅ Clear separation of concerns
- ✅ Works for migrations and imports

### For the System

- ✅ Consistent data structure
- ✅ No special-case handling
- ✅ Easy to add features (e.g., story templates)
- ✅ Cleaner codebase
- ✅ Easier to maintain

---

## Future Enhancements

Potential additions to the system:

1. **Story Templates**
   ```bash
   python -m app.cli create-story my_story --template fantasy
   ```

2. **Story Import/Export**
   ```bash
   python -m app.cli export-story veil_of_thornreach > story.json
   python -m app.cli import-story story.json --id restored_story
   ```

3. **Story Editing**
   ```bash
   python -m app.cli edit-story veil_of_thornreach --add-segment
   ```

4. **Web-based Creator**
   - Interactive UI for creating stories
   - Drag-and-drop segment editor
   - Character avatar customizer

5. **Batch Creation**
   ```python
   from app.utils.story_builder import StoryBuilder
   
   stories = [
       StoryBuilder(...).save() for _ in range(10)
   ]
   ```

---

## Troubleshooting

### Q: Where are my stories saved?
**A:** In `.infinite_story_data/<story_id>/` in the project root.

### Q: Can I edit a story after creation?
**A:** Yes, edit the JSON files in `.infinite_story_data/` or use the API to programmatically modify.

### Q: How do I delete a story?
**A:** `python -m app.cli delete-story <story_id>`

### Q: Can I create multiple stories?
**A:** Yes, each gets a unique story ID and separate files.

### Q: What if I want a story with 100 segments?
**A:** Use the API to programmatically create them, or manually add JSON files.

### Q: Can I share my story?
**A:** Yes, share the `.infinite_story_data/<story_id>/` directory or export to JSON.

---

## Summary

The old hardcoded story scripts have been replaced with:

1. **`StoryBuilder`** - A flexible, reusable API for creating stories
2. **`create-story` CLI command** - Interactive story creation
3. **`setup_example_stories.py`** - Pre-made example stories
4. **`STORY_CREATION_GUIDE.md`** - Comprehensive documentation

This makes it easy to create, manage, and extend stories without writing code.

**Get started:**
```bash
python -m app.cli create-story my_story --title "My Story" --description "..." --genre "..."
```
