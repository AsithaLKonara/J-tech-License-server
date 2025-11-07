# Upload Bridge - Complete User Flows Documentation

## 📋 Table of Contents
1. [Application Overview](#application-overview)
2. [Entry Points](#entry-points)
3. [Primary User Flows](#primary-user-flows)
4. [Tab-Specific Flows](#tab-specific-flows)
5. [Advanced Flows](#advanced-flows)
6. [Error Handling & Recovery](#error-handling--recovery)

---

## 🎯 Application Overview

**Upload Bridge** is a universal LED pattern flasher application with 5 main tabs:

1. **🎬 Media Upload** - Convert images, GIFs, videos to LED patterns
2. **👁️ Preview** - Visualize and edit LED patterns
3. **⚡ Flash** - Build firmware and upload via USB
4. **📡 WiFi Upload** - Upload patterns wirelessly to ESP devices
5. **🔧 Arduino IDE** - Integrated Arduino development environment

**Key Features:**
- Supports 14+ microcontroller types (ESP8266, ESP32, AVR, STM32, PIC, Nuvoton)
- Auto-detects pattern dimensions from files
- Real-time preview and editing
- Multi-format support (.bin, .hex, .dat, .leds, .ledproj, .json, media files)
- Cross-platform (Windows, Linux, macOS)

---

## 🚪 Entry Points

### 1. **Application Launch**
```
User → Launches Upload Bridge → Main Window Opens
                                         ↓
                    Shows status: "Ready - Load a pattern to get started"
                    Displays 5 tabs: Media Upload | Preview | Flash | WiFi Upload | Arduino IDE
```

### 2. **File Menu Actions**
- **File > Open** - Open pattern/media file
- **File > Open Project** - Open saved .ledproj project
- **File > Save Project** - Save current pattern as project
- **File > Save Project As** - Save with new name
- **File > Export** - Export pattern to various formats
- **File > Exit** - Close application

### 3. **Toolbar Quick Actions**
- **📂 Open** - Quick file open
- **💾 Save** - Quick save
- **👁️ Preview** - Switch to Preview tab
- **⚡ Flash** - Switch to Flash tab

---

## 🌊 Primary User Flows

### **Flow 1: Loading a Pattern File**

```
START: User clicks "File > Open" or Toolbar "Open"
         ↓
    File Dialog Opens
    Shows filters:
    - All Supported (*.bin *.hex *.dat *.leds *.ledproj *.mp4 *.avi ...)
    - Pattern Files (*.bin *.hex *.dat *.leds)
    - Media Files (*.mp4 *.avi *.mov *.mkv *.webm *.gif *.jpg *.jpeg *.png *.bmp)
    - Project Files (*.ledproj)
    - All Files (*.*)
         ↓
    User selects file
         ↓
    ┌─────────────────────────────────────────┐
    │  File Type Detection                    │
    └─────────────────────────────────────────┘
         │
         ├─→ Media File (video/image/gif)
         │   ↓
         │   Convert to Pattern
         │   ↓
         │   Load to ALL tabs
         │
         ├─→ Project File (.ledproj)
         │   ↓
         │   Load from JSON format
         │   ↓
         │   Load to ALL tabs
         │
         └─→ Pattern File (.bin/.hex/.dat/.leds)
             ↓
             Try Auto-Detection
                 ├─→ Success → Auto-detect LEDs/Frames
                 │              ↓
                 │         Load to ALL tabs
                 │
                 └─→ Failure → Ask user for:
                                 - LED count
                                 - Frame count
                                 ↓
                            Load to ALL tabs
         ↓
    Pattern loaded to:
    • Preview Tab (visual preview)
    • Flash Tab (ready to upload)
    • WiFi Upload Tab (ready for wireless)
         ↓
    Switch to Preview Tab automatically
         ↓
    Success dialog shows:
    - Name
    - Dimensions
    - Frames
    - Duration
    - FPS
         ↓
    Window title updates: "Upload Bridge - [filename]"
    Status bar: "Loaded: [info]"
         ↓
END: Pattern ready for use across all tabs
```

### **Flow 2: Converting Media to Pattern**

```
START: User is on Media Upload Tab
         ↓
    Option A: Click "Select Media File" button
    Option B: Drag & drop file
    Option C: File > Open (auto-routes to Media Upload)
         ↓
    File Dialog Opens
    Shows media formats:
    - Images: PNG, JPG, JPEG, BMP
    - Animations: GIF
    - Videos: MP4, AVI, MOV, MKV, WebM
         ↓
    User selects media file
         ↓
    ┌─────────────────────────────────────────┐
    │  Media Preview Widget                    │
    └─────────────────────────────────────────┘
    • Shows preview of media
    • Displays file info (resolution, duration, etc.)
    • Shows frame-by-frame for videos/GIFs
         ↓
    ┌─────────────────────────────────────────┐
    │  Conversion Settings                    │
    └─────────────────────────────────────────┘
    User can adjust:
    • Target Dimensions (width x height)
    • Brightness
    • Frame Extraction (for videos)
    • Color Reduction
    • FPS (for animations)
         ↓
    User clicks "Convert to Pattern"
         ↓
    ┌─────────────────────────────────────────┐
    │  Media Converter Processing             │
    └─────────────────────────────────────────┘
    • Extracts frames (video/GIF)
    • Resizes to target dimensions
    • Converts to RGB values
    • Creates Pattern object
         ↓
    Pattern created
         ↓
    Emits "pattern_loaded" signal
         ↓
    Main Window receives signal
         ↓
    ┌─────────────────────────────────────────┐
    │  load_pattern_to_all_tabs()            │
    └─────────────────────────────────────────┘
    • Stores pattern in main window
    • Loads to Preview tab
    • Loads to Flash tab
    • Loads to WiFi Upload tab
    • Switches to Preview tab
         ↓
    Success message shows pattern details
         ↓
END: Pattern ready in all tabs, user can:
    • Preview/edit in Preview tab
    • Flash via USB in Flash tab
    • Upload wirelessly in WiFi Upload tab
```

### **Flow 3: Previewing and Editing Pattern**

```
START: User on Preview Tab (pattern already loaded)
         ↓
    ┌─────────────────────────────────────────┐
    │  Enhanced LED Simulator Widget         │
    └─────────────────────────────────────────┘
    Displays:
    • Visual LED matrix simulation
    • Real-time animation playback
    • Frame navigation controls
         ↓
    ┌─────────────────────────────────────────┐
    │  Playback Controls                      │
    └─────────────────────────────────────────┘
    • Play/Pause button
    • Stop button
    • Frame slider (scrub through frames)
    • Frame counter (current/total)
    • Speed control (0.1x - 5.0x)
         ↓
    ┌─────────────────────────────────────────┐
    │  Brightness Controls                    │
    └─────────────────────────────────────────┘
    • Brightness slider (0-255)
    • Advanced brightness controller (if enabled)
         ↓
    ┌─────────────────────────────────────────┐
    │  Advanced Controls (Optional)           │
    └─────────────────────────────────────────┘
    • FPS adjustment
    • Speed interpolation
    • Per-channel brightness
    • Curve types (linear, exponential, etc.)
         ↓
    User makes edits
         ↓
    Changes apply in real-time
         ↓
    User can:
    • Export modified pattern
    • Save as project
    • Navigate to Flash tab
    • Navigate to WiFi Upload tab
         ↓
END: Pattern ready for upload with modifications
```

### **Flow 4: Flashing Pattern to Device (USB)**

```
START: User on Flash Tab (pattern already loaded)
         ↓
    ┌─────────────────────────────────────────┐
    │  Target Chip Selection                 │
    └─────────────────────────────────────────┘
    Dropdown shows supported chips:
    • ESP8266 variants
    • ESP32 variants
    • AVR (ATmega328P, ATmega2560, ATtiny85)
    • STM32 (STM32F103C8, etc.)
    • PIC (PIC16F876A)
    • Nuvoton (NuMicro M051)
         ↓
    User selects chip
         ↓
    ┌─────────────────────────────────────────┐
    │  Port Selection                        │
    └─────────────────────────────────────────┘
    • Auto-detects available COM ports
    • User selects port from dropdown
    • Refresh button available
         ↓
    ┌─────────────────────────────────────────┐
    │  GPIO Configuration                     │
    └─────────────────────────────────────────┘
    • Data pin selection
    • Clock pin selection (if applicable)
    • Chip-specific options
         ↓
    ┌─────────────────────────────────────────┐
    │  Build Options                          │
    └─────────────────────────────────────────┘
    • Verify upload (checkbox)
    • Baud rate selection
    • Flash mode selection (ESP chips)
         ↓
    User clicks "Build & Flash" button
         ↓
    ┌─────────────────────────────────────────┐
    │  Firmware Builder                       │
    └─────────────────────────────────────────┘
    • Selects appropriate firmware template
    • Embeds pattern data into firmware
    • Compiles for target chip
    • Generates binary file
         ↓
    Progress bar shows build progress
    Log shows detailed build output
         ↓
    Build successful
         ↓
    ┌─────────────────────────────────────────┐
    │  Uploader Process                      │
    └─────────────────────────────────────────┘
    • Initializes communication with device
    • Erases flash (if needed)
    • Uploads firmware in chunks
    • Shows progress (0-100%)
         ↓
    ┌─────────────────────────────────────────┐
    │  Verification (if enabled)               │
    └─────────────────────────────────────────┘
    • Reads back firmware
    • Compares with uploaded data
    • Verifies integrity
         ↓
    Success/Error message
         ↓
    ┌─────────────────────────────────────────┐
    │  Result                                 │
    └─────────────────────────────────────────┘
    ✅ SUCCESS:
       • "Flash successful!" in status bar
       • Log shows upload details
       • Duration and bytes written displayed
    
    ❌ ERROR:
       • Error message in dialog
       • Detailed error in log
       • User can retry
         ↓
END: Pattern flashed to device (success) or error shown (retry)
```

### **Flow 5: Uploading Pattern via WiFi**

```
START: User on WiFi Upload Tab (pattern already loaded)
         ↓
    ┌─────────────────────────────────────────┐
    │  Connection Settings                    │
    └─────────────────────────────────────────┘
    User enters:
    • ESP Device IP Address (e.g., 192.168.1.100)
    • Port (default: 80)
    • WiFi SSID (if setting up device)
    • WiFi Password (if setting up device)
         ↓
    ┌─────────────────────────────────────────┐
    │  Connection Test (Optional)             │
    └─────────────────────────────────────────┘
    User clicks "Test Connection"
         ↓
    Connection Status Indicator shows:
    • 🟢 Connected - ESP device reachable
    • 🔴 Disconnected - Cannot reach device
         ↓
    ┌─────────────────────────────────────────┐
    │  Pattern Selection                      │
    └─────────────────────────────────────────┘
    • Shows current pattern (if loaded)
    • "Browse" button to select different file
    • Pattern info display (dimensions, frames)
         ↓
    ┌─────────────────────────────────────────┐
    │  Upload Settings                        │
    └─────────────────────────────────────────┘
    • Auto-start playback (checkbox)
    • Brightness level
    • FPS adjustment
         ↓
    User clicks "Upload Pattern" button
         ↓
    ┌─────────────────────────────────────────┐
    │  WiFi Upload Worker Thread             │
    └─────────────────────────────────────────┘
    • Checks ESP device connection
    • Validates pattern file
    • Creates HTTP request
    • Uploads pattern data
         ↓
    Progress bar updates (0-100%)
    Status log shows:
    • "Connecting to ESP8266..."
    • "Uploading pattern..."
    • "Upload complete!"
         ↓
    ┌─────────────────────────────────────────┐
    │  Result                                 │
    └─────────────────────────────────────────┘
    ✅ SUCCESS:
       • Success message dialog
       • Pattern available on ESP device
       • Auto-plays if enabled
       • Connection status: 🟢 Connected
    
    ❌ ERROR:
       • Error dialog with details
       • Connection status: 🔴 Disconnected
       • User can check:
         - IP address correct?
         - ESP device powered on?
         - WiFi connected?
         - Firewall blocking?
         ↓
END: Pattern uploaded wirelessly (success) or error (troubleshoot)
```

### **Flow 6: Arduino IDE Development**

```
START: User on Arduino IDE Tab
         ↓
    ┌─────────────────────────────────────────┐
    │  Code Editor                            │
    └─────────────────────────────────────────┘
    • Syntax highlighting for C/C++
    • Line numbers
    • Auto-indentation
    • Text editing capabilities
         ↓
    ┌─────────────────────────────────────────┐
    │  File Operations                        │
    └─────────────────────────────────────────┘
    User can:
    • New Sketch - Create new Arduino file
    • Open Sketch - Load existing .ino file
    • Save Sketch - Save current code
    • Save As - Save with new name
         ↓
    User writes/edits Arduino code
         ↓
    ┌─────────────────────────────────────────┐
    │  Board Configuration                    │
    └─────────────────────────────────────────┘
    • Board Selection (dropdown)
      - Arduino Uno
      - Arduino Nano
      - ESP8266 variants
      - ESP32 variants
      - Custom boards
    • Port Selection (COM ports)
    • Programmer selection
         ↓
    ┌─────────────────────────────────────────┐
    │  Compilation                            │
    └─────────────────────────────────────────┘
    User clicks "Compile" button
         ↓
    Arduino CLI compiles sketch
         ↓
    Compile output shows in:
    • Progress bar
    • Output log (compiler messages)
         ↓
    ✅ Compilation Success:
       • Shows "Compilation successful"
       • Binary size displayed
       • Ready for upload
    
    ❌ Compilation Error:
       • Error messages in log
       • Line numbers highlighted
       • User fixes code
         ↓
    ┌─────────────────────────────────────────┐
    │  Upload to Board                       │
    └─────────────────────────────────────────┘
    User clicks "Upload" button
         ↓
    Arduino CLI uploads sketch
         ↓
    Upload progress shown
         ↓
    ✅ Upload Success:
       • "Upload successful"
       • Sketch running on board
    
    ❌ Upload Error:
       • Error message shown
       • Check port/board settings
         ↓
    ┌─────────────────────────────────────────┐
    │  Serial Monitor (Optional)             │
    └─────────────────────────────────────────┘
    • Open serial monitor
    • Set baud rate
    • View serial output from board
    • Send serial commands
         ↓
END: Arduino sketch uploaded and running
```

---

## 📑 Tab-Specific Flows

### **Media Upload Tab Flows**

#### **Sub-Flow 1.1: Image Conversion**
```
Select Image File (.png/.jpg/.bmp)
    ↓
Preview shows image
    ↓
Set dimensions (e.g., 64x32)
    ↓
Adjust brightness/color options
    ↓
Convert to Pattern
    ↓
Pattern created with single frame
    ↓
Auto-distributed to all tabs
```

#### **Sub-Flow 1.2: GIF Conversion**
```
Select GIF File
    ↓
Preview shows animated GIF
    ↓
Frame navigation controls active
    ↓
Extract frames (all or selected)
    ↓
Set target dimensions
    ↓
Convert to Pattern
    ↓
Pattern created with multiple frames
    ↓
Auto-distributed to all tabs
```

#### **Sub-Flow 1.3: Video Conversion**
```
Select Video File (.mp4/.avi/.mov)
    ↓
Preview shows video with playback controls
    ↓
Set frame extraction:
    • All frames
    • Sample every N frames
    • Time range
    ↓
Set target dimensions
    ↓
Convert to Pattern
    ↓
Pattern created with video frames
    ↓
Auto-distributed to all tabs
```

### **Preview Tab Flows**

#### **Sub-Flow 2.1: Pattern Playback**
```
Pattern loaded in Preview Tab
    ↓
Click "Play" button
    ↓
Animation plays at configured FPS
    ↓
Real-time visual update
    ↓
Adjust speed (0.1x - 5.0x)
    ↓
Pause/Resume anytime
    ↓
Frame slider to scrub
```

#### **Sub-Flow 2.2: Brightness Adjustment**
```
Pattern loaded
    ↓
Adjust brightness slider
    ↓
Real-time preview updates
    ↓
Advanced controls (if enabled):
    • Per-channel brightness
    • Curve type selection
    • Brightness presets
    ↓
Changes apply immediately
```

#### **Sub-Flow 2.3: Pattern Export**
```
Pattern loaded and edited
    ↓
Click "Export" (from menu or button)
    ↓
Choose export format:
    • .bin (binary)
    • .hex (Intel HEX)
    • .leds (LEDS format)
    • .ledproj (project)
    • .json (JSON)
    ↓
Save file
    ↓
Pattern exported successfully
```

### **Flash Tab Flows**

#### **Sub-Flow 3.1: ESP8266 Upload**
```
Select ESP8266 chip
    ↓
Select COM port
    ↓
Set GPIO pin (e.g., D4)
    ↓
Build & Flash
    ↓
Firmware built with pattern embedded
    ↓
esptool.py uploads to ESP8266
    ↓
Verification (if enabled)
    ↓
Success!
```

#### **Sub-Flow 3.2: AVR Upload**
```
Select AVR chip (e.g., ATmega328P)
    ↓
Select COM port
    ↓
Set GPIO pins
    ↓
Build & Flash
    ↓
Firmware compiled for AVR
    ↓
avrdude uploads via USB
    ↓
Verification
    ↓
Success!
```

### **WiFi Upload Tab Flows**

#### **Sub-Flow 4.1: First-Time Setup**
```
ESP device not configured
    ↓
Enter WiFi SSID
    ↓
Enter WiFi Password
    ↓
Enter device IP (or use auto-detect)
    ↓
Test Connection
    ↓
Device configured and connected
    ↓
Ready for upload
```

#### **Sub-Flow 4.2: Pattern Upload**
```
ESP device already configured
    ↓
Test connection (optional)
    ↓
Select pattern (or use current)
    ↓
Configure upload settings
    ↓
Upload Pattern
    ↓
HTTP POST to ESP device
    ↓
Pattern stored on ESP flash
    ↓
Auto-play if enabled
```

### **Arduino IDE Tab Flows**

#### **Sub-Flow 5.1: New Sketch Creation**
```
Click "New Sketch"
    ↓
Blank editor opens
    ↓
Default template loaded:
    void setup() {}
    void loop() {}
    ↓
User writes code
    ↓
Save sketch
    ↓
Ready for compile/upload
```

#### **Sub-Flow 5.2: Existing Sketch Editing**
```
Click "Open Sketch"
    ↓
Select .ino file
    ↓
Code loads in editor
    ↓
Edit code with syntax highlighting
    ↓
Save changes
    ↓
Compile/Upload
```

---

## 🚀 Advanced Flows

### **Flow A: Multi-File Batch Processing**

```
File > Open (multiple selection)
    ↓
For each file:
    - Load/Convert
    - Preview
    - Flash (if batch enabled)
    ↓
Process queue
    ↓
All files uploaded
```

### **Flow B: Pattern Editing Workflow**

```
1. Load pattern file
    ↓
2. Preview and inspect
    ↓
3. Make edits (brightness, speed, etc.)
    ↓
4. Preview changes
    ↓
5. Export edited pattern
    OR
5. Save as project
    OR
5. Flash to device
```

### **Flow C: Cross-Tab Workflow**

```
START: Media Upload Tab
    Convert video to pattern
        ↓
Auto-switch to Preview Tab
    Preview and adjust
        ↓
Navigate to Flash Tab
    Configure chip/port
    Flash to device
        ↓
OR Navigate to WiFi Upload Tab
    Configure ESP device
    Upload wirelessly
```

### **Flow D: Project Management**

```
Create new project:
    File > Open (pattern/media)
        ↓
Edit pattern in Preview
        ↓
File > Save Project
    Save as .ledproj
        ↓
Close application
        ↓
Later: File > Open Project
    Load .ledproj
    Pattern restored with all settings
```

---

## ⚠️ Error Handling & Recovery

### **Error Flow 1: File Load Error**

```
User opens file
    ↓
Parser fails
    ↓
Error dialog shows:
    "Failed to load pattern: [error details]"
    ↓
User options:
    • Try different file
    • Enter manual dimensions
    • Cancel
```

### **Error Flow 2: Build Failure**

```
User clicks "Build & Flash"
    ↓
Firmware build fails
    ↓
Error log shows:
    • Compilation errors
    • Missing dependencies
    • Template issues
    ↓
User fixes issues or:
    • Try different chip
    • Check toolchain installation
    • Use Arduino IDE tab
```

### **Error Flow 3: Upload Failure**

```
Upload starts
    ↓
Device communication fails
    ↓
Error dialog shows:
    • Port not found
    • Device not responding
    • Timeout error
    ↓
User troubleshooting:
    • Check USB connection
    • Verify port selection
    • Reset device
    • Try different port
    ↓
Retry upload
```

### **Error Flow 4: WiFi Connection Failure**

```
User clicks "Upload Pattern"
    ↓
Connection test fails
    ↓
Status: 🔴 Disconnected
    ↓
Error message shows
    ↓
User checks:
    • IP address correct?
    • ESP device powered on?
    • WiFi network connected?
    • Firewall settings?
    ↓
Test connection again
    OR
    Reconfigure ESP device
```

### **Error Flow 5: Media Conversion Error**

```
User converts media file
    ↓
Conversion fails
    ↓
Error dialog shows:
    • Unsupported format
    • Corrupted file
    • Memory error
    ↓
User options:
    • Try different file
    • Use simpler settings
    • Check file integrity
```

---

## 📊 Integration Matrix

| Feature | Media Upload | Preview | Flash | WiFi Upload | Arduino IDE |
|---------|-------------|---------|-------|-------------|-------------|
| **Load Pattern** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Edit Pattern** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Preview Pattern** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Convert Media** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Upload USB** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Upload WiFi** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Arduino Dev** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Save Project** | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## 🎯 Quick Reference: Common Workflows

### **Workflow 1: Quick Pattern Flash**
```
File > Open (pattern file)
    → Auto-loads to all tabs
    → Switch to Flash tab
    → Select chip/port
    → Build & Flash
```

### **Workflow 2: Video to LED Matrix**
```
Open Media Upload tab
    → Select video file
    → Preview and adjust settings
    → Convert to pattern
    → Auto-loads to all tabs
    → Flash to device OR Upload via WiFi
```

### **Workflow 3: Edit and Re-upload**
```
File > Open (pattern)
    → Preview tab
    → Adjust brightness/speed
    → Save as project OR Export
    → Flash with changes
```

### **Workflow 4: Wireless Setup**
```
WiFi Upload tab
    → Configure ESP device (first time)
    → Load pattern
    → Upload Pattern
    → Pattern plays on ESP device
```

### **Workflow 5: Arduino Integration**
```
Arduino IDE tab
    → Write custom Arduino code
    → Compile
    → Upload to board
    → Serial monitor for debugging
```

---

## 🔄 Signal Flow Diagram

```
MediaUploadTab
    pattern_loaded signal
         ↓
MainWindow.load_pattern_from_media()
         ↓
MainWindow.load_pattern_to_all_tabs()
         ↓
    ├─→ PreviewTab.load_pattern()
    ├─→ FlashTab.load_pattern()
    └─→ WiFiUploadTab.set_pattern()

PreviewTab
    pattern_modified signal
         ↓
MainWindow.on_pattern_modified()
         ↓
Updates main pattern state

FlashTab
    flash_complete signal
         ↓
MainWindow.on_flash_complete()
         ↓
Updates status bar
```

---

## 📝 Notes

- **Auto-Save**: Settings are automatically saved to QSettings
- **State Persistence**: Window geometry, last directory, preferences saved
- **Thread Safety**: All upload operations run in separate threads to keep UI responsive
- **Progress Feedback**: All long-running operations show progress bars and detailed logs
- **Error Recovery**: Detailed error messages guide users to resolution
- **Cross-Platform**: File dialogs, path handling work on Windows, Linux, macOS

---

**End of User Flows Documentation**


