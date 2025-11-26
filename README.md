# 🎨 Upload Bridge - LED Matrix Studio

<div align="center">

**Universal firmware uploader and pattern editor for LED matrices across multiple microcontroller platforms**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-PySide6-green.svg)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](docs/PROJECT_STATUS.md)

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 📖 Overview

**Upload Bridge** is a professional, cross-platform desktop application for creating, editing, and uploading LED animation patterns to microcontroller boards. It provides a unified interface for managing LED patterns across **9+ microcontroller types** with support for **10+ file formats**.

### What Makes Upload Bridge Special?

- 🎨 **Professional Pattern Editor** - Full-featured design tools with 8 drawing tools, layers, and timeline
- 🎬 **Media Conversion** - Convert images, GIFs, and videos directly to LED patterns
- 🔌 **Multi-Platform Support** - ESP32, ATmega, ATtiny, STM32, PIC, Nuvoton microcontrollers
- ⚡ **Real-time Preview** - 60 FPS LED matrix visualization with frame-by-frame control
- 🤖 **Automation Engine** - Parametric actions for scroll, rotate, mirror, invert, and more
- ✨ **Effects Library** - Procedural visual effects for stunning animations
- 💾 **Project Management** - Save/load projects with versioning and metadata

---

## ✨ Features

### 🎨 Design Tools

- **8 Drawing Tools**: Pixel, Rectangle, Circle, Line, Fill, Gradient, Random Spray, Text
- **Multi-Layer System**: Create complex patterns with multiple layers and blend modes
- **Timeline Editor**: Visual timeline with multi-select, drag & drop, and frame management
- **Keyframe Animation**: Smooth animations with easing functions
- **Undo/Redo**: Full history system for pattern editing

### 🎬 Media Upload

Convert media files directly to LED patterns:

- **Images**: PNG, JPG, JPEG, BMP
- **Animations**: GIF (animated)
- **Videos**: MP4, AVI, MOV, MKV, WebM

### 🔌 Hardware Support

**9 Microcontroller Types:**
- ESP32 (4 variants: ESP32, ESP32-S, ESP32-C3, ESP32-S3)
- ATmega2560
- ATtiny85
- STM32F407
- PIC18F4550
- Nuvoton M051

### 📤 Export & Import

**Supported Formats:**
- `.ledproj` - LED Matrix Studio project files
- `.bin` - Binary pattern files
- `.hex` - Intel HEX files
- `.dat` - Data files
- `.leds` - LED pattern files
- `.json` - JSON pattern files
- `.csv` - CSV pattern files
- `.txt` - Text pattern files

### 🤖 Automation & Effects

- **7 Automation Actions**: Scroll, Rotate, Mirror, Invert, Wipe, Reveal, Bounce
- **92 Visual Effects**: Procedural effects library
- **Parametric Control**: Adjustable parameters for all actions

### ⚡ Advanced Features

- **Real-time Preview**: 60 FPS visualization
- **Brightness Control**: Global, per-channel, and curve-based control
- **Speed Control**: Variable speed with keyframes and easing
- **Auto-Detection**: Automatic pattern information detection
- **WiFi Upload**: OTA firmware updates for ESP chips
- **Batch Operations**: Flash multiple devices simultaneously

---

## 🚀 Installation

### Quick Installation

#### Windows
1. Download installer: `upload_bridge_3.0.0.msi`
2. Run installer and follow wizard
3. Launch from Start Menu

#### macOS
1. Download installer: `upload_bridge_3.0.0.pkg`
2. Run installer and follow wizard
3. Launch from Applications

