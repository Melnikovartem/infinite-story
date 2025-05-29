## 🧩 Core MVP Objects (Detailed)

### 🧠 **Story**

* `id`
* `title`
* `description` *(required)*
* `genre` *(optional)*
* `user_id`
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
* `story_id`
* `from_choice_id`
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
* `text`: `string` (e.g., “Open the door”)
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
 ├─ StoryContext
 ├─ StorySegment
 │   ├─ Characters (introduced + status)
 │   ├─ Locations (introduced + status)
 │   └─ Choice(s)
 └─ User (optional)
```
