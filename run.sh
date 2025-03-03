#!/bin/bash
# File: run.sh
set -e

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
# CHANGED: Added --system-site-packages flag to access system PyQt5
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with system packages..."
    python3 -m venv --system-site-packages venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
if [ ! -f ".requirements_installed" ]; then
    echo "Installing requirements..."
    # ADDED: Skip trying to reinstall PyQt5 via pip
    grep -v "PyQt" requirements.txt > requirements_filtered.txt
    pip install -r requirements_filtered.txt
    touch .requirements_installed
fi

# Create examples directory if it doesn't exist
mkdir -p examples

# Check if there are any images in the examples directory
if [ -z "$(find examples -maxdepth 1 -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" 2>/dev/null)" ]; then
    echo "No images found in examples directory. Creating a sample image..."
    
    # Run a simple Python script to create one sample image
    python -c "
from PIL import Image
import os

# Create directory if it doesn't exist
os.makedirs('examples', exist_ok=True)

# Create a simple test image
img = Image.new('L', (200, 100), 255)  # White background
for x in range(0, 200, 10):
    for y in range(100):
        if x % 20 < 10:
            img.putpixel((x, y), 0)
img.save('examples/sample_barcode.png')
print('Created sample image: examples/sample_barcode.png')
"
fi

# Parse command line arguments
GUI_MODE=true
VIRTUAL_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --cli)
            GUI_MODE=false
            shift
            ;;
        --virtual)
            VIRTUAL_MODE=true
            shift
            ;;
        *)
            # Pass remaining arguments to the application
            break
            ;;
    esac
done

# ADDED: Debug information
echo "Debug info:"
which python
python -c "import sys; print(sys.path)"
echo "Attempting to import PyQt5..."
python -c "import PyQt5; print('PyQt5 found at:', PyQt5.__file__)"

# Run the application
if [ "$GUI_MODE" = true ]; then
    echo "Starting E-ink Barcode Testing GUI..."
    if [ "$VIRTUAL_MODE" = true ]; then
        python scripts/run_app.py --virtual "$@"
    else
        python scripts/run_app.py "$@"
    fi
else
    echo "Starting E-ink Barcode Testing CLI..."
    if [ "$VIRTUAL_MODE" = true ]; then
        python scripts/run_cli.py --virtual "$@"
    else
        python scripts/run_cli.py "$@"
    fi
fi