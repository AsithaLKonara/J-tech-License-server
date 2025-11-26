# Upload Bridge - User Manual

Complete guide to using Upload Bridge for LED matrix pattern design and firmware flashing.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Design Tools](#design-tools)
4. [Drawing Tools](#drawing-tools)
5. [Timeline and Frame Management](#timeline-and-frame-management)
6. [Layers and Blending](#layers-and-blending)
7. [Automation and Effects](#automation-and-effects)
8. [Media Upload](#media-upload)
9. [Export and Firmware Flashing](#export-and-firmware-flashing)
10. [Project Management](#project-management)
11. [Keyboard Shortcuts](#keyboard-shortcuts)
12. [Tips and Best Practices](#tips-and-best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Introduction

Upload Bridge is a professional LED matrix pattern design and firmware generation tool. It allows you to:

- Create custom LED patterns with a powerful drawing toolset
- Design animations with frame-based timeline editing
- Convert images, GIFs, and videos to LED patterns
- Generate and flash firmware for multiple microcontroller platforms
- Export patterns in various formats

### System Requirements

- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+, Debian 11+, Fedora 34+)
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB

### Installation

See [Installation Guide](INSTALLATION.md) for detailed platform-specific instructions.

---

## Getting Started

### First Launch

1. Launch Upload Bridge
2. You'll see the main window with multiple tabs:
   - **Design Tools**: Pattern editor
   - **Media Upload**: Convert media to patterns
   - **Flash**: Firmware generation and flashing
   - **Preview**: Pattern preview

### Creating Your First Pattern

1. Go to **Design Tools** tab
2. Set matrix dimensions (e.g., 32x32, 64x32)
3. Select a drawing tool
4. Choose a color
5. Draw on the canvas
6. Add frames for animation
7. Preview your pattern
8. Save your project

For detailed step-by-step instructions, see [Quick Start Guide](QUICKSTART.md).

---

## Design Tools

The Design Tools tab is the main workspace for creating LED patterns.

### Canvas

The canvas displays your pattern at the current frame. You can:

- **Draw**: Click and drag to draw with the selected tool
- **Zoom**: Use mouse wheel or zoom controls
- **Pan**: Middle-click and drag, or use scrollbars
- **Grid**: Toggle grid display for alignment

### Toolbar

The toolbar contains:

- **Drawing Tools**: 8 different drawing tools (see [Drawing Tools](#drawing-tools))
- **Color Picker**: Select colors for drawing
- **Palette**: Quick color selection
- **Layer Controls**: Add, remove, reorder layers
- **Frame Controls**: Add, delete, duplicate frames
- **Playback Controls**: Play, pause, stop animation

### Properties Panel

The properties panel shows:

- **Tool Settings**: Brush size, opacity, hardness
- **Frame Properties**: Duration, name
- **Layer Properties**: Opacity, blend mode, visibility
- **Pattern Properties**: Dimensions, FPS, metadata

---

## Drawing Tools

Upload Bridge provides 8 professional drawing tools:

### 1. Pixel Tool

Draw individual pixels or small areas.

**Usage:**
- Click to place a pixel
- Click and drag for continuous drawing
- Adjust brush size for larger areas

**Settings:**
- Brush size (1-50 pixels)
- Opacity (0-100%)
- Hardness (soft to hard edges)

### 2. Rectangle Tool

Draw rectangles and squares.

**Usage:**
- Click and drag to draw rectangle
- Hold Shift for perfect square
- Hold Alt to draw from center

**Settings:**
- Fill mode (filled, outline, both)
- Corner radius (rounded corners)
- Line width (for outline)

### 3. Circle Tool

Draw circles and ellipses.

**Usage:**
- Click and drag to draw ellipse
- Hold Shift for perfect circle
- Hold Alt to draw from center

**Settings:**
- Fill mode (filled, outline, both)
- Line width (for outline)

### 4. Line Tool

Draw straight lines.

**Usage:**
- Click start point, drag to end point
- Hold Shift for horizontal/vertical/diagonal lines
- Click to set points for multi-segment lines

**Settings:**
- Line width (1-50 pixels)
- Anti-aliasing (smooth edges)

### 5. Fill Tool

Fill areas with color.

**Usage:**
- Click on area to fill
- Fills connected pixels of same color
- Adjust tolerance for color matching

**Settings:**
- Tolerance (0-100, color matching sensitivity)
- Contiguous (fill only connected pixels)

### 6. Gradient Tool

Create color gradients.

**Usage:**
- Click and drag to set gradient direction
- Choose gradient type (linear, radial)
- Select start and end colors

**Settings:**
- Gradient type (linear, radial)
- Color stops (multiple colors)
- Opacity stops (transparency)

### 7. Random Spray Tool

Spray random pixels.

**Usage:**
- Click and drag to spray
- Creates random pixel distribution
- Adjust density and size

**Settings:**
- Density (pixels per area)
- Size variation (random pixel sizes)
- Color variation (random colors)

### 8. Text Tool

Add text to patterns.

**Usage:**
- Click to set text position
- Type text in dialog
- Configure font, size, alignment

**Settings:**
- Font family
- Font size
- Alignment (left, center, right)
- Bold, italic, underline

---

## Timeline and Frame Management

The timeline shows all frames in your pattern and allows frame management.

### Timeline View

- **Frames**: Each frame is displayed as a thumbnail
- **Playhead**: Current frame indicator
- **Selection**: Selected frames are highlighted
- **Markers**: Visual markers for important frames

### Frame Operations

**Add Frame:**
- Click "+" button
- Or press Insert key
- New frame is added after current frame

**Delete Frame:**
- Select frame(s)
- Press Delete key
- Or use context menu

**Duplicate Frame:**
- Right-click frame → Duplicate
- Or press Ctrl+D
- Creates copy after selected frame

**Reorder Frames:**
- Drag frame to new position
- Or use Move Up/Down buttons

### Multi-Select

Select multiple frames for bulk operations:

- **Click**: Select single frame
- **Ctrl+Click**: Add to selection
- **Shift+Click**: Select range
- **Ctrl+A**: Select all frames

**Bulk Operations:**
- Set duration for all selected frames
- Delete all selected frames
- Duplicate all selected frames
- Copy/paste frame sequences

### Frame Properties

Each frame has properties:

- **Duration**: How long frame displays (milliseconds)
- **Name**: Optional frame name/label
- **Tags**: Metadata tags for organization

---

## Layers and Blending

Upload Bridge supports multiple layers per frame for complex compositions.

### Layer Management

**Add Layer:**
- Click "Add Layer" button
- New layer appears above current layer
- Layers are numbered (Layer 1, Layer 2, etc.)

**Remove Layer:**
- Select layer
- Click "Remove Layer" button
- Bottom layer cannot be removed

**Reorder Layers:**
- Drag layer up/down in layer list
- Or use Move Up/Down buttons
- Top layers appear above bottom layers

**Merge Layers:**
- Select layers to merge
- Click "Merge Layers"
- Creates single layer with combined content

### Blend Modes

Each layer can use different blend modes:

- **Normal**: Standard opaque blending
- **Add**: Additive blending (brightens)
- **Multiply**: Multiplicative blending (darkens)
- **Screen**: Screen blending (lightens)
- **Overlay**: Overlay blending (contrast)

### Layer Properties

- **Opacity**: 0-100% transparency
- **Visibility**: Show/hide layer
- **Blend Mode**: Blending algorithm
- **Lock**: Prevent editing

---

## Automation and Effects

Automation actions create dynamic effects without manual frame-by-frame editing.

### Parametric Actions

**Scroll:**
- Scrolls pattern horizontally or vertically
- Configurable direction, speed, wrap mode

**Rotate:**
- Rotates pattern by degrees
- Clockwise or counter-clockwise
- Configurable center point

**Mirror:**
- Mirrors pattern horizontally or vertically
- Can mirror entire pattern or selection

**Invert:**
- Inverts colors
- Can invert entire pattern or selection

**Wipe:**
- Wipes pattern in specified direction
- Configurable wipe speed and direction

**Reveal:**
- Reveals pattern progressively
- Configurable reveal direction and speed

**Bounce:**
- Bounces pattern back and forth
- Configurable bounce distance and speed

### Using Automation

1. Select source frame(s)
2. Choose automation action
3. Configure parameters
4. Preview result
5. Apply to create new frames

### Effects Engine

The effects engine provides procedural visual effects:

- **Noise**: Random noise patterns
- **Blur**: Gaussian blur
- **Glow**: Glow effect
- **Outline**: Edge detection
- **Color Shift**: Hue/saturation adjustments

---

## Media Upload

Convert images, GIFs, and videos to LED patterns.

### Supported Formats

- **Images**: PNG, JPG, JPEG, BMP
- **Animations**: GIF (animated)
- **Videos**: MP4, AVI, MOV, MKV, WebM

### Conversion Process

1. Go to **Media Upload** tab
2. Click "Select Media File"
3. Choose your file
4. Configure settings:
   - **Dimensions**: Target LED matrix size
   - **FPS**: Frame rate (for videos/GIFs)
   - **Brightness**: 0-100%
   - **Color Order**: RGB, GRB, BRG, etc.
5. Preview conversion
6. Click "Convert to LED Pattern"
7. Pattern loads in Design Tools tab

### Conversion Tips

- Use high contrast images for better visibility
- Shorter videos (under 10 seconds) work best
- GIFs with fewer colors convert faster
- Test with small dimensions first
- Adjust brightness based on LED type

---

## Export and Firmware Flashing

Export patterns to various formats and flash to hardware.

### Export Formats

Upload Bridge supports multiple export formats:

- **BIN**: Binary format
- **HEX**: Intel HEX format
- **DAT**: Data format
- **LEDS**: LED pattern format
- **JSON**: JSON format
- **CSV**: CSV format
- **TXT**: Text format

### Export Process

1. Create or load pattern
2. Go to **Flash** tab
3. Select export format
4. Configure export settings
5. Click "Export"
6. Choose save location
7. File is saved

### Firmware Flashing

Flash patterns directly to microcontrollers:

1. **Select Chip**: Choose microcontroller type
   - ESP32, ESP32-S, ESP32-C3, ESP32-S3
   - ATmega2560, ATtiny85
   - STM32F407
   - PIC18F4550
   - Nuvoton M051

2. **Configure Settings**:
   - Serial port (COM port)
   - LED type (WS2812B, SK6812, etc.)
   - Color order (RGB, GRB, etc.)
   - Number of LEDs
   - GPIO pin number
   - Brightness

3. **Build Firmware**:
   - Click "Build Firmware"
   - Wait for compilation
   - Firmware is generated with pattern embedded

4. **Flash to Device**:
   - Click "Flash Firmware"
   - Wait for upload
   - Pattern plays on hardware

### Device Detection

Upload Bridge can auto-detect connected devices:

- Click "Detect Device"
- Application scans serial ports
- Detected devices are listed
- Select device from list

---

## Project Management

### Project Files

Upload Bridge uses `.ledproj` project files that contain:

- Pattern data (all frames, layers)
- Project metadata (name, author, tags)
- Settings (dimensions, FPS, etc.)
- Frame presets
- Layer configurations

### Saving Projects

**Save Project:**
- File → Save Project (Ctrl+S)
- Choose location and filename
- Project is saved as `.ledproj` file

**Save As:**
- File → Save As (Ctrl+Shift+S)
- Save with new name/location

**Auto-Save:**
- Projects auto-save every 5 minutes (configurable)
- Auto-save location: `~/.upload_bridge/autosave/`

### Loading Projects

**Open Project:**
- File → Open Project (Ctrl+O)
- Select `.ledproj` file
- Project loads with all frames and settings

**Recent Projects:**
- File → Recent Projects
- Quick access to recently opened projects

### Project Metadata

Each project can have metadata:

- **Name**: Project name
- **Author**: Creator name
- **Description**: Project description
- **Tags**: Categorization tags
- **Created**: Creation date/time
- **Modified**: Last modification date/time

---

## Keyboard Shortcuts

### General

- **Ctrl+N**: New project
- **Ctrl+O**: Open project
- **Ctrl+S**: Save project
- **Ctrl+Shift+S**: Save As
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+A**: Select all
- **Ctrl+C**: Copy
- **Ctrl+V**: Paste
- **Ctrl+X**: Cut
- **Delete**: Delete selection
- **F5**: Refresh
- **F11**: Fullscreen
- **Esc**: Cancel operation

### Design Tools

- **Space**: Play/pause animation
- **Left Arrow**: Previous frame
- **Right Arrow**: Next frame
- **Home**: First frame
- **End**: Last frame
- **Insert**: Add frame
- **Ctrl+D**: Duplicate frame
- **Ctrl+[**: Previous frame
- **Ctrl+]**: Next frame
- **+**: Zoom in
- **-**: Zoom out
- **0**: Reset zoom
- **R**: Rotate canvas
- **G**: Toggle grid

### Drawing Tools

- **P**: Pixel tool
- **R**: Rectangle tool
- **C**: Circle tool
- **L**: Line tool
- **F**: Fill tool
- **G**: Gradient tool
- **S**: Spray tool
- **T**: Text tool

### Layers

- **Ctrl+Shift+N**: New layer
- **Ctrl+Shift+Delete**: Delete layer
- **Ctrl+Shift+]**: Move layer up
- **Ctrl+Shift+[**: Move layer down
- **Ctrl+E**: Merge layers

---

## Tips and Best Practices

### Pattern Design

- **Start Small**: Begin with small matrices (8x8, 16x16) to learn
- **Use Layers**: Use multiple layers for complex compositions
- **Frame Duration**: 100-500ms works well for most animations
- **Color Contrast**: Use high contrast for better visibility
- **Test Often**: Preview frequently to catch issues early

### Performance

- **Optimize Patterns**: Remove unnecessary frames
- **Use RLE**: Enable RLE compression for large patterns
- **Limit Layers**: Too many layers can slow rendering
- **Close Unused Tabs**: Close tabs you're not using

### Hardware

- **Test Wiring**: Verify LED wiring before flashing
- **Check Power**: Ensure adequate power supply
- **Color Order**: Verify color order matches hardware
- **Brightness**: Start with lower brightness, increase as needed

### Workflow

- **Save Frequently**: Use Ctrl+S often
- **Use Presets**: Save common frame patterns as presets
- **Version Control**: Keep multiple versions of projects
- **Documentation**: Add notes to project metadata

---

## Troubleshooting

### Application Issues

**Application Won't Start:**
- Check Python version (needs 3.10+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check error logs

**Application Crashes:**
- Check available memory
- Close other applications
- Update graphics drivers
- Report issue with error details

### Pattern Issues

**Pattern Doesn't Display:**
- Check matrix dimensions
- Verify frame has content
- Check layer visibility
- Try refreshing (F5)

**Animation Too Fast/Slow:**
- Adjust frame durations
- Check FPS settings
- Verify timeline playback speed

### Hardware Issues

**Can't Connect to Device:**
- Check USB cable
- Verify COM port selection
- Install device drivers
- Try different USB port
- Check USB permissions (Linux)

**Pattern Doesn't Play on Hardware:**
- Verify firmware flashed successfully
- Check LED wiring
- Verify color order settings
- Check power supply
- Review brightness settings

**Colors Are Wrong:**
- Check color order (RGB vs GRB)
- Verify LED type selection
- Check wiring configuration
- Review brightness/color settings

### Export Issues

**Export Fails:**
- Check file permissions
- Verify disk space
- Check export format compatibility
- Review error messages

**Exported File Is Wrong:**
- Verify export format
- Check export settings
- Review pattern dimensions
- Try different format

For more detailed troubleshooting, see [Troubleshooting Guide](TROUBLESHOOTING.md).

---

## Additional Resources

- **[Quick Start Guide](QUICKSTART.md)** - Get started quickly
- **[Installation Guide](INSTALLATION.md)** - Installation instructions
- **[API Reference](../enterprise/API_REFERENCE.md)** - Developer documentation
- **[Chip Integration Guide](../enterprise/CHIP_INTEGRATION_GUIDE.md)** - Adding new chips

---

**Happy Pattern Creating!** 🎨✨

