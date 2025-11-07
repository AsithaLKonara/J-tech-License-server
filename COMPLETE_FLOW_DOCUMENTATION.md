# Complete Flow: File Open → Flash Complete

## Overview
This document traces the complete data flow from opening a pattern file through to flashing firmware to hardware.

---

## Stage 1: File Opening & Loading

### Entry Point: Main Window
**File:** `ui/main_window.py`

```
User clicks "Open Pattern" button
↓
MainWindow.on_open_pattern()
    ↓
    Opens file dialog → selects file
    ↓
    Calls self.load_pattern(file_path)
```

### Pattern Loading
**File:** `ui/main_window.py` → `load_pattern()`

```
MainWindow.load_pattern(file_path)
    ↓
    1. Detects file format using ParserRegistry
       File: parsers/parser_registry.py
       Function: detect_format(file_path)
       → Checks file extension and content
    ↓
    2. Selects appropriate parser (e.g., enhanced_binary_parser.py)
       File: parsers/enhanced_binary_parser.py
       Function: EnhancedBinaryParser.parse(file_path)
       → Reads binary file
       → Extracts frames (pixel data)
       → Extracts metadata (width, height, fps, etc.)
       → Returns Pattern object
    ↓
    3. Passes Pattern to PreviewTab
       File: ui/tabs/preview_tab.py
       Function: PreviewTab.load_pattern(pattern, file_path)
```

**Key Data Structure Created:**
```python
Pattern(
    name: str,
    metadata: PatternMetadata(
        width: int,
        height: int,
        color_order: str,
        brightness: float,
        wiring_mode: str,
        data_in_corner: str,
        original_wiring_mode: str,  # Set during preview load
        original_data_in_corner: str,
        already_unwrapped: bool
    ),
    frames: List[Frame(
        pixels: List[Tuple[int, int, int]],  # RGB tuples
        duration_ms: int
    )]
)
```

---

## Stage 2: Preview Layer Processing

### Preview Tab Load
**File:** `ui/tabs/preview_tab.py` → `load_pattern()`

```
PreviewTab.load_pattern(pattern, file_path)
    ↓
    1. SERPENTINE DETECTION & UNWRAPPING
       File: core/pattern_converter.py
       Function: detect_serpentine_pattern(pattern)
       → Analyzes pixel patterns to detect if file is serpentine
       
       If detected as serpentine:
           ↓
           Store original format in metadata:
               pattern.metadata.original_wiring_mode = 'Serpentine'
               pattern.metadata.original_data_in_corner = 'LT'
           ↓
           UNWRAP to design order:
           File: core/pattern_converter.py
           Function: hardware_to_design_order(pattern, 'Serpentine', 'LT')
               ↓
               For each frame:
                   Uses WiringMapper to convert hardware → design order
                   File: core/wiring_mapper.py
                   → Builds reverse mapping table
                   → Reorders pixels to sequential L→R, T→B
               ↓
               Returns new Pattern with unwrapped frames
               Sets: pattern.metadata.already_unwrapped = True
       
       If NOT serpentine (Row-major):
           pattern.metadata.original_wiring_mode = 'Row-major'
           pattern.metadata.original_data_in_corner = 'LT'
           pattern.metadata.already_unwrapped = False
    ↓
    2. STORE PATTERN
       self.pattern = pattern  # Design-order pattern for preview
       self._base_pattern = pattern
    ↓
    3. SET INITIAL LOAD FLAG
       self.simulator._initial_load = True
       → Ensures UI dropdowns sync with metadata only once
    ↓
    4. BUILD PREVIEW PATTERN
       File: ui/tabs/preview_tab.py
       Function: _rebuild_preview_pattern()
       → Applies FPS changes
       → Applies brightness changes
       → Applies speed curves
       → Creates self._preview_pattern
    ↓
    5. LOAD INTO SIMULATOR
       File: ui/widgets/enhanced_led_simulator.py
       Function: EnhancedLEDSimulatorWidget.load_pattern(pattern)
           ↓
           Stores pattern
           ↓
           Syncs UI dropdowns with metadata (ONLY if _initial_load=True):
               - Wiring mode dropdown
               - Data-in corner dropdown
               - Layout type
           ↓
           Resets _initial_load = False
           ↓
           Passes pattern to LEDDisplayWidget
               File: ui/widgets/enhanced_led_simulator.py
               Function: LEDDisplayWidget.load_pattern(pattern)
                   ↓
                   Stores frames
                   ↓
                   Calculates LED positions for visual display
                   ↓
                   Triggers update() → draws preview
```

