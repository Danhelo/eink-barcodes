#!/bin/bash
# Run test suite with coverage

# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create test report directory
mkdir -p test_reports

# Run tests with coverage
python3 wasabi-toolbag/tools/test_runner.py \
  --test-dir tests \
  --report-dir test_reports \
  --verbose
