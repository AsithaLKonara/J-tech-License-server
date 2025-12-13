# Upload Bridge - Installation Guide

Complete installation instructions for Windows, macOS, and Linux.

---

## System Requirements

### Windows
- **OS**: Windows 10 or Windows 11
- **Python**: Python 3.10 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for application + dependencies
- **Additional**: USB port for device connection

### macOS
- **OS**: macOS 10.15 (Catalina) or later
- **Python**: Python 3.10 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for application + dependencies
- **Additional**: USB port for device connection

### Linux
- **OS**: Ubuntu 20.04+, Debian 11+, or Fedora 34+
- **Python**: Python 3.10 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for application + dependencies
- **Additional**: USB port for device connection, USB permissions

---

## Windows Installation

### Option 1: Using Installer (Recommended)

1. **Download Installer**
   - Download `upload_bridge_3.0.0.msi` from releases
   - Or build from source: `installer\windows\build_installer.ps1`

2. **Run Installer**
   - Double-click the `.msi` file
   - Follow the installation wizard
   - Choose installation location (default: `C:\Program Files\UploadBridge`)
   - Select components to install

3. **Launch Application**
   - Find "Upload Bridge" in Start Menu
   - Or use desktop shortcut
   - Or run from command line: `upload-bridge`

4. **Verify Installation**
   - Application should launch successfully
   - Check that all tabs are visible
   - Try opening a sample pattern

### Option 2: Manual Installation

1. **Install Python**
   - Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
   - Run installer
   - **Important**: Check "Add Python to PATH" during installation
   - Verify: Open Command Prompt, run `python --version`

2. **Clone or Download Repository**
   ```bash
   git clone https://github.com/your-repo/upload_bridge.git
   cd upload_bridge
   ```
   Or download and extract ZIP file

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   python main.py
   ```

5. **Create Desktop Shortcut (Optional)**
   - Right-click `main.py`
   - Create shortcut
   - Move shortcut to Desktop
   - Rename to "Upload Bridge"

---

## macOS Installation

### Option 1: Using Installer (Recommended)

1. **Download Installer**
   - Download `upload_bridge_3.0.0.pkg` from releases
   - Or build from source: `installer/macos/build_installer.sh`

2. **Run Installer**
   - Double-click the `.pkg` file
   - Follow the installation wizard
   - Enter administrator password when prompted
   - Installation location: `/Applications/UploadBridge`

3. **Launch Application**
   - Open Applications folder
   - Double-click "Upload Bridge"
   - Or use Spotlight: Cmd+Space, type "Upload Bridge"

4. **Verify Installation**
   - Application should launch successfully
   - Check that all tabs are visible

### Option 2: Manual Installation

1. **Install Python**
   - Python 3.10+ is included with macOS, or
   - Download from [python.org](https://www.python.org/downloads/)
   - Or use Homebrew: `brew install python@3.10`
   - Verify: Open Terminal, run `python3 --version`

2. **Install Xcode Command Line Tools** (if needed)
   ```bash
   xcode-select --install
   ```

3. **Clone or Download Repository**
   ```bash
   git clone https://github.com/your-repo/upload_bridge.git
   cd upload_bridge
   ```

4. **Install Dependencies**

   **Full Installation** (recommended - all features):
   ```bash
   pip3 install -r requirements.txt
   ```
   
   **Minimal Installation** (basic features only):
   ```bash
   pip3 install -r requirements_simple.txt
   ```
   
   See [Minimal vs Full Installation](#minimal-vs-full-installation) section for details.

5. **Verify Installation**
   ```bash
   python3 main.py
   ```

6. **Create Application Bundle (Optional)**
   - Use Automator or create `.app` bundle
   - Or use `py2app` to create standalone app

---

## Minimal vs Full Installation

Upload Bridge supports two installation modes:

### Full Installation (Recommended)

**Use**: `requirements.txt`

**Includes**:
- All core dependencies (GUI, serial communication, file handling)
- Media conversion support (images, GIFs, videos)
- License system security
- Health monitoring
- Schema validation
- HTTP requests
- All optional utilities

**Installation**:
```bash
pip install -r requirements.txt
```

**Features Available**:
- ✅ All drawing tools
- ✅ All automation actions
- ✅ Media import/export (images, GIFs, videos)
- ✅ License activation
- ✅ Health monitoring
- ✅ Full pattern library
- ✅ All hardware support

### Minimal Installation

**Use**: `requirements_simple.txt`

**Includes**:
- Core dependencies only (GUI, serial communication, file handling)
- Basic ESP chip support

**Installation**:
```bash
pip install -r requirements_simple.txt
```

**Missing Features** (compared to full install):
- ❌ Media conversion (needs: opencv-python, imageio, imageio-ffmpeg, numpy)
- ❌ License system (needs: cryptography)
- ❌ Health monitoring (needs: psutil)
- ❌ Schema validation (needs: jsonschema)
- ❌ HTTP requests (needs: requests)
- ❌ Path utilities for older Python (needs: pathlib2)

**Features Still Available**:
- ✅ All drawing tools
- ✅ All automation actions
- ✅ Pattern creation and editing
- ✅ Basic import/export (without media conversion)
- ✅ Hardware upload support
- ✅ Frame and layer management

**When to Use Minimal Install**:
- Limited disk space
- Quick testing/prototyping
- Systems where media conversion isn't needed
- Embedded systems with resource constraints

**Upgrading from Minimal to Full**:
```bash
pip install -r requirements.txt
```
This will install all additional dependencies without removing existing ones.

---

## Linux Installation

### Option 1: Using Package Manager

#### Ubuntu/Debian (DEB Package)

1. **Download DEB Package**
   - Download `upload-bridge_3.0.0_amd64.deb` from releases
   - Or build from source: `installer/linux/deb/build_deb.sh`

2. **Install Package**
   ```bash
   sudo dpkg -i upload-bridge_3.0.0_amd64.deb
   ```

3. **Fix Dependencies (if needed)**
   ```bash
   sudo apt-get install -f
   ```

4. **Launch Application**
   ```bash
   upload-bridge
   ```
   Or find in Applications menu

#### Fedora/RHEL (RPM Package)

1. **Download RPM Package**
   - Download `upload-bridge-3.0.0-1.x86_64.rpm` from releases
   - Or build from source: `installer/linux/rpm/build_rpm.sh`

2. **Install Package**
   ```bash
   sudo rpm -ivh upload-bridge-3.0.0-1.x86_64.rpm
   ```

3. **Launch Application**
   ```bash
   upload-bridge
   ```

### Option 2: Manual Installation

1. **Install Python**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3.10 python3-pip
   
   # Fedora
   sudo dnf install python3.10 python3-pip
   ```

2. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev python3-tk
   
   # Fedora
   sudo dnf install python3-devel python3-tkinter
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/your-repo/upload_bridge.git
   cd upload_bridge
   ```

4. **Install Python Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Set USB Permissions** (for device flashing)
   ```bash
   # Add user to dialout group (for serial port access)
   sudo usermod -a -G dialout $USER
   # Log out and back in for changes to take effect
   ```

6. **Verify Installation**
   ```bash
   python3 main.py
   ```

7. **Create Desktop Entry (Optional)**
   ```bash
   # Create .desktop file in ~/.local/share/applications/
   cat > ~/.local/share/applications/upload-bridge.desktop << EOF
   [Desktop Entry]
   Name=Upload Bridge
   Comment=LED Pattern Designer
   Exec=/usr/bin/python3 /path/to/upload_bridge/main.py
   Icon=upload-bridge
   Terminal=false
   Type=Application
   Categories=Graphics;Development;
   EOF
   ```

---

## Python Installation (If Needed)

### Windows
1. Visit [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.10 or higher
3. Run installer
4. **Important**: Check "Add Python to PATH"
5. Verify: `python --version` in Command Prompt

### macOS
- Python 3.10+ may be pre-installed
- Or use Homebrew: `brew install python@3.10`
- Or download from python.org

### Linux
```bash
# Ubuntu/Debian
sudo apt-get install python3.10 python3-pip

# Fedora
sudo dnf install python3.10 python3-pip
```

---

## Dependency Installation

### Installation Options

**Full Installation** (recommended - all features):
```bash
pip install -r requirements.txt
```

**Minimal Installation** (basic features only):
```bash
pip install -r requirements_simple.txt
```

See [Minimal vs Full Installation](#minimal-vs-full-installation) section above for detailed comparison.

### Core Dependencies
All dependencies are listed in `requirements.txt`. For minimal install, see `requirements_simple.txt`.

```bash
# Install all dependencies (full install)
pip install -r requirements.txt

