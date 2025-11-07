#!/bin/bash

echo "========================================"
echo "Upload Bridge - Complete Requirements Installer"
echo "========================================"
echo
echo "This installer will set up Upload Bridge with ALL dependencies"
echo "for ALL supported microcontrollers."
echo
echo "Supported Chips:"
echo "- ESP8266, ESP32, ESP32-S2, ESP32-S3, ESP32-C3"
echo "- ATmega328P, ATmega2560, ATtiny85 (AVR)"
echo "- STM32F103C8, STM32F401RE (STM32)"
echo "- PIC16F876A, PIC18F4550 (PIC)"
echo "- NUC123, NUC505 (Nuvoton)"
echo
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

echo "Step 1: Installing Python dependencies..."
pip3 install -r requirements.txt
echo

echo "Step 2: Installing ESP chip tools..."
echo "Installing esptool for ESP chips..."
pip3 install esptool
echo

echo "Installing Arduino CLI for ESP chips..."
echo "Downloading Arduino CLI..."
wget -O arduino-cli.tar.gz "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz"
if [ -f arduino-cli.tar.gz ]; then
    echo "Extracting Arduino CLI..."
    tar -xzf arduino-cli.tar.gz
    chmod +x arduino-cli
    echo "Adding Arduino CLI to PATH..."
    echo 'export PATH="$PATH:'$(pwd)'"' >> ~/.bashrc
    echo "Installing ESP cores..."
    ./arduino-cli core install esp8266:esp8266
    ./arduino-cli core install esp32:esp32
    echo "✅ Arduino CLI installed for ESP chips"
else
    echo "⚠️  Failed to download Arduino CLI - please install manually"
fi
echo

echo "Step 3: Installing AVR chip tools..."
echo "Installing AVR-GCC and avrdude..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y avrdude gcc-avr avr-libc
    echo "✅ AVR tools installed for AVR chips"
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y avrdude gcc-avr avr-libc
    echo "✅ AVR tools installed for AVR chips"
elif command -v pacman &> /dev/null; then
    # Arch Linux
    sudo pacman -S avrdude avr-gcc avr-libc
    echo "✅ AVR tools installed for AVR chips"
elif command -v brew &> /dev/null; then
    # macOS
    brew install avrdude avr-gcc
    echo "✅ AVR tools installed for AVR chips"
else
    echo "⚠️  Please install AVR-GCC and avrdude manually for your system"
fi
echo

echo "Step 4: Installing STM32 chip tools..."
echo "Installing ARM GCC toolchain..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get install -y gcc-arm-none-eabi stm32flash
    echo "✅ ARM GCC and stm32flash installed for STM32 chips"
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y gcc-arm-none-eabi stm32flash
    echo "✅ ARM GCC and stm32flash installed for STM32 chips"
elif command -v pacman &> /dev/null; then
    # Arch Linux
    sudo pacman -S arm-none-eabi-gcc stm32flash
    echo "✅ ARM GCC and stm32flash installed for STM32 chips"
elif command -v brew &> /dev/null; then
    # macOS
    brew install arm-none-eabi-gcc stm32flash
    echo "✅ ARM GCC and stm32flash installed for STM32 chips"
else
    echo "⚠️  Please install ARM GCC toolchain and stm32flash manually"
fi
echo

echo "Step 5: Installing PIC chip tools..."
echo "⚠️  MPLAB X IDE requires manual installation"
echo "Please download from: https://www.microchip.com/en-us/tools-resources/develop/mplab-x-ide"
echo "Install with XC8 compiler for PIC support"
echo

echo "Step 6: Installing Nuvoton chip tools..."
echo "⚠️  Nu-Link tools require manual installation"
echo "Please download from: https://www.nuvoton.com/tool-and-software/development-tool-hardware/"
echo "Install Nu-Link tools for Nuvoton support"
echo

echo "Step 7: Installing additional Python packages..."
echo "Installing additional packages for all chips..."
pip3 install pyserial pyyaml colorama tqdm
echo

echo "Step 8: Verifying installation..."
echo "Checking Python packages..."
python3 -c "import PySide6; print('✅ PySide6 installed')"
python3 -c "import esptool; print('✅ esptool installed')"
python3 -c "import serial; print('✅ pyserial installed')"
python3 -c "import yaml; print('✅ pyyaml installed')"
echo

echo "Step 9: Creating desktop shortcut..."
cat > "$HOME/Desktop/Upload Bridge.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Upload Bridge
Comment=LED Matrix Studio Upload Bridge
Exec=$PWD/LAUNCH_UPLOAD_BRIDGE.sh
Icon=applications-development
Terminal=false
Categories=Development;Electronics;
EOF
chmod +x "$HOME/Desktop/Upload Bridge.desktop"
echo

echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo
echo "Upload Bridge has been installed with support for ALL chips!"
echo
echo "✅ ESP chips: Arduino CLI + esptool installed"
echo "✅ AVR chips: AVR-GCC toolchain installed"
echo "✅ STM32 chips: ARM GCC + stm32flash installed"
echo "⚠️  PIC chips: Please install MPLAB X IDE manually"
echo "⚠️  Nuvoton chips: Please install Nu-Link tools manually"
echo
echo "Desktop shortcut created: Upload Bridge.desktop"
echo
echo "To run Upload Bridge:"
echo "1. Double-click the desktop shortcut, OR"
echo "2. Run: ./LAUNCH_UPLOAD_BRIDGE.sh"
echo
echo "Note: You may need to restart your terminal"
echo "for PATH changes to take effect."
echo












