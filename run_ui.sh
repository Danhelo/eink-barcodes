#!/bin/bash

# Kill any existing Xvfb processes
pkill Xvfb || true

# Start Xvfb with specific display and error handling
Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!
export DISPLAY=:99

# Wait for Xvfb to start and verify it's running
sleep 2
if ! ps -p $XVFB_PID > /dev/null; then
    echo "Error: Failed to start Xvfb"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure required packages are installed
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

if ! python3 -c "import PyQt5" >/dev/null 2>&1; then
    echo "Error: PyQt5 is required but not installed"
    echo "Please install with: pip install PyQt5"
    exit 1
fi

# Run the UI application with error handling
python3 app_ui.py
UI_EXIT_CODE=$?

# Cleanup
kill $XVFB_PID || pkill Xvfb

# Exit with the UI's exit code
exit $UI_EXIT_CODE
