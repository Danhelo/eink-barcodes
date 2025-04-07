#!/bin/bash
# File: run.sh
set -e

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing AWS CLI..."
    # Detect architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
        AWS_ZIP_URL="https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip"
    else
        AWS_ZIP_URL="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"
    fi
    
    curl "$AWS_ZIP_URL" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    
    # Clean up
    rm -rf aws awscliv2.zip
    
    echo "AWS CLI installed successfully."
    
    # Run AWS configure for credentials setup
    echo "Setting up AWS credentials..."
    aws configure
else
    echo "AWS CLI is already installed."
    
    # Check if AWS credentials are configured
    if [ ! -f ~/.aws/credentials ]; then
        echo "AWS credentials not found. Running aws configure..."
        aws configure
    else
        echo "AWS credentials already configured."
    fi
fi

# Check and install IT8951 package for Raspberry Pi if the folder exists and not already installed
if [ -d "IT8951" ] && [ ! -f ".it8951_installed" ]; then
    echo "Installing IT8951 Raspberry Pi dependencies..."
    pushd IT8951 > /dev/null
    pip install ./[rpi] --break-system-packages
    if [ $? -eq 0 ]; then
        echo "IT8951 installation successful."
        touch ../.it8951_installed
    else
        echo "Error: IT8951 installation failed."
        exit 1
    fi
    popd > /dev/null
elif [ -d "IT8951" ] && [ -f ".it8951_installed" ]; then
    echo "IT8951 already installed. Skipping installation."
else
    echo "Notice: IT8951 folder not found. Skipping IT8951 installation."
fi

# Install requirements if needed
if [ ! -f ".requirements_installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt --break-system-packages
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
COMMAND=""

# Display help function
show_help() {
    cat <<EOF
Usage: ./run.sh [OPTIONS] [COMMAND] [COMMAND_OPTIONS]

OPTIONS:
  --cli           Run in CLI mode (default: GUI mode)
  --virtual       Use virtual display instead of hardware
  --help          Show this help message

CLI COMMANDS:
  quick-test      Run a quick test with simplified controls
  custom-test     Run a custom test with advanced options
  generate        Generate barcodes using AWS API

Run './run.sh --cli COMMAND --help' for specific command options.
EOF
}

# Process options
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
        --help)
            show_help
            exit 0
            ;;
        quick-test|custom-test|generate)
            COMMAND=$1
            shift
            break
            ;;
        -*)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            # First non-option argument might be a command
            if [ -z "$COMMAND" ] && [[ "$GUI_MODE" == "false" ]]; then
                COMMAND=$1
                shift
            fi
            break
            ;;
    esac
done

# Run the application
if [ "$GUI_MODE" = true ]; then
    # GUI mode
    echo "Starting E-ink Barcode Testing GUI..."
    if [ "$VIRTUAL_MODE" = true ]; then
        python scripts/run_app.py --virtual "$@"
    else
        python scripts/run_app.py "$@"
    fi
else
    # CLI mode
    echo "Starting E-ink Barcode Testing CLI..."
    
    # If no command is specified, show help
    if [ -z "$COMMAND" ]; then
        python scripts/run_cli.py --help
        exit 1
    fi
    
    # Run the specified command
    if [ "$VIRTUAL_MODE" = true ]; then
        python scripts/run_cli.py --virtual "$COMMAND" "$@"
    else
        python scripts/run_cli.py "$COMMAND" "$@"
    fi
fi
