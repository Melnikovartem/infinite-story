## 🗂️ Project Structure

```
infinite_story/
├── backend/                 # All backend logic (Python)
│   ├── app/                 # Core application logic
│   │   ├── main.py          # CLI entry point
│   │   ├── engine/          # Story engine: runner, AI generator
│   │   ├── models/          # Typed data models (Story, Segment, etc.)
│   │   └── utils/           # Prompt builders, CLI helpers
│   ├── data/                # JSON files as temporary storage
│   ├── tests/               # Unit tests for backend logic
│   ├── requirements.txt     # Python dependencies
│   └── mypy.ini             # Type checker config
│
├── frontend/                # Placeholder for future web interface
│   ├── src/                 # React/Vue app code
│   └── public/              # Static assets
│
├── docs/                    # Project documentation
│   ├── mvp_plan.md
│   ├── architecture.md
│   └── models_overview.md
│
├── README.md                # Project overview
└── .gitignore
```

---

## 🧰 Tech Stack

### 🐍 **Backend**

* **Language**: Python 3.10+
* **Framework**: Flask (planned), CLI-based for MVP
* **Typing**: `mypy` with strong typing (`dataclasses` or `pydantic`)
* **Storage**: JSON files (for now) as makeshift database
* **Testing**: `unittest` or `pytest`

### 🌐 **Frontend** *(planned)*

* Framework: React or Vue (Vite-based setup)
* Assets: Optional AI-generated images per segment
* Communication: REST API (Flask backend)

### 📄 **Documentation**

* Markdown docs in `/docs`
* Structure: MVP plan, architecture, models, future roadmap

