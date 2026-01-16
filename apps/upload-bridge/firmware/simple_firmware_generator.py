#!/usr/bin/env python3
"""
Simple Firmware Generator - Compatible with old working firmware format
"""

from pathlib import Path
from typing import Dict, Any
from core.pattern import Pattern
import hashlib
import logging

logger = logging.getLogger(__name__)

def generate_simple_firmware(pattern: Pattern, chip_id: str, output_dir: Path, config: Dict[str, Any]) -> Path:
    """Generate simple firmware compatible with old working format"""
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate pattern_data.h in old format
    pattern_data_h = output_dir / "pattern_data.h"
    _generate_pattern_data_h_old_format(pattern, pattern_data_h, config)
    
    # Generate simple .ino file
    ino_file = output_dir / f"{output_dir.name}.ino"
    _generate_simple_ino(ino_file, chip_id, config)
    
    # Calculate checksums for determinism verification
    try:
        with open(pattern_data_h, 'rb') as f:
            h_checksum = hashlib.sha256(f.read()).hexdigest()
        with open(ino_file, 'rb') as f:
            ino_checksum = hashlib.sha256(f.read()).hexdigest()
        
        logger.info(f"🔐 Firmware determinism check:")
        logger.info(f"   pattern_data.h SHA-256: {h_checksum[:16]}...")
        logger.info(f"   {ino_file.name} SHA-256: {ino_checksum[:16]}...")
    except Exception as e:
        logger.warning(f"Could not calculate firmware checksums: {e}")
    
    return ino_file

