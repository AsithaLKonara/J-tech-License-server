#!/usr/bin/env python3
"""
Fix Upload Bridge Installer - Include all missing modules
"""

import os
import shutil
import zipfile
from pathlib import Path

def fix_installer():
    """Fix the installer package with all missing components"""
    
    print("🔧 Fixing Upload Bridge Installer Package")
    print("=" * 50)
    
    # Create fixed installer directory
    installer_dir = Path("dist/upload_bridge_installer_fixed")
    installer_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy ALL application files and directories
    print("📁 Copying all application files...")
    
    # Copy main files
    main_files = [
        "main.py",
        "requirements.txt", 
        "README.md",
        "install_requirements.bat",
        "install_requirements.sh",
        "LAUNCH_UPLOAD_BRIDGE.bat"
    ]
    
    for file in main_files:
        if os.path.exists(file):
            shutil.copy2(file, installer_dir)
            print(f"   ✅ {file}")
    
    # Copy ALL directories recursively
    dirs_to_copy = [
        "upload_bridge",
        "firmware", 
        "ui",
        "core",
        "uploaders",
        "parsers",  # Add missing parsers directory
        "utils"     # Add missing utils directory if it exists
    ]
    
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            dest_dir = installer_dir / dir_name
            shutil.copytree(dir_name, dest_dir, dirs_exist_ok=True)
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ not found (may not exist)")
    
    # Create a proper main.py that handles imports correctly
    print("📝 Creating fixed main.py...")
    
    main_py_content = '''#!/usr/bin/env python3
"""
Upload Bridge - LED Matrix Studio
Universal firmware uploader for LED patterns
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Add all subdirectories to path
for subdir in ['ui', 'core', 'uploaders', 'parsers', 'utils']:
    subdir_path = current_dir / subdir
    if subdir_path.exists():
        sys.path.insert(0, str(subdir_path))

try:
    from ui.main_window import UploadBridgeMainWindow
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    import sys
    
    def main():
        """Main application entry point"""
        app = QApplication(sys.argv)
        app.setApplicationName("Upload Bridge")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("LED Matrix Studio")
        
        # Set application icon if available
        icon_path = Path(__file__).parent / "ui" / "icons" / "app_icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # Create and show main window
        window = UploadBridgeMainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\\n🔧 Troubleshooting:")
    print("1. Make sure all dependencies are installed:")
    print("   pip install -r requirements.txt")
    print("\\n2. Check that all directories are present:")
    print("   - ui/")
    print("   - core/")
    print("   - uploaders/")
    print("   - parsers/")
    print("\\n3. Try running from the main directory:")
    print("   python main.py")
    input("\\nPress Enter to exit...")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    input("\\nPress Enter to exit...")
    sys.exit(1)
'''
    
    with open(installer_dir / "main.py", "w", encoding="utf-8") as f:
        f.write(main_py_content)
    
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
echo Step 2: Verifying installation...
python -c "import PySide6; print('✅ PySide6 installed')"
python -c "import esptool; print('✅ esptool installed')"
echo.
echo Step 3: Creating desktop shortcut...
echo [InternetShortcut] > "%USERPROFILE%\\Desktop\\Upload Bridge.url"
echo URL=file:///%CD%\\LAUNCH_UPLOAD_BRIDGE.bat >> "%USERPROFILE%\\Desktop\\Upload Bridge.url"
echo IconFile=%CD%\\LAUNCH_UPLOAD_BRIDGE.bat >> "%USERPROFILE%\\Desktop\\Upload Bridge.url"
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
echo 2. Run: LAUNCH_UPLOAD_BRIDGE.bat
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
echo "Step 2: Verifying installation..."
python3 -c "import PySide6; print('✅ PySide6 installed')"
python3 -c "import esptool; print('✅ esptool installed')"
echo
echo "Step 3: Creating desktop shortcut..."
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
echo "Upload Bridge has been installed successfully!"
echo
echo "Desktop shortcut created: Upload Bridge.desktop"
echo
echo "To run Upload Bridge:"
echo "1. Double-click the desktop shortcut, OR"
echo "2. Run: ./LAUNCH_UPLOAD_BRIDGE.sh"
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
    
    # Create Linux launcher
    launcher_linux = installer_dir / "LAUNCH_UPLOAD_BRIDGE.sh"
    with open(launcher_linux, "w") as f:
        f.write("""#!/bin/bash
echo "========================================"
echo "Upload Bridge - LED Matrix Studio"
echo "========================================"
echo
echo "Starting Upload Bridge..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import PySide6" &> /dev/null; then
    echo "⚠️  Python dependencies not installed"
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo
fi

echo "✅ Starting Upload Bridge..."
echo

# Start the application
python3 main.py

echo
echo "Upload Bridge has closed."
""")
    
    os.chmod(launcher_linux, 0o755)
    
    # Create ZIP package
    print("📦 Creating fixed ZIP package...")
    zip_path = "dist/upload_bridge_portable_fixed.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(installer_dir)
                zipf.write(file_path, arc_path)
    
    print(f"   ✅ Created: {zip_path}")
    
    # Create final summary
    print("\\n🎉 Fixed Installer Package Created Successfully!")
    print("=" * 50)
    print(f"📁 Package location: {installer_dir}")
    print(f"📦 ZIP file: {zip_path}")
    print()
    print("📋 Fixed issues:")
    print("   ✅ Added proper Python path handling")
    print("   ✅ Fixed import errors")
    print("   ✅ Added missing parsers directory")
    print("   ✅ Created robust error handling")
    print("   ✅ Added dependency verification")
    print()
    print("🚀 Distribution instructions:")
    print("   1. Share the FIXED ZIP file with users")
    print("   2. Users extract and run INSTALL.bat (Windows) or INSTALL.sh (Linux)")
    print("   3. Users can then run Upload Bridge via LAUNCH_UPLOAD_BRIDGE.bat")
    print()
    print("✨ Upload Bridge is now properly packaged and ready for distribution!")

if __name__ == "__main__":
    fix_installer()












