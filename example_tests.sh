#!/bin/bash
# example_tests.sh - Example script for automating barcode tests using the CLI
#
# This script demonstrates how to:
# 1. Generate multiple types of barcodes
# 2. Run tests with various configurations on the generated barcodes
# 3. Log results for later analysis

# Set up logging
LOG_FILE="test_results_$(date +%Y%m%d_%H%M%S).log"
echo "Starting E-ink barcode tests at $(date)" > "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

# Function to log messages
log() {
    echo "[$(date +%H:%M:%S)] $1"
    echo "[$(date +%H:%M:%S)] $1" >> "$LOG_FILE"
}

# Function to run a test and log the result
run_test() {
    local test_name="$1"
    local command="$2"
    
    log "Running test: $test_name"
    log "Command: $command"
    
    # Run the command and capture output
    output=$(eval "$command" 2>&1)
    exit_code=$?
    
    # Log the result
    if [ $exit_code -eq 0 ]; then
        log "✓ Test PASSED: $test_name"
    else
        log "✗ Test FAILED: $test_name"
    fi
    
    # Log the output
    echo "Output:" >> "$LOG_FILE"
    echo "$output" >> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"
    
    return $exit_code
}

# Create test directories
mkdir -p test_results/code128
mkdir -p test_results/datamatrix

# Step 1: Generate test barcodes
log "Generating barcodes for testing..."
run_test "Generate Code128 barcodes" \
    "./app.py generate --type code128 --quantity 5 --output-dir test_results/code128 --virtual"

run_test "Generate DataMatrix barcodes" \
    "./app.py generate --type datamatrix --quantity 5 --output-dir test_results/datamatrix --virtual"

# Step 2: Run Quick Tests with different barcode types
log "Running Quick Tests with different barcode types..."
for type in code128 datamatrix; do
    run_test "Quick Test - $type standard" \
        "./app.py quick-test --type $type --directory test_results/$type --virtual"
    
    run_test "Quick Test - $type rotated" \
        "./app.py quick-test --type $type --directory test_results/$type --rotate 90 --virtual"
done

# Step 3: Run Custom Tests with various configurations
log "Running Custom Tests with various transformations..."

# Test with mirroring
run_test "Custom Test - With mirroring" \
    "./app.py custom-test --directory test_results/code128 --mirror --center --virtual"

# Test with absolute sizing
run_test "Custom Test - Absolute sizing" \
    "./app.py custom-test --directory test_results/datamatrix --scale-type absolute --scale-width 30 --virtual"

# Test with repetitions
run_test "Custom Test - With repetitions" \
    "./app.py custom-test --directory test_results/code128 --repetitions 2 --delay 0.2 --virtual"

# Final summary
passed=$(grep "PASSED" "$LOG_FILE" | wc -l)
failed=$(grep "FAILED" "$LOG_FILE" | wc -l)
total=$((passed + failed))

log "Testing complete!"
log "Summary: $passed/$total tests passed, $failed failed"
log "Full results available in $LOG_FILE"

exit 0