def _generate_pattern_data_h_old_format(pattern: Pattern, output_path: Path, config: Dict[str, Any]):
    """Generate pattern_data.h in old working format"""
    
    gpio_pin = config.get('gpio_pin', 3)
    led_count = pattern.led_count
    frame_count = pattern.frame_count
    brightness = int(pattern.metadata.brightness * 255)  # Convert 0.0-1.0 to 0-255
    
    # Calculate pixel data checksum BEFORE writing (for determinism verification)
    if frame_count > 0 and len(pattern.frames) > 0:
        first_frame_bytes = bytes([c for pixel in pattern.frames[0].pixels for c in pixel])
        pixel_checksum = hashlib.sha256(first_frame_bytes).hexdigest()
        logger.info(f"🔐 Input pixel data checksum (first frame): {pixel_checksum[:16]}...")
    
    logger.info("="*70)
    logger.info("FIRMWARE GENERATION - pattern_data.h")
    logger.info("="*70)
    logger.info(f"LED count: {led_count}")
    logger.info(f"Frame count: {frame_count}")
    logger.info(f"GPIO pin: {gpio_pin}")
    logger.info(f"Brightness: {brightness} (0-255)")
    logger.info(f"Total data size: {4 + frame_count * (led_count * 3 + 2)} bytes")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"// Auto-generated pattern data - Test Pattern\n")
        f.write(f"// LEDs: {led_count}, Frames: {frame_count}\n")
        f.write(f"// Data pin: {gpio_pin}\n")
        f.write(f"// Total size: {4 + frame_count * (led_count * 3 + 2)} bytes\n")
        f.write("#include <stdint.h>\n")
        f.write("#include <avr/pgmspace.h>\n\n")
        
        # Calculate total data size
        total_size = 4 + frame_count * (led_count * 3 + 2)
        f.write(f"const uint32_t pattern_data_size = {total_size};\n\n")
        
        # Start pattern data array
        f.write("const uint8_t pattern_data[] PROGMEM = {\n")
        
        # Write header: num_leds (2 bytes), num_frames (2 bytes)
        f.write(f"  {led_count & 0xFF:3d}, {(led_count >> 8) & 0xFF:3d},  // num_leds\n")
        f.write(f"  {frame_count & 0xFF:3d}, {(frame_count >> 8) & 0xFF:3d},  // num_frames\n")
        
        # Check if target_fps is set in metadata
        target_fps = getattr(pattern.metadata, 'target_fps', None)
        
        # Write frame data
        for frame_idx, frame in enumerate(pattern.frames):
            # Write frame delay (2 bytes)
            # Calculate delay from target FPS if set, otherwise use original
            if target_fps and target_fps > 0:
                delay_ms = int(1000 / target_fps)  # Uniform delay based on FPS
            else:
                delay_ms = frame.duration_ms  # Original delay
            
            f.write(f"  {delay_ms & 0xFF:3d}, {(delay_ms >> 8) & 0xFF:3d},  // frame {frame_idx} delay\n")
            
            # Write pixel data (3 bytes per LED) in the order already provided.
            # Remapping (wiring/origin/rotation/mirror) should be applied BEFORE calling this
            # generator (e.g., FlashTab remaps a working copy). Avoid double-mapping here.
            export_pixels = frame.pixels
            for led_idx, pixel in enumerate(export_pixels):
                r, g, b = pixel
                f.write(f"  {r:3d}, {g:3d}, {b:3d}")
                if led_idx < led_count - 1 or frame_idx < frame_count - 1:
                    f.write(",")
                f.write(f"  // LED {led_idx}\n")
        
        f.write("};\n")
        
        # Add configuration defines
        f.write(f"\n// Configuration\n")
        f.write(f"#define DATA_PIN {gpio_pin}\n")
        f.write(f"#define LED_TYPE WS2812B\n")
        f.write(f"#define COLOR_ORDER GRB\n")
        f.write(f"#define MAX_LEDS {led_count}\n")
        f.write(f"#define BRIGHTNESS {brightness}\n")
        # Emit whether pattern_data is in design order (0=hardware order, 1=design order)
        # Default remains 0 to preserve current behavior
        f.write(f"#define PATTERN_ORDER_DESIGN 0\n")
        
        # Export advanced brightness settings
        f.write(f"\n// Advanced Brightness Settings\n")
        brightness_curve = getattr(pattern.metadata, 'brightness_curve', 'gamma_corrected')
        f.write(f"#define BRIGHTNESS_CURVE \"{brightness_curve}\"\n")
        
        per_channel = getattr(pattern.metadata, 'per_channel_brightness', False)
        f.write(f"#define PER_CHANNEL_BRIGHTNESS {'1' if per_channel else '0'}\n")
        
        if per_channel:
            red_b = int(getattr(pattern.metadata, 'red_brightness', 1.0) * 255)
            green_b = int(getattr(pattern.metadata, 'green_brightness', 1.0) * 255)
            blue_b = int(getattr(pattern.metadata, 'blue_brightness', 1.0) * 255)
            f.write(f"#define RED_BRIGHTNESS {red_b}\n")
            f.write(f"#define GREEN_BRIGHTNESS {green_b}\n")
            f.write(f"#define BLUE_BRIGHTNESS {blue_b}\n")
        
        # Export speed control settings
        f.write(f"\n// Speed Control Settings\n")
        speed_curve = getattr(pattern.metadata, 'speed_curve', 'linear')
        f.write(f"#define SPEED_CURVE \"{speed_curve}\"\n")
        
        variable_speed = getattr(pattern.metadata, 'variable_speed', False)
        f.write(f"#define VARIABLE_SPEED {'1' if variable_speed else '0'}\n")
        
        # Export interpolation settings
        f.write(f"\n// Interpolation Settings\n")
        interpolation = getattr(pattern.metadata, 'interpolation_enabled', False)
        f.write(f"#define INTERPOLATION_ENABLED {'1' if interpolation else '0'}\n")
        
        if interpolation:
            interp_factor = getattr(pattern.metadata, 'interpolation_factor', 1.0)
            f.write(f"#define INTERPOLATION_FACTOR {interp_factor:.2f}\n")
        
        # Export wiring configuration
        f.write(f"\n// Wiring Configuration\n")
        wiring_mode = getattr(pattern.metadata, 'wiring_mode', 'Row-major')
        data_in = getattr(pattern.metadata, 'data_in_corner', 'LT')
        f.write(f"#define WIRING_MODE \"{wiring_mode}\"\n")
        f.write(f"#define DATA_IN_CORNER \"{data_in}\"\n")
        f.write(f"#define MATRIX_WIDTH {pattern.metadata.width}\n")
        f.write(f"#define MATRIX_HEIGHT {pattern.metadata.height}\n")
        # Also export numeric IDs for fast mapping in firmware
        mode_id = {'Row-major':0, 'Serpentine':1, 'Column-major':2, 'Column-serpentine':3}.get(wiring_mode, 0)
        corner_id = {'LT':0, 'LB':1, 'RT':2, 'RB':3}.get(data_in, 0)
        f.write(f"#define WIRING_MODE_ID {mode_id}\n")
        f.write(f"#define DATA_IN_CORNER_ID {corner_id}\n")
        
    logger.info(f"Wiring mode: {wiring_mode} (ID={mode_id})")
    logger.info(f"Data-In corner: {data_in} (ID={corner_id})")
    logger.info(f"Matrix: {pattern.metadata.width}×{pattern.metadata.height}")
    logger.info(f"Pattern order: {'DESIGN' if 0 else 'HARDWARE'}")
    logger.info("="*70)

