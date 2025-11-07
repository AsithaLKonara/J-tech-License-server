#!/usr/bin/env python3
"""
Create Professional Installer Package for J Tech Pixel Upload Bridge
Includes GUI installer, all requirements, and auto-launch functionality
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_professional_installer():
    """Create a professional installer package"""
    
    print("🚀 Creating Professional J Tech Pixel Upload Bridge Installer")
    print("=" * 70)
    
    # Create installer directory
    installer_dir = Path("dist/j_tech_pixel_upload_bridge_installer")
    installer_dir.mkdir(parents=True, exist_ok=True)
    
    print("📁 Copying all files from current working directory...")
    
    # Copy all Python files and directories
    items_to_copy = [
        "main.py",
        "requirements.txt", 
        "README.md",
        "setup.py",
        "ui/",
        "core/",
        "uploaders/",
        "parsers/",
        "firmware/",
        "config/",
        "build/",
        "create_gui_installer.py",
        "INSTALL_UPLOAD_BRIDGE.bat"
    ]
    
    for item in items_to_copy:
        source_path = Path(item)
        if source_path.exists():
            if source_path.is_file():
                shutil.copy2(source_path, installer_dir)
                print(f"   ✅ {item}")
            elif source_path.is_dir():
                dest_path = installer_dir / source_path.name
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                print(f"   ✅ {item}/")
        else:
            print(f"   ⚠️  {item} not found")
    
    # Create professional installer script
    print("📝 Creating professional installer script...")
    
    installer_script = installer_dir / "INSTALL_J_TECH_PIXEL_BRIDGE.bat"
    with open(installer_script, "w") as f:
        f.write("""@echo off
title J Tech Pixel Upload Bridge - Professional Installer
color 0A

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running with administrator privileges
) else (
    echo ❌ This installer requires administrator privileges
    echo.
    echo Please right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo  ██╗     ████████╗███████╗ ██████╗██╗  ██╗    ██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗
echo  ██║     ╚══██╔══╝██╔════╝██╔════╝██║  ██║    ██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝
echo  ██║        ██║   █████╗  ██║     ███████║    ██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗  
echo  ██║        ██║   ██╔══╝  ██║     ██╔══██║    ██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝  
echo  ███████╗   ██║   ███████╗╚██████╗██║  ██║    ██║  ██║██║  ██║██║██████╔╝╚██████╔╝███████╗
echo  ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝
echo.
echo  ██╗     ██╗██████╗  ██████╗ ███████╗    ███████╗████████╗██╗   ██╗██████╗ ██╗   ██╗
echo  ██║     ██║██╔══██╗██╔════╝ ██╔════╝    ██╔════╝╚══██╔══╝██║   ██║██╔══██╗╚██╗ ██╔╝
echo  ██║     ██║██║  ██║██║  ███╗█████╗      █████╗     ██║   ██║   ██║██████╔╝ ╚████╔╝ 
echo  ██║     ██║██║  ██║██║   ██║██╔══╝      ██╔══╝     ██║   ██║   ██║██╔══██╗  ╚██╔╝  
echo  ███████╗██║██████╔╝╚██████╔╝███████╗    ███████╗   ██║   ╚██████╔╝██║  ██║   ██║   
echo  ╚══════╝╚═╝╚═════╝  ╚═════╝ ╚══════╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
echo.
echo ========================================
echo  J Tech Pixel Upload Bridge
echo  Professional GUI Installer
echo ========================================
echo.
echo  Universal LED Matrix Firmware Uploader
echo  Supports: ESP8266, ESP32, AVR, STM32, PIC, Nuvoton
echo.
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from: https://python.org
    echo Then run this installer again.
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if tkinter is available
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ❌ tkinter is not available
    echo.
    echo Please install tkinter with your Python installation
    echo.
    pause
    exit /b 1
)

echo ✅ tkinter available
echo.

echo 🚀 Starting GUI installer...
echo.