**Current State:**
- Pattern is in DESIGN ORDER (all rows L→R, T→B)
- Metadata stores original file format
- Preview displays pattern correctly
- UI dropdowns show wiring settings

---

## Stage 3: User Modifies Settings (Optional)

### Preview Tab UI Changes
**File:** `ui/widgets/enhanced_led_simulator.py`

```
User changes wiring dropdown:
    ↓
    wiring_combo.currentTextChanged signal
    ↓
    set_wiring_mode(mode)
    ↓
    Updates: self.wiring_mode
    Updates: pattern.metadata.wiring_mode
    ↓
    Triggers display update (visual path overlay changes)

User changes data-in dropdown:
    ↓
    datain_combo.currentTextChanged signal
    ↓
    set_data_in_corner(corner)
    ↓
    Updates: self.data_in_corner
    Updates: pattern.metadata.data_in_corner
    ↓
    Triggers display update
```

**Important:** These changes update the TARGET wiring for hardware, not the preview display order.

---

## Stage 4: Flash Process Initiated

### User Clicks Flash Button
**File:** `ui/tabs/flash_tab.py` → `on_flash()`

```
FlashTab.on_flash()
    ↓
    1. VALIDATE
       - Check pattern exists
       - Check port selected
       - Check chip selected
    ↓
    2. GET SETTINGS
       chip_id = self.chip_combo.currentText()
       port = self.port_combo.currentText()
       gpio = self.gpio_spin.value()
       verify = self.verify_checkbox.isChecked()
    ↓
    3. CREATE WORKING COPY
       File: ui/tabs/flash_tab.py
       
       import copy
       pattern_copy = Pattern(
           name=self.pattern.name,
           metadata=copy.deepcopy(self.pattern.metadata),  # DEEP COPY
           frames=self.pattern.frames  # SHARED (read-only)
       )
       
       Why? To prevent modifying preview's pattern during flash
    ↓
    4. READ TARGET WIRING FROM PREVIEW TAB
       Navigate to MainWindow → PreviewTab → Simulator
       
       wiring_text = simulator.wiring_combo.currentText()
       datain_text = simulator.datain_combo.currentText()
       
       Update pattern_copy metadata:
           pattern_copy.metadata.wiring_mode = wiring_text
           pattern_copy.metadata.data_in_corner = datain_text (converted to LT/LB/RT/RB)
    ↓
    5. READ FLIP SETTINGS
       flip_x = self.flip_x_checkbox.isChecked()
       flip_y = self.flip_y_checkbox.isChecked()
    ↓
    6. CHECK IF CONVERSION NEEDED
       File: ui/tabs/flash_tab.py
       
       already_unwrapped = pattern_copy.metadata.already_unwrapped
       
       If already_unwrapped == True:
           → Pattern is in design order, needs mapping to hardware
           → GO TO STAGE 5A
       
       If already_unwrapped == False:
           → Pattern might be in hardware order
           → Check if format matches target
           → GO TO STAGE 5B
```

---

## Stage 5A: Design Order → Hardware Order Conversion

**File:** `ui/tabs/flash_tab.py`

