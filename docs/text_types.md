

### 📘 **Narrative Structure**

| `text_type`           | Description                          | Example Text                                |
| --------------------- | ------------------------------------ | ------------------------------------------- |
| `narrator_describing` | Describes setting, action, events    | *The sun dipped behind the hills.*          |
| `narrator_commentary` | Subjective or meta narrator opinions | *And so, fate played its hand again.*       |
| `flashback`           | Narration flagged as a memory        | *Years ago, in a quieter time...*           |
| `dream_sequence`      | Used for surreal/dreamlike segments  | *He was flying, but the ground never left.* |

---

### 🗣️ **Dialogue & Internal**

| `text_type`         | Description                             | Example Text                                 |
| ------------------- | --------------------------------------- | -------------------------------------------- |
| `character_speech`  | Spoken dialogue by a character          | *"What are you doing here?"*                 |
| `character_thought` | Internal monologue or unspoken thoughts | *I don’t trust him at all.*                  |
| `poem_or_song`      | Stylized lyrics or verses               | *"Twinkle, twinkle, little star..."*         |
| `letter_or_note`    | Written in-world content                | *Dear diary, today I saw something strange.* |

---

### 🔊 **Audio/Visual Cues**

| `text_type`     | Description                               | Example Text                         |
| --------------- | ----------------------------------------- | ------------------------------------ |
| `sfx`           | Sound effects written out                 | *BANG! The door slammed shut.*       |
| `visual_cue`    | Description of visual transitions/actions | *\[The screen fades to black]*       |
| `media_overlay` | Cue to show media like image/video/music  | *\[Play: ambient\_forest\_loop.mp3]* |

---

### 🗺️ **UI & Meta Text**

| `text_type`      | Description                     | Example Text                       |
| ---------------- | ------------------------------- | ---------------------------------- |
| `scene_title`    | Title of a new chapter or scene | *Chapter 4: The Awakening*         |
| `location_label` | Label for current location      | *Abandoned Temple — Inner Sanctum* |
| `system_message` | In-game or meta system text     | *You have unlocked a new memory.*  |

---

### ✅ Tips for Usage

* Keep each entry focused and mutually exclusive.
* You can use additional fields like `character`, `emotion`, `visual_asset`, or `sound_asset` depending on your engine needs.
* If rendering as a visual novel, many engines (Ren’Py, for example) already differentiate between narration and speech with minor syntax differences — this schema just formalizes it for JSON-driven engines.
