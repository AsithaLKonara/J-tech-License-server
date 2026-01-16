# EXE Packing and Requirements Installation Process

**Upload Bridge v3.0.0**

---

## Overview

Upload Bridge uses **PyInstaller** to create a standalone Windows executable (`.exe`) that bundles all Python dependencies and application code into a single file. This document explains the complete build process from requirements installation to final executable creation.

---

## Table of Contents

1. [Licensing Model](#licensing-model)
2. [Requirements Installation](#requirements-installation)
3. [Build Process](#build-process)
4. [PyInstaller Configuration](#pyinstaller-configuration)
5. [Runtime Authentication Flow](#runtime-authentication-flow)
6. [Build Scripts](#build-scripts)
7. [Troubleshooting](#troubleshooting)

---

## Requirements Installation

### Step 1: Install Python Dependencies

**Location**: `apps/upload-bridge/requirements.txt`

**Command**:
```bash
cd apps/upload-bridge
pip install -r requirements.txt
```

**Key Dependencies**:

#### Core GUI Framework
- `PySide6>=6.5.0` - Qt-based GUI framework
- `pathlib2>=2.3.7` - Path utilities

#### Hardware Support
- `esptool>=4.6.0` - ESP8266/ESP32 chip support
- `pyserial>=3.5` - Serial communication

#### Media Processing
- `Pillow>=10.0.0` - Image processing
- `opencv-python>=4.8.0` - Video/image processing
- `imageio>=2.31.0` - Image I/O
- `imageio-ffmpeg>=0.4.8` - Video codec support
- `numpy>=1.24.0` - Numerical computing

#### Security & Authentication
- `cryptography>=41.0.0` - Encryption for token storage
- `certifi>=2023.0.0` - SSL certificate bundle for HTTPS connections
- `requests>=2.25.0` - HTTP requests for license server and authentication

#### Authentication System (Standard Library)
The following modules are part of Python's standard library and do **not** require pip installation:

- `webbrowser` - Opens browser for OAuth flows and magic link callbacks
- `http.server` - Local callback server for OAuth authorization code exchange
- `socket` - Network operations for OAuth callback server
- `threading` - Background processing for non-blocking OAuth flow

These modules are automatically included by PyInstaller and do not need to be listed in requirements.txt.

#### Utilities
- `pyyaml>=6.0` - YAML configuration parsing
- `colorama>=0.4.4` - Terminal colors
- `tqdm>=4.64.0` - Progress bars
- `psutil>=5.9.0` - System monitoring
- `jsonschema>=4.0.0` - JSON schema validation

#### Development Tools (Optional)
- `pytest>=7.0.0` - Testing framework
- `pytest-qt>=4.0.0` - Qt testing support
- `black>=22.0.0` - Code formatter
- `flake8>=4.0.0` - Linter

### Step 2: Install Build Tools

**PyInstaller** (required for building):
```bash
pip install pyinstaller
```

**Optional Build Tools**:
- `pywin32` - For Windows version embedding (optional)
- `upx` - For executable compression (optional, improves size)

### Step 3: External Tools (Not Packaged)

These tools are **NOT** included in the executable and must be installed separately on the target system:

- **Arduino CLI**: For Arduino chip support
  - Download: https://arduino.github.io/arduino-cli/
  
- **AVR Tools**: For AVR chip support
  - `avrdude` and `avr-gcc`
  - Download: https://www.microchip.com/en-us/tools-resources/develop/microchip-studio

- **STM32 Tools**: For STM32 chip support
  - `stm32flash` and `arm-none-eabi-gcc`
  - Download: https://developer.arm.com/downloads/-/gnu-rm

- **PIC Tools**: For PIC chip support
  - MPLAB X IDE and XC compilers
  - Download: https://www.microchip.com/en-us/tools-resources/develop/mplab-x-ide

- **Nuvoton Tools**: For Nuvoton chip support
  - Nu-Link tools
  - Download: https://www.nuvoton.com/tool-and-software/development-tool-hardware/

**Note**: The executable will detect these tools at runtime if they're installed in the system PATH.

### Authentication Dependencies

**Third-Party Packages** (installed via pip):
- `certifi` - SSL certificate bundle for reliable HTTPS connections
- `requests` - HTTP client for authentication and license validation
- `cryptography` - Token encryption and secure storage

**Standard Library Modules** (auto-included, no pip install needed):
- `webbrowser` - Opens system browser for OAuth flows
- `http.server` - Local HTTP server for OAuth callback handling
- `socket` - Network socket operations
- `threading` - Background thread management

**Why These Matter**:
- **SSL Certificates**: `certifi` ensures reliable HTTPS connections to the license server and OAuth provider
- **OAuth Flow**: Standard library modules handle the browser-based OAuth authorization code flow with PKCE
- **Offline Grace Period**: Tokens are encrypted and cached locally using `cryptography`

---

## Build Process

### Method 1: Using Build Script (Recommended)

**Script Location**: `apps/upload-bridge/scripts/build_executable.py`

**Command**:
```bash
cd apps/upload-bridge
python scripts/build_executable.py
```

**What It Does**:
1. ✅ Checks if PyInstaller is installed (installs if missing)
2. ✅ Verifies required dependencies are present
3. ✅ Cleans previous build artifacts (`build/`, `dist/`, `__pycache__/`)
4. ✅ Extracts version from `setup.py`
5. ✅ Uses PyInstaller spec file: `installer/windows/UploadBridge.spec`
6. ✅ Builds single-file executable: `dist/UploadBridge.exe`
7. ✅ Embeds version in executable metadata (Windows)
8. ✅ Records build hashes for verification

**Output**:
- Executable: `apps/upload-bridge/dist/UploadBridge.exe`
- Size: Typically 100-200 MB (depends on dependencies)

### Method 2: Direct PyInstaller Command

**Command**:
```bash
cd apps/upload-bridge
pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec
```

**What It Does**:
- Uses the spec file directly
- `--noconfirm`: Overwrites existing build without asking
- `--clean`: Cleans PyInstaller cache before building

### Method 3: Using Installer Builder

**Script Location**: `scripts/build_installers.py`

**Command**:
```bash
python scripts/build_installers.py --platform windows --version 3.0.0
```

**What It Does**:
1. Creates executable using build script
2. Optionally creates installer packages (MSI, ZIP, etc.)
3. Handles versioning and distribution

---

## PyInstaller Configuration

### Spec File Location

**File**: `apps/upload-bridge/installer/windows/UploadBridge.spec`

### Key Configuration Sections

#### 1. Hidden Imports

PyInstaller needs explicit imports for dynamically loaded modules:

```python
hiddenimports = [
    'PIL',              # Pillow (image processing)
    'cv2',              # OpenCV
    'numpy',            # NumPy
    'PySide6',          # Qt framework
    'cryptography',     # Encryption
    'ui',               # UI modules
    'core',             # Core modules
    'parsers',          # File parsers
    'uploaders',        # Hardware uploaders
    'domain',           # Domain logic
    # Authentication modules
    'core.oauth_handler',           # OAuth flow handler
    'core.auth_manager',            # Authentication manager
    'ui.dialogs.login_dialog',      # Login dialog
    'ui.dialogs.license_activation_dialog',  # Activation dialog
    'ui.dialogs.license_status_dialog',      # License status dialog
]

# Auto-collect all submodules
hiddenimports += collect_submodules('ui')
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('parsers')
hiddenimports += collect_submodules('uploaders')
```

**Note**: Standard library modules used for authentication (`webbrowser`, `http.server`, `socket`, `threading`) are automatically included by PyInstaller and do not need to be added to hidden imports.

#### 2. Data Files

Files that need to be bundled with the executable:

```python
import certifi

datas=[
    ('config/chip_database.yaml', 'config'),
    ('config/app_config.yaml', 'config'),
    ('firmware/templates', 'firmware/templates'),
    ('config', 'config'),
    ('ui', 'ui'),
    ('core', 'core'),
    ('parsers', 'parsers'),
    ('uploaders', 'uploaders'),
    ('LEDMatrixStudio_icon.ico', '.'),
    # SSL Certificate Bundle (critical for HTTPS connections)
    (certifi.where(), 'certifi'),
]
```

**Why CA Certificates Matter**: PyInstaller sometimes fails to bundle CA certificates correctly, causing SSL verification failures (`SSL: CERTIFICATE_VERIFY_FAILED`) on some Windows machines. Explicitly bundling `certifi` ensures reliable HTTPS connections for:
- License server authentication
- OAuth token exchange (Auth0)
- License validation API calls

#### 3. Executable Configuration

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UploadBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,              # Enable UPX compression
    console=False,         # No console window (GUI app)
    icon='LEDMatrixStudio_icon.ico',
)
```

**Key Options**:
- `console=False`: No console window (GUI application)
- `upx=True`: Compress executable (reduces size)
- `icon`: Application icon file
- `debug=False`: Production build (no debug info)

#### 4. Excluded Modules

Modules to exclude to reduce size:

```python
excludes=['matplotlib', 'pandas']  # Not used, exclude to save space
```

---

## Runtime Authentication Flow

### Installer vs Application Activation

**Important**: The installer only handles **file installation**. It does **NOT** handle license activation. Activation happens on **first app launch** after installation.

### Complete Flow Diagram

```
┌─────────────────────────────────────────┐
│  1. User Runs Installer                │
│     - Copies files to install location │
│     - Creates shortcuts                │
│     - NO activation required           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. User Launches App (First Time)     │
│     - Executable starts                │
│     - License check runs               │
│     - No valid token found             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Login Dialog Appears               │
│     - Email/Password tab               │
│     - Magic Link tab                   │
│     - OAuth (Google/GitHub) tab        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. User Logs In                       │
│     Option A: Email + Password         │
│     Option B: Magic Link (email sent)  │
│     Option C: OAuth (browser opens)    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Authentication Process             │
│     - Credentials sent to server       │
│     - Token received and encrypted     │
│     - Stored locally (encrypted)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  6. License Validation                 │
│     - Online check to license server   │
│     - License status retrieved         │
│     - Validation timestamp saved       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  7. App Ready                          │
│     - Main window opens                │
│     - 7-day offline grace period       │
│     - All features unlocked            │
└─────────────────────────────────────────┘
```

### Offline Grace Period

After successful online validation:

1. **First 7 Days**: App can run **completely offline** without re-authentication
2. **After 7 Days**: App requires **online re-authentication** to continue
3. **Background Refresh**: App may attempt to refresh tokens in the background if online

### Subsequent Launches

After initial activation:

```
Launch App
↓
Check for valid token (encrypted local storage)
↓
If token valid AND within grace period:
  → App opens immediately
Else:
  → Login dialog appears (re-authentication required)
```

### OAuth Flow Details

When using OAuth (Google/GitHub):

1. User clicks "Login with Google" or "Login with GitHub"
2. System browser opens to Auth0 Universal Login
3. User authenticates with provider
4. Auth0 redirects to local callback server (`http://127.0.0.1:<port>/callback`)
5. App receives authorization code
6. App exchanges code for tokens (PKCE flow)
7. Tokens stored encrypted locally
8. License validated with tokens

**Note**: The local callback server uses `http.server` (standard library) and runs on a random port to avoid conflicts.

---

## Build Scripts

### Main Build Script

**File**: `apps/upload-bridge/scripts/build_executable.py`

**Functions**:

1. **`check_dependencies()`**
   - Verifies PyInstaller is installed
   - Checks for PySide6, NumPy, etc.
   - Installs PyInstaller if missing

2. **`clean_build_directories()`**
   - Removes `build/` directory
   - Removes `dist/` directory
   - Removes `__pycache__/` directories

3. **`build_executable()`**
   - Gets version from `setup.py`
   - Updates spec file with version
   - Runs PyInstaller
   - Verifies executable was created
   - Embeds version metadata (Windows)
   - Records build hashes

4. **`get_version_from_setup()`**
   - Extracts version from `setup.py`
   - Default: "3.0.0"

5. **`embed_version_in_exe()`**
   - Embeds version in Windows executable metadata
   - Requires `pywin32` (optional)

### Alternative Build Script

**File**: `apps/upload-bridge/build_test_exe.py`

Simpler build script for quick testing:
- Cleans build directories
- Runs PyInstaller directly
- Verifies executable exists

---

## Build Output

### Directory Structure

After successful build:

```
apps/upload-bridge/
├── build/              # Temporary build files (can be deleted)
│   └── UploadBridge/
├── dist/               # Final output directory
│   └── UploadBridge.exe # Final executable
└── installer/
    └── windows/
        └── UploadBridge.spec  # PyInstaller spec file
```

### Executable Properties

- **Name**: `UploadBridge.exe`
- **Type**: Single-file executable (onefile mode)
- **Size**: ~100-200 MB (includes all dependencies)
- **Icon**: Uses `LEDMatrixStudio_icon.ico`
- **Console**: No console window (GUI app)
- **Compression**: UPX compression enabled

### What's Included

✅ **All Python Dependencies**:
- PySide6 (Qt framework)
- NumPy, OpenCV, Pillow (media processing)
- Cryptography (security)
- All other requirements.txt packages

✅ **Application Code**:
- All `ui/` modules
- All `core/` modules
- All `parsers/` modules
- All `uploaders/` modules
- All `domain/` modules

✅ **Data Files**:
- Configuration files (`config/`)
- Firmware templates (`firmware/templates/`)
- Application icon

❌ **NOT Included** (must be installed separately):
- External tools (Arduino CLI, avrdude, etc.)
- System libraries (handled by PyInstaller)

---

## Build Process Flow

```
┌─────────────────────────────────────────┐
│  1. Install Requirements               │
│     pip install -r requirements.txt    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Install Build Tools                 │
│     pip install pyinstaller             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Run Build Script                    │
│     python scripts/build_executable.py  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. PyInstaller Analysis                │
│     - Scans main.py                     │
│     - Finds all imports                 │
│     - Collects dependencies             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Bundle Creation                     │
│     - Packages Python runtime           │
│     - Includes all modules              │
│     - Adds data files                   │
│     - Compresses with UPX               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  6. Executable Output                   │
│     dist/UploadBridge.exe               │
│     (Ready for distribution)            │
└─────────────────────────────────────────┘
```

---

## Requirements Installation Details

### Virtual Environment (Recommended)

**Create Virtual Environment**:
```bash
cd apps/upload-bridge
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**Install Requirements**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### System-Wide Installation

**Install to System Python**:
```bash
pip install -r requirements.txt
```

**Note**: May require administrator/sudo privileges.

### Development Installation

**Install with Development Tools**:
```bash
pip install -r requirements.txt
pip install pytest pytest-qt black flake8
```

Or use setup.py:
```bash
pip install -e .[dev]
```

---

## Troubleshooting

### Common Build Issues

#### 1. "PyInstaller not found"

**Solution**:
```bash
pip install pyinstaller
```

#### 2. "Module not found" errors during build

**Cause**: Missing hidden imports in spec file

**Solution**: Add missing module to `hiddenimports` in spec file:
```python
hiddenimports += ['missing_module']
```

#### 3. "File not found" errors

**Cause**: Data files not included in spec file

**Solution**: Add to `datas` list in spec file:
```python
datas=[
    ('path/to/file', 'destination'),
]
```

#### 4. Large executable size

**Causes**:
- Too many dependencies included
- UPX compression disabled
- Debug symbols included

**Solutions**:
- Enable UPX: `upx=True` in spec file
- Exclude unused modules: `excludes=['module']`
- Set `debug=False` in spec file

#### 5. Executable doesn't run

**Check**:
- Run from command line to see errors
- Check Windows Event Viewer for crashes
- Verify all data files are included
- Check for missing DLLs (use Dependency Walker)

#### 6. "ImportError" at runtime

**Cause**: Dynamic imports not detected by PyInstaller

**Solution**: Add to `hiddenimports`:
```python
hiddenimports += ['module.submodule']
```

#### 7. "SSL: CERTIFICATE_VERIFY_FAILED" errors

**Cause**: CA certificates not bundled correctly by PyInstaller

**Symptoms**:
- Login fails with SSL errors
- OAuth flow fails to connect
- License validation fails

**Solution**: Ensure `certifi` is bundled in spec file:
```python
import certifi
datas=[
    # ... other data files ...
    (certifi.where(), 'certifi'),
]
```

**Verification**: After build, check that `certifi/cacert.pem` exists in the bundled data.

#### 8. OAuth callback server fails to start

**Cause**: Port conflicts or firewall blocking

**Symptoms**:
- "Address already in use" errors
- OAuth flow times out
- Login dialog shows connection errors

**Solution**:
- The app automatically tries different ports
- Check firewall settings allow localhost connections
- Verify no other apps are using ports 8000-9000

#### 9. Login dialog doesn't appear on first launch

**Cause**: Stale token or cache issue

**Solution**: Delete cached authentication data:
```
%USERPROFILE%\.upload_bridge\auth\*
```

**Note**: This will require re-authentication on next launch.

### Verification Steps

**1. Check Executable Exists**:
```bash
dir dist\UploadBridge.exe
```

**2. Test Executable**:
```bash
dist\UploadBridge.exe
```

**3. Check File Size**:
- Should be 100-200 MB
- If too small (< 50 MB), dependencies may be missing
- If too large (> 500 MB), may include unnecessary files

**4. Verify Dependencies**:
```bash
# Use Dependency Walker or similar tool
# Check for missing DLLs
```

---

## Build Optimization

### Size Optimization

**1. Enable UPX Compression**:
```python
upx=True,  # In spec file
```

**2. Exclude Unused Modules**:
```python
excludes=['matplotlib', 'pandas', 'scipy']
```

**3. Use OneFile Mode** (already enabled):
- Single executable file
- Extracts to temp directory at runtime

### Performance Optimization

**1. Disable Console** (already enabled):
```python
console=False,  # No console window
```

**2. Strip Debug Symbols**:
```python
strip=True,  # Remove debug info
```

**3. Optimize Python Bytecode**:
```python
optimize=2,  # Maximum optimization
```

---

## Continuous Integration

### GitHub Actions

**Workflow**: `.github/workflows/installer-validate.yml`

**Build Command**:
```yaml
- name: Build executable
  run: |
    cd apps/upload-bridge
    pyinstaller --noconfirm --clean installer/windows/UploadBridge.spec
```

**Verification**:
- Checks executable exists
- Verifies file size
- Tests executable launch

---

## Summary

### Quick Build Checklist

- [ ] Install Python 3.10+ (3.10, 3.11, or 3.12)
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Install PyInstaller: `pip install pyinstaller`
- [ ] Run build script: `python scripts/build_executable.py`
- [ ] Verify executable: `dist/UploadBridge.exe`
- [ ] Test executable launch
- [ ] Check file size (should be 100-200 MB)

### Build Time

- **First Build**: 5-10 minutes (downloads dependencies)
- **Subsequent Builds**: 2-5 minutes (uses cache)

### Output

- **Location**: `apps/upload-bridge/dist/UploadBridge.exe`
- **Size**: ~100-200 MB
- **Type**: Standalone executable (no Python installation required)

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0