```
Pattern is in DESIGN ORDER (already_unwrapped = True)
    ↓
    1. GET TARGET SETTINGS
       target_wiring = pattern_copy.metadata.wiring_mode  # From UI
       target_corner = pattern_copy.metadata.data_in_corner  # From UI
    ↓
    2. LOG CONFIGURATION
       Logs: Original file wiring (for reference)
       Logs: Target hardware wiring
       Logs: Matrix dimensions
    ↓
    3. SNAPSHOT BEFORE CONVERSION (for logging/debugging)
       design_snapshot = list(first_frame.pixels)
       Calculate SHA-256 checksum
       Log first 12 pixels
    ↓
    4. LOCK PATTERN
       pattern_copy._flash_locked = True
       → Prevents concurrent modifications
    ↓
    5. CREATE WIRING MAPPER
       File: core/wiring_mapper.py
       
       mapper = WiringMapper(
           width=width,
           height=height,
           wiring_mode=target_wiring,
           data_in_corner=target_corner,
           flip_x=flip_x,
           flip_y=flip_y
       )
    ↓
    6. CONVERT ALL FRAMES
       remapped_frames = []
       
       For each frame in pattern_copy.frames:
           ↓
           design_pixels_snapshot = list(frame.pixels)  # Fresh copy
           ↓
           hardware_pixels = mapper.design_to_hardware(design_pixels_snapshot)
               ↓
               INSIDE WiringMapper.design_to_hardware():
               File: core/wiring_mapper.py
               
               1. Build mapping table:
                  _build_mapping_table() →
                      - Determines start position from data_in_corner
                      - Builds traversal path based on wiring_mode:
                          * Serpentine: rows zigzag L→R, R→L
                          * Row-major: all rows L→R (or R→L if corner is right)
                          * Column-major: traverse columns
                          * Column-serpentine: columns zigzag T→B, B→T
                      - Apply flip transformations if flip_x or flip_y enabled:
                          * flip_x: x = (width-1) - x
                          * flip_y: y = (height-1) - y
                      - Convert (x,y) coordinates to design cell indices
                      - Returns: List[int] mapping hardware_idx → design_idx
               
               2. Preallocate destination buffer:
                  hardware_pixels = [None] * (width * height)
               
               3. Fill buffer by index (PURE FUNCTION):
                  for hardware_idx in range(pixel_count):
                      design_idx = mapping[hardware_idx]
                      hardware_pixels[hardware_idx] = design_pixels[design_idx]
               
               4. Sanity check: assert all pixels filled
               
               5. Return hardware_pixels
           ↓
           Validate pixel count matches
           ↓
           remapped_frames.append(Frame(pixels=hardware_pixels, duration_ms=frame.duration_ms))
    ↓
    7. REPLACE FRAMES
       pattern_copy.frames = remapped_frames
    ↓
    8. UNLOCK PATTERN
       pattern_copy._flash_locked = False
    ↓
    9. LOG AFTER CONVERSION
       hardware_snapshot = list(first_frame.pixels)
       Calculate SHA-256 checksum
       Log first 12 pixels
       → Checksums should be DETERMINISTIC (same input = same output)
    ↓
    10. FIRMWARE VERIFICATION DUMP
        Function: _dump_firmware_verification(pattern_copy, "After re-wrapping")
        → Logs first 2 rows of pixel data
        → For visual debugging
    ↓
    GO TO STAGE 6
```

---

## Stage 5B: Hardware Order → Different Hardware Order

**File:** `ui/tabs/flash_tab.py`

```
Pattern is in HARDWARE ORDER (already_unwrapped = False)
    ↓
    1. GET FILE FORMAT
       file_wiring_mode = pattern_copy.metadata.original_wiring_mode
       file_data_in = pattern_copy.metadata.original_data_in_corner
    ↓
    2. GET TARGET FORMAT
       target_wiring_mode = pattern_copy.metadata.wiring_mode  # From UI
       target_data_in = pattern_copy.metadata.data_in_corner  # From UI
    ↓
    3. CHECK IF CONVERSION NEEDED
       If file_wiring_mode == target_wiring_mode AND file_data_in == target_data_in:
           → No conversion needed
           → GO TO STAGE 6
       Else:
           → Need to convert
           ↓
           4. STEP 1: Hardware → Design Order
              File: core/pattern_converter.py
              Function: hardware_to_design_order(pattern_copy, file_wiring_mode, file_data_in)
              
              → Uses WiringMapper in reverse
              → Converts from file's hardware order to design order
              → Returns pattern with design-ordered frames
           ↓
           5. STEP 2: Design Order → Target Hardware Order
              → Same process as Stage 5A steps 5-10
              → Creates mapper with target settings
              → Converts all frames
           ↓
           GO TO STAGE 6
```

---

## Stage 6: Firmware Generation

### Create Flash Thread
**File:** `ui/tabs/flash_tab.py`

```
self.flash_thread = FlashThread(pattern_copy, chip_id, port, gpio, verify)
Connect signals:
    - flash_thread.progress → on_progress (update UI)
    - flash_thread.finished → on_flash_complete
    - flash_thread.log → log (display in UI)
    - flash_thread.build_result_ready → on_build_result_ready
flash_thread.start()
```

### Flash Thread Execution
**File:** `ui/tabs/flash_tab.py` → `FlashThread.run()`

