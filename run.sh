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
echo "  run-story [story_id]          Play a story (opens picker if no ID given)"
echo "  create-story-ai [id]          Create story with AI generation"
echo "  create-story-step [id]        Create story step-by-step (can skip/retry broken steps)"
echo "  list-stories                  List all available stories"
echo "  delete-story <story_id>       Delete a story"
echo "  clear-state <story_id>        Reset story to beginning"
    echo ""
    echo "Options for run-story:"
    echo "  --resume                      Resume from previous session"
    echo "  --auto-pick N                 Auto-select choice 1 for N turns (0=unlimited)"
    echo ""
    echo "Options for create-story-ai:"
    echo "  --title TEXT                  Story title (required)"
    echo "  --description TEXT            Story description (required)"
    echo "  --genre TEXT                  Genre like Fantasy, Sci-Fi, etc (required)"
    echo "  --world TEXT                  Optional: world vision (AI expands if empty)"
    echo "  --scene TEXT                  Optional: opening scene direction (AI creates if empty)"
    echo ""
    echo "Examples:"
    echo "  ./run.sh                                    # Open story picker"
    echo "  ./run.sh my_story                           # Play a story"
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
STORY_NAME=""
REMAINING_ARGS=()

if [ $# -gt 0 ]; then
    case "$1" in
        run-story|create-story-ai|create-story-step|list-stories|delete-story|clear-state|test-generation)
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

# Handle run-story command
if [ "$COMMAND" = "run-story" ]; then
    print_message "Starting the story CLI..."
    if [ -n "$STORY_NAME" ]; then
        python -u -m app.cli run-story "$STORY_NAME" "${REMAINING_ARGS[@]}"
    else
        # No story ID provided — CLI will open the story picker
        python -u -m app.cli run-story "${REMAINING_ARGS[@]}"
    fi
else
    # Run other commands directly
    case "$COMMAND" in
        create-story-ai)
            print_message "🤖 Creating story with AI generation..."
            python -u -m app.cli create-story-ai "${REMAINING_ARGS[@]}"
            ;;
        create-story-step)
            print_message "🔧 Creating story step-by-step..."
            python -u -m app.cli create-story-step "${REMAINING_ARGS[@]}"
            ;;
        list-stories)
            print_message "Listing available stories..."
            python -u -m app.cli list-stories
            ;;
        delete-story)
            if [ ${#REMAINING_ARGS[@]} -eq 0 ]; then
                print_error "Please specify a story ID to delete"
                exit 1
            fi
            print_message "Deleting story '${REMAINING_ARGS[0]}'..."
            python -u -m app.cli delete-story "${REMAINING_ARGS[@]}"
            ;;
        clear-state)
            if [ ${#REMAINING_ARGS[@]} -eq 0 ]; then
                print_error "Please specify a story ID to clear"
                exit 1
            fi
            print_message "Clearing state for story '${REMAINING_ARGS[0]}'..."
            python -u -m app.cli clear-state "${REMAINING_ARGS[@]}"
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            print_message "Run './run.sh --help' for available commands"
            exit 1
            ;;
    esac
fi

# Deactivate virtual environment
deactivate