# EXE Packaging System Verification

This document verifies that all required files and directories are included in the EXE packaging system.

## Current Configuration Status

### ✅ PyInstaller Spec File (`installer/windows/UploadBridge.spec`)

**Included Packages:**
- ✅ `ui` - UI components (includes all submodules)
- ✅ `core` - Core functionality (includes all submodules)
- ✅ `parsers` - File parsers (includes all submodules)
- ✅ `uploaders` - Hardware uploaders (includes all submodules)
- ✅ `domain` - Domain logic (includes all submodules) **[FIXED]**

**Included Data Files:**
- ✅ `config/chip_database.yaml` - Chip configuration
- ✅ `config/app_config.yaml` - Application configuration
- ✅ `firmware/templates` - Firmware templates directory
- ✅ `config` - Entire config directory (includes all config files)
- ✅ `ui` - Entire UI directory (includes icons, styles, etc.)
- ✅ `core` - Entire core directory
- ✅ `parsers` - Entire parsers directory
- ✅ `uploaders` - Entire uploaders directory
- ✅ `domain` - Entire domain directory **[FIXED]**
- ✅ `LEDMatrixStudio_icon.ico` - Application icon

**Hidden Imports:**
- ✅ PIL (Pillow)
- ✅ cv2 (OpenCV)
- ✅ numpy
- ✅ PySide6
- ✅ cryptography
- ✅ jsonschema (with all dependencies)

### ✅ Inno Setup Installer (`installers/UploadBridge_Installer.iss`)

**Files Included:**
- ✅ `UploadBridge.exe` - Main executable
- ✅ `LAUNCH_UPLOAD_BRIDGE.vbs` - VBS launcher script
- ✅ `LAUNCH_UPLOAD_BRIDGE.bat` - Batch launcher script
- ✅ `LAUNCH_UPLOAD_BRIDGE_DEBUG.bat` - Debug batch launcher
- ✅ `LICENSE_KEYS.txt` - License keys for offline activation

**File Associations:**
- ✅ `.bin` files
- ✅ `.dat` files
- ✅ `.leds` files

### ✅ GitHub Workflow (`.github/workflows/installer-validate.yml`) **[UPDATED]**

**Current PyInstaller Command:**
```powershell
# Use the comprehensive spec file that includes all packages and data files
# This ensures ui, core, parsers, uploaders, domain, and all resources are included
pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec
```

**Status:**
- ✅ Now uses the comprehensive spec file
- ✅ Includes all package directories (ui, core, parsers, uploaders, domain)
- ✅ Includes all data files and resources
- ✅ Consistent with local build process

## Required Files Checklist

### Core Application Files
- ✅ `main.py` - Application entry point
- ✅ `LEDMatrixStudio_icon.ico` - Application icon

### Configuration Files
- ✅ `config/chip_database.yaml` - Chip database
- ✅ `config/app_config.yaml` - App configuration
- ✅ `config/LICENSE_KEYS.txt` - License keys (optional, for offline activation)
- ✅ `LICENSE_KEYS.txt` - License keys (for installer)

### Launcher Scripts (Windows)
- ✅ `windows/LAUNCH_UPLOAD_BRIDGE.vbs` - VBS launcher
- ✅ `windows/LAUNCH_UPLOAD_BRIDGE.bat` - Batch launcher
- ✅ `windows/LAUNCH_UPLOAD_BRIDGE_DEBUG.bat` - Debug launcher

### Package Directories
- ✅ `ui/` - User interface components
- ✅ `core/` - Core application logic
- ✅ `parsers/` - File parsers
- ✅ `uploaders/` - Hardware uploaders
- ✅ `domain/` - Domain logic and models **[FIXED]**
- ✅ `firmware/templates/` - Firmware templates

### Resource Directories
- ✅ `resources/` - Resource files (currently empty, but structure exists)
- ✅ `resources/icons/` - Icon files

## Issues Found and Fixed

### 1. Missing `domain` Package in Spec File ✅ FIXED
**Issue:** The `domain` directory is imported by the application (specifically `ui/tabs/design_tools_tab.py`) but was not explicitly included in the PyInstaller spec file.

**Fix:** Added `domain` to both `hiddenimports` (via `collect_submodules('domain')`) and `datas` section in `installer/windows/UploadBridge.spec`.

### 2. Workflow Not Using Spec File ✅ FIXED
**Issue:** The GitHub workflow was using command-line PyInstaller flags instead of the comprehensive spec file, potentially missing some files.

**Fix:** Updated `.github/workflows/installer-validate.yml` to use the spec file with `pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec`.

## Build Instructions

### Recommended: Build Using Spec File

The PyInstaller spec file (`installer/windows/UploadBridge.spec`) contains all necessary references:

**All Included Packages:**
- `ui` - UI components with all submodules
- `core` - Core functionality with all submodules
- `parsers` - File parsers with all submodules
- `uploaders` - Hardware uploaders with all submodules
- `domain` - Domain logic with all submodules

**All Included Data Files:**
- `config/` - All configuration files
- `firmware/templates/` - Firmware templates directory
- `LEDMatrixStudio_icon.ico` - Application icon
- All package data files via directory inclusion

**Build Command:**
```powershell
cd apps/upload-bridge
pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec
```

This will:
- ✅ Use all hidden imports (PIL, cv2, numpy, PySide6, cryptography, jsonschema)
- ✅ Include all package directories (ui, core, parsers, uploaders, domain)
- ✅ Include all data files (config, firmware templates, icons)
- ✅ Generate a single-file EXE: `dist/UploadBridge.exe`

### Alternative: Build Script (Optional)

You can create a build script for convenience that:
- Verifies all required files exist
- Uses the spec file with all necessary references
- Provides clean build option
- Checks for PyInstaller installation

**Example build script structure:**
```python
# scripts/build/build_windows_exe.py
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
spec_file = PROJECT_ROOT / 'installer/windows/UploadBridge.spec'

subprocess.run([
    sys.executable, '-m', 'PyInstaller',
    '--noconfirm', '--clean',
    str(spec_file)
], check=True, cwd=PROJECT_ROOT)
```

### Build Steps

1. **Build the EXE:**
   ```powershell
   cd apps/upload-bridge
   pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec
   ```

2. **Test the EXE:**
   - Run `dist/UploadBridge.exe` directly
   - Verify all UI components load
   - Test file opening/saving
   - Test firmware template loading
   - Verify license activation works

3. **Build the Installer:**
   ```powershell
   & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installers\UploadBridge_Installer.iss
   ```

4. **Test the Installer:**
   - Install the application
   - Verify all files are installed
   - Test file associations (.bin, .dat, .leds)
   - Launch the application
   - Verify license activation

## Summary

✅ **All required files are now included in the packaging configuration.**

The spec file (`installer/windows/UploadBridge.spec`) has been updated to include:
- All package directories (ui, core, parsers, uploaders, domain)
- All configuration files
- Firmware templates
- Application icon

The Inno Setup installer correctly includes:
- Main executable
- Launcher scripts
- License keys

**Current Status:**
- ✅ PyInstaller spec file includes all necessary references (ui, core, parsers, uploaders, domain)
- ✅ GitHub workflow updated to use spec file
- ✅ All packaging references are consistent
- ✅ All required files and directories are included in the build

**To Build:**
```powershell
cd apps/upload-bridge
pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec
```

The spec file is the single source of truth for what gets included in the EXE, ensuring all packages, data files, and resources are properly bundled.


