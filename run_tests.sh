#!/bin/bash
# File: run_tests.sh
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

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

# Run tests with coverage
echo "Running tests with coverage..."
# Use --virtual for tests to ensure they run in any environment
pytest tests/ -v --cov=src --cov-report=term

# Run core test example with hardware display (now default)
echo -e "\nRunning core test example with rotation and scaling on hardware..."
python run_core_test.py --rotation 90 --scale 0.8 --delay 0.5

echo -e "\nAll tests completed successfully!"