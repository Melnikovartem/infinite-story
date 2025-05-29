## 🧪 MVP: Infinite Interactive Story Engine

We are building an **infinite interactive storytelling engine**, where **any user can explore any narrative branch** in a digitalized story world made up of modular blocks.

### 🎯 Goals

* Create endlessly branching stories using AI
* Let users **explore**, **continue**, or **create** parts of the story
* **Structure the story as reusable data blocks** (characters, choices, locations, etc.)

---

## 🛠️ MVP Tech Stack

* **Backend**: Python with **Flask**
* **Typing**: Strong typing with `mypy` support
* **Storage**: Raw `.json` files for now (no DB yet)
* **Interface**: **Terminal-based** CLI interaction

---

## 🧩 Story Interaction Flow

When a user reaches a `StorySegment`, they are presented with:

1. 🔝 The **2 most popular choices**
2. 📜 An option to **view all available choices**
3. ✍️ An option to **write a new choice**

Choices connect segments and drive story progression. Segments include AI-generated `text_blocks` and updated state for characters and locations.

---

## 🔮 Next Step Ideas

| Feature                | Description                                              |
| ---------------------- | -------------------------------------------------------- |
| 🌐 Web UI              | Build a browser-based interface with AI-generated images |
| 🗃️ DB Storage         | Transition from JSON files to a proper database          |
| 🧠 Multi-model support | Plug in different LLMs and compare results               |
| 🔒 User accounts       | Add login, track saved stories and segments              |
| 🚫 Usage limits        | Limit generations for anonymous users                    |

---

Let me know if you'd like:

* A file/folder layout suggestion
* Terminal interaction sample code
* Type-safe Python model definitions (with `pydantic` or `dataclasses`)
