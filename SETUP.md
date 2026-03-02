# Setup Guide

## Prerequisites

- Python 3.13+
- Node.js 18+ and npm
- An API key from [OpenRouter](https://openrouter.ai) (recommended) or [OpenAI](https://platform.openai.com)

## Installation

### Using Make (recommended)

```bash
make setup
```

This installs backend (pip) and frontend (npm) dependencies and creates `backend/.env` from the example file.

### Manual

```bash
# backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# frontend
cd ../frontend
npm install
```

## Configuration

Edit `backend/.env` with your API key and preferences:

```bash
# Provider: "openrouter" (recommended) or "openai"
AI_PROVIDER=openrouter

# OpenRouter (if AI_PROVIDER=openrouter)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
AI_MODEL=deepseek-v3

# OpenAI (if AI_PROVIDER=openai)
OPENAI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o-mini

# Generation tuning
AI_TEMPERATURE=0.7          # 0.0 = deterministic, 1.0+ = creative
AI_MAX_TOKENS=2000           # longer = more detailed scenes
```

### Model Options

| Model | Provider | Speed | Quality | Cost |
|-------|----------|-------|---------|------|
| `deepseek-v3` | OpenRouter | Fast | Excellent | Cheap |
| `gpt-4-turbo` | OpenRouter/OpenAI | Moderate | Excellent | Moderate |
| `gpt-3.5-turbo` | OpenRouter/OpenAI | Very fast | Good | Cheap |
| `claude-3-opus` | OpenRouter | Moderate | Excellent | Expensive |
| `gpt-4o-mini` | OpenAI | Fast | Good | Cheap |

Switch models by changing `AI_MODEL` in `.env` -- no code changes needed.

CLI helper: `cd backend && python -m app.cli list-models`

## Running

### Web App (backend + frontend)

```bash
make start
```

- Backend API: http://localhost:8000 (Swagger docs at /docs)
- Frontend: http://localhost:5173

```bash
make stop              # stop all processes
make logs              # view logs
```

### CLI Only

```bash
./run.sh                       # run default story
./run.sh <story_name>          # run specific story
```

Or directly:
```bash
cd backend
source venv/bin/activate
PYTHONPATH=. python -m app.cli run-story
```

### CLI Gameplay

```
What would you like to do?
1. Investigate the weakening wards      # quick pick (top 2)
2. Venture into The Veil                # quick pick (top 2)
3. Show all options                     # see all choices
4. Write your own choice                # AI generates what happens
5. Save and exit
6. Exit without saving
```

Writing a custom choice sends the full story context to the AI, which generates a new scene and 2 new choices. Progress auto-saves after each generated scene and resumes automatically next time.

## Testing

```bash
make test                                        # all backend tests
cd backend && python -m pytest tests/ -v         # verbose
cd backend && python -m pytest tests/test_story_models.py  # specific file
```

## Creating New Stories

Run the included story creation scripts:

```bash
cd backend
source venv/bin/activate
python scripts/save_story.py            # The Veil of Thornreach
python scripts/save_story_pirate.py     # Pirate story
python scripts/save_story_scifi.py      # Sci-fi story
```

## Troubleshooting

**"OPENROUTER_API_KEY not found"** / **"OPENAI_API_KEY not found"**
- Check `backend/.env` exists and has the correct key set
- Make sure `AI_PROVIDER` matches which key you've configured

**"No stories available"**
- Run `cd backend && python scripts/save_story.py` to create the default story

**"Failed to generate content"**
- Verify your API key is valid and has credits
- Check internet connection
- Try a different model: `AI_MODEL=gpt-3.5-turbo`

**Port already in use**
- `lsof -i :8000` then `kill -9 <PID>` (same for :5173)
- Or: `make stop` to kill all related processes

**Stories too short / repetitive**
- Increase `AI_MAX_TOKENS=3000`
- Increase `AI_TEMPERATURE=0.9`
- Try a different model

## Make Commands Reference

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies + create .env |
| `make start` | Start backend + frontend |
| `make stop` | Stop all processes |
| `make test` | Run backend tests |
| `make logs` | View all logs |
| `make backend-start` | Start backend only (port 8000) |
| `make frontend-start` | Start frontend only (port 5173) |
| `make clean` | Remove venv, node_modules, caches |
