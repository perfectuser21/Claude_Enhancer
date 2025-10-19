#!/usr/bin/env bash
# Code Quality Checker Bash Wrapper
# Provides a convenient shell interface to the Python-based code quality checker

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$PROJECT_ROOT/src/main.py"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}" >&2
    echo "Please install Python 3.8 or higher" >&2
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo -e "${RED}Error: Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher required${NC}" >&2
    exit 1
fi

# Check if virtual environment exists
VENV_PATH="$PROJECT_ROOT/venv"
if [[ ! -d "$VENV_PATH" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not found at $VENV_PATH${NC}"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"

    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r "$PROJECT_ROOT/requirements.txt"
    echo -e "${GREEN}Setup completed!${NC}"
else
    source "$VENV_PATH/bin/activate"
fi

# Run the Python script with all arguments
python3 "$PYTHON_SCRIPT" "$@"

# Capture and forward exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

exit $EXIT_CODE
