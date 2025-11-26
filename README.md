# Upload Bridge - LED Matrix Studio

Universal firmware uploader for LED patterns across multiple microcontroller platforms.

## Features

### Core Features
- **🎨 Design Tools**: Professional LED pattern editor with 8 drawing tools
- **🎬 Media Upload**: Convert images, GIFs, and videos to LED patterns (PNG, JPG, BMP, GIF, MP4, AVI, MOV, MKV, WebM)
- **📐 Multi-Layer System**: Create complex patterns with multiple layers and blend modes
- **⏱️ Timeline Editor**: Visual timeline with multi-select, drag & drop, and frame management
- **🤖 Automation**: Parametric actions (scroll, rotate, mirror, invert, wipe, reveal, bounce)
- **✨ Effects Engine**: Procedural visual effects library
- **💾 Project Files**: Save/load projects with `.ledproj` format

### Hardware Support
- **Multi-Platform Support**: ESP32 (4 variants), ATmega2560, ATtiny85, STM32F407, PIC18F4550, Nuvoton M051
- **9 Chip Uploaders**: Complete firmware generation and flashing for all supported chips
- **Device Profiles**: JSON-based configuration for each chip type
- **Firmware Verification**: Hash-based verification system

### Advanced Features
- **Advanced Brightness Control**: Gamma correction, per-channel control, hardware-specific mapping
- **Pattern Speed Control**: Variable speed with keyframes, easing functions, frame interpolation
- **Real-time Preview**: Live pattern visualization with brightness adjustment
- **Auto-Detection**: Automatic pattern information detection from various file formats
- **Export Pipeline**: Export to 7+ formats (BIN, HEX, DAT, LEDS, JSON, CSV, TXT)
- **Professional UI**: Modern, responsive interface with accessibility and i18n support

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

**New to Upload Bridge?** Start here:
- 📖 **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in 5 minutes
- 📘 **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions
- 📚 **[User Manual](docs/USER_MANUAL.md)** - Comprehensive documentation

### Quick Installation

**Windows:**
1. Download installer: `upload_bridge_3.0.0.msi`
2. Run installer and follow wizard
3. Launch from Start Menu

**macOS:**
1. Download installer: `upload_bridge_3.0.0.pkg`
2. Run installer and follow wizard
3. Launch from Applications

**Linux:**
```bash
# DEB (Ubuntu/Debian)
sudo dpkg -i upload-bridge_3.0.0_amd64.deb

# RPM (Fedora/RHEL)
sudo rpm -ivh upload-bridge-3.0.0-1.x86_64.rpm
```

**Manual Installation:**
```bash
# Clone repository
git clone https://github.com/your-repo/upload_bridge.git
cd upload_bridge

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

For detailed installation instructions, see [Installation Guide](docs/INSTALLATION.md).

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

### Basic Workflow

1. **Create Pattern**: Use Design Tools tab to draw your pattern
2. **Add Frames**: Create multiple frames for animation
3. **Preview**: Use preview to see your animation
4. **Export**: Export pattern to desired format
5. **Flash**: Select chip, configure settings, and flash to device

### Detailed Guides

- **[Quick Start Guide](docs/QUICKSTART.md)** - Create your first pattern in 10 steps
- **[User Manual](docs/USER_MANUAL.md)** - Complete feature documentation
- **[Installation Guide](docs/INSTALLATION.md)** - Platform-specific installation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

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

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in minutes
- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions
- **[User Manual](docs/USER_MANUAL.md)** - Comprehensive feature documentation
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[API Reference](docs/enterprise/API_REFERENCE.md)** - Developer documentation
- **[Chip Integration Guide](docs/enterprise/CHIP_INTEGRATION_GUIDE.md)** - Adding new chips

## Support

- **Issues**: [GitHub Issues](https://github.com/AsithaLKonara/Microcontroller-Uploader/issues)
- **Documentation**: See [Documentation](#documentation) section above
- **Discussions**: [GitHub Discussions](https://github.com/AsithaLKonara/Microcontroller-Uploader/discussions)

## Troubleshooting

Common issues and quick fixes:

- **Application won't start**: Check Python version (needs 3.10+), reinstall dependencies
- **Can't connect to device**: Check USB cable, verify COM port, install drivers
- **Pattern doesn't display**: Check LED wiring, verify color order, check dimensions

For detailed troubleshooting, see [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## Changelog

### v3.0.0 (Enterprise Edition)
- ✅ Complete Design Tools implementation (8 drawing tools, layers, timeline)
- ✅ 9 chip uploaders with firmware templates
- ✅ Export pipeline (7+ formats)
- ✅ Automation and effects engine
- ✅ Project file format (.ledproj) with versioning
- ✅ Comprehensive test suite (300+ tests)
- ✅ CI/CD workflows and Docker images
- ✅ Cross-platform installers (Windows, macOS, Linux)
- ✅ Complete documentation (User Manual, Quick Start, Installation Guide)

### v1.0.0
- Initial release
- Support for 11+ microcontroller types
- Advanced brightness and speed control
- Real-time pattern preview
- Auto-detection of pattern information
- Professional UI with scrollable areas