#!/bin/bash
# Upload Bridge Launcher - Linux/macOS
# Quick start script

echo ""
echo "================================================================"
echo " Upload Bridge v3.0 - Universal LED Pattern Flasher"
echo "================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.8+ from python.org"
    exit 1
fi

echo "Checking dependencies..."
echo ""

# Check PySide6
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "WARNING: PySide6 not found"
    echo "Installing PySide6..."
    pip3 install PySide6
fi

# Check PyYAML
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "WARNING: PyYAML not found"
    echo "Installing PyYAML..."
    pip3 install PyYAML
fi

# Check pyserial
if ! python3 -c "import serial" 2>/dev/null; then
    echo "WARNING: pyserial not found"
    echo "Installing pyserial..."
    pip3 install pyserial
fi

echo ""
echo "Launching Upload Bridge..."
echo ""

# Launch application
python3 RUN.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application failed to launch"
    echo "Check dependencies: pip3 install -r requirements.txt"
fi

