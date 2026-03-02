#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_help() {
    echo -e "${CYAN}Infinite Story Engine${NC}"
    echo ""
    echo "Usage: ./run.sh [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  run-story [story_id]          Play a story (default command)"
    echo "  create-story-ai [id]          Create story with AI generation (NEW!)"
    echo "  list-stories                  List all available stories"
    echo "  delete-story [story_id]       Delete a story"
    echo "  clear-state [story_id]        Reset story to beginning"
    echo "  test-generation [story_id]    Test AI generation on a story"
    echo ""
    echo "Options for run-story:"
    echo "  --mode [immersive|debug]      Display mode (default: immersive)"
    echo "  --resume                      Resume from previous session"
    echo ""
    echo "Options for create-story-ai:"
    echo "  --title TEXT                  Story title (required)"
    echo "  --description TEXT            Story description (required)"
    echo "  --genre TEXT                  Genre like Fantasy, Sci-Fi, etc (required)"
    echo "  --world TEXT                  Optional: world vision (AI expands if empty)"
    echo "  --scene TEXT                  Optional: opening scene direction (AI creates if empty)"
    echo ""
    echo "Examples:"
    echo "  ./run.sh                                    # Play default story"
    echo "  ./run.sh my_story --mode debug              # Play with debug output"
    echo "  ./run.sh my_story --resume                  # Resume previous session"
    echo "  ./run.sh create-story-ai my_story --title \"Lost City\" --description \"An ancient city awakens\" --genre \"Adventure\""
    echo "  ./run.sh create-story-ai my_story --title \"Lost City\" --description \"An ancient city awakens\" --genre \"Adventure\" --world \"Tech and nature merged\""
    echo "  ./run.sh list-stories                       # List all stories"
    echo ""
}

# Show help if requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ] || [ "$1" = "help" ]; then
    print_help
    exit 0
fi

# Determine if first arg is a command or story name
COMMAND="run-story"
STORY_NAME="veil_of_thornreach"
REMAINING_ARGS=()

if [ $# -gt 0 ]; then
    case "$1" in
        run-story|create-story-ai|list-stories|delete-story|clear-state|test-generation)
            COMMAND="$1"
            shift
            REMAINING_ARGS=("$@")
            ;;
        *)
            # Assume first arg is story name for run-story
            STORY_NAME="$1"
            shift
            REMAINING_ARGS=("$@")
            ;;
    esac
fi

VENV_DIR="$SCRIPT_DIR/backend/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/backend/requirements.txt"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_message "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" > /dev/null 2>&1
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install requirements if needed
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_message "Installing requirements..."
    if ! pip install -r "$REQUIREMENTS_FILE" > /dev/null 2>&1; then
        print_error "Failed to install requirements!"
        pip install -r "$REQUIREMENTS_FILE"  # Show error output
        exit 1
    fi
else
    print_warning "Requirements file not found at $REQUIREMENTS_FILE"
fi

cd "$SCRIPT_DIR/backend"

# Enable unbuffered output to prevent hanging on terminal I/O
export PYTHONUNBUFFERED=1
export PYTHONPATH="$SCRIPT_DIR/backend"

# Handle run-story command specifically (check if story exists)
if [ "$COMMAND" = "run-story" ]; then
    print_message "Checking if story '$STORY_NAME' exists..."
    python -c "
from app.models.story import Story
story_ids = Story.list_stories()
if '$STORY_NAME' not in story_ids:
    exit(1)
"
    
    # Check if the Python command failed
    if [ $? -ne 0 ]; then
        if [ "$STORY_NAME" = "veil_of_thornreach" ]; then
            print_warning "Story '$STORY_NAME' does not exist! Setting up example stories..."
            if ! python scripts/setup_example_stories.py > /dev/null 2>&1; then
                print_error "Failed to create example stories!"
                python scripts/setup_example_stories.py  # Show error output
                exit 1
            fi
            print_message "Example stories created successfully!"
        else
            print_error "Story '$STORY_NAME' does not exist!"
            print_message "Use './run.sh list-stories' to see available stories"
            print_message "Use './run.sh create-story my_story --title \"Title\" --description \"...\" --genre \"Genre\"' to create a new story"
            exit 1
        fi
    fi
    
    # Run the story with remaining arguments
    print_message "Starting the story CLI..."
    python -u -m app.cli run-story "$STORY_NAME" "${REMAINING_ARGS[@]}"
else
    # Run other commands directly
    case "$COMMAND" in
        create-story-ai)
            print_message "🤖 Creating story with AI generation..."
            python -u -m app.cli create-story-ai "${REMAINING_ARGS[@]}"
            ;;
        list-stories)
            print_message "Listing available stories..."
            python -u -m app.cli list-stories
            ;;
        delete-story)
            if [ -z "$STORY_NAME" ] || [ "$STORY_NAME" = "veil_of_thornreach" ]; then
                print_error "Please specify a story ID to delete"
                exit 1
            fi
            print_message "Deleting story '$STORY_NAME'..."
            python -u -m app.cli delete-story "$STORY_NAME"
            ;;
        clear-state)
            if [ -z "$STORY_NAME" ] || [ "$STORY_NAME" = "veil_of_thornreach" ]; then
                STORY_NAME="${REMAINING_ARGS[0]:-veil_of_thornreach}"
            fi
            print_message "Clearing state for story '$STORY_NAME'..."
            python -u -m app.cli clear-state "$STORY_NAME"
            ;;
        test-generation)
            if [ -z "$STORY_NAME" ] || [ "$STORY_NAME" = "veil_of_thornreach" ]; then
                STORY_NAME="${REMAINING_ARGS[0]:-veil_of_thornreach}"
            fi
            print_message "Testing generation for story '$STORY_NAME'..."
            python -u -m app.cli test-generation "$STORY_NAME"
            ;;
    esac
fi

# Deactivate virtual environment
deactivate