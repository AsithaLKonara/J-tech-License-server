#!/usr/bin/env python3
"""
Package Upload Bridge with License System
Creates distributable package with all dependencies
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    """Build package"""
    print("\n" + "="*70)
    print("UPLOAD BRIDGE - PACKAGE BUILDER")
    print("="*70)
    
    # Check PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=False)
    
    # Create build directory
    build_dir = Path("dist/UploadBridge")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n📦 Building package...")
    print("="*70)
    
    # Determine icon
    icon_candidates = [
        Path("LEDMatrixStudio_icon.ico"),
        Path("resources/icons/LEDMatrixStudio_icon.ico"),
        Path("assets/icons/LEDMatrixStudio_icon.ico"),
    ]
    icon_path = next((p for p in icon_candidates if p.exists()), None)

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=UploadBridge",
        "--onefile",
        "--windowed",
        "--paths=.",
        "--noconfirm",
    ]
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    else:
        cmd.append("--icon=NONE")
    cmd.extend([
        f"--add-data=config/chip_database.yaml;config",
        f"--add-data=config/app_config.yaml;config",
        f"--add-data=firmware/templates;firmware/templates",
        f"--add-data=config;config",
        f"--add-data=ui;ui",
        f"--add-data=core;core",
        f"--add-data=parsers;parsers",
        f"--add-data=uploaders;uploaders",
    ])
    if icon_path:
        # Include icon at runtime as well (for setWindowIcon paths)
        cmd.append(f"--add-data={icon_path};.")
    cmd.extend([
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=PySide6",
        "--hidden-import=cryptography",
        "--hidden-import=ui",
        "--hidden-import=ui.main_window",
        "--hidden-import=ui.tabs.preview_tab",
        "--hidden-import=ui.tabs.flash_tab",
        "--hidden-import=ui.tabs.media_upload_tab",
        "--hidden-import=ui.tabs.wifi_upload_tab",
        "--hidden-import=ui.tabs.arduino_ide_tab",
        "--hidden-import=ui.dialogs.activation_dialog",
        "--hidden-import=core",
        "--hidden-import=core.pattern",
        "--hidden-import=parsers.parser_registry",
        "--hidden-import=uploaders.uploader_registry",
        "--collect-submodules=ui",
        "--collect-submodules=core",
        "--collect-submodules=parsers",
        "--collect-submodules=uploaders",
        "--exclude-module=matplotlib",
        "--exclude-module=pandas",
        "main.py",
    ])
    
    print("\n🔨 Running PyInstaller...")
    print("Command:", " ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Build successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False

    # Build ONEDIR portable testing version
    print("\n🔨 Building Portable Testing Version (onedir)...")
    onedir_cmd = [
        "pyinstaller",
        "--name=UploadBridge_Test",
        "--onedir",
        "--windowed",
        "--paths=.",
        "--noconfirm",
    ]
    if icon_path:
        onedir_cmd.append(f"--icon={icon_path}")
    else:
        onedir_cmd.append("--icon=NONE")
    onedir_cmd.extend([
        f"--add-data=config/chip_database.yaml;config",
        f"--add-data=config/app_config.yaml;config",
        f"--add-data=firmware/templates;firmware/templates",
        f"--add-data=config;config",
        f"--add-data=LEDMatrixStudio_icon.ico;." if icon_path else "",
        f"--add-data=ui;ui",
        f"--add-data=core;core",
        f"--add-data=parsers;parsers",
        f"--add-data=uploaders;uploaders",
        "--hidden-import=ui",
        "--hidden-import=ui.main_window",
        "--hidden-import=ui.tabs.preview_tab",
        "--hidden-import=ui.tabs.flash_tab",
        "--hidden-import=ui.tabs.media_upload_tab",
        "--hidden-import=ui.tabs.wifi_upload_tab",
        "--hidden-import=ui.tabs.arduino_ide_tab",
        "--hidden-import=ui.dialogs.activation_dialog",
        "--hidden-import=core",
        "--hidden-import=core.pattern",
        "--hidden-import=parsers.parser_registry",
        "--hidden-import=uploaders.uploader_registry",
        "--collect-submodules=ui",
        "--collect-submodules=core",
        "--collect-submodules=parsers",
        "--collect-submodules=uploaders",
        "main.py",
    ])
    onedir_cmd = [a for a in onedir_cmd if a]
    print("Command:", " ".join(onedir_cmd))
    try:
        subprocess.run(onedir_cmd, check=True)
        print("\n✅ Portable testing build successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Portable testing build failed: {e}")
        # continue; installer build still useful

    # Build Installer GUI (onefile)
    print("\n🔨 Building Installer...")
    installer_icon = icon_path if icon_path else None
    installer_cmd = [
        "pyinstaller",
        "--name=UploadBridgeInstaller",
        "--onefile",
        "--windowed",
    ]
    if installer_icon:
        installer_cmd.append(f"--icon={installer_icon}")
    else:
        installer_cmd.append("--icon=NONE")
    # Include license keys file to allow validation even if run standalone
    # Embed the built UploadBridge.exe into the installer payload so it works even if separated
    payload_exe = Path("dist/UploadBridge.exe")
    installer_cmd.extend([
        f"--add-data=config;config",
        f"--add-data=LICENSE_KEYS.txt;." if Path("LICENSE_KEYS.txt").exists() else "",
        f"--add-data={payload_exe};payload" if payload_exe.exists() else "",
        f"--add-data=windows;windows",
        "installer/installer.py",
    ])
    # Remove empty entries
    installer_cmd = [a for a in installer_cmd if a]
    print("Command:", " ".join(installer_cmd))
    try:
        subprocess.run(installer_cmd, check=True)
        print("\n✅ Installer build successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Installer build failed: {e}")
        # Continue packaging even if installer fails
    
    # Create final package structure (clean root: exe, installer, README, LICENSE_KEYS.txt)
    print("\n📁 Creating package structure...")
    
    package_dir = Path(f"dist/UploadBridge_Package_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe = Path("dist/UploadBridge.exe")
    if exe.exists():
        shutil.copy(exe, package_dir / "UploadBridge.exe")
        print(f"✅ Copied: UploadBridge.exe")
    
    # Copy installer
    installer_exe = Path("dist/UploadBridgeInstaller.exe")
    if installer_exe.exists():
        shutil.copy(installer_exe, package_dir / "UploadBridgeInstaller.exe")
        print(f"✅ Copied: UploadBridgeInstaller.exe")
    
    # Copy LICENSE_KEYS.txt (mandatory for offline activation)
    if Path("LICENSE_KEYS.txt").exists():
        shutil.copy("LICENSE_KEYS.txt", package_dir / "LICENSE_KEYS.txt")
        print("✅ Copied: LICENSE_KEYS.txt")

    # Create README with embedded keys preview and steps
    readme = package_dir / "README.txt"
    keys_preview = ""
    try:
        if (package_dir / "LICENSE_KEYS.txt").exists():
            keys_txt = (package_dir / "LICENSE_KEYS.txt").read_text(encoding="utf-8", errors="ignore")
            # Extract first 10 matching keys for quick view
            import re as _re
            matches = _re.findall(r"ULBP-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}", keys_txt.upper())
            if matches:
                keys_preview = "\n" + "\n".join(f"- {m}" for m in matches[:10]) + "\n"
    except Exception:
        pass

    readme.write_text(f"""Upload Bridge - Universal LED Pattern Flasher
