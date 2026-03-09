# Story Creation Quick Start

## 30-Second Overview

The old story scripts have been deleted. You now create stories via:

1. **Interactive CLI** (no coding needed)
2. **StoryBuilder API** (for Python developers)
3. **Example setup script** (3 pre-made stories)

---

## Create a Story (Interactive)

```bash
python -m app.cli create-story my_story \
  --title "My Story Title" \
  --description "A longer description" \
  --genre "Fantasy"
```

This guides you through:
- Adding worldbuilding rules
- Creating characters
- Creating locations
- Writing the opening scene
- Creating opening choices

Then play it:
```bash
python -m app.cli run-story my_story
```

---

## Create a Story (Code)

```python
from app.utils.story_builder import StoryBuilder

builder = StoryBuilder("my_story", "My Title", "Description", "Genre")

builder.add_worldbuilding(
    fundamental_truths=["Rule 1", "Rule 2"],
    worldbuilding={"setting": "..."}
)

builder.add_character("char_id", "Name", "Description", "Background")
builder.add_location("loc_id", "Location Name", "Description")

builder.add_opening_segment("opening", "Title", "Narrative text...")
builder.add_choice("c1", "opening", "Choice text", to_segment_id=None)

builder.save()
```

---

## Setup Example Stories

```bash
python backend/scripts/setup_example_stories.py
```

Creates 3 playable stories:
- `veil_of_thornreach` (Dark Fantasy)
- `station_aurora` (Sci-Fi)
- `midnight_library` (Mystery)

---

## Key Commands

```bash
# Create story interactively
python -m app.cli create-story <id> --title "T" --description "D" --genre "G"

# List all stories
python -m app.cli list-stories

# Play a story
python -m app.cli run-story <story_id>

# Delete a story
python -m app.cli delete-story <story_id>

# Reset story to start
python -m app.cli clear-state <story_id>
```

---

## File Locations

Old (deleted):
```
❌ backend/scripts/save_story.py
❌ backend/scripts/save_story_scifi.py
❌ backend/scripts/save_story_pirate.py
```

New:
```
✅ backend/app/utils/story_builder.py          (StoryBuilder class)
✅ backend/scripts/setup_example_stories.py    (3 example stories)
✅ STORY_CREATION_GUIDE.md                     (Full documentation)
```

---

## What Changed

| Before | After |
|--------|-------|
| Hardcoded Python scripts | Flexible StoryBuilder API |
| One story per file | Unlimited stories |
| Manual file editing | CLI commands or code |
| No validation | Built-in validation |
| Hard to extend | Easy to customize |

---

## Key Classes & Methods

### StoryBuilder

```python
StoryBuilder(story_id, title, description, genre="Unknown")
  .add_worldbuilding(fundamental_truths, worldbuilding)
  .add_character(char_id, name, description, background, avatar_shape, avatar_color)
  .add_location(loc_id, name, description)
  .add_opening_segment(segment_id, title, content, atmosphere, episode_number, episode_tone)
  .add_segment(segment_id, title, content, atmosphere, episode_number, episode_tone, parent_segment_id)
  .add_choice(choice_id, from_segment_id, text, to_segment_id)
  .save()  # Returns story_id
```

---

## Data Structure

Stories save to:
```
.infinite_story_data/<story_id>/
├── story/
├── storycontext/
├── storycharacter/
├── storylocation/
├── storysegment/
└── storychoice/
```

All JSON files, easy to inspect and modify.

---

## Next Steps

1. **Try interactive creation:**
   ```bash
   python -m app.cli create-story my_adventure --title "Adventure" --description "..." --genre "Fantasy"
   ```

2. **Or create example stories:**
   ```bash
   python backend/scripts/setup_example_stories.py
   ```

3. **Play your story:**
   ```bash
   python -m app.cli run-story my_adventure
   ```

---

## Documentation

- **Full Guide**: `STORY_CREATION_GUIDE.md`
- **Technical Details**: `STORY_CREATION_SYSTEM_CHANGES.md`
- **Game Loop Analysis**: `GAME_LOOP_WORLD_CREATION_ANALYSIS.md`

---

## Troubleshooting

**Q: Where do I start?**
A: Run `python -m app.cli create-story --help` to see options.

**Q: Can I edit stories after creating them?**
A: Yes, either use the API again or edit JSON files in `.infinite_story_data/`.

**Q: How do I share a story?**
A: Share the `.infinite_story_data/<story_id>/` directory.

**Q: Can I import old stories?**
A: Use the StoryBuilder API to programmatically migrate them.

---

## Summary

✅ **Old scripts deleted** - No more hardcoded stories  
✅ **CLI command added** - `python -m app.cli create-story`  
✅ **API available** - `StoryBuilder` for programmers  
✅ **Examples included** - 3 ready-to-play stories  
✅ **Documentation complete** - Full guides provided  

**You can now create unlimited stories in any genre!**