#### Linux
```bash
# DEB (Ubuntu/Debian)
sudo dpkg -i upload-bridge_3.0.0_amd64.deb

# RPM (Fedora/RHEL)
sudo rpm -ivh upload-bridge-3.0.0-1.x86_64.rpm
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge.git
cd upload_bridge

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Additional Tools Required

#### ESP Chips (ESP8266, ESP32)
- **Arduino CLI**: [Download](https://arduino.github.io/arduino-cli/)
- Install ESP cores:
  ```bash
  arduino-cli core install esp8266:esp8266
  arduino-cli core install esp32:esp32
  ```

#### AVR Chips (ATmega, ATtiny)
- **AVR-GCC Toolchain**: [Download](https://www.microchip.com/en-us/tools-resources/develop/microchip-studio)
- **avrdude**: Usually included with AVR-GCC

#### STM32 Chips
- **ARM GCC Toolchain**: [Download](https://developer.arm.com/downloads/-/gnu-rm)
- **stm32flash**: Install via package manager

#### PIC Chips
- **MPLAB X IDE**: [Download](https://www.microchip.com/en-us/tools-resources/develop/mplab-x-ide)
- **XC Compilers**: Install with MPLAB X IDE

#### Nuvoton Chips
- **Nu-Link Tools**: [Download](https://www.nuvoton.com/tool-and-software/development-tool-hardware/)

For detailed installation instructions, see [Installation Guide](docs/INSTALLATION.md).

---

## 🎯 Quick Start

### 1. Create Your First Pattern

1. Launch Upload Bridge
2. Go to **Design Tools** tab
3. Select a drawing tool (e.g., Rectangle)
4. Draw on the canvas
5. Add frames for animation
6. Preview your pattern

### 2. Convert Media to Pattern

1. Go to **Media Upload** tab
2. Click **"Select Media File"**
3. Choose your image/GIF/video
4. Adjust conversion settings
5. Click **"Convert to LED Pattern"**

### 3. Flash to Device

1. Go to **Flash** tab
2. Select your microcontroller type
3. Choose COM port
4. Configure settings (brightness, speed, etc.)
5. Click **"Build & Upload"**

**📖 For detailed guides, see:**
- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [User Manual](docs/USER_MANUAL.md) - Complete feature documentation
- [Installation Guide](docs/INSTALLATION.md) - Platform-specific installation

---

## 📚 Documentation

### Getting Started
- 📖 **[Quick Start Guide](docs/QUICKSTART.md)** - Create your first pattern in 10 steps
- 📘 **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions
- 📚 **[User Manual](docs/USER_MANUAL.md)** - Comprehensive feature documentation

### Support & Help
- 🔧 **[Support Guide](docs/SUPPORT.md)** - Troubleshooting and FAQ
- 🐛 **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- 📝 **[Release Notes](docs/RELEASE_NOTES.md)** - What's new in this version
- 📋 **[Changelog](docs/CHANGELOG.md)** - Complete version history

### Technical Documentation
- 🔌 **[Chip Integration Guide](docs/enterprise/CHIP_INTEGRATION_GUIDE.md)** - Adding new chips
- 🏗️ **[Architecture Documentation](docs/architecture/)** - System architecture
- 📊 **[API Reference](docs/enterprise/API_REFERENCE.md)** - Developer documentation
- 🧪 **[Testing Guide](docs/TESTING_GUIDE.md)** - Testing documentation

### Project Documentation
- 📊 **[Project Status](docs/PROJECT_STATUS.md)** - Current project status
- ✅ **[Completion Summary](docs/TASKS_COMPLETED_SUMMARY.md)** - Completed tasks
- 📋 **[Remaining Tasks](docs/REMAINING_TASKS.md)** - Future work

**📑 [Full Documentation Index](docs/INDEX.md)** - Complete documentation catalog

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────┐
│      Upload Bridge Application          │
│         (PySide6 Qt GUI)                 │
├─────────────────────────────────────────┤
│  UI Layer                                │
│  ├─ Main Window                         │
│  ├─ Design Tools Tab                    │
│  ├─ Preview Tab                         │
│  ├─ Flash Tab                           │
│  └─ Media Upload Tab                    │
├─────────────────────────────────────────┤
│  Core Layer                              │
│  ├─ Pattern Service                     │
│  ├─ Export Service                      │
│  ├─ Flash Service                       │
│  └─ Pattern Repository                  │
├─────────────────────────────────────────┤
│  Domain Layer                            │
│  ├─ Pattern Models                      │
│  ├─ Drawing Tools                       │
│  ├─ Effects Engine                      │
│  └─ Automation                          │
├─────────────────────────────────────────┤
│  Hardware Layer                         │
│  ├─ ESP Uploaders                       │
│  ├─ AVR Uploaders                       │
│  ├─ STM32 Uploaders                     │
│  └─ PIC/Nuvoton Uploaders               │
└─────────────────────────────────────────┘
```