def _remap_pixels_for_hardware(pixels, pattern: Pattern):
    """Return a new list of pixels reordered according to pattern.metadata wiring
    and orientation/mirror so firmware output matches Preview."""
    meta = pattern.metadata
    w, h = meta.width, meta.height
    if w * h != len(pixels) or w == 0 or h == 0:
        return pixels
    # Build function to map display coordinate (x,y) to source index in row-major pixels
    def source_index_for_xy(x, y):
        sx, sy = x, y
        # Apply inverse mirror (display->source)
        if getattr(meta, 'mirror_h', False):
            sx = w - 1 - sx
        if getattr(meta, 'mirror_v', False):
            sy = h - 1 - sy
        # Apply inverse rotation
        deg = getattr(meta, 'orientation_deg', 0)
        if deg == 90:
            sx, sy = sy, w - 1 - sx
            sw, sh = h, w
        elif deg == 180:
            sx, sy = w - 1 - sx, h - 1 - sy
            sw, sh = w, h
        elif deg == 270:
            sx, sy = h - 1 - sy, sx
            sw, sh = h, w
        else:
            sw, sh = w, h
        return sy * sw + sx
    # Pre-corner transform (map top-left origin to selected data-in corner)
    def corner_xy(x, y):
        c = getattr(meta, 'data_in_corner', 'LT')
        if c == 'LB':
            return (x, h - 1 - y)
        if c == 'RT':
            return (w - 1 - x, y)
        if c == 'RB':
            return (w - 1 - x, h - 1 - y)
        return (x, y)
    # Iterate hardware order and collect pixels
    wiring = getattr(meta, 'wiring_mode', 'Row-major')
    out = []
    if wiring == 'Row-major':
        for y in range(h):
            for x in range(w):
                cx, cy = corner_xy(x, y)
                idx = source_index_for_xy(cx, cy)
                out.append(pixels[idx])
    elif wiring == 'Serpentine':
        for y in range(h):
            xs = range(w-1, -1, -1) if (y % 2 == 1) else range(w)
            for x in xs:
                cx, cy = corner_xy(x, y)
                idx = source_index_for_xy(cx, cy)
                out.append(pixels[idx])
    elif wiring == 'Column-major':
        for x in range(w):
            for y in range(h):
                cx, cy = corner_xy(x, y)
                idx = source_index_for_xy(cx, cy)
                out.append(pixels[idx])
    elif wiring == 'Column-serpentine':
        for x in range(w):
            ys = range(h-1, -1, -1) if (x % 2 == 1) else range(h)
            for y in ys:
                cx, cy = corner_xy(x, y)
                idx = source_index_for_xy(cx, cy)
                out.append(pixels[idx])
    else:
        # Fallback: row-major
        for y in range(h):
            for x in range(w):
                cx, cy = corner_xy(x, y)
                idx = source_index_for_xy(cx, cy)
                out.append(pixels[idx])
    return out

