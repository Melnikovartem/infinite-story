## 🧩 Core MVP Objects (Detailed)

### 🧠 **Story**

* `id`
* `title`
* `description` *(required)*
* `genre` *(optional)*
* `user_id`
* `start_segment_id` *(optional)* - Reference to the first segment of the story
* `created_at`
* `updated_at`

---

### 🌐 **StoryContext** (Worldbuilding & Lore)

> World-level container for background and truth of the universe.

* `id`
* `story_id`
* `fundamental_truths`: `string[]`
* `worldbuilding`: `string` or `json` (history, cosmology, magic system…)
* `created_at`

---

### 📜 **StorySegment** (Scene)

> Core building block: represents one scene between two choices.

* `id`
* `story_id` - Backlink to the parent story
* `from_choice_id` - Reference to the choice that led to this segment (null for start segment)
* `text_blocks`: `[{ type: "narration" | "dialogue", content: string }]`
* `characters`: `[{ character_id, ai_status: string }]`
* `locations`: `[{ location_id, ai_status: string }]`
* `created_at`

---

### 🔘 **Choice**

> Connects two StorySegments.

* `id`
* `story_id`
* `from_segment_id`
* `to_segment_id`
* `text`: `string` (e.g., "Open the door")
* `clicks_logged`: `int`
* `clicks_anonymous`: `int`
* `flags`: `{ nsfw: boolean, violent: boolean, etc. }`
* `created_at`

---

### 👤 **User**

* `id`
* `email`
* `username`
* `created_at`

---

### 🎭 **Character**

* `id`
* `story_id`
* `name`
* `description`
* `background`: `string`
* `created_at`

---

### 🗺️ **Location**

* `id`
* `story_id`
* `name`
* `description`
* `created_at`

---

## 🔄 Relationships Overview

```plaintext
Story
 ├─ start_segment_id (points to first StorySegment)
 ├─ StoryContext
 ├─ StorySegment
 │   ├─ Characters (introduced + status)
 │   ├─ Locations (introduced + status)
 │   └─ Choice(s)
 └─ User (optional)
```

## 📝 Notes on Story Structure

* Each story has exactly one start segment (referenced by `start_segment_id`)
* The start segment has `from_choice_id` set to `null`
* All other segments are reached through choices
* Each segment maintains a backlink to its parent story via `story_id`
* The story structure forms a directed graph where:
  - Nodes are StorySegments
  - Edges are Choices
  - The start segment is the entry point
  - Multiple paths can lead to the same segment