```
FlashThread.run()
    ↓
    1. GET UPLOADER
       File: uploaders/uploader_registry.py
       Function: get_uploader(chip_id)
       → Returns ESP8266Uploader or ESP32Uploader instance
    ↓
    2. BUILD FIRMWARE
       File: firmware/builder.py
       
       builder = FirmwareBuilder()
       build_result = builder.build(
           pattern=pattern_copy,
           chip_id=chip_id,
           config={'gpio_pin': gpio}
       )
       
       INSIDE FirmwareBuilder.build():
       ↓
       a. Create temporary build directory
          Path: build/{chip_id}/{timestamp}/
       ↓
       b. Generate firmware files
          File: firmware/simple_firmware_generator.py
          Function: generate_simple_firmware(pattern, chip_id, build_dir, gpio_pin)
          
          GENERATES TWO FILES:
          
          ═══════════════════════════════════════════════════
          FILE 1: pattern_data.h
          ═══════════════════════════════════════════════════
          
          Creates C header file with pattern data in PROGMEM
          
          Structure:
          ```c
          // Header info
          const uint32_t pattern_data_size = XXXX;
          
          // Pattern data array
          const uint8_t pattern_data[] PROGMEM = {
              // LED count (2 bytes, little-endian)
              72, 0,
              
              // Frame count (2 bytes, little-endian)
              18, 0,
              
              // For each frame:
              //   Frame delay (2 bytes, little-endian)
              //   For each LED:
              //     R, G, B (3 bytes)
              
              77, 1,  // Frame 0 delay = 333ms
              255, 0, 0,  // LED 0: Red
              0, 255, 0,  // LED 1: Green
              // ... 70 more LEDs
              
              77, 1,  // Frame 1 delay
              // ... Frame 1 pixel data
              
              // ... 16 more frames
          };
          
          // Configuration defines
          #define DATA_PIN 3
          #define LED_TYPE WS2812B
          #define COLOR_ORDER GRB
          #define MAX_LEDS 72
          #define BRIGHTNESS 255
          #define PATTERN_ORDER_DESIGN 0  // 0=hardware order, 1=design order
          
          // Wiring configuration
          #define WIRING_MODE "Column-serpentine"
          #define DATA_IN_CORNER "LB"
          #define MATRIX_WIDTH 12
          #define MATRIX_HEIGHT 6
          #define WIRING_MODE_ID 3  // Numeric ID
          #define DATA_IN_CORNER_ID 1  // Numeric ID
          ```
          
          **CRITICAL:** At this stage, the pixel data is already in the
          FINAL HARDWARE ORDER for the target wiring mode. The firmware
          will play these pixels sequentially (LED 0, 1, 2, ...).
          
          ═══════════════════════════════════════════════════
          FILE 2: {chip_id}.ino
          ═══════════════════════════════════════════════════
          
          Copies template from: firmware/templates/{chip_id}/{chip_id}.ino
          
          The .ino file:
          ```cpp
          #include <FastLED.h>
          #include "pattern_data.h"
          
          CRGB leds[MAX_LEDS];
          
          void setup() {
              FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, MAX_LEDS);
              FastLED.setBrightness(BRIGHTNESS);
              FastLED.clear(true);
          }
          
          void loop() {
              // Read pattern header
              uint16_t num_leds = read_u16_pgm(pattern_data, 0);
              uint16_t num_frames = read_u16_pgm(pattern_data, 2);
              
              uint32_t idx = 4;
              
              // Play all frames
              for (frame = 0; frame < num_frames; frame++) {
                  uint16_t delay_ms = read_u16_pgm(pattern_data, idx);
                  idx += 2;
                  
                  // Read RGB for each LED
                  for (led = 0; led < num_leds; led++) {
                      uint8_t r = read_u8_pgm(pattern_data, idx++);
                      uint8_t g = read_u8_pgm(pattern_data, idx++);
                      uint8_t b = read_u8_pgm(pattern_data, idx++);
                      
                      leds[led] = CRGB(r, g, b);  // ← SEQUENTIAL ORDER
                  }
                  
                  FastLED.show();  // ← Display to physical LEDs
                  delay(delay_ms);
              }
          }
          ```
          
          **KEY POINT:** The firmware plays pixels in sequential order
          (leds[0], leds[1], leds[2], ...). The WiringMapper has already
          reordered the pixels to match the physical LED strip order.
       ↓
       c. Calculate checksums (for determinism verification)
          SHA-256 of pattern_data.h
          SHA-256 of .ino file
          SHA-256 of first frame pixel data
       ↓
       d. Use Arduino CLI or PlatformIO to compile
          Command: arduino-cli compile --fqbn {chip_fqbn} {build_dir}
          
          Produces: {chip_id}.ino.bin (compiled binary)
       ↓
       e. Return build_result object:
          BuildResult(
              success=True,
              firmware_path="{build_dir}/{chip_id}.ino.bin",
              size_bytes=278176,
              build_dir=build_dir
          )
    ↓
    3. UPLOAD FIRMWARE
       File: uploaders/esp8266_uploader.py or esp32_uploader.py
       
       uploader.upload(firmware_path, {'port': port})
       
       Uses esptool.py to upload:
       Command: esptool.py --port {port} --baud 921600 write_flash 0x0 {firmware_path}
       
       Emits progress signals during upload
    ↓
    4. VERIFY (if enabled)
       uploader.verify(firmware_path, {'port': port})
       → Reads back flash and compares checksums
    ↓
    5. EMIT FINISHED SIGNAL
       self.finished.emit(True, "Pattern uploaded successfully!")
```

