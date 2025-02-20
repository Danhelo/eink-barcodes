#!/bin/bash

# Ensure Python environment is activated
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set Mac-specific environment variables
export QT_MAC_WANTS_LAYER=1
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Check if running from terminal
if [ -t 0 ]; then
    echo "Running from terminal"
    # Run with debug output
    python app_ui.py
else
    echo "Running from GUI"
    # Run without debug output
    pythonw app_ui.py
fi
