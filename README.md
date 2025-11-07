# Upload Bridge - LED Matrix Studio

Universal firmware uploader for LED patterns across multiple microcontroller platforms.

## Features

- **🎬 Media Upload**: Convert images, GIFs, and videos to LED patterns (PNG, JPG, BMP, GIF, MP4, AVI, MOV, MKV, WebM)
- **Multi-Platform Support**: ESP8266, ESP32, AVR (ATmega/ATtiny), STM32, PIC, Nuvoton
- **Advanced Brightness Control**: Gamma correction, per-channel control, hardware-specific mapping
- **Pattern Speed Control**: Variable speed with keyframes, easing functions, frame interpolation
- **Real-time Preview**: Live pattern visualization with brightness adjustment
- **Auto-Detection**: Automatic pattern information detection from various file formats
- **Professional UI**: Modern, responsive interface with scrollable areas

## Media Upload Feature

Upload Bridge now supports converting images, GIFs, and videos directly into LED patterns!

### Supported Formats
- **Images**: PNG, JPG, JPEG, BMP
- **Animations**: GIF (animated)
- **Videos**: MP4, AVI, MOV, MKV, WebM

### How to Use Media Upload
1. Launch Upload Bridge
2. Go to the **🎬 Media Upload** tab
3. Click **"Select Media File"** and choose your image/GIF/video
4. Adjust conversion settings:
   - **Dimensions**: Set target LED matrix size (e.g., 64x32)
   - **FPS**: Frame rate for video/GIF conversion
   - **Brightness**: Adjust brightness (0-100%)
   - **Color Order**: Choose RGB, GRB, BRG, etc.
5. Preview the conversion result
6. Click **"Convert to LED Pattern"**
7. Load the pattern and flash to your device!

### Conversion Tips
- Use high contrast images for better LED visibility
- Shorter videos (under 10 seconds) work best
- GIFs with fewer colors convert faster
- Test with small dimensions first, then scale up
- Adjust brightness based on your LED strip type

## Quick Start

### Windows
1. Run `install_requirements.bat` to install Python dependencies
2. Install additional tools as prompted
3. Run `python main.py` to start the application

### Linux/macOS
1. Run `chmod +x install_requirements.sh && ./install_requirements.sh`
2. Install additional tools as prompted
3. Run `python3 main.py` to start the application

## Installation

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Additional Tools Required

#### ESP Chips (ESP8266, ESP32)
- **Arduino CLI**: Download from [arduino.github.io](https://arduino.github.io/arduino-cli/)
- Install ESP cores:
  ```bash
  arduino-cli core install esp8266:esp8266
  arduino-cli core install esp32:esp32
  ```

#### AVR Chips (ATmega, ATtiny)
- **AVR-GCC Toolchain**: Download from [Microchip Studio](https://www.microchip.com/en-us/tools-resources/develop/microchip-studio)
- **avrdude**: Usually included with AVR-GCC

#### STM32 Chips
- **ARM GCC Toolchain**: Download from [ARM Developer](https://developer.arm.com/downloads/-/gnu-rm)
- **stm32flash**: Install via package manager or compile from source

#### PIC Chips
- **MPLAB X IDE**: Download from [Microchip](https://www.microchip.com/en-us/tools-resources/develop/mplab-x-ide)
- **XC Compilers**: Install with MPLAB X IDE

#### Nuvoton Chips
- **Nu-Link Tools**: Download from [Nuvoton](https://www.nuvoton.com/tool-and-software/development-tool-hardware/)

## Supported File Formats

- `.ledproj` - LED Matrix Studio project files
- `.bin` - Binary pattern files
- `.hex` - Intel HEX files
- `.dat` - Data files
- `.leds` - LED pattern files
- `.ledadmin` - LED Admin files
- `.json` - JSON pattern files
- `.csv` - CSV pattern files
- `.txt` - Text pattern files

## Usage

1. **Load Pattern**: Click "Open" to load a pattern file
2. **Select Chip**: Choose your microcontroller from the dropdown
3. **Configure Settings**: Set GPIO pin, brightness, speed, etc.
4. **Preview**: Use the preview tab to see your pattern
5. **Upload**: Click "Flash" to build and upload firmware

## Brightness Control

The application supports advanced brightness control:

- **Global Brightness**: 0-100% slider control
- **Per-Channel Control**: Individual R, G, B brightness adjustment
- **Brightness Curves**: Linear, gamma-corrected, logarithmic, exponential, S-curve
- **Hardware Mapping**: LED-type specific brightness optimization

## Speed Control

Advanced speed control features:

- **Variable Speed**: Different speeds for different parts of the animation
- **Keyframes**: Set speed at specific frames
- **Easing Functions**: Smooth speed transitions
- **Frame Interpolation**: Smooth animation between frames

## Development

### Setup Development Environment
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black .
flake8 .
```

### Logging & Code Quality

- Logging is initialized via `core/logging_config.setup_logging()`. Configure with env vars:
  - `UPLOADBRIDGE_LOG_LEVEL` (e.g., DEBUG, INFO)
  - `UPLOADBRIDGE_LOG_FILE` (optional file path)
- Audit the codebase:
  ```bash
  python tools/project_checkup.py --output text
  ```
- Lint and format:
  ```bash
  ruff check .
  black --check --line-length 120 .
  ```
  Ruff is configured to forbid `print()` in non-test code and ignore tests.

## Architecture

- **Core**: Pattern data structures and processing
- **UI**: PySide6-based modern interface
- **Uploaders**: Chip-specific firmware generation and upload
- **Firmware**: Universal firmware templates for all supported chips

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/AsithaLKonara/Microcontroller-Uploader/issues)
- **Documentation**: [README](https://github.com/AsithaLKonara/Microcontroller-Uploader#readme)
- **Discussions**: [GitHub Discussions](https://github.com/AsithaLKonara/Microcontroller-Uploader/discussions)

## Changelog

### v1.0.0
- Initial release
- Support for 11+ microcontroller types
- Advanced brightness and speed control
- Real-time pattern preview
- Auto-detection of pattern information
- Professional UI with scrollable areas