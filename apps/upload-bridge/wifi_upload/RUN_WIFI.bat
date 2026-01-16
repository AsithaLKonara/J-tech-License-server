@echo off
echo 🎨 ESP8266 Pattern Flasher with WiFi Upload
echo ==========================================
echo Starting enhanced GUI application...
echo Features:
echo   ✓ USB Flash (original functionality)
echo   ✓ WiFi Upload (new!)
echo   ✓ Web interface integration
echo   ✓ Real-time status monitoring
echo ==========================================
echo.

python RUN_WIFI.py

if errorlevel 1 (
    echo.
    echo ❌ Error occurred. Please check:
    echo   1. Python is installed and in PATH
    echo   2. Dependencies are installed: pip install -r requirements.txt
    echo   3. Try running: python main.py (original version)
    echo.
    pause
)

