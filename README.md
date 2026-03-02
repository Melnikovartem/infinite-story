# Infinite Story Engine

An infinite interactive storytelling engine where users explore branching narratives in a modular story world. AI generates story content dynamically as users make choices, creating an endlessly expanding narrative tree.

## How It Works

A story is a directed graph. Nodes are **segments** (scenes), edges are **choices** (decisions). When a user picks a choice that leads nowhere yet, the AI generates a new segment -- extending the tree infinitely.

At each segment, the user sees:

1. The **2 most popular choices** (quick picks)
2. An option to **view all available choices**
3. An option to **write their own choice** (AI generates what happens)

The AI receives full context when generating: worldbuilding rules, the last N scenes, character states, location states, and the user's choice. It produces a new scene with typed text blocks (narration, dialogue, sound effects, etc.) and 2 new choices to continue from.

## Quick Start

```bash
# setup
make setup                    # install deps + create .env
nano backend/.env             # add your API key (see SETUP.md)

# run (web app - backend + frontend)
make start                    # backend on :8000, frontend on :5173

# run (CLI only)
./run.sh                      # or: ./run.sh <story_name>
```

See [SETUP.md](SETUP.md) for full setup instructions including API key configuration.

## Project Structure

```
infinite_story/
├── backend/                  # Python 3.13+ / FastAPI / Pydantic
│   ├── app/
│   │   ├── models/           # Data models (Story, Segment, Choice, etc.)
│   │   ├── engine/           # Story runner + AI generators
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Auto-save, etc.
│   │   ├── utils/            # Prompt builder, error handling, debug
│   │   ├── cli.py            # Typer CLI
│   │   └── main.py           # FastAPI app
│   ├── tests/                # pytest test suite
│   ├── scripts/              # Story creation scripts
│   └── .infinite_story_data/ # JSON file storage (runtime data)
│
├── frontend/                 # React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── components/       # UI components
│       ├── pages/            # Route pages
│       ├── contexts/         # React context (story state)
│       ├── services/         # API client
│       └── types/            # TypeScript types
│
├── docs/                     # Additional documentation
├── ARCHITECTURE.md           # Technical overview & abstractions
├── SETUP.md                  # Setup & configuration guide
└── AGENTS.md                 # AI agent instructions (Claude Code)
```

## Documentation

| Doc | What it covers |
|-----|----------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Data model hierarchy, storage system, AI generation flow, story graph |
| [SETUP.md](SETUP.md) | Installation, configuration, API keys, running, troubleshooting |
| [docs/api.md](docs/api.md) | REST API endpoint reference with request/response examples |
| [docs/text_types.md](docs/text_types.md) | All 13 text block types (narration, dialogue, SFX, etc.) |
| [docs/text_story_example.md](docs/text_story_example.md) | Full example scene using all text block types |
| [AGENTS.md](AGENTS.md) | Instructions for AI coding agents working on this codebase |

## Tech Stack

- **Backend**: Python 3.13+, FastAPI, Pydantic, Typer + Rich (CLI)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **AI**: OpenRouter (recommended, multi-model) or OpenAI direct
- **Storage**: JSON files on disk (no database yet)
- **Testing**: pytest (backend), Vitest (frontend)
