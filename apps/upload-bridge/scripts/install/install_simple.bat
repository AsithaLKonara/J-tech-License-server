@echo off
echo ========================================
echo Upload Bridge - Simple Installer
echo ========================================

REM Change to the directory where this batch file is located
cd /d "%~dp0"
echo.
echo This installer will set up Upload Bridge with minimal dependencies
echo for basic functionality on any Windows PC.
echo.
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from: https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
python --version

echo.
echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing core dependencies...
pip install -r requirements_simple.txt

echo.
echo Step 3: Verifying installation...
python -c "import PySide6; print('✅ PySide6 installed')" 2>nul || echo "❌ PySide6 failed"
python -c "import serial; print('✅ pyserial installed')" 2>nul || echo "❌ pyserial failed"
python -c "import yaml; print('✅ pyyaml installed')" 2>nul || echo "❌ pyyaml failed"
python -c "import colorama; print('✅ colorama installed')" 2>nul || echo "❌ colorama failed"
python -c "import tqdm; print('✅ tqdm installed')" 2>nul || echo "❌ tqdm failed"

echo.
echo Step 4: Testing application...
python -c "import sys; sys.path.insert(0, '.'); from main import main; print('✅ Application imports successfully')" 2>nul || echo "❌ Application import failed"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run Upload Bridge:
echo 1. Double-click: RUN_SIMPLE.bat
echo 2. Or run: python main.py
echo.
echo If you encounter any issues:
echo 1. Make sure Python 3.8+ is installed
echo 2. Run this installer again
echo 3. Check that all dependencies installed correctly
echo.
pause