Version: 3.0
Package Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

First-Time Setup (Offline):
1) Run UploadBridgeInstaller.exe
2) Choose install folder and click Install
3) Open LICENSE_KEYS.txt and copy a key
4) Paste the key in the installer and click Activate
5) Click Launch Upload Bridge

Notes:
- No internet required. Activation is offline.
- Activation is stored locally for this device.

Quick Keys (for convenience):{keys_preview if keys_preview else '\n- See LICENSE_KEYS.txt'}

""")

    # Create dedicated testing portable package folder
    test_src = Path("dist/UploadBridge_Test")
    if test_src.exists():
        test_pkg = Path(f"dist/UploadBridge_TestPortable_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copytree(test_src, test_pkg)
        # Add launchers to portable
        if Path("windows/LAUNCH_UPLOAD_BRIDGE.bat").exists():
            shutil.copy("windows/LAUNCH_UPLOAD_BRIDGE.bat", test_pkg / "LAUNCH_UPLOAD_BRIDGE.bat")
        if Path("windows/LAUNCH_UPLOAD_BRIDGE.vbs").exists():
            shutil.copy("windows/LAUNCH_UPLOAD_BRIDGE.vbs", test_pkg / "LAUNCH_UPLOAD_BRIDGE.vbs")
        # Drop keys and a focused testing README
        if Path("LICENSE_KEYS.txt").exists():
            shutil.copy("LICENSE_KEYS.txt", test_pkg / "LICENSE_KEYS.txt")
        (test_pkg / "README_TESTING.txt").write_text(
            """Upload Bridge - Testing Portable Build (No Installer)\n\n" +
            "Run: UploadBridge_Test.exe (or LAUNCH_UPLOAD_BRIDGE.vbs for hidden launch)\n\n" +
            "Activation (offline):\n" +
            "1) Open LICENSE_KEYS.txt and copy a key\n" +
            "2) In the app, License → Activate, paste key, Activate\n\n" +
            "Notes:\n" +
            "- All required resources are included in this folder.\n" +
            "- Logs: UploadBridge.log will appear next to the EXE after first run.\n" +
            """,
            encoding="utf-8",
        )
        print(f"✅ Created testing portable: {test_pkg}")
    
    print(f"✅ Created: README.txt")
    
    # Summary
    print("\n" + "="*70)
    print("PACKAGE CREATED SUCCESSFULLY!")
    print("="*70)
    print(f"\n📦 Package Location: {package_dir}")
    print(f"\n📋 Package Contents:")
    print(f"  • UploadBridge.exe")
    print(f"  • UploadBridgeInstaller.exe")
    print(f"  • LICENSE_KEYS.txt")
    print(f"  • README.txt")
    test_portable_dirs = [p for p in Path("dist").glob("UploadBridge_TestPortable_*")]
    if test_portable_dirs:
        print(f"  • {test_portable_dirs[-1].name}")
    print(f"\n✅ Ready for distribution!")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    main()

