#!/usr/bin/env python3
"""
Toolchain Detection and Setup Script
Checks for required toolchains and provides installation instructions
"""

import subprocess
import shutil
import platform
import os
from pathlib import Path

class ToolchainDetector:
    """Detects and validates toolchain installations"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.toolchains = {
            'avr': {
                'commands': ['avr-gcc', 'avrdude'],
                'description': 'AVR GCC Toolchain + avrdude',
                'install_url': 'https://www.microchip.com/en-us/tools-resources/develop/microchip-studio'
            },
            'arm': {
                'commands': ['arm-none-eabi-gcc', 'stm32flash'],
                'description': 'ARM GCC Toolchain + stm32flash',
                'install_url': 'https://developer.arm.com/downloads/-/gnu-rm'
            },
            'pic': {
                'commands': ['xc8'],
                'description': 'MPLAB X IDE with XC8 Compiler',
                'install_url': 'https://www.microchip.com/en-us/tools-resources/develop/mplab-x-ide'
            },
            'esp': {
                'commands': ['arduino-cli', 'esptool.py'],
                'description': 'Arduino CLI + esptool.py',
                'install_url': 'https://arduino.github.io/arduino-cli/'
            }
        }
    
    def check_command(self, command):
        """Check if a command is available in PATH"""
        return shutil.which(command) is not None
    
    def check_toolchain(self, toolchain_name):
        """Check if a toolchain is properly installed"""
        toolchain = self.toolchains[toolchain_name]
        missing_commands = []
        
        for command in toolchain['commands']:
            if not self.check_command(command):
                missing_commands.append(command)
        
        return {
            'available': len(missing_commands) == 0,
            'missing_commands': missing_commands,
            'description': toolchain['description'],
            'install_url': toolchain['install_url']
        }
    
    def detect_all_toolchains(self):
        """Detect all toolchains and return status"""
        results = {}
        
        for toolchain_name in self.toolchains:
            results[toolchain_name] = self.check_toolchain(toolchain_name)
        
        return results
    
    def print_status(self):
        """Print toolchain detection status"""
        print("🔧 Toolchain Detection Report")
        print("=" * 50)
        
        results = self.detect_all_toolchains()
        
        for toolchain_name, status in results.items():
            if status['available']:
                print(f"✅ {toolchain_name.upper()}: {status['description']}")
            else:
                print(f"❌ {toolchain_name.upper()}: {status['description']}")
                print(f"   Missing: {', '.join(status['missing_commands'])}")
                print(f"   Install: {status['install_url']}")
        
        print("\n📋 Installation Instructions:")
        print("-" * 30)
        
        if self.system == 'windows':
            print("Windows:")
            print("1. AVR: Install Arduino IDE (includes avr-gcc + avrdude)")
            print("2. ARM: Download ARM GCC from ARM Developer website")
            print("3. PIC: Install MPLAB X IDE with XC8 compiler")
            print("4. ESP: Install Arduino CLI + esptool.py via pip")
            
        elif self.system == 'linux':
            print("Linux:")
            print("1. AVR: sudo apt install avrdude gcc-avr")
            print("2. ARM: sudo apt install gcc-arm-none-eabi stm32flash")
            print("3. PIC: Download MPLAB X IDE from Microchip")
            print("4. ESP: pip install esptool && install Arduino CLI")
            
        elif self.system == 'darwin':
            print("macOS:")
            print("1. AVR: brew install avrdude avr-gcc")
            print("2. ARM: brew install gcc-arm-embedded")
            print("3. PIC: Download MPLAB X IDE from Microchip")
            print("4. ESP: pip install esptool && install Arduino CLI")

def main():
    """Main function"""
    detector = ToolchainDetector()
    detector.print_status()
    
    # Check if any toolchains are available
    results = detector.detect_all_toolchains()
    available_count = sum(1 for status in results.values() if status['available'])
    
    print(f"\n📊 Summary: {available_count}/{len(results)} toolchains available")
    
    if available_count == 0:
        print("⚠️  No toolchains detected. Please install at least one toolchain.")
    elif available_count < len(results):
        print("ℹ️  Some toolchains missing. Install additional toolchains for full support.")
    else:
        print("🎉 All toolchains detected! Upload Bridge is fully configured.")

if __name__ == "__main__":
    main()

