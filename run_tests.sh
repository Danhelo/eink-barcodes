#!/bin/bash

# Exit on any error
set -e

echo "Starting test suite setup and execution..."

# Function to print section headers
print_header() {
    echo
    echo "=== $1 ==="
    echo
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo "✓ $1 successful"
    else
        echo "✗ $1 failed"
        exit 1
    fi
}

# Ensure we're in the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Install pytest and test dependencies directly
print_header "Installing test dependencies"
pip install pytest pytest-qt pytest-cov pytest-asyncio --break-system-packages #remove arg if not in the RPi
check_success "Test dependencies installation"

# Set QT_QPA_PLATFORM for headless testing if no display is available
if [ -z "${DISPLAY}" ]; then
    export QT_QPA_PLATFORM=offscreen
    echo "Set QT_QPA_PLATFORM=offscreen for headless testing"
fi

# Run the tests
print_header "Running tests"
python3 -m pytest \
    --verbose \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    -v \
    src/tests/
check_success "Test execution"

print_header "Test Results"
echo "Coverage report has been generated in htmlcov/index.html"
