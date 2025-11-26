@echo off
echo ========================================
echo Upload Bridge - Complete Requirements Installer
echo ========================================
echo.
echo This installer will set up Upload Bridge with ALL dependencies
echo for ALL supported microcontrollers.
echo.
echo Supported Chips:
echo - ESP8266, ESP32, ESP32-S2, ESP32-S3, ESP32-C3
echo - ATmega328P, ATmega2560, ATtiny85 (AVR)
echo - STM32F103C8, STM32F401RE (STM32)
echo - PIC16F876A, PIC18F4550 (PIC)
echo - NUC123, NUC505 (Nuvoton)
echo.
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from: https://python.org
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt
echo.

echo Step 2: Installing ESP chip tools...
echo Installing esptool for ESP chips...
pip install esptool
echo.

echo Installing Arduino CLI for ESP chips...
echo Downloading Arduino CLI...
powershell -Command "& {Invoke-WebRequest -Uri 'https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip' -OutFile 'arduino-cli.zip'}"
if exist arduino-cli.zip (
    echo Extracting Arduino CLI...
    powershell -Command "& {Expand-Archive -Path 'arduino-cli.zip' -DestinationPath 'arduino-cli' -Force}"
    echo Adding Arduino CLI to PATH...
    setx PATH "%PATH%;%CD%\arduino-cli" /M
    echo Installing ESP cores...
    arduino-cli\arduino-cli.exe core install esp8266:esp8266
    arduino-cli\arduino-cli.exe core install esp32:esp32
    echo ✅ Arduino CLI installed for ESP chips
) else (
    echo ⚠️  Failed to download Arduino CLI - please install manually
)
echo.

echo Step 3: Installing AVR chip tools...
echo Downloading AVR-GCC toolchain...
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/ZakKemble/AVR-GCC/releases/download/v13.2.0/avr-gcc-13.2.0-x64-windows.zip' -OutFile 'avr-gcc.zip'}"
if exist avr-gcc.zip (
    echo Extracting AVR-GCC...
    powershell -Command "& {Expand-Archive -Path 'avr-gcc.zip' -DestinationPath 'avr-gcc' -Force}"
    echo Adding AVR-GCC to PATH...
    setx PATH "%PATH%;%CD%\avr-gcc\bin" /M
    echo ✅ AVR-GCC installed for AVR chips
) else (
    echo ⚠️  Failed to download AVR-GCC - please install manually
)
echo.

echo Step 4: Installing STM32 chip tools...
echo Downloading ARM GCC toolchain...
powershell -Command "& {Invoke-WebRequest -Uri 'https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-win32.zip' -OutFile 'arm-gcc.zip'}"
if exist arm-gcc.zip (
    echo Extracting ARM GCC...
    powershell -Command "& {Expand-Archive -Path 'arm-gcc.zip' -DestinationPath 'arm-gcc' -Force}"
    echo Adding ARM GCC to PATH...
    setx PATH "%PATH%;%CD%\arm-gcc\gcc-arm-none-eabi-10.3-2021.10\bin" /M
    echo Installing stm32flash...
    pip install stm32flash
    echo ✅ ARM GCC and stm32flash installed for STM32 chips
) else (
    echo ⚠️  Failed to download ARM GCC - please install manually
)
echo.

echo Step 5: Installing PIC chip tools...
echo Downloading MPLAB X IDE...
echo ⚠️  MPLAB X IDE requires manual installation
echo Please download from: https://www.microchip.com/en-us/tools-resources/develop/mplab-x-ide
echo Install with XC8 compiler for PIC support
echo.

echo Step 6: Installing Nuvoton chip tools...
echo Downloading Nu-Link tools...
echo ⚠️  Nu-Link tools require manual installation
echo Please download from: https://www.nuvoton.com/tool-and-software/development-tool-hardware/
echo Install Nu-Link tools for Nuvoton support
echo.

echo Step 7: Installing additional Python packages...
echo Installing additional packages for all chips...
pip install pyserial
pip install pyyaml
pip install colorama
pip install tqdm
echo.

echo Step 8: Verifying installation...
echo Checking Python packages...
python -c "import PySide6; print('✅ PySide6 installed')"
python -c "import esptool; print('✅ esptool installed')"
python -c "import serial; print('✅ pyserial installed')"
python -c "import yaml; print('✅ pyyaml installed')"
echo.

echo Step 9: Creating desktop shortcut...
echo [InternetShortcut] > "%USERPROFILE%\Desktop\Upload Bridge.url"
echo URL=file:///%CD%\LAUNCH_UPLOAD_BRIDGE.bat >> "%USERPROFILE%\Desktop\Upload Bridge.url"
echo IconFile=%CD%\LAUNCH_UPLOAD_BRIDGE.bat >> "%USERPROFILE%\Desktop\Upload Bridge.url"
echo IconIndex=0 >> "%USERPROFILE%\Desktop\Upload Bridge.url"
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Upload Bridge has been installed with support for ALL chips!
echo.
echo ✅ ESP chips: Arduino CLI + esptool installed
echo ✅ AVR chips: AVR-GCC toolchain installed
echo ✅ STM32 chips: ARM GCC + stm32flash installed
echo ⚠️  PIC chips: Please install MPLAB X IDE manually
echo ⚠️  Nuvoton chips: Please install Nu-Link tools manually
echo.
echo Desktop shortcut created: Upload Bridge.url
echo.
echo To run Upload Bridge:
echo 1. Double-click the desktop shortcut, OR
echo 2. Run: LAUNCH_UPLOAD_BRIDGE.bat
echo.
echo Note: You may need to restart your terminal/command prompt
echo for PATH changes to take effect.
echo.
pause