REM Run the GUI installer
python create_gui_installer.py

echo.
echo Installer has completed.
pause
""")
    
    # Create README for installer
    readme_path = installer_dir / "README_INSTALLER.txt"
    with open(readme_path, "w") as f:
        f.write("""J Tech Pixel Upload Bridge - Professional Installer
====================================================

This installer provides a complete GUI-based installation experience for
J Tech Pixel Upload Bridge with all chip requirements.

INSTALLATION INSTRUCTIONS:
==========================

1. RIGHT-CLICK on "INSTALL_J_TECH_PIXEL_BRIDGE.bat"
2. Select "Run as administrator"
3. Follow the GUI installation wizard
4. The installer will automatically:
   - Install Python dependencies
   - Download and install ESP chip tools (Arduino CLI + esptool)
   - Download and install AVR chip tools (AVR-GCC + avrdude)
   - Download and install STM32 chip tools (ARM GCC + stm32flash)
   - Create desktop shortcut
   - Launch the application

SUPPORTED CHIPS:
================

ESP Family (5 chips):
- ESP8266, ESP32, ESP32-S2, ESP32-S3, ESP32-C3

AVR Family (3 chips):
- ATmega328P, ATmega2560, ATtiny85

STM32 Family (2 chips):
- STM32F103C8, STM32F401RE

PIC Family (2 chips):
- PIC16F876A, PIC18F4550

Nuvoton Family (2 chips):
- NUC123, NUC505

FEATURES:
=========

✅ Professional GUI installer with progress bars
✅ Automatic requirement checking and installation
✅ Administrator privilege handling
✅ Desktop shortcut creation
✅ Auto-launch after installation
✅ Complete chip support (14 microcontrollers)
✅ Working brightness control for all chips
✅ Error handling and user feedback

REQUIREMENTS:
=============

- Windows 10/11
- Python 3.8+ (will be checked automatically)
- Administrator privileges
- Internet connection (for downloading tools)

TROUBLESHOOTING:
================

If installation fails:
1. Ensure you're running as administrator
2. Check internet connection
3. Verify Python 3.8+ is installed
4. Check Windows Defender/antivirus settings

For support, contact J Tech Pixel support team.

====================================================
J Tech Pixel Upload Bridge - Professional Installer
====================================================
""")
    
    # Create ZIP package
    print("📦 Creating professional installer ZIP package...")
    zip_path = "dist/j_tech_pixel_upload_bridge_installer.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(installer_dir)
                zipf.write(file_path, arc_path)
    
    print(f"   ✅ Created: {zip_path}")
    
    # Create final summary
    print("\\n🎉 Professional Installer Package Created Successfully!")
    print("=" * 70)
    print(f"📁 Package location: {installer_dir}")
    print(f"📦 ZIP file: {zip_path}")
    print()
    print("📋 Professional installer includes:")
    print("   ✅ Complete GUI installer with progress bars")
    print("   ✅ Administrator privilege checking")
    print("   ✅ Automatic requirement installation")
    print("   ✅ ESP chip tools (Arduino CLI + esptool)")
    print("   ✅ AVR chip tools (AVR-GCC + avrdude)")
    print("   ✅ STM32 chip tools (ARM GCC + stm32flash)")
    print("   ✅ Desktop shortcut creation")
    print("   ✅ Auto-launch functionality")
    print("   ✅ Error handling and user feedback")
    print("   ✅ All 14 chip types supported")
    print("   ✅ Working brightness control")
    print()
    print("🚀 Distribution instructions:")
    print("   1. Share the ZIP file with users")
    print("   2. Users extract and run INSTALL_J_TECH_PIXEL_BRIDGE.bat as administrator")
    print("   3. Users follow the GUI installation wizard")
    print("   4. Application launches automatically after installation")
    print()
    print("✨ J Tech Pixel Upload Bridge is now ready for professional distribution!")

if __name__ == "__main__":
    create_professional_installer()











