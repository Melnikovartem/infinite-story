#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Set default story name if not provided
STORY_NAME="${1:-veil_of_thornreach}"
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

# Check if story exists
print_message "Checking if story '$STORY_NAME' exists..."
cd "$SCRIPT_DIR/backend"
python -c "
from app.models.story import Story
story_ids = Story.list_stories()
if '$STORY_NAME' not in story_ids:
    exit(1)
"

# Check if the Python command failed
if [ $? -ne 0 ]; then
    if [ "$STORY_NAME" = "veil_of_thornreach" ]; then
        print_warning "Story '$STORY_NAME' does not exist! Running save_story.py..."
        if ! python scripts/save_story.py > /dev/null 2>&1; then
            print_error "Failed to create story using save_story.py!"
            python scripts/save_story.py  # Show error output
            exit 1
        fi
        print_message "Story created successfully!"
    else
        print_error "Story '$STORY_NAME' does not exist!"
        exit 1
    fi
fi

# Run the CLI with proper terminal handling
print_message "Starting the story CLI..."
cd "$SCRIPT_DIR/backend"  # Go to backend directory

# Enable unbuffered output to prevent hanging on terminal I/O
export PYTHONUNBUFFERED=1

# Run with stdin/stdout properly connected to terminal
# Pass the story name if provided
PYTHONPATH="$SCRIPT_DIR/backend" python -u -m app.cli run-story "$STORY_NAME"

# Deactivate virtual environment
deactivate 