# 📦 J-Tech Pixel LED Upload Bridge - EXE Packing Guide

This guide explains how to package the Python application into a secure, production-ready Windows executable.

---

## 🏗️ The Build Pipeline

We use **PyInstaller** to bundle the application along with its dependencies and static assets.

### 🛡️ Secure Production Builder (`build_prod_exe.py`)
This script is specifically designed for releases:
1. **Environment Wipe**: Cleans previous `build/` and `dist/` artifacts.
2. **Security Audit**: Automatically detects and temporarily moves `license_keys.yaml` to prevent development keys from being bundled.
3. **Spec Enforcement**: Uses `installer/windows/UploadBridge.spec` for consistent bundling.

---

## 🚀 How to Build

### Prerequisites
- Python 3.10
- PyInstaller (`pip install pyinstaller`)
- All requirements installed (`pip install -r apps/upload-bridge/requirements.txt`)

### Execution
Run the builder from the root:
```bash
python apps/upload-bridge/build_prod_exe.py
```

---

## 📄 What's Bundled?
The `.spec` file ensures the following items are included in the EXE:
- **Core Logic**: All Python modules in `apps/upload-bridge/`.
- **Assets**: Icons (`.ico`) and firmware templates.
- **Resources**: UI definitions and style sheets.

---

## ⚠️ Troubleshooting

### Build Fails with "Permission Error"
- Close any running instances of `UploadBridge.exe`.
- Ensure the `dist/` folder is not open in another window.

### Missing Resources
- Verify the relative paths in `apps/upload-bridge/main.py` against the file system.

---

**Built with**: PyInstaller 6.x  
**Platform**: Windows 10/11
