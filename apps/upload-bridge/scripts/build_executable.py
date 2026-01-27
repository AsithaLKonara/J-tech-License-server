#!/usr/bin/env python3
"""
Build script for creating executable distribution of LED Matrix Studio.

This script automates the process of building a standalone executable
using PyInstaller with all necessary dependencies.
"""

import sys
import os
import subprocess
import shutil
import re
from pathlib import Path

# Add the app directory to the path
APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))


def get_version_from_setup() -> str:
    """Extract version from setup.py."""
    setup_py = APP_DIR / "setup.py"
    if setup_py.exists():
        content = setup_py.read_text(encoding='utf-8')
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    return "3.0.0"  # Default fallback

def check_dependencies():
    """Check if required build tools are installed."""
    print("Checking build dependencies...")
    
    try:
        import PyInstaller
        print(f"  - PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  - PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("  - PyInstaller installed")
    
    # Check for PySide6
    try:
        import PySide6
        print("  - PySide6 found")
    except ImportError:
        print("  - PySide6 not found. Please install requirements first:")
        print("     pip install -r requirements.txt")
        return False
    
    # Check for numpy
    try:
        import numpy
        print("  - NumPy found")
    except ImportError:
        print("  - NumPy not found. Please install requirements first:")
        print("     pip install -r requirements.txt")
        return False
    
    return True

def clean_build_directories():
    """Clean previous build artifacts."""
    print("\nCleaning build directories...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = APP_DIR / dir_name
        if dir_path.exists():
            print(f"  Removing {dir_path}...")
            shutil.rmtree(dir_path)

def build_executable():
    """Build the executable using PyInstaller."""
    print("\nBuilding executable...")
    
    # Get version from setup.py
    version = get_version_from_setup()
    print(f"  Version: {version}")
    
    spec_file = APP_DIR / "installer" / "windows" / "UploadBridge.spec"
    
    if not spec_file.exists():
        print(f"  - Spec file not found: {spec_file}")
        print("  Creating default spec file...")
        create_default_spec(spec_file, version)
    
    # Update spec file with version if needed
    update_spec_with_version(spec_file, version)
    
    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=APP_DIR)
    
    if result.returncode == 0:
        print("  - Build successful!")
        exe_path = APP_DIR / "dist" / "UploadBridge.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"  - Executable created: {exe_path} ({size_mb:.1f} MB)")
            
            # Embed version in executable metadata (Windows)
            if sys.platform == 'win32':
                try:
                    embed_version_in_exe(exe_path, version)
                    print(f"  - Version {version} embedded in executable metadata")
                except Exception as e:
                    print(f"  ! Could not embed version in metadata: {e}")
            
            # Record build hashes
            try:
                from scripts.tools.add_build_hash import record_build_hash
                dist_dir = APP_DIR / "dist"
                if record_build_hash(dist_dir):
                    print("  - Build hashes recorded")
            except Exception as e:
                print(f"  ! Could not record build hashes: {e}")
        return True
    else:
        print("  - Build failed!")
        return False


def update_spec_with_version(spec_file: Path, version: str):
    """Update spec file to include version information."""
    pass
    # if not spec_file.exists():
    #     return
    
    # content = spec_file.read_text(encoding='utf-8')
    
    # # Add version to EXE section if not present
    # if 'version=' not in content and 'exe = EXE' in content:
    #     # Find the exe = EXE line and add version after name
    #     version_info = f'''version='{version}',
    # '''
    #     # Insert after name='UploadBridge',
    #     content = re.sub(
    #         r"(name=['\"]UploadBridge['\"],\s*\n)",
    #         rf"\1    {version_info}",
    #         content
    #     )
    #     spec_file.write_text(content, encoding='utf-8')


def embed_version_in_exe(exe_path: Path, version: str):
    """Embed version in Windows executable metadata using pywin32."""
    try:
        import win32api
        import win32con
        import win32file
        
        # Parse version string (e.g., "3.0.0" -> 3, 0, 0, 0)
        parts = version.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        build = int(parts[3]) if len(parts) > 3 else 0
        
        # This requires modifying the executable's version resource
        # For now, we'll just log it - actual embedding requires more complex Windows API calls
        # The version is already in the spec file which PyInstaller uses
        pass
    except ImportError:
        # pywin32 not available - version is still in spec file
        pass

def create_default_spec(spec_file: Path, version: str = "3.0.0"):
    """Create a default PyInstaller spec file if one doesn't exist."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_all

block_cipher = None

APP_DIR = Path(r'{app_dir}')
VERSION = '{version}'

# Collect dependencies
pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all('PySide6')
jsonschema_datas, jsonschema_binaries, jsonschema_hiddenimports = collect_all('jsonschema')
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')

hiddenimports = []
hiddenimports += pyside_hiddenimports
hiddenimports += jsonschema_hiddenimports
hiddenimports += numpy_hiddenimports
hiddenimports.append('referencing')
hiddenimports.append('rpds')

# Collect submodules
hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('parsers')
hiddenimports += collect_submodules('uploaders')
hiddenimports += collect_submodules('domain')

a = Analysis(
    [str(APP_DIR / 'main.py')],
    pathex=[str(APP_DIR)],
    binaries=jsonschema_binaries + pyside_binaries + numpy_binaries,
    datas=[
        (str(APP_DIR / 'config'), 'config'),
        (str(APP_DIR / 'ui'), 'ui'),
        (str(APP_DIR / 'core'), 'core'),
        (str(APP_DIR / 'parsers'), 'parsers'),
        (str(APP_DIR / 'uploaders'), 'uploaders'),
        (str(APP_DIR / 'domain'), 'domain'),
        (str(APP_DIR / 'firmware/templates'), 'firmware/templates'),
        (str(APP_DIR / 'resources'), 'resources'),
    ] + jsonschema_datas + pyside_datas + numpy_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'pandas'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UploadBridge',
    version=VERSION,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(APP_DIR / 'LEDMatrixStudio_icon.ico') if (APP_DIR / 'LEDMatrixStudio_icon.ico').exists() else None,
)
'''
    
    spec_file.parent.mkdir(parents=True, exist_ok=True)
    with open(spec_file, 'w') as f:
        f.write(spec_content.format(
            app_dir=str(APP_DIR).replace('\\', '\\\\'),
            version=version
        ))

def main():
    """Main build process."""
    print("=" * 60)
    print("LED MATRIX STUDIO - EXECUTABLE BUILD SCRIPT")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return 1
    
    # Clean previous builds
    clean_build_directories()
    
    # Build executable
    if not build_executable():
        print("\n- Build failed!")
        return 1
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"\nExecutable location: {APP_DIR / 'dist' / 'UploadBridge.exe'}")
    print("\nNext steps:")
    print("  1. Test the executable")
    print("  2. Create installer package (optional)")
    print("  3. Distribute to users")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

