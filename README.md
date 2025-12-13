# 🎨 Upload Bridge - LED Matrix Studio

<div align="center">

**Professional LED matrix pattern designer, editor, and firmware generator for multiple microcontroller platforms**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-PySide6-green.svg)](https://www.qt.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](docs/PROJECT_STATUS.md)
[![Tests](https://img.shields.io/badge/Tests-99.7%25%20Passing-success.svg)](tests/README.md)

[Features](#-comprehensive-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 📖 Overview

**Upload Bridge** is a professional, cross-platform desktop application for creating, editing, previewing, and uploading LED animation patterns to microcontroller boards. It serves as a complete LED matrix design and deployment solution, providing everything from pattern creation to firmware generation and device flashing.

### What Makes Upload Bridge Special?

- 🎨 **Professional Pattern Editor** - Full-featured design tools with 8 drawing tools, multi-layer system, and timeline editor
- 🎬 **Media Conversion** - Convert images, GIFs, and videos directly to LED patterns with advanced conversion options
- 🔌 **Multi-Platform Hardware Support** - 29 total chips supported (9 fully tested with dedicated uploaders + 20 via generic uploaders). Supports ESP32, ATmega, ATtiny, STM32, PIC, Nuvoton and more.
- ⚡ **Real-time Preview** - 60 FPS LED matrix visualization with hardware-accurate simulation
- 🤖 **Automation Engine** - 17 parametric automation actions for dynamic animations
- ✨ **Effects Library** - 92 procedural visual effects for stunning animations
- 💾 **Project Management** - Save/load projects with versioning, metadata, and pattern library
- 📡 **WiFi Upload** - Over-the-air firmware updates for ESP chips
- 🔄 **Batch Operations** - Flash multiple devices simultaneously
- 🎯 **Auto-Detection** - Automatic pattern information detection from various file formats

### Key Statistics

- **Supported Chips**: 29 total chips (9 fully supported with dedicated uploaders + 20 via generic uploaders)
- **File Formats**: 17 import formats, 12 export formats
- **Drawing Tools**: 8 professional tools
- **Automation Actions**: 17 parametric actions (12 core + 5 advanced)
- **Visual Effects**: 92 procedural effects
- **Test Coverage**: 300+ tests (99.7%+ passing)
- **Lines of Code**: 50,000+ production code
- **Documentation**: 100+ pages

---

## ✨ Comprehensive Features

### 🎨 Design Tools & Pattern Creation

#### 8 Professional Drawing Tools

1. **Pixel Tool** - Single pixel painting with adjustable brush size (1-50 pixels)
   - Brush shape (square/circle)
   - Hardness control (0.0-1.0 edge falloff)
   - Opacity control (0.0-1.0 transparency)
   - Multi-draw mode (broadcast across all frames)

2. **Rectangle Tool** - Draw filled/outline rectangles
   - Corner radius support
   - Perfect square mode (Shift key)
   - Center-draw mode (Alt key)
   - Adjustable line width

3. **Circle Tool** - Draw filled/outline circles and ellipses
   - Perfect circle mode (Shift key)
   - Center-draw mode (Alt key)
   - Smooth anti-aliased edges

4. **Line Tool** - Precise line drawing
   - Bresenham's line algorithm
   - Adjustable line width
   - Smooth line rendering

5. **Fill Tool** - Flood fill connected pixels
   - Tolerance control
   - Fill mode options
   - Pattern-aware filling

6. **Gradient Tool** - Linear gradient between two colors
   - Direction control (horizontal/vertical/diagonal)
   - Multiple color stops
   - Smooth color transitions

7. **Random Spray Tool** - Random pixel spray
   - Density control (0.0-1.0)
   - Spray area size
   - Random color variation

8. **Text Tool** - Bitmap font rendering
   - Multiple bitmap fonts support
   - Built-in 5x7 font
   - Custom font loading from `Res/fonts/`
   - Text effects (outline, shadow, gradients)
   - Typing and scrolling animations

#### Advanced Brush System

- **Brush Size**: 1-50 pixels adjustable
- **Brush Shape**: Square or Circle
- **Hardness**: 0.0-1.0 edge falloff control
- **Opacity**: 0.0-1.0 brush transparency
- **Multi-draw Mode**: Broadcast operations across all frames simultaneously

---

### 🎭 Multi-Layer System

#### Layer Management

- **Multiple Layers**: Up to 16 layers per frame
- **Layer Opacity**: 0.0-1.0 per-layer control
- **Blend Modes**: Normal, Add, Multiply, Screen
- **Layer Visibility**: Per-layer show/hide toggle
- **Layer Reordering**: Drag and drop reordering
- **Solo Mode**: Show single layer in isolation
- **Layer Locking**: Prevent accidental edits
- **Layer Merging**: Merge layers down
- **Layer Duplication**: Copy layers between frames
- **Layer Binding**: Bind layers to automation actions

#### Layer Composition

- **Independent Layers**: Each frame has its own set of layers
- **Layer Groups**: Organize related layers (planned)
- **Layer Masks**: Per-pixel masking (planned)
- **Layer Effects**: Apply effects to individual layers

---

### ⚡ Automation & Effects Engine

#### Automation Actions (17 Actions)

**Core Actions (12):**
1. **Move Left** - Shift pixels left by one column
2. **Move Right** - Shift pixels right by one column
3. **Move Up** - Shift pixels up by one row
4. **Move Down** - Shift pixels down by one row
5. **Scroll Text** - Scroll the active text buffer
6. **Rotate 90°** - Rotate the frame 90° clockwise
7. **Mirror Horizontal** - Mirror horizontally (left/right)
8. **Mirror Vertical** - Mirror vertically (top/bottom)
9. **Invert** - Invert frame colours
10. **Fade** - Apply fade effect using current palette
11. **Brightness** - Adjust brightness by provided value
12. **Randomize** - Randomize pixels (seed controlled)

**Advanced Actions (5):**
13. **Wipe** - Directional wipe effect with fade
   - Directions: Left-to-Right, Right-to-Left, Top-to-Bottom, Bottom-to-Top
   - Offset control (pixels per frame)
   - Fade intensity multiplier
14. **Reveal** - Progressive reveal from direction
   - Directions: Left, Right, Top, Bottom
   - Offset control (pixels per frame)
   - Edge softening
15. **Bounce** - Ping-pong scroll animation
   - Horizontal or vertical axis
   - Oscillating motion
16. **Colour Cycle** - Cycle color channels
   - Modes: RGB, RYB, custom
   - Channel rotation
17. **Radial** - Radial effects from center
   - Types: Spiral, Pulse, Sweep
   - Center-based transformations

#### Automation Features

- **Automation Queue**: Queue multiple actions for sequential execution
- **Preview Automation**: Preview before applying
- **Frame Range Selection**: Apply to specific frames
- **Action Inspector**: Detailed parameter editing
- **Automation Presets**: Save/load automation configurations
- **Action Broadcasting**: Apply to all frames or selected range

#### Effects Library (92 Effects)

- **Procedural Effects**: CPU-side image effects
- **Preview Thumbnails**: Visual effect preview
- **Intensity Control**: Adjustable effect intensity (0-100%)
- **Frame Range Selection**: Apply effects to specific frames
- **Effect Stacking**: Apply multiple effects in sequence
- **Effect Categories**: Linear effects, proliferation, symmetrical, over effects, others

**Effect Categories:**
- Linear Effects (30+ effects)
- Proliferation Effects (4+ effects)
- Symmetrical Effects (2+ effects)
- Over Effects (4+ effects)
- Other Effects (3+ effects)
- Plus 50+ additional effects

---

### 🎬 Timeline & Animation

#### Timeline Widget

- **Frame Visualization**: Thumbnail previews for each frame
- **Playhead**: Current frame indicator
- **Markers**: Visual markers on timeline
- **Overlays**: Automation action visualization
- **Layer Tracks**: Per-layer timeline rows
- **Zoom**: 25%-400% zoom control
- **Drag & Drop**: Frame reordering
- **Multi-Select**: Select multiple frames
- **Frame Duration Display**: Show frame durations

#### Animation Features

- **Frame Duration Control**: 50-5000ms per frame
- **FPS Control**: Adjustable frames per second
- **Loop Control**: Loop/once playback
- **Frame-by-Frame Navigation**: Step through frames
- **Playback Controls**: Play, pause, stop, step forward/backward
- **Keyframe Animation**: Smooth animations with easing functions (planned)
- **Animation Curves**: Custom animation curves (planned)

---

### 🎬 Media Upload & Conversion

Convert media files directly to LED patterns with advanced conversion options.

#### Supported Media Formats

**Images:**
- PNG, JPG, JPEG, BMP
- Automatic dimension detection
- Color quantization
- Brightness adjustment

**Animations:**
- GIF (animated) - Frame extraction
- Frame rate control
- Loop detection

**Videos:**
- MP4, AVI, MOV, MKV, WebM
- Frame extraction
- FPS control
- Time range selection
- Frame sampling

#### Conversion Features

- **Dimension Control**: Set target LED matrix size
- **FPS Control**: Frame rate for video/GIF conversion
- **Brightness Adjustment**: 0-100% brightness control
- **Color Order**: RGB, GRB, BRG, BGR, RBG, GBR
- **Color Quantization**: Reduce color palette
- **Frame Sampling**: Extract every Nth frame
- **Preview**: Preview conversion result before applying

---

### 🔌 Hardware Support

#### Hardware Support Overview

**29 Total Chips Supported:**
- **9 Fully Tested** - These chips have dedicated uploader implementations and are fully tested:
  1. **ESP32** - Dual-core WiFi/Bluetooth microcontroller
  2. **ESP32-S2** - ESP32 variant with enhanced features
  3. **ESP32-S3** - ESP32-S3 variant with advanced capabilities
  4. **ESP32-C3** - RISC-V based ESP32 variant
  5. **ATmega2560** - Arduino Mega compatible
  6. **ATtiny85** - Small AVR microcontroller
  7. **STM32F407** - ARM Cortex-M4 microcontroller
  8. **PIC18F4550** - PIC microcontroller
  9. **Nuvoton M051** - ARM Cortex-M0 microcontroller

- **20 Additional Chips** - Supported via generic uploaders (AVR, ESP, STM32, PIC, Nuvoton families)

See [Chip Support Matrix](docs/CHIP_SUPPORT_MATRIX.md) for complete details.

#### Upload Methods

- **USB Flashing**: Direct USB upload via serial port
- **WiFi Upload**: Network-based upload for ESP chips (OTA)
- **Batch Flashing**: Flash multiple devices simultaneously
- **Firmware Building**: Build device-specific firmware
- **Progress Tracking**: Real-time upload progress
- **Firmware Verification**: Hash-based verification system

#### Hardware Features

- **Device Profiles**: JSON-based configuration for each chip
- **Auto-Detection**: Automatic chip detection
- **COM Port Selection**: Manual or automatic port selection
- **Baud Rate Control**: Adjustable communication speed
- **Reset Control**: Automatic device reset after upload

---

### 📤 Import & Export System

#### Import Formats (17 Formats)

**Pattern Files:**
- **`.ledproj`** - LED Matrix Studio project files (with versioning)
- **`.bin`** - Binary pattern files
- **`.hex`** - Intel HEX files
- **`.dat`** - LED Matrix Studio data files
- **`.leds`** - LEDS format files
- **`.json`** - JSON pattern files

**Media Files:**
- **Images**: PNG, JPG/JPEG, BMP
- **Animations**: GIF (animated)
- **Videos**: MP4, AVI, MOV, MKV, WebM
- **Vector Graphics**: SVG, PDF

#### Export Formats (12 Formats)

**Pattern Formats:**
- **`.ledproj`** - Project format with metadata
- **`.bin`** - Binary format
- **`.hex`** - Intel HEX format
- **`.dat`** - LED Matrix Studio format
- **`.leds`** - LEDS format
- **`.json`** - JSON pattern format (WLED compatible)

**Code Formats:**
- **`.h`** - C/C++ header files

**Media Formats:**
- **`.png`** - PNG sprite sheet
- **`.gif`** - Animated GIF

**Player Formats:**
- **WLED** - WLED JSON format
- **Falcon Player** - Falcon Player sequence format
- **xLights** - xLights sequence format

#### Advanced Export Options

- **Auto Dimension Detection**: Detect matrix size automatically
- **Format Conversion**: Convert between formats
- **Metadata Export**: Include pattern metadata
- **Build Manifest**: Generate build information
- **MSB/LSB Bit Ordering**: Configurable bit order (planned)
- **Row/Column Scanning**: Configurable scan direction (planned)
- **Serpentine Wiring**: Alternate wiring patterns (planned)
- **RGB/BGR/GRB Ordering**: Color channel ordering (planned)

---

### 🎯 Pattern Management

#### Pattern Operations

- **Pattern Library**: Store and organize patterns
- **Pattern Search**: Search patterns by name/metadata
- **Pattern Filtering**: Filter by dimensions, format, tags
- **Pattern Duplication**: Clone patterns
- **Pattern Versioning**: Track pattern versions
- **Pattern Templates**: 15+ pre-built pattern templates
- **Pattern Metadata**: Author, description, tags, creation date

#### Pattern Optimization

- **One-Click Optimization**: Optimize pattern size
- **Frame Deduplication**: Remove duplicate frames
- **Color Optimization**: Reduce color palette
- **Compression**: Compress pattern data
- **Dimension Caching**: Cache pattern dimensions

---

### 🎨 Advanced Visualization & Preview

#### Preview Features

- **Real-Time LED Simulator**: Hardware-accurate preview
- **60 FPS Playback**: Smooth animation preview
- **Brightness Control**: Global, per-channel, and curve-based
- **Speed Control**: Variable speed with keyframes and easing
- **Zoom Controls**: Zoom in/out preview (25%-400%)
- **Grid Overlay**: Show pixel grid for alignment
- **Multiple View Modes**: Matrix, Circle, and other view modes
- **Frame-by-Frame Preview**: Step through frames
- **Pattern Swap**: Swap patterns in preview

#### Brightness Control

- **Global Brightness**: 0-100% slider control
- **Per-Channel Control**: Individual R, G, B brightness adjustment
- **Brightness Curves**: Linear, gamma-corrected, logarithmic, exponential, S-curve
- **Hardware Mapping**: LED-type specific brightness optimization

#### Speed Control

- **Variable Speed**: Different speeds for different parts of animation
- **Keyframes**: Set speed at specific frames
- **Easing Functions**: Smooth speed transitions
- **Frame Interpolation**: Smooth animation between frames

---

### 🛠️ Advanced Tools & Utilities

#### Scratchpads

- **10 User Buffers**: Quick copy/paste experiments
- **Cross-Project Buffers**: Use buffers across projects
- **Buffer Management**: Organize scratchpads
- **Pixel Copy/Paste**: Copy pixels to/from scratchpad

#### Presets

- **Resolution Presets**: Store resolution/color combinations
- **Hardware Presets**: Frequently targeted hardware configurations
- **Export Presets**: Save export configurations
- **Frame Presets**: Save frame configurations

#### Batch Operations

- **Batch Validation**: Validate multiple patterns
- **Batch Flashing**: Flash multiple devices
- **Batch Export**: Export multiple patterns
- **Batch Conversion**: Convert multiple files

---

### 🤖 AI & Advanced Generation

#### AI Features

- **AI Pattern Generator**: Generate patterns using AI
- **Pattern Templates**: 15+ pre-built pattern library
- **Template Categories**: Animation, Effects, Text

#### Audio Features

- **Audio Reactive**: Audio-reactive pattern generation
- **Real-time Audio Processing**: Process audio input
- **Frequency Analysis**: Analyze audio frequencies

---

### 📡 WiFi Upload

#### WiFi Features

- **OTA Updates**: Over-the-air firmware updates for ESP chips
- **Network Discovery**: Automatic device discovery
- **Manual Connection**: Manual IP/port configuration
- **Progress Tracking**: Real-time upload progress
- **Connection Status**: Device connection status monitoring

---

### 🔧 Arduino IDE Integration

#### Arduino Features

- **Integrated IDE**: Arduino development environment
- **Code Generation**: Generate Arduino code
- **Sketch Management**: Manage Arduino sketches
- **Library Integration**: Use Arduino libraries

---

### 🎯 Project Management

#### Project Features

- **Project Files**: Save/load `.ledproj` projects
- **Versioning**: Track project versions
- **Metadata**: Author, description, tags, creation date
- **Auto-Save**: Automatic project saving
- **Backup**: Automatic backup creation
- **History**: Project history tracking

#### Undo/Redo System

- **Unlimited History**: Full undo/redo support
- **History Navigation**: Navigate through history
- **History Snapshot**: Save history snapshots
- **Command Pattern**: Efficient history management

---

### 🔐 Enterprise Features

#### Logging & Monitoring

- **Structured Logging**: JSON format logging
- **Log Rotation**: Automatic log rotation
- **Audit Trail**: Complete audit logging
- **Performance Metrics**: Operation performance tracking
- **Error Tracking**: Comprehensive error tracking

#### Configuration

- **Environment-Based Config**: Dev/staging/prod configs
- **Configuration Validation**: Validate configuration
- **Secrets Management**: Secure secrets handling
- **Config Hot-Reload**: Reload configuration without restart

#### Health Monitoring

- **Health Checks**: System health monitoring
- **Resource Monitoring**: Memory, CPU, disk monitoring
- **Health Status API**: Health status reporting
- **Performance Budgets**: Performance constraint management

---

### 🎨 User Interface

#### Modern UI Features

- **Dark Theme**: Professional dark theme
- **Responsive Design**: Adapts to window size
- **Accessibility**: Full accessibility support
- **Internationalization**: Multi-language support (i18n)
- **Customizable Layout**: Adjustable panel layout
- **Tooltips**: Comprehensive tooltips
- **Keyboard Shortcuts**: Full keyboard navigation

#### Tabs & Views

1. **Design Tools Tab** - Main pattern editor
2. **Media Upload Tab** - Media conversion
3. **Preview Tab** - Pattern preview
4. **Flash Tab** - Firmware flashing
5. **WiFi Upload Tab** - WiFi upload
6. **Arduino IDE Tab** - Arduino integration
7. **Pattern Library Tab** - Pattern management
8. **Batch Flash Tab** - Batch operations
9. **Audio Reactive Tab** - Audio-reactive patterns

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
# For full features (recommended):
pip install -r requirements.txt

# For minimal install (basic functionality only):
# pip install -r requirements_simple.txt
# Note: Minimal install disables media conversion, license system, 
# health monitoring, and schema validation features.

# Run application
python main.py
```
<｜tool▁call▁begin｜>
read_file

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
3. Set matrix dimensions (e.g., 32x32, 64x32)
4. Select a drawing tool (e.g., Rectangle)
5. Choose a color from the palette
6. Draw on the canvas
7. Add frames for animation using the timeline
8. Preview your pattern in the Preview tab
9. Save your project (`.ledproj` format)

### 2. Convert Media to Pattern

1. Go to **Media Upload** tab
2. Click **"Select Media File"**
3. Choose your image/GIF/video
4. Adjust conversion settings:
   - Dimensions (target LED matrix size)
   - FPS (for videos/GIFs)
   - Brightness (0-100%)
   - Color order (RGB, GRB, etc.)
5. Preview the conversion result
6. Click **"Convert to LED Pattern"**
7. The pattern will be loaded in Design Tools tab

### 3. Flash to Device

1. Go to **Flash** tab
2. Select your microcontroller type
3. Choose COM port (or auto-detect)
4. Configure settings:
   - Brightness (0-100%)
   - Speed (frame duration)
   - Color order
   - Wiring mode
5. Click **"Build & Upload"**
6. Monitor progress in the status bar
7. Device will reset and display pattern

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
- 📁 **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Complete folder structure

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
│  ├─ Media Upload Tab                    │
│  ├─ WiFi Upload Tab                    │
│  └─ Arduino IDE Tab                     │
├─────────────────────────────────────────┤
│  Core Layer                              │
│  ├─ Pattern Service                     │
│  ├─ Export Service                      │
│  ├─ Flash Service                       │
│  ├─ OTA Service                         │
│  └─ Pattern Repository                  │
├─────────────────────────────────────────┤
│  Domain Layer                            │
│  ├─ Pattern Models                      │
│  ├─ Drawing Tools                       │
│  ├─ Effects Engine                      │
│  ├─ Automation                          │
│  └─ Animation System                    │
├─────────────────────────────────────────┤
│  Hardware Layer                         │
│  ├─ ESP Uploaders (4 variants)          │
│  ├─ AVR Uploaders                      │
│  ├─ STM32 Uploaders                     │
│  └─ PIC/Nuvoton Uploaders               │
└─────────────────────────────────────────┘
```

### Key Components

- **Core Services**: PatternService, ExportService, FlashService, OTAService
- **Domain Models**: Pattern, Frame, Layer, Automation, Effects
- **UI Components**: 9 main tabs with comprehensive functionality
- **Uploaders**: Chip-specific firmware generation and upload
- **Firmware Templates**: Universal templates for all supported chips
- **Event System**: Event-driven architecture for decoupling
- **Error Handling**: Centralized error handling system

For detailed architecture documentation, see [Architecture Guide](docs/architecture/SERVICE_LAYER_ARCHITECTURE.md).

---

## 🧪 Testing

### Test Coverage

- **Unit Tests**: 300+ test methods
- **Integration Tests**: Service and UI integration
- **E2E Tests**: Complete workflow testing
- **Performance Tests**: Large pattern and long session testing
- **Hardware Tests**: Device-specific testing
- **UX Tests**: User experience validation
- **Edge Case Tests**: Comprehensive edge case coverage

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
├── parsers/           # File format parsers
├── tests/             # Test suite
├── docs/              # Documentation
├── scripts/           # Utility scripts
│   ├── build/         # Build scripts
│   ├── install/       # Installation scripts
│   ├── development/   # Development tools
│   ├── testing/       # Testing utilities
│   └── tools/         # General tools
├── resources/         # Static resources
└── data/              # Runtime data
```

For complete structure, see [Project Structure](docs/PROJECT_STRUCTURE.md).

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
- ✅ 29 chip support (9 fully tested + 20 via generic uploaders) with firmware templates
- ✅ Export pipeline (12 formats)
- ✅ Automation and effects engine (17 actions, 92 effects)
- ✅ Project file format (.ledproj) with versioning
- ✅ Comprehensive test suite (300+ tests)
- ✅ Cross-platform installers (Windows, macOS, Linux)
- ✅ Complete documentation (100+ pages)
- ✅ WiFi upload (OTA for ESP chips)
- ✅ Media conversion (images, GIFs, videos)
- ✅ Pattern library and templates
- ✅ Batch operations

For detailed status, see [Project Status](docs/PROJECT_STATUS.md).

---

## 🐛 Troubleshooting

### Common Issues

**Application won't start**
- Check Python version (needs 3.10+)
- Reinstall dependencies: `pip install -r requirements.txt`
- Check for missing system libraries

**Can't connect to device**
- Check USB cable connection
- Verify COM port (Windows) or `/dev/tty*` (Linux/Mac)
- Install device drivers
- Check device permissions (Linux)

**Pattern doesn't display correctly**
- Check LED wiring configuration
- Verify color order (RGB, GRB, etc.)
- Check matrix dimensions
- Verify brightness settings

**Export fails**
- Check file permissions
- Verify disk space
- Check format compatibility
- Review error messages in logs

**For more help:**
- 📖 [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- 💬 [Support Guide](docs/SUPPORT.md)
- 🐛 [GitHub Issues](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/issues)

---

## 📝 Changelog

### v3.0.0 (Enterprise Edition) - Current

**Major Features:**
- ✅ Complete Design Tools implementation (8 drawing tools, layers, timeline)
- ✅ 29 chip support (9 fully tested + 20 via generic uploaders) with firmware templates
- ✅ Export pipeline (12 formats)
- ✅ Automation and effects engine (17 actions, 92 effects)
- ✅ Project file format (.ledproj) with versioning
- ✅ Comprehensive test suite (300+ tests)
- ✅ Cross-platform installers (Windows, macOS, Linux)
- ✅ Complete documentation (100+ pages)
- ✅ WiFi upload (OTA for ESP chips)
- ✅ Media conversion (images, GIFs, videos)
- ✅ Pattern library and templates (15+ templates)
- ✅ Batch operations

**Improvements:**
- Enhanced UI with dark theme
- Improved performance (60 FPS preview)
- Better error handling
- Expanded hardware support
- Comprehensive logging system
- Health monitoring

For complete changelog, see [CHANGELOG.md](docs/CHANGELOG.md).

---

## 🤝 Support

### Get Help

- 📖 **Documentation**: [Full Documentation Index](docs/INDEX.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/AsithaLKonara/J-Tech-Pixel-LED---Upload-Bridge/discussions)
- 📧 **Contact**: [Contact via GitHub](https://github.com/AsithaLKonara)

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
- **LED Matrix Community** - Inspiration and feedback

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
