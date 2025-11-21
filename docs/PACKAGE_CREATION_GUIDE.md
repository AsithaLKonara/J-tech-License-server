# Package Creation Guide

This guide explains how to create different package variants for Upload Bridge.

## Package Variants

### 1. Development/Internal Package

**Use case**: Internal testing, development, or lab environments where offline license keys are acceptable.

**Command**:
```python
from create_deployment_package import create_deployment_package
create_deployment_package(include_license_keys=True)
```

**Includes**:
- ✅ All executables (UploadBridge.exe, UploadBridgeInstaller.exe)
- ✅ Complete documentation
- ✅ Diagnostic tools
- ✅ **LICENSE_KEYS.txt** (offline activation keys)

### 2. Production/Hardened Package

**Use case**: Public distribution, customer deployments, or any scenario where you don't want to bundle offline license keys.

**Command**:
```python
from create_deployment_package import create_deployment_package
create_deployment_package(include_license_keys=False)
```

**Includes**:
- ✅ All executables (UploadBridge.exe, UploadBridgeInstaller.exe)
- ✅ Complete documentation
- ✅ Diagnostic tools
- ❌ **No LICENSE_KEYS.txt** (users must obtain keys separately)

## Quick Start

### Using the Script Directly

1. **Edit `create_deployment_package.py`**:
   - Change the default `include_license_keys` parameter if needed
   - Or call it programmatically with your desired setting

2. **Run the script**:
   ```bash
   python create_deployment_package.py
   ```

3. **Check the output**:
   - Package will be created in `dist/UploadBridge_UniversalFix_Deployment_YYYYMMDD_HHMMSS/`
   - Review `START_HERE.txt` to verify the package contents match your intent

## Package Contents

Both variants include:

- **Executables**: Standalone application and installer
- **Documentation**: 
  - PACKAGE_README.md
  - AUTO_DETECT_AND_BRIGHTNESS_SUMMARY.md
  - UNIVERSAL_FIX_SUMMARY.md
  - COMPLETE_FLOW_DOCUMENTATION.md
  - DIAGNOSTIC_TOOLS_README.md
  - TROUBLESHOOTING_GUIDE.md
  - README.md
- **Diagnostic Tools**: All verification scripts and test patterns

## Security Considerations

- **Offline License Keys**: If included, these are plain text and should be treated as sensitive
- **Production Deployments**: Always use `include_license_keys=False` for public distribution
- **Internal Use**: Development/internal packages can safely include keys for convenience

## Notes

- The script automatically detects the source package location
- Missing files are reported but don't stop package creation
- Package size and file counts are displayed in the console output

