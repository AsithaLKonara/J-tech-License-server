# Upload Bridge - Ultimate User Guide

Welcome to the comprehensive user guide for **Upload Bridge**, the Universal LED Pattern Flasher and Design Studio. This guide covers every feature, tab, and workflow available in the application.

---

## 📚 Table of Contents
1. [Getting Started](#getting-started)
   - [Authentication & License](#authentication--license)
2. [Interface Overview](#interface-overview)
   - [Menu Bar](#menu-bar)
   - [Main tabs](#main-tabs)
3. [Tab Workflows](#tab-workflows)
   - [🎬 Media Upload](#-media-upload-tab)
   - [🎨 Design Tools](#-design-tools-tab)
   - [👁️ Preview Tab](#%EF%B8%8F-preview-tab)
   - [⚡ Flash Tab](#-flash-tab)
   - [📚 Pattern Library](#-pattern-library-tab)
   - [📡 WiFi Upload](#-wifi-upload-tab)
   - [🔧 Arduino IDE](#-arduino-ide-tab)
4. [Advanced Features](#advanced-features)
   - [Multi-Device Sync](#multi-device-sync)
   - [Firmware Builder](#firmware-builder)

---

## Getting Started

### Authentication & License
Upon launching Upload Bridge, you will be prompted to log in.
1. **Login**: Enter your credentials to authenticate with the J-Tech License Server.
2. **License Activation**: If you have a valid license key, the application will activate automatically.
   - **Offline Grace Period**: You can use the app offline for a limited time after initial activation.
   - **Manage License**: Go to `License > Activate / Manage License` to view status or deactivate the current device.

---

## Interface Overview

The main window consists of a **Menu Bar** at the top and a **Tabbed Interface** in the center.

### Menu Bar
- **File**
  - **Open Pattern** (`Ctrl+O`): Open .bin, .json, .leds files.
  - **Save Project** (`Ctrl+S`): Save current work as a project.
  - **Save Project As** (`Ctrl+Shift+S`): Save copy of project.
  - **New/Duplicate Pattern**: Create fresh workspaces.
  - **Exit** (`Ctrl+Q`): Close application.
  
- **Edit**
  - **Copy/Paste Pattern** (`Ctrl+C`/`V`): distinct from text copy/paste; copies entire LED patterns between tabs.
  - **Undo/Redo** (`Ctrl+Z`/`Y`): Revert changes in Design Tools.

- **View**
  - **Workspace**: Toggle side panels.

- **Tools**
  - **Refresh Ports** (`F5`): Scan for new USB serial devices.
  - **Force Dimensions**: Manually override pattern width/height if auto-detection fails.

- **License**
  - Manage activation status and deactivation.

---

## Tab Workflows

### 🎬 Media Upload Tab
*Convert videos, GIFs, and images into LED patterns.*

**Features:**
1. **Media Import**: Drag & drop or browse for images/videos (MP4, AVI, GIF, PNG, JPG).
2. **Preview**: Real-time playback of the source media.
3. **Quick Settings**:
   - **Preset**: Select standard sizes (8x8, 16x16, 64x32, etc.).
   - **Custom**: Define exact LED matrix dimensions.
4. **Pattern Info**: detailed stats on LED count, frames, duration, and FPS.
5. **Actions**:
   - **Load Pattern**: Converts media and sends it to **Flash** and **Preview** tabs.
   - **Save Pattern**: Save converted result to disk.

**Workflow:**
1. Import a GIF/Video.
2. Select your Matrix size (e.g., 16x16).
3. Click **Load Pattern**.
4. Go to **Flash Tab** to upload.

---

### 🎨 Design Tools Tab
*Create custom pixel art and animations from scratch.*

**Features:**
- **Canvas**: Interactive grid for drawing.
- **Drawing Tools**: Pencil, Line, Rectangle, Circle, Fill Bucket.
- **Timeline**: Frame-by-frame animation control (Add, Remove, Duplicate frames).
- **Layers**: Support for multiple design layers.
- **Color Palette**: Pick and save colors.

**Workflow:**
1. Create a `New Pattern` via File menu.
2. Draw pixel art using tools.
3. Add frames for animation.
4. Switch to **Preview Tab** to see the result.

---

### 👁️ Preview Tab
*Visualize patterns before flashing.*

**Features:**
- **Real-time Simulation**: accurate rendering of LED behavior.
- **Wiring Simulation**:
  - **Wiring Mode**: Serpentine, Z-Shape, Raster.
  - **Data In**: Select corner (Top-Left, Bottom-Right, etc.).
  - **RGB Order**: GRB, RGB, BRG selection.
- **Playback Controls**: Play, Pause, Scrub timeline, Speed control.
- **Brightness**: Adjust simulation brightness.

**Critical Note:** The *Wiring Simulation* settings here determine how the **Flash Tab** converts your data. Ensure these match your physical build!

---

### ⚡ Flash Tab
*Upload firmware and patterns to physical hardware.*

**Key Sections:**
1. **Target Chip**:
   - Select microcontroller (ESP8266, ESP32, AVR).
   - Shows chip specs (Flash size, RAM).
2. **Serial Port**:
   - Select COM port of connected device.
   - Use **Refresh** if device was just plugged in.
3. **Configuration**:
   - **Data GPIO**: Pin number where LEDs are connected.
   - **Verify**: Read back data after flash to ensure integrity.
4. **Orientation Corrections**:
   - **Flip X / Flip Y**: Fix mirrored hardware setups (hardware patch).
5. **Flash Process**:
   - **Build**: Compiles custom firmware with your pattern.
   - **Upload**: Flashes binary to chip.
   - **Log**: Detailed output of build/flash process.

**Pro Workflow:**
- If your physical matrix is wired differently than the file:
  1. Go to **Preview Tab**.
  2. Adjust **Wiring Mode** simulation until preview looks correct.
  3. Go to **Flash Tab**.
  4. Ensure **Flip X/Y** are unchecked (unless needed).
  5. Click **Flash to Device**. The app automatically converts data from "Preview Wire Order" to "Physical Wire Order".

---

### 📚 Pattern Library Tab
*Manage your local collection of patterns.*

**Features:**
- **Search**: Filter by name, category, or LED count.
- **Grid View**: Visual thumbnails of your library.
- **Metadata**: Add tags, descriptions, and authors.
- **Management**: Add, Remove, or Edit existing library entries.
- **Load**: Double-click any pattern to load it into the editor/flasher.

---

### 📡 WiFi Upload Tab
*Wireless management for ESP8266/ESP32 devices.*

**Features:**
1. **Connection**:
   - Enter Device IP (default `192.168.4.1` for AP mode).
   - Enter WiFi SSID/Pass to configure device.
2. **File Selection**: Pick local .bin/.dat files.
3. **Controls**:
   - **Upload via WiFi**: OTA transfer.
   - **Brightness**: Set remote device brightness.
   - **Sync**: Send pattern to multiple IPs simultaneously.
4. **Scheduling**:
   - Set patterns to play at specific times (requires device time sync).
5. **Security Warning**: Only use on trusted local networks.

---

### 🔧 Arduino IDE Tab
*Advanced code editing and raw flashing.*

**Features:**
- **Code Editor**: C++ syntax highlighting.
- **Presets**: Default templates for FastLED/NeoPixel sketches.
- **Board Config**: Select board FQBN (e.g., `arduino:avr:uno`) and Port.
- **Actions**:
  - **Compile**: Verify code validity.
  - **Upload**: Flash sketch to board.
  - **Verify**: Check for errors.
- **Output**: Real-time compiler/uploader feedback.

---

## Advanced Features

### Multi-Device Sync
In the **WiFi Upload Tab**, use the "Multi-Device Sync" group to enter multiple IP addresses (comma-separated). Clicking "Sync Pattern" will sequentially upload the current file to all listed devices.

### Firmware Builder
The application includes a built-in **Firmware Builder** (backend service). When you flash a pattern, the app:
1. Generates a valid C++ Sketch (`.ino`).
2. Embeds your pattern data (compressed).
3. Compiles using `arduino-cli`.
4. Uploads the binary.

This ensures you don't need to manually write Arduino code for standard pattern playback. Use the **View Firmware** button in the Flash Tab logs to inspect the generated code.

---

*Copyright © 2026 J-Tech. All rights reserved.*
