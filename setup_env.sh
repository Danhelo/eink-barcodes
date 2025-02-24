#!/bin/bash
# Setup script for E-Ink project environment

# Exit on error
set -e

# Function to check if running on Raspberry Pi
is_raspberry_pi() {
    if [ -f /sys/firmware/devicetree/base/model ]; then
        if grep -q "Raspberry Pi" /sys/firmware/devicetree/base/model; then
            return 0
        fi
    fi
    return 1
}

echo "Setting up E-Ink project environment..."

# Check Python version
REQUIRED_PYTHON="python3.11"
if command -v $REQUIRED_PYTHON >/dev/null 2>&1; then
    echo "Python 3.11 is installed"
else
    echo "Error: Python 3.11 is required but not installed"
    echo "Please install Python 3.11 first"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $REQUIRED_PYTHON -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install Qt dependencies if on Raspberry Pi
if is_raspberry_pi; then
    echo "Raspberry Pi detected - installing Qt dependencies..."
    if [ ! -f "/usr/lib/qt6/bin/qmake6" ]; then
        # Make install_qt_deps.sh executable
        chmod +x install_qt_deps.sh
        # Run Qt dependencies installation script
        ./install_qt_deps.sh
    else
        echo "Qt6 dependencies already installed"
    fi
fi

# Install Python dependencies
echo "Installing Python dependencies..."

# First install wheel and setuptools
pip install --upgrade wheel setuptools

# Install PyQt6 with specific options for Raspberry Pi
if is_raspberry_pi; then
    echo "Installing PyQt6 for Raspberry Pi..."
    # Set environment variables for PyQt6 installation
    export QMAKE=/usr/lib/qt6/bin/qmake6
    export QT_SELECT=qt6

    # Install PyQt6 with verbose output
    pip install --verbose "PyQt6>=6.8.1" "PyQt6-Qt6>=6.8.1" "PyQt6-sip>=13.6.0"
else
    # Regular PyQt6 installation for other platforms
    pip install "PyQt6>=6.8.1"
fi

# Install other project dependencies
pip install -r requirements.txt

echo "Environment setup completed successfully"

# Verify PyQt6 installation
python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 installation verified')"

# Print environment information
echo -e "\nEnvironment Information:"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
if is_raspberry_pi; then
    echo "Qt version: $(qmake6 --version)"
fi
echo "PyQt6 version: $(pip show PyQt6 | grep Version)"