---

## Stage 7: Completion

### Flash Complete Handler
**File:** `ui/tabs/flash_tab.py` → `on_flash_complete()`

```
FlashTab.on_flash_complete(success, message)
    ↓
    If success:
        Log: "✅ FLASH SUCCESSFUL!"
        Enable flash button
        Update progress bar to 100%
    Else:
        Log: "❌ FLASH FAILED: {message}"
        Enable flash button
        Show error dialog
    ↓
    Emit signal to MainWindow
    ↓
    User can test on hardware
```

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ FILE (12.6 rows up down.bin)                                    │
│ Format: Serpentine (row-based), LT                              │
│ Pixel order: Hardware order (zigzag rows)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PARSER (enhanced_binary_parser.py)                              │
│ - Reads binary data                                             │
│ - Creates Pattern object with frames                            │
│ - Metadata: width=12, height=6, 72 LEDs, 18 frames             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PREVIEW LAYER (preview_tab.py)                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ SERPENTINE DETECTION (pattern_converter.py)                 │ │
│ │ - Detects: File is Serpentine                               │ │
│ │ - Stores: original_wiring_mode = 'Serpentine'               │ │
│ │           original_data_in_corner = 'LT'                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                            ↓                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ UNWRAP TO DESIGN ORDER (hardware_to_design_order)           │ │
│ │ - Input: Hardware order (rows zigzag)                       │ │
│ │   Row 0: 0→1→2...11                                         │ │
│ │   Row 1: 23←22←21...12 (REVERSED)                           │ │
│ │   Row 2: 24→25→26...35                                      │ │
│ │ - Output: Design order (all rows L→R)                       │ │
│ │   Row 0: 0→1→2...11                                         │ │
│ │   Row 1: 12→13→14...23 (FIXED)                              │ │
│ │   Row 2: 24→25→26...35                                      │ │
│ │ - Sets: already_unwrapped = True                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                            ↓                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ DISPLAY (enhanced_led_simulator.py)                         │ │
│ │ - Shows pattern in design order                             │ │
│ │ - All rows display L→R ✓                                    │ │
│ │ - User sees CORRECT pattern                                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                   USER SETS TARGET WIRING
                   (e.g., Column-serpentine LB)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FLASH LAYER (flash_tab.py)                                      │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CREATE WORKING COPY                                          │ │
