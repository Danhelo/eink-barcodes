# E-ink Barcode Application CLI Usage Guide

This document provides instructions for using the command-line interface (CLI) of the E-ink Barcode Application. The CLI offers the same functionality as the GUI, allowing you to run barcode tests and generate barcodes through a terminal or SSH connection.

## Quick Start

The application can be run in CLI mode using either `app.py` directly or through the `run.sh` script:

```bash
# Using app.py directly
./app.py quick-test --type code128 --rotate 45

# Using run.sh script
./run.sh --cli quick-test --type code128 --rotate 45
```

## Available Commands

The CLI supports three main commands, matching the functionality of the GUI tabs:

1. **quick-test**: Run a simple test with basic options (similar to Quick Test page)
2. **custom-test**: Run a test with advanced options (similar to Custom Test page)
3. **generate**: Generate barcodes using the AWS API (similar to Generate Barcodes page)

## Common Options

These options apply to all commands:

```
--virtual       Use virtual display instead of hardware
--help          Show help for the command
```

## Quick Test Command

Run a quick test with simplified controls:

```bash
./app.py quick-test [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Barcode type (code128, upca, upce, datamatrix, qrcode) | code128 |
| `--directory DIR` | Directory containing test images | examples |
| `--rotate ANGLE` | Rotation angle in degrees | 0 |
| `--scale-type TYPE` | Scaling type: relative or absolute | relative |
| `--scale-factor FACTOR` | Scale factor in percent | 100% |
| `--scale-width WIDTH` | Width in mm for absolute scaling | 20mm |
| `--delay DELAY` | Delay between images in seconds | 0.5 |

Example:
```bash
./app.py quick-test --type datamatrix --rotate 90 --scale-factor 150
```

## Custom Test Command

Run a custom test with advanced options:

```bash
./app.py custom-test [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--files FILE [FILE...]` | Specific image files to test | None |
| `--directory DIR` | Directory containing test images | examples |
| `--rotate ANGLE` | Rotation angle in degrees | 0 |
| `--scale-type TYPE` | Scaling type: relative or absolute | relative |
| `--scale-factor FACTOR` | Scale factor | 1.0 |
| `--scale-width WIDTH` | Width in mm for absolute scaling | 20mm |
| `--mirror` | Mirror images horizontally | False |
| `--center` | Auto-center images on display | False |
| `--delay DELAY` | Delay between images in seconds | 1.0 |
| `--repetitions NUM` | Number of repetitions | 1 |

Example:
```bash
./app.py custom-test --files examples/Code128/*.png --rotate 45 --mirror --center --repetitions 3
```

## Generate Command

Generate barcodes using AWS API:

```bash
./app.py generate [OPTIONS]
```

The generate command requires either `--type` (for single type) or `--multi-types` (for multiple types):

| Option | Description | Default |
|--------|-------------|---------|
| `--type TYPE` | Barcode type for single type generation | Required |
| `--quantity NUMBER` | Number of barcodes to generate | 10 |
| `--multi-types TYPE:QTY [TYPE:QTY ...]` | Multiple barcode types with quantities | None |
| `--prefix PREFIX` | Prefix for barcode values | None |
| `--transform EFFECT` | Transformation effect (none, blur) | none |
| `--dpi DPI` | DPI for generated barcodes (72, 150, 300, 600) | 300 |
| `--output-dir DIR` | Output directory | examples |

Examples:
```bash
# Generate 20 code128 barcodes
./app.py generate --type code128 --quantity 20

# Generate multiple types of barcodes with prefixes
./app.py generate --multi-types code128:10 datamatrix:5 --prefix test --transform blur --output-dir ./generated
```

## SSH / Remote Usage

The CLI mode is designed to work over SSH connections, making it ideal for remote operations:

```bash
# Connect via SSH and run a quick test
ssh user@remote-machine "cd /path/to/app && ./app.py quick-test --type code128 --virtual"

# Run a test and save results to a file
ssh user@remote-machine "cd /path/to/app && ./app.py custom-test --files examples/*.png --virtual" > test_results.txt
```

## Scripting Examples

The CLI is designed to be easily used in scripts:

```bash
#!/bin/bash
# Example script to test multiple barcode types

TYPES=("code128" "datamatrix" "upca" "upce")

for type in "${TYPES[@]}"; do
    echo "Testing $type barcodes..."
    ./app.py quick-test --type $type --rotate 0 --virtual
    ./app.py quick-test --type $type --rotate 90 --virtual
    echo "-----------------------"
done
```

## Return Codes

The CLI commands return standard exit codes:
- 0: Success
- 1: Error (initialization failed, test failed, etc.)

You can use these codes in scripts to check if operations were successful:

```bash
./app.py generate --type code128 --quantity 5
if [ $? -eq 0 ]; then
    echo "Generation successful"
else
    echo "Generation failed"
fi
```
