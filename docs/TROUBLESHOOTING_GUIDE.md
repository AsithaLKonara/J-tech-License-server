# Upload Bridge - Troubleshooting Guide

## Quick Fix for Installation Issues

If you're having trouble installing or running Upload Bridge on another PC, follow these steps:

### Step 1: Install Python 3.12
1. Download Python 3.12 from: https://python.org/downloads/
2. **IMPORTANT**: During installation, check "Add Python to PATH"
3. Verify installation by opening Command Prompt and typing: `python --version`

### Step 2: Use the Simple Installer
1. Run `install_simple.bat` (not the complex installer)
2. This installs only essential dependencies
3. Wait for completion

### Step 3: Test Installation
1. Run `test_installation.py` to verify everything works
2. If tests pass, you're ready to go!

### Step 4: Run Upload Bridge
1. Double-click `RUN_SIMPLE.bat`
2. Or run: `python main.py`

## Common Issues and Solutions

### Issue 1: "Python is not recognized"
**Solution:**
- Python is not installed or not in PATH
- Reinstall Python and check "Add Python to PATH"
- Or manually add Python to PATH in System Environment Variables

### Issue 2: "No module named 'PySide6'"
**Solution:**
```bash
pip install PySide6
```
Or run the simple installer: `install_simple.bat`

### Issue 3: "Import error" or "ModuleNotFoundError"
**Solution:**
- Make sure you're in the upload_bridge directory
- Run: `pip install -r requirements_simple.txt`
- Check that all files are present

### Issue 4: Application crashes on startup
**Solution:**
1. Run `test_installation.py` to identify the issue
2. Check Python version (needs 3.8+)
3. Reinstall dependencies: `pip install -r requirements_simple.txt`

### Issue 5: GUI doesn't appear
**Solution:**
- Check if you have a display (for remote connections)
- Try running in Command Prompt: `python main.py`
- Check for error messages

## Manual Installation (if batch files don't work)

1. Open Command Prompt in the upload_bridge directory
2. Run these commands:
```bash
python -m pip install --upgrade pip
pip install PySide6
pip install pyserial
pip install pyyaml
pip install colorama
pip install tqdm
pip install esptool
```

## File Structure Check

Make sure these files exist:
```
upload_bridge/
├── main.py
├── requirements_simple.txt
├── install_simple.bat
├── RUN_SIMPLE.bat
├── test_installation.py
├── ui/
│   └── main_window.py
├── core/
│   └── pattern.py
└── parsers/
    └── parser_registry.py
```

## Still Having Issues?

1. **Check Python version**: `python --version` (should be 3.8+)
2. **Check pip**: `pip --version`
3. **Run test script**: `python test_installation.py`
4. **Check error messages**: Look for specific error details
5. **Try manual installation**: Use pip commands above

## For Advanced Users

If you need full functionality with all chip support:
1. Use `install_all_requirements.bat` (more complex)
2. Install additional tools manually as needed
3. Check individual chip requirements in the main requirements.txt

## Support

If you're still having issues:
1. Run `test_installation.py` and share the output
2. Check the error messages carefully
3. Make sure Python 3.8+ is installed and in PATH
4. Try the manual installation steps above