│ │ - Deep copy metadata (preserves original_wiring_mode)       │ │
│ │ - Share frames (read-only)                                  │ │
│ │ - Update: wiring_mode = 'Column-serpentine' (from UI)      │ │
│ │           data_in_corner = 'LB' (from UI)                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                            ↓                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ WIRING MAPPER (wiring_mapper.py)                            │ │
│ │ - Input: Design order (all rows L→R)                        │ │
│ │ - Target: Column-serpentine LB                              │ │
│ │ - Process:                                                   │ │
│ │   1. Build path for Column-serpentine LB:                   │ │
│ │      Col 0: (0,5)→(0,4)→(0,3)→(0,2)→(0,1)→(0,0) ↑          │ │
│ │      Col 1: (1,0)→(1,1)→(1,2)→(1,3)→(1,4)→(1,5) ↓          │ │
│ │      Col 2: (2,5)→(2,4)→(2,3)→(2,2)→(2,1)→(2,0) ↑          │ │
│ │      ... zigzag through columns                             │ │
│ │   2. Apply flip_x / flip_y if enabled                       │ │
│ │   3. Convert (x,y) to design indices                        │ │
│ │   4. Reorder pixels: hardware_pixels[hw_idx] = design[d_idx]│ │
│ │ - Output: Hardware order for Column-serpentine LB           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FIRMWARE GENERATION (simple_firmware_generator.py)              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ pattern_data.h                                               │ │
│ │ - Writes pixels in hardware order                           │ │
│ │ - LED 0 = pixel at hardware position 0                      │ │
│ │ - LED 1 = pixel at hardware position 1                      │ │
│ │ - ...                                                        │ │
│ │ - LED 71 = pixel at hardware position 71                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ {chip}.ino                                                   │ │
│ │ - Reads pattern_data sequentially                           │ │
│ │ - Plays: leds[0], leds[1], leds[2], ... leds[71]           │ │
│ │ - FastLED outputs to physical strip                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        COMPILE & UPLOAD
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHYSICAL HARDWARE                                                │
│ - Receives data in sequential order                             │
│ - Physical wiring determines actual positions                   │
│ - If wiring matches target: Pattern displays correctly ✓        │
│ - If wiring mismatches: Pattern displays incorrectly ✗          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Files Reference

### Core Files
1. **`core/pattern.py`** - Pattern & PatternMetadata data structures
2. **`core/wiring_mapper.py`** - Design ↔ Hardware order conversion
3. **`core/pattern_converter.py`** - Serpentine detection & unwrapping

### Parser Files
4. **`parsers/parser_registry.py`** - Format detection
5. **`parsers/enhanced_binary_parser.py`** - Binary file parsing

### UI Files
6. **`ui/main_window.py`** - Main application window
7. **`ui/tabs/preview_tab.py`** - Preview layer & pattern loading
8. **`ui/tabs/flash_tab.py`** - Flash orchestration
9. **`ui/widgets/enhanced_led_simulator.py`** - Visual LED display

### Firmware Files
10. **`firmware/builder.py`** - Firmware build orchestration
11. **`firmware/simple_firmware_generator.py`** - Generate .ino & pattern_data.h
12. **`firmware/templates/{chip}/{chip}.ino`** - Arduino sketch templates

### Uploader Files
13. **`uploaders/uploader_registry.py`** - Uploader selection
14. **`uploaders/esp8266_uploader.py`** - ESP8266 flashing
15. **`uploaders/esp32_uploader.py`** - ESP32 flashing

---

## Critical Points

### 1. **Pattern is ALWAYS in design order in preview**
- Preview unwraps serpentine files automatically
- All rows display left-to-right
- Wiring dropdown is for TARGET hardware, not preview

### 2. **Flash creates working copy**
- Prevents modifying preview's pattern
- Deep copies metadata (preserves original_wiring_mode)
- Shares frames (read-only, memory efficient)

### 3. **Wiring mapper is deterministic**
- Same input → same output (verified with SHA-256)
- Pure function (no side effects)
- Snapshots prevent buffer aliasing

### 4. **Firmware plays pixels sequentially**
- leds[0], leds[1], leds[2], ...
- No on-device mapping (for performance)
- All mapping done during firmware generation

### 5. **The "flipping issue" occurs when:**
- Target wiring doesn't match physical hardware
- Solution: Select correct wiring mode in UI
- Or use Flip X/Y checkboxes for orientation correction

---

## Debugging Flow

### If preview is wrong:
- Check: `preview_tab.py` → serpentine detection
- Check: `pattern_converter.py` → unwrapping logic
- File might not be serpentine format

### If hardware doesn't match preview:
- Check: Flash tab wiring settings (read from Preview tab)
- Check: `wiring_mapper.py` → mapping logic
- Check: Physical hardware wiring
- Use Flip X/Y checkboxes if needed

### If firmware not updating:
- Check: Build logs for compilation errors
- Check: Upload logs for port/driver issues
- Try: Erase flash first
- Try: Hold BOOT button during upload

---

This is the complete, end-to-end flow from file open to flash completion.