def _generate_simple_ino(output_path: Path, chip_id: str, config: Dict[str, Any]):
    """Generate simple .ino file based on old working firmware"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('''// esp_matrix_player.ino
// ESP8266 LED Matrix Pattern Player
// Reads pattern data from PROGMEM (flash) and displays on WS2812/NeoPixel LEDs
// 
// Requirements:
// - FastLED library (install via Arduino Library Manager)
// - pattern_data.h (generated by Upload Bridge)

#include <Arduino.h>
#include <FastLED.h>
#include <pgmspace.h> // for PROGMEM access

// Include the pattern data (generated by Upload Bridge)
#include "pattern_data.h"

// ---------- CONFIG ----------
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB

// LED array (allocated in RAM for FastLED)
CRGB leds[MAX_LEDS];

// ---------- HELPER FUNCTIONS ----------

// Read little-endian uint16 from PROGMEM at given index
uint16_t read_u16_pgm(const uint8_t *ptr, uint32_t idx) {
  uint8_t b0 = pgm_read_byte(ptr + idx);
  uint8_t b1 = pgm_read_byte(ptr + idx + 1);
  return (uint16_t)(b0 | (b1 << 8));
}

// Read single byte from PROGMEM
uint8_t read_u8_pgm(const uint8_t *ptr, uint32_t idx) {
  return pgm_read_byte(ptr + idx);
}

// ---------- DESIGN->HARDWARE MAPPING (optional) ----------
// If PATTERN_ORDER_DESIGN==1, pattern_data[] contains pixels in DESIGN order.
// We map (x,y) in design grid to hardware linear index using WIRING_MODE_ID and DATA_IN_CORNER_ID.

// Transform (x,y) from DATA_IN_CORNER to LT reference frame
static inline void corner_to_LT(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t cornerId, uint16_t &ox, uint16_t &oy) {
  switch (cornerId) {
    case 0: /* LT */ ox = x;            oy = y;            break;
    case 1: /* LB */ ox = x;            oy = (h - 1 - y);  break;
    case 2: /* RT */ ox = (w - 1 - x);  oy = y;            break;
    case 3: /* RB */ ox = (w - 1 - x);  oy = (h - 1 - y);  break;
    default:          ox = x;           oy = y;            break;
  }
}

static inline uint16_t mapDesignXYToHardwareIndex(uint16_t x, uint16_t y) {
  const uint16_t w = MATRIX_WIDTH;
  const uint16_t h = MATRIX_HEIGHT;
  uint16_t rx, ry; // referenced to LT corner
  corner_to_LT(x, y, w, h, DATA_IN_CORNER_ID, rx, ry);
  switch (WIRING_MODE_ID) {
    case 0: // Row-major
      return (uint16_t)(ry * w + rx);
    case 1: // Serpentine (row-zigzag)
      if ((ry % 2) == 0) {
        return (uint16_t)(ry * w + rx);
      } else {
        return (uint16_t)(ry * w + (w - 1 - rx));
      }
    case 2: // Column-major
      return (uint16_t)(rx * h + ry);
    case 3: // Column-serpentine (column-zigzag)
      if ((rx % 2) == 0) {
        return (uint16_t)(rx * h + ry);
      } else {
        return (uint16_t)(rx * h + (h - 1 - ry));
      }
    default:
      return (uint16_t)(ry * w + rx);
  }
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\\n\\nESP8266 Matrix Pattern Player - Upload Bridge");
  Serial.println("=============================================");
  
  // Initialize FastLED
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, MAX_LEDS);
  FastLED.setBrightness(BRIGHTNESS);  // Use brightness from pattern
  FastLED.clear(true);
  
  delay(50);
  Serial.println("✓ FastLED initialized");
  Serial.printf("✓ Pattern data size: %u bytes\\n", pattern_data_size);
  Serial.println("✓ Starting playback...\\n");
}

// ---------- MAIN LOOP ----------
void loop() {
  const uint8_t *p = pattern_data; // Pointer to pattern data in PROGMEM
  uint32_t idx = 0;

  // Read pattern header (4 bytes)
  if (pattern_data_size < 4) {
    Serial.println("ERROR: Pattern data too small!");
    delay(5000);
    return;
  }

  uint16_t num_leds = read_u16_pgm(p, idx); 
  idx += 2;
  uint16_t num_frames = read_u16_pgm(p, idx); 
  idx += 2;

  // Validate pattern header
  if (num_leds == 0 || num_leds > MAX_LEDS) {
    Serial.printf("ERROR: Invalid num_leds=%u (MAX_LEDS=%u)\\n", num_leds, MAX_LEDS);
    Serial.println("Check your pattern file or increase MAX_LEDS");
    delay(5000);
    return;
  }

  if (num_frames == 0) {
    Serial.println("ERROR: num_frames=0");
    delay(5000);
    return;
  }

  // Print pattern info (once per loop)
  static bool first_run = true;
  if (first_run) {
    Serial.printf("Pattern: %u LEDs × %u frames\\n", num_leds, num_frames);
    first_run = false;
  }

  // Play all frames
  for (uint32_t frame_num = 0; frame_num < num_frames; ++frame_num) {
    // Check bounds
    if (idx + 2 > pattern_data_size) {
      Serial.printf("ERROR: Unexpected end of data at frame %u\\n", frame_num);
      delay(5000);
      return;
    }

    // Read frame delay (milliseconds)
    uint16_t delay_ms = read_u16_pgm(p, idx); 
    idx += 2;

    // Check if we have enough data for all pixel bytes
    uint32_t pixel_bytes = (uint32_t)num_leds * 3;
    if (idx + pixel_bytes > pattern_data_size) {
      Serial.printf("ERROR: Not enough pixel data at frame %u\\n", frame_num);
      delay(5000);
      return;
    }

    // Read RGB data for each LED
    for (uint16_t i = 0; i < num_leds; ++i) {
      uint8_t r = read_u8_pgm(p, idx++);
      uint8_t g = read_u8_pgm(p, idx++);
      uint8_t b = read_u8_pgm(p, idx++);
      CRGB pix = CRGB(r, g, b);
#if PATTERN_ORDER_DESIGN
      // Map design-linear index to hardware index
      uint16_t x = (uint16_t)(i % MATRIX_WIDTH);
      uint16_t y = (uint16_t)(i / MATRIX_WIDTH);
      uint16_t hw = mapDesignXYToHardwareIndex(x, y);
      if (hw < MAX_LEDS) {
        leds[hw] = pix;
      }
#else
      // pattern_data is already in hardware order
      leds[i] = pix;
#endif
    }

    // Display the frame
    FastLED.show();

    // ✅ FIXED: Accurate delay with watchdog feeding
    // ESP8266 requires yield() calls to avoid watchdog resets
    if (delay_ms > 0) {
        // For delays > 10ms, use efficient chunked delays
        if (delay_ms >= 10) {
            uint32_t chunks = delay_ms / 10;
            uint32_t remainder = delay_ms % 10;
            
            for (uint32_t i = 0; i < chunks; i++) {
                delay(10);
                yield();
            }
            
            if (remainder > 0) {
                delay(remainder);
            }
        } else {
            // For short delays (1-9ms), use direct delay
            delay(delay_ms);
        }
        yield();
    } else {
        yield(); // Always yield even for 0ms delays
    }
  }

  // Pattern complete - loop will restart automatically
  // Small pause between loops
  delay(10);
  yield();
}
''')
