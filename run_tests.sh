#!/bin/bash
# Run test suite with coverage

# Ensure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Virtual environment not activated. Please run: source venv/bin/activate"
    exit 1
fi

# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run tests with pytest
pytest \
    --verbose \
    --cov=src \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-branch \
    tests/
