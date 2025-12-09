# Changelog

All notable changes to Upload Bridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2024

### Added

#### Core Features
- **Pattern Creation and Editing**
  - Create patterns with customizable dimensions (1x1 to 256x256)
  - Multi-frame animation support
  - Frame-by-frame editing
  - Frame duplication and management
  - Undo/Redo system with unlimited history

- **Drawing Tools**
  - Brush tool with adjustable size
  - Pencil tool for pixel-perfect editing
  - Fill tool (bucket)
  - Line tool
  - Rectangle tool
  - Circle tool
  - Color picker (eyedropper)
  - Eraser tool

- **Layer System**
  - Multi-layer support per frame
  - Layer visibility toggle
  - Layer opacity control (0-100%)
  - Layer reordering (drag and drop)
  - Layer groups
  - Per-pixel layer masks
  - Blend modes (normal, add, multiply, screen)

- **Animation Features**
  - Frame timeline with visual editor
  - Frame duration control (1ms to 65535ms)
  - Animation preview with play/pause/stop
  - Frame insertion and deletion
  - Frame copying and pasting
  - Animation effects (fade, scroll, bounce, reveal)

- **Text Tool**
  - Enhanced text rendering with live preview
  - Multiple bitmap fonts (5x7, 8x8, custom)
  - Text effects:
    - Outline with customizable color and thickness
    - Shadow with offset and color
    - Gradient fills (vertical/horizontal)
  - Character spacing control
  - Line spacing control
  - Text alignment (left, center, right)
  - Multi-line text support
  - Typing animation
  - Scrolling text animation (all directions)

- **Template Library**
  - 15+ built-in pattern templates
  - Template categories:
    - Animation (Bouncing Ball, Wave, Spiral)
    - Effects (Fire, Rain, Matrix Rain, Color Cycle, Pulse, Fade, Random Pixels)
    - Text (Scrolling Text, Clock, Weather Display)
  - Customizable template parameters
  - Template preview

- **Import/Export**
  - **Import Formats**:
    - PNG, BMP, JPEG images
    - Animated GIFs
    - SVG vector graphics
    - PDF documents (single page or all pages)
  - **Export Formats**:
    - Binary (.bin)
    - Intel HEX (.hex)
    - DAT format (.dat)
    - LEDS format (.leds)
    - JSON (.json)
    - CSV (.csv)
    - Text (.txt)
    - C Header (.h)
    - Project file (.ledproj)
    - Video (MP4, AVI, MOV)
  - **Advanced Export Options**:
    - MSB/LSB bit ordering
    - Bit position (Top/Bottom)
    - Row/Column scanning direction
    - Scan order (LeftToRight, RightToLeft, TopToBottom, BottomToTop, Alternate)
    - Serpentine wiring support
    - RGB color ordering (RGB, BGR, GRB, BRG, RBG, GBR)
    - Color space (RGB888, RGB565)
    - Bit depth per channel
    - Bytes per line grouping
    - Number format (Hex, Decimal, Binary)

- **Firmware Support**
  - **Supported Chips**:
    - ESP8266 (NodeMCU, ESP-01)
    - ESP32
    - ESP32-S2
    - ESP32-C3
    - STM32F103C8
    - STM32F030F4P6
    - ATmega328P (Arduino)
    - PIC16F877A
    - NuMicro M031
  - Firmware templates with customizable options
  - GPIO pin configuration
  - Brightness control
  - Build manifest generation
  - Batch flashing support

- **Device Upload**
  - Serial port detection
  - Automatic device detection
  - Upload progress tracking
  - Upload verification
  - Error handling and recovery
  - OTA update support (WiFi-enabled devices)

- **Keyframe Animation System**
  - Keyframe-based animation
  - Multiple keyframe types (position, color, scale, rotation, opacity)
  - Animation curves (linear, ease-in, ease-out, bounce, elastic, etc.)
  - Tweening and interpolation
  - Motion paths
  - Keyframe editor UI

- **Pattern Templates**
  - Pre-built pattern generators
  - Parameter customization
  - Template preview
  - Template library browser

#### User Interface
- Modern, intuitive Qt-based interface
- Tabbed interface (Design Tools, Firmware, Batch Flash, Settings)
- Canvas with zoom and pan
- Timeline editor
- Layer panel with drag-and-drop
- Color picker with palette
- Tool palette
- Status bar with pattern information
- Context menus
- Keyboard shortcuts
- Tooltips and help text

#### Advanced Features
- Pattern validation
- Export preview
- Hardware preview simulation
- Frame caching for performance
- Background processing
- Configuration management
- Plugin system architecture
- Scripting API foundation

### Changed
- Improved pattern loading performance
- Enhanced error messages
- Better file format detection
- Improved UI responsiveness

### Fixed
- Fixed frame synchronization issues
- Fixed layer compositing bugs
- Fixed export format issues
- Fixed memory leaks in pattern handling
- Fixed undo/redo edge cases

### Security
- Input validation for all file operations
- Safe file path handling
- Secure firmware building process

---

## [Unreleased]

### Added

#### Layer System Enhancements
- **Automation Layer Integration**
  - Automation operations now create new layers instead of modifying frames directly
  - Automation layers are prefixed with "Auto:" for easy identification (e.g., "Auto: Scroll Left")
  - Original layers remain intact, enabling non-destructive workflows
  - Multiple automation layers can be stacked and toggled independently

- **Layer Sync Detection**
  - Automatic detection when layers are out of sync with frame pixels
  - Warning banner appears when sync issues are detected
  - "Sync Layers" button to restore synchronization
  - Real-time sync state checking and updates

- **Copy Layer to Frames**
  - Right-click context menu option to copy layers between frames
  - Copy to multiple target frames simultaneously
  - Preserves layer name, pixels, and all properties
  - Original layer remains unchanged

- **Hidden Layer Prevention**
  - Blocks painting operations on hidden layers
  - Clear error dialog when attempting to paint on hidden layer
  - Prevents accidental edits on hidden layers

- **Brush Broadcast Feedback**
  - Visual feedback when brush broadcast mode is active
  - Timeline frame highlighting (yellow/orange) for all affected frames
  - Warning dialog on first enable with clear explanation
  - Visual indicators: red border, warning icon, warning banner
  - Enhanced user awareness of destructive operations

- **Performance Optimizations**
  - Batch updates for layer operations
  - Dirty region tracking for efficient canvas rendering
  - Optimized layer composite calculations

### Planned
- Real-time collaboration
- Cloud pattern storage
- Advanced AI pattern generation
- 3D preview mode
- VR preview mode
- Enhanced plugin system
- Full scripting API

---

**For detailed information about specific features, see the [User Manual](docs/USER_MANUAL.md).**

**For installation instructions, see the [Installation Guide](docs/INSTALLATION.md).**

**For support, see [SUPPORT.md](docs/SUPPORT.md).**

---

**Last Updated**: 2024
