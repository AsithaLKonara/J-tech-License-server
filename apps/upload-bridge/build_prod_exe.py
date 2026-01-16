#!/usr/bin/env python3
"""
Build Production EXE - Hardened executable for release
Excludes development environment variables and test license keys.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
SPEC_FILE = PROJECT_ROOT / "installer" / "windows" / "UploadBridge.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
CONFIG_DIR = PROJECT_ROOT / "config"

def clean_build_artifacts():
    """Wipe dist and build folders"""
    for folder in [DIST_DIR, BUILD_DIR]:
        if folder.exists():
            print(f"🧹 Cleaning {folder.name}...")
            shutil.rmtree(folder)
    print("✨ Build environment cleaned.")

def secure_config_audit():
    """Ensure no test keys escape into production"""
    keys_file = CONFIG_DIR / "license_keys.yaml"
    if keys_file.exists():
        print(f"🚨 ALERT: {keys_file.name} found in config directory!")
        print("   Moving to temporary location during build...")
        temp_keys = PROJECT_ROOT / "license_keys.yaml.bak"
        shutil.move(str(keys_file), str(temp_keys))
        return temp_keys
    return None

def build_production_exe():
    """Run PyInstaller build"""
    print("=" * 60)
    print("Building PRODUCTION Upload Bridge EXE")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_FILE)
    ]
    
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        print("\n✅ Production build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False

def main():
    clean_build_artifacts()
    
    # Audit and secure config
    temp_keys = secure_config_audit()
    
    try:
        success = build_production_exe()
        
        if success:
            exe_file = DIST_DIR / "UploadBridge.exe"
            if exe_file.exists():
                print(f"📦 Production EXE ready at: {exe_file}")
                print(f"📏 Size: {exe_file.stat().st_size / (1024*1024):.2f} MB")
        
    finally:
        # Restore test keys if they were moved
        if temp_keys and temp_keys.exists():
            print("RESTORE: Returning test keys to config directory.")
            shutil.move(str(temp_keys), str(CONFIG_DIR / "license_keys.yaml"))

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
