#!/bin/bash
# Setup development environment

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e .[test,dev]

# Create necessary directories
mkdir -p test_reports

echo "Environment setup complete. Activate it with: source venv/bin/activate"
