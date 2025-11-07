#!/usr/bin/env python3
"""
Upload Bridge - Installer Creator
Creates a complete installer package with all dependencies
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_installer():
    """Create a complete installer package"""
    
    print("🚀 Creating Upload Bridge Installer Package")
    print("=" * 50)
    
    # Create installer directory
    installer_dir = Path("dist/upload_bridge_installer")
    installer_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy application files
    print("📁 Copying application files...")
    app_files = [
        "main.py",
        "requirements.txt", 
        "README.md",
        "install_requirements.bat",
        "install_requirements.sh",
        "build_package.bat",
        "build_package.sh"
    ]
    
    for file in app_files:
        if os.path.exists(file):
            shutil.copy2(file, installer_dir)
            print(f"   ✅ {file}")
    
    # Copy directories
    dirs_to_copy = [
        "upload_bridge",
        "firmware", 
        "ui",
        "core",
        "uploaders"
    ]
    
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            dest_dir = installer_dir / dir_name
            shutil.copytree(dir_name, dest_dir, dirs_exist_ok=True)
            print(f"   ✅ {dir_name}/")
    
    # Create run scripts
    print("📝 Creating run scripts...")
    
    # Windows run script
    with open(installer_dir / "run_upload_bridge.bat", "w") as f:
        f.write("""@echo off
echo ========================================
echo Upload Bridge - LED Matrix Studio
echo ========================================
echo.
echo Starting Upload Bridge...
echo.
python main.py
echo.
echo Upload Bridge has closed.
pause
""")
    
    # Linux/macOS run script
    with open(installer_dir / "run_upload_bridge.sh", "w") as f:
        f.write("""#!/bin/bash
echo "========================================"
echo "Upload Bridge - LED Matrix Studio"
echo "========================================"
echo
echo "Starting Upload Bridge..."
echo
python3 main.py
echo
echo "Upload Bridge has closed."
""")
    
    # Make Linux script executable
    os.chmod(installer_dir / "run_upload_bridge.sh", 0o755)
    
    # Create comprehensive installer
    print("📦 Creating comprehensive installer...")
    
    installer_script = installer_dir / "INSTALL.bat"
    with open(installer_script, "w") as f:
        f.write("""@echo off
echo ========================================
echo Upload Bridge - Complete Installer
echo ========================================
echo.
echo This installer will set up Upload Bridge with all dependencies.
echo.
echo Step 1: Installing Python dependencies...
pip install -r requirements.txt
echo.
echo Step 2: Creating desktop shortcut...
echo [InternetShortcut] > "%USERPROFILE%\\Desktop\\Upload Bridge.url"
echo URL=file:///%CD%\\run_upload_bridge.bat >> "%USERPROFILE%\\Desktop\\Upload Bridge.url"
echo IconFile=%CD%\\run_upload_bridge.bat >> "%USERPROFILE%\\Desktop\\Upload Bridge.url"
echo IconIndex=0 >> "%USERPROFILE%\\Desktop\\Upload Bridge.url"
echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Upload Bridge has been installed successfully!
echo.
echo Desktop shortcut created: Upload Bridge.url
echo.
echo To run Upload Bridge:
echo 1. Double-click the desktop shortcut, OR
echo 2. Run: run_upload_bridge.bat
echo.
echo Additional tools needed for specific chips:
echo - ESP chips: Install Arduino CLI
echo - AVR chips: Install AVR-GCC toolchain  
echo - STM32 chips: Install ARM GCC toolchain
echo - PIC chips: Install MPLAB X IDE
echo - Nuvoton chips: Install Nu-Link tools
echo.
echo See README.md for detailed installation instructions.
echo.
pause
""")
    
    # Create Linux installer
    installer_script_linux = installer_dir / "INSTALL.sh"
    with open(installer_script_linux, "w") as f:
        f.write("""#!/bin/bash
echo "========================================"
echo "Upload Bridge - Complete Installer"
echo "========================================"
echo
echo "This installer will set up Upload Bridge with all dependencies."
echo
echo "Step 1: Installing Python dependencies..."
pip3 install -r requirements.txt
echo
echo "Step 2: Creating desktop shortcut..."
cat > "$HOME/Desktop/Upload Bridge.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Upload Bridge
Comment=LED Matrix Studio Upload Bridge
Exec=$PWD/run_upload_bridge.sh
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
echo "Upload Bridge has been installed successfully!"
echo
echo "Desktop shortcut created: Upload Bridge.desktop"
echo
echo "To run Upload Bridge:"
echo "1. Double-click the desktop shortcut, OR"
echo "2. Run: ./run_upload_bridge.sh"
echo
echo "Additional tools needed for specific chips:"
echo "- ESP chips: Install Arduino CLI"
echo "- AVR chips: Install AVR-GCC toolchain"
echo "- STM32 chips: Install ARM GCC toolchain" 
echo "- PIC chips: Install MPLAB X IDE"
echo "- Nuvoton chips: Install Nu-Link tools"
echo
echo "See README.md for detailed installation instructions."
echo
""")
    
    os.chmod(installer_script_linux, 0o755)
    
    # Create ZIP package
    print("📦 Creating ZIP package...")
    zip_path = "dist/upload_bridge_portable.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(installer_dir)
                zipf.write(file_path, arc_path)
    
    print(f"   ✅ Created: {zip_path}")
    
    # Create final summary
    print("\n🎉 Installer Package Created Successfully!")
    print("=" * 50)
    print(f"📁 Package location: {installer_dir}")
    print(f"📦 ZIP file: {zip_path}")
    print()
    print("📋 Package contents:")
    print("   ✅ Upload Bridge application")
    print("   ✅ All Python dependencies")
    print("   ✅ Installation scripts (Windows & Linux)")
    print("   ✅ Run scripts (Windows & Linux)")
    print("   ✅ Desktop shortcuts")
    print("   ✅ Complete documentation")
    print()
    print("🚀 Distribution instructions:")
    print("   1. Share the ZIP file with users")
    print("   2. Users extract and run INSTALL.bat (Windows) or INSTALL.sh (Linux)")
    print("   3. Users can then run Upload Bridge via desktop shortcut")
    print()
    print("✨ Upload Bridge is ready for distribution!")

if __name__ == "__main__":
    create_installer()