# Or install individually
pip install PySide6>=6.5.0
pip install esptool>=4.6.0
pip install pyserial>=3.5
pip install Pillow>=10.0.0
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0
# ... (see requirements.txt for complete list)
```

### Platform-Specific Dependencies

#### Windows
- No additional dependencies required
- USB drivers for your microcontroller (installed automatically)

#### macOS
- Xcode Command Line Tools: `xcode-select --install`
- USB drivers for your microcontroller

#### Linux
- Python development headers: `python3-dev` or `python3-devel`
- Tkinter: `python3-tk` or `python3-tkinter`
- USB permissions: Add user to `dialout` group

---

## Verification Steps

After installation, verify everything works:

1. **Launch Application**
   ```bash
   python main.py
   # or
   upload-bridge
   ```

2. **Check All Tabs**
   - Design Tools tab should open
   - Media Upload tab should be accessible
   - Flash tab should be visible
   - All tabs should be functional

3. **Test Basic Functionality**
   - Create a new pattern
   - Draw on canvas
   - Add a frame
   - Save project

4. **Test Device Connection** (if hardware available)
   - Connect microcontroller
   - Select chip type in Flash tab
   - Verify device detection

---

## Troubleshooting Installation Issues

### Python Not Found
**Problem**: `python: command not found` or `python3: command not found`

**Solution**:
- Windows: Reinstall Python with "Add to PATH" checked
- macOS: Use `python3` instead of `python`
- Linux: Install python3: `sudo apt-get install python3`

### Module Not Found Errors
**Problem**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or install specific module
pip install <module-name>
```

### Import Errors on Windows
**Problem**: DLL or import errors

**Solution**:
- Install Visual C++ Redistributable
- Reinstall Python
- Use virtual environment: `python -m venv venv && venv\Scripts\activate`

### USB Permission Issues (Linux)
**Problem**: Cannot access serial port

**Solution**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, or:
newgrp dialout
```

### Installer Won't Run
**Problem**: Installer fails or won't start

**Solution**:
- Check file integrity (re-download)
- Run as administrator (Windows/Linux)
- Check disk space
- Try manual installation instead

### Application Crashes on Launch
**Problem**: Application crashes immediately

**Solution**:
- Check Python version: `python --version` (needs 3.10+)
- Check dependencies: `pip list`
- Check error logs
- Try running from command line to see error messages

---

## Uninstallation

### Windows (Installer)
1. Open Settings → Apps
2. Find "Upload Bridge"
3. Click "Uninstall"

### Windows (Manual)
1. Delete installation directory
2. Remove Start Menu shortcuts
3. Remove desktop shortcuts

### macOS (Installer)
1. Open Applications folder
2. Drag "Upload Bridge" to Trash
3. Empty Trash

### macOS (Manual)
1. Delete application directory
2. Remove from Applications if copied there

### Linux (Package Manager)
```bash
# DEB
sudo dpkg -r upload-bridge

# RPM
sudo rpm -e upload-bridge
```

### Linux (Manual)
1. Delete installation directory
2. Remove desktop entry: `rm ~/.local/share/applications/upload-bridge.desktop`
3. Remove from PATH if added

---

## Upgrade Instructions

### From Previous Version

1. **Backup Your Projects**
   - Copy all `.ledproj` files to safe location
   - Export any important patterns

2. **Uninstall Old Version**
   - Follow uninstallation steps above

3. **Install New Version**
   - Follow installation steps for your platform

4. **Verify Projects**
   - Open old project files
   - Verify they load correctly
   - Projects are automatically migrated if needed

---

## Next Steps

After successful installation:

1. **Read Quick Start Guide**: See `docs/QUICKSTART.md`
2. **Read User Manual**: See `docs/USER_MANUAL.md`
3. **Try Example Patterns**: Check `examples/` directory
4. **Connect Hardware**: Follow hardware setup guide

---

## Support

If you encounter installation issues:

1. Check this guide's troubleshooting section
2. Review `docs/TROUBLESHOOTING.md`
3. Check GitHub Issues for known problems
4. Create a new issue with:
   - Operating system and version
   - Python version
   - Error messages
   - Installation method used

---

**Happy Installing!** 🚀