### Key Components

- **Core Services**: PatternService, ExportService, FlashService
- **Domain Models**: Pattern, Frame, Layer, Automation
- **UI Components**: DesignToolsTab, PreviewTab, FlashTab
- **Uploaders**: Chip-specific firmware generation and upload
- **Firmware Templates**: Universal templates for all supported chips

For detailed architecture documentation, see [Architecture Guide](docs/architecture/SERVICE_LAYER_ARCHITECTURE.md).

---

## 🧪 Testing

### Test Coverage

- **Unit Tests**: 300+ test methods
- **Integration Tests**: Service and UI integration
- **E2E Tests**: Complete workflow testing
- **Performance Tests**: Large pattern and long session testing
- **Hardware Tests**: Device-specific testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov --cov-report=html
```

For testing documentation, see [Testing Guide](docs/TESTING_GUIDE.md).

---

## 💻 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge.git
cd upload_bridge

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Project Structure

```
upload_bridge/
├── core/              # Core services and logic
├── domain/            # Domain models
├── ui/                # User interface
├── uploaders/         # Chip-specific uploaders
├── firmware/          # Firmware templates
├── tests/             # Test suite
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

For development guidelines, see [Developer Migration Guide](docs/DEVELOPER_MIGRATION_GUIDE.md).

---

## 📊 Project Status

### Current Version: v3.0.0 (Enterprise Edition)

**Status**: ✅ **Production Ready**

### Completion Status

- ✅ **Code**: 100% complete
- ✅ **Tests**: 99.7%+ passing (297/298+ tests)
- ✅ **Documentation**: 100% complete
- ✅ **Release Prep**: 100% complete

### Features Implemented

- ✅ Complete Design Tools (8 drawing tools, layers, timeline)
- ✅ 9 chip uploaders with firmware templates
- ✅ Export pipeline (7+ formats)
- ✅ Automation and effects engine
- ✅ Project file format (.ledproj) with versioning
- ✅ Comprehensive test suite (300+ tests)
- ✅ Cross-platform installers (Windows, macOS, Linux)
- ✅ Complete documentation

For detailed status, see [Project Status](docs/PROJECT_STATUS.md).

---

## 🐛 Troubleshooting

### Common Issues

**Application won't start**
- Check Python version (needs 3.10+)
- Reinstall dependencies: `pip install -r requirements.txt`

**Can't connect to device**
- Check USB cable
- Verify COM port
- Install device drivers

**Pattern doesn't display**
- Check LED wiring
- Verify color order
- Check dimensions

**For more help:**
- 📖 [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- 💬 [Support Guide](docs/SUPPORT.md)
- 🐛 [GitHub Issues](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/issues)

---

## 📝 Changelog

### v3.0.0 (Enterprise Edition) - Current

**Major Features:**
- ✅ Complete Design Tools implementation
- ✅ 9 chip uploaders with firmware templates
- ✅ Export pipeline (7+ formats)
- ✅ Automation and effects engine
- ✅ Project file format (.ledproj)
- ✅ Comprehensive test suite
- ✅ Cross-platform installers
- ✅ Complete documentation

**Improvements:**
- Enhanced UI with dark theme
- Improved performance
- Better error handling
- Expanded hardware support

For complete changelog, see [CHANGELOG.md](docs/CHANGELOG.md).

---

## 🤝 Support

### Get Help

- 📖 **Documentation**: [Full Documentation Index](docs/INDEX.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/discussions)
- 📧 **Email**: [Contact via GitHub](https://github.com/AsithaLKonara)

### Contributing

We welcome contributions! Please see [Contributing Guidelines](#-contributing) above.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Qt/PySide6** - Cross-platform GUI framework
- **Arduino** - ESP chip support
- **Microchip** - AVR and PIC support
- **STMicroelectronics** - STM32 support
- **Nuvoton** - Nuvoton chip support

---

## 🔗 Links

- **Repository**: [GitHub](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge)
- **Issues**: [GitHub Issues](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/discussions)
- **Documentation**: [Full Documentation](docs/INDEX.md)

---

<div align="center">

**Made with ❤️ for the LED matrix community**

[⬆ Back to Top](#-upload-bridge---led-matrix-studio)

</div>
