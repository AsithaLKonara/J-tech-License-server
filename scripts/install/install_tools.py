#!/usr/bin/env python3
"""
Tool Installation Helper - Install required tools for chip support
Automated installation of esptool, avrdude, and other required tools
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def install_python_package(package):
    """Install Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False


def check_command(command):
    """Check if command is available in PATH"""
    try:
        subprocess.run([command, "--version"], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_esp_tools():
    """Install ESP8266/ESP32 tools"""
    print("🔧 Installing ESP8266/ESP32 tools...")
    
    # Install esptool
    if not check_command("esptool"):
        print("  Installing esptool...")
        if install_python_package("esptool"):
            print("  ✅ esptool installed")
        else:
            print("  ❌ Failed to install esptool")
            return False
    else:
        print("  ✅ esptool already installed")
    
    # Check Arduino CLI
    if not check_command("arduino-cli"):
        print("  ⚠️  Arduino CLI not found")
        print("  Please download from: https://arduino.github.io/arduino-cli/")
        print("  Or install via package manager")
    else:
        print("  ✅ Arduino CLI found")
    
    return True


def install_avr_tools():
    """Install AVR tools"""
    print("🔧 Installing AVR tools...")
    
    system = platform.system().lower()
    
    if system == "windows":
        print("  ⚠️  Windows detected")
        print("  Please install Arduino IDE from: https://www.arduino.cc/en/software")
        print("  This includes avrdude, avr-gcc, and avr-objcopy")
        return True
    
    elif system == "linux":
        print("  Installing AVR tools via apt...")
        try:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", 
                          "avrdude", "gcc-avr", "avr-libc"], check=True)
            print("  ✅ AVR tools installed")
            return True
        except subprocess.CalledProcessError:
            print("  ❌ Failed to install AVR tools")
            return False
    
    elif system == "darwin":  # macOS
        print("  Installing AVR tools via Homebrew...")
        try:
            subprocess.run(["brew", "install", "avrdude", "avr-gcc"], check=True)
            print("  ✅ AVR tools installed")
            return True
        except subprocess.CalledProcessError:
            print("  ❌ Failed to install AVR tools")
            return False
    
    else:
        print(f"  ⚠️  Unsupported system: {system}")
        print("  Please install avrdude, avr-gcc, and avr-libc manually")
        return False


def install_stm32_tools():
    """Install STM32 tools"""
    print("🔧 Installing STM32 tools...")
    
    system = platform.system().lower()
    
    if system == "linux":
        print("  Installing STM32 tools via apt...")
        try:
            subprocess.run(["sudo", "apt", "install", "-y", "stm32flash"], check=True)
            print("  ✅ STM32 tools installed")
            return True
        except subprocess.CalledProcessError:
            print("  ❌ Failed to install STM32 tools")
            return False
    
    elif system == "darwin":  # macOS
        print("  Installing STM32 tools via Homebrew...")
        try:
            subprocess.run(["brew", "install", "stm32flash"], check=True)
            print("  ✅ STM32 tools installed")
            return True
        except subprocess.CalledProcessError:
            print("  ❌ Failed to install STM32 tools")
            return False
    
    else:
        print(f"  ⚠️  Unsupported system: {system}")
        print("  Please install stm32flash manually")
        return False


def install_pic_tools():
    """Install PIC tools"""
    print("🔧 Installing PIC tools...")
    print("  ⚠️  PIC tools require manual installation")
    print("  Please download MPLAB IPE from: https://www.microchip.com/en-us/development-tools-tools-and-software/mplab-ipe")
    print("  Install PICkit drivers for your programmer")
    return True


def install_numicro_tools():
    """Install Nuvoton tools"""
    print("🔧 Installing Nuvoton tools...")
    print("  ⚠️  Nuvoton tools require manual installation")
    print("  Please download Nu-Link tools from: https://www.nuvoton.com/tool-and-software/development-tool-hardware/debugger/")
    return True


def check_all_tools():
    """Check status of all tools"""
    print("🔍 Checking tool installation status...")
    print("=" * 50)
    
    tools = {
        "esptool": "ESP8266/ESP32",
        "arduino-cli": "Arduino CLI",
        "avrdude": "AVR chips",
        "avr-gcc": "AVR compilation",
        "stm32flash": "STM32 chips",
        "pk3cmd": "PIC chips (PICkit)",
        "mplab_ipe": "PIC chips (MPLAB)",
        "nu-link": "Nuvoton chips"
    }
    
    status = {}
    
    for tool, description in tools.items():
        if check_command(tool):
            print(f"  ✅ {tool:15s} - {description}")
            status[tool] = True
        else:
            print(f"  ❌ {tool:15s} - {description}")
            status[tool] = False
    
    return status


def main():
    """Main installation function"""
    print("🛠️  Upload Bridge Tool Installation Helper")
    print("=" * 60)
    print("This script will help install required tools for chip support")
    print("=" * 60)
    
    # Check current status
    print("\n1. Checking current tool status...")
    tool_status = check_all_tools()
    
    # Ask user what to install
    print("\n2. What would you like to install?")
    print("  [1] ESP8266/ESP32 tools (esptool)")
    print("  [2] AVR tools (avrdude, avr-gcc)")
    print("  [3] STM32 tools (stm32flash)")
    print("  [4] PIC tools (manual installation)")
    print("  [5] Nuvoton tools (manual installation)")
    print("  [6] Install all available tools")
    print("  [0] Exit")
    
    try:
        choice = input("\nEnter your choice (0-6): ").strip()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled.")
        return 0
    
    if choice == "0":
        print("Exiting...")
        return 0
    
    success_count = 0
    total_count = 0
    
    if choice == "1" or choice == "6":
        total_count += 1
        if install_esp_tools():
            success_count += 1
    
    if choice == "2" or choice == "6":
        total_count += 1
        if install_avr_tools():
            success_count += 1
    
    if choice == "3" or choice == "6":
        total_count += 1
        if install_stm32_tools():
            success_count += 1
    
    if choice == "4" or choice == "6":
        total_count += 1
        if install_pic_tools():
            success_count += 1
    
    if choice == "5" or choice == "6":
        total_count += 1
        if install_numicro_tools():
            success_count += 1
    
    # Final status check
    print("\n3. Final tool status check...")
    final_status = check_all_tools()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INSTALLATION SUMMARY")
    print("=" * 60)
    
    if total_count > 0:
        print(f"Installation attempts: {total_count}")
        print(f"Successful installations: {success_count}")
        print(f"Success rate: {success_count/total_count*100:.1f}%")
    
    print(f"\nTool status:")
    working_tools = sum(1 for working in final_status.values() if working)
    total_tools = len(final_status)
    print(f"  Working tools: {working_tools}/{total_tools}")
    
    if working_tools >= 3:  # At least ESP + AVR + one other
        print(f"\n✅ Good tool coverage! You can use Upload Bridge with multiple chip types.")
    elif working_tools >= 1:
        print(f"\n⚠️  Limited tool coverage. Consider installing more tools for better chip support.")
    else:
        print(f"\n❌ No tools installed. Please install at least esptool for ESP8266/ESP32 support.")
    
    print(f"\n🚀 Next steps:")
    print(f"  1. Run: python verify_chip_integrations.py")
    print(f"  2. Launch: python main.py")
    print(f"  3. Test with your LED hardware")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())













