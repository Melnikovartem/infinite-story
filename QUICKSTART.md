# 🚀 Quick Start - Infinite Story Engine

Get up and running in 3 minutes!

## Step 1: Setup (First Time Only)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup your API key
cp .env.example .env
nano .env  # Or use any text editor
```

**Edit `.env` and add your OpenAI API key:**
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 2: Run the Story

```bash
# From project root
./run.sh

# OR from backend directory
PYTHONPATH=. python -m app.cli run-story
```

## Step 3: Play!

You'll see a menu like this:

```
================================================================================

The Last Sanctuary

The ancient trees of Thornreach Grove sway gently...

================================================================================

What would you like to do?
1. Investigate the weakening wards with Eira and Brother Cellen
2. Venture into The Veil to understand its nature
3. Show all options
4. Write your own choice
5. Save and exit
6. Exit without saving

Select an option:
```

### Options Explained

- **1-2**: Quick choices (most popular paths)
- **3**: See ALL available choices
- **4**: Write your own action (AI generates what happens!)
- **5**: Save progress and quit
- **6**: Quit without saving

## 🎮 Tips for Playing

### Writing Custom Choices

When you select option 4, you can type anything:

```
Enter your choice: Ask Nyx about the Memory Weaver's whereabouts
```

The AI will:
1. Read the entire story context
2. Understand character personalities
3. Generate a new scene based on your choice
4. Create 2 new choices for what to do next

### Auto-Save

Don't worry about losing progress! The system auto-saves:
- ✅ After every AI-generated scene
- ✅ When you manually choose "Save and exit"

### Resuming

Next time you run the story, it automatically resumes where you left off!

```
Resuming from saved state...
Resumed at segment: A mysterious room reveals its secrets
```

## 🔧 Troubleshooting

### "OPENAI_API_KEY environment variable is required"

**Fix:** Create `.env` file in `backend/` directory:
```bash
cd backend
cp .env.example .env
# Edit .env with your API key
```

### "No stories available"

**Fix:** Run the story creation script:
```bash
cd backend
python scripts/save_story.py
```

### "Failed to generate content"

**Check:**
- ✓ API key is valid
- ✓ You have OpenAI credits
- ✓ Internet connection is working

### Tests failing

**Fix:** Make sure virtual environment is activated:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -m pytest
```

## 📊 What Happens Behind the Scenes

```
You write: "Ask Nyx about the Memory Weaver"
    ↓
AI receives full context:
  - Story worldbuilding
  - Last 10 scenes
  - All character backgrounds
  - Current location state
  - Your choice
    ↓
AI generates:
  - New scene description
  - Character dialogue
  - Scene atmosphere
  - 2 new choices
    ↓
System saves everything
    ↓
You continue playing!
```

## 🎯 Example Session

```bash
$ ./run.sh

Available Stories
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID                  ┃ Title                  ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ veil_of_thornreach  │ The Veil of Thornreach │
└─────────────────────┴────────────────────────┘

Select a story ID: veil_of_thornreach

Starting story: The Veil of Thornreach
Story started successfully!

[Scene displays...]

What would you like to do?
1. Investigate the weakening wards
2. Venture into The Veil

Select an option: 4
Enter your choice: Try to commune with the ancient trees

⠋ Generating next scene...
Scene generated successfully!

[New AI-generated scene appears...]
```

## 🎨 Customization

### Change AI Model

Edit `.env`:
```bash
OPENAI_MODEL=gpt-4o  # More creative, more expensive
# or
OPENAI_MODEL=gpt-4o-mini  # Faster, cheaper (default)
```

### Adjust Creativity

Edit `.env`:
```bash
OPENAI_TEMPERATURE=0.9  # More random/creative
# or
OPENAI_TEMPERATURE=0.5  # More consistent/conservative
```

### Longer Responses

Edit `.env`:
```bash
OPENAI_MAX_TOKENS=3000  # Longer scenes (default: 2000)
```

## 📚 Learn More

- **Full Guide**: `backend/README.md`
- **Architecture**: `CLAUDE.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`

## 🎉 You're Ready!

The infinite story awaits. Every choice you make creates a new branch in the narrative tree. Have fun exploring! 🌳✨
