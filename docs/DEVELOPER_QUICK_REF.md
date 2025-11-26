# 🚀 UPLOAD BRIDGE - DEVELOPER QUICK REFERENCE

## Table of Contents
- [Common Tasks](#common-tasks)
- [Code Examples](#code-examples)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)
- [Testing Guide](#testing-guide)

---

## Common Tasks

### Task 1: Load and Preview a Pattern

```python
from parsers.parser_registry import ParserRegistry

# Load pattern
registry = ParserRegistry.instance()
pattern = registry.parse_pattern_file(
    'patterns/p1.bin',
    led_count=76,
    frame_count=400
)

# Print pattern info
print(f"Loaded: {pattern.led_count} LEDs, {pattern.frame_count} frames")
print(f"Duration: {pattern.duration_ms}ms")
print(f"Average FPS: {pattern.average_fps:.1f}")
print(f"Memory needed: {pattern.estimate_memory_bytes() / 1024:.1f}KB")
```

---

### Task 2: Build Firmware for ESP8266

```python
from uploaders.uploader_registry import UploaderRegistry
from firmware.builder import FirmwareBuilder

# Load pattern (from above)

# Build firmware
builder = FirmwareBuilder()
result = builder.build(
    pattern=pattern,
    chip='esp8266',
    config={
        'gpio_pin': 3,      # GPIO3 for data
        'brightness': 100,  # 0-100
        'fps': 30
    }
)

if result.success:
    print(f"Firmware built: {result.firmware_path}")
    print(f"Binary size: {result.binary_size} bytes")
else:
    print(f"Build failed: {result.error_message}")
```

---

### Task 3: Flash Pattern to Device

```python
from uploaders.uploader_registry import UploaderRegistry

# Get the appropriate uploader
registry = UploaderRegistry.instance()
uploader = registry.get_uploader('esp8266')

# Upload
result = uploader.upload(
    firmware_path='build/firmware.bin',
    upload_config={
        'port': 'COM3',          # Serial port
        'baud_rate': 115200,     # Upload speed
        'chip': 'esp8266'
    }
)

if result.success:
    print("✅ Upload successful!")
else:
    print(f"❌ Upload failed: {result.error_message}")
```

---

### Task 4: Apply Brightness Curve to Pattern

```python
from core.pattern import Pattern

# Pattern loaded (from Task 1)

# Apply brightness curve
pattern.metadata.brightness = 0.8  # 80% brightness
pattern.metadata.brightness_curve = 'gamma_corrected'
pattern.metadata.per_channel_brightness = True
pattern.metadata.red_brightness = 1.0
pattern.metadata.green_brightness = 0.9
pattern.metadata.blue_brightness = 0.8

# Save pattern
pattern.save_project('patterns/my_pattern.ledproj')
```

---

### Task 5: Change Animation Speed

```python
from core.pattern import Pattern

# Pattern loaded (from Task 1)

# Apply speed multiplier
pattern.metadata.fps = pattern.metadata.fps * 0.5  # Half speed
# Or directly:
pattern.metadata.fps = 15.0  # 15 FPS

# Apply easing function
pattern.metadata.speed_curve = 'ease-in-out'

# With variable speed (keyframes)
pattern.metadata.variable_speed = True
pattern.metadata.speed_keyframes = [
    {'frame': 0, 'speed': 1.0},      # Normal speed
    {'frame': 200, 'speed': 0.5},    # Half speed
    {'frame': 400, 'speed': 1.0}     # Back to normal
]
```

---

### Task 6: Detect LED Matrix Layout

```python
from core.matrix_detector import MatrixDetector

# Pattern loaded (from Task 1)

# Auto-detect layout
detector = MatrixDetector()
layout = detector.detect_layout(pattern)

print(f"Detected layout: {layout.layout_type}")  # 'strip', 'matrix', 'ring'
print(f"Width: {layout.width}, Height: {layout.height}")
print(f"Confidence: {layout.confidence}%")

# Update pattern metadata if confident
if layout.confidence > 70:
    pattern.metadata.width = layout.width
    pattern.metadata.height = layout.height
```

---

### Task 7: Batch Flash Multiple Patterns

```python
from core.batch_flasher import BatchFlasher

# Create flasher
flasher = BatchFlasher()

# Configure batch job
flasher.add_pattern(
    pattern_file='patterns/p1.bin',
    led_count=76,
    frame_count=400,
    device='esp8266',
    port='COM3',
    gpio_pin=3
)

flasher.add_pattern(
    pattern_file='patterns/p2.bin',
    led_count=100,
    frame_count=600,
    device='esp8266',
    port='COM3',
    gpio_pin=3
)

# Execute batch
results = flasher.flash_all()

for result in results:
    status = "✅" if result.success else "❌"
    print(f"{status} {result.pattern_file}: {result.message}")
```

---

## Code Examples

### Example 1: Parse Binary Pattern File

```python
from parsers.raw_rgb_parser import RawRGBParser
import struct

# Read file
with open('pattern.bin', 'rb') as f:
    data = f.read()

# Parse as raw RGB
parser = RawRGBParser()
pattern = parser.parse('pattern.bin', led_count=76, frame_count=400)

# Access frame data
frame = pattern.frames[0]
print(f"First LED of first frame: RGB{frame.pixels[0]}")

# Get all pixels as bytes
frame_bytes = frame.to_bytes()
print(f"Frame size: {len(frame_bytes)} bytes")
```

---

### Example 2: Create Pattern Programmatically

```python
from core.pattern import Pattern, PatternMetadata, Frame

# Create metadata
metadata = PatternMetadata(
    width=10,
    height=1,
    color_order='RGB',
    brightness=1.0,
    brightness_curve='gamma_corrected'
)

# Create pattern
pattern = Pattern(name='Rainbow', metadata=metadata)

# Add frames
for frame_num in range(100):
    pixels = []
    for led_num in range(10):
        # Create rainbow effect
        hue = (frame_num + led_num * 2.55) % 360
        r = int((1 + __import__('math').cos(hue * 3.14159 / 180)) * 127)
        g = int((1 + __import__('math').cos((hue + 120) * 3.14159 / 180)) * 127)
        b = int((1 + __import__('math').cos((hue + 240) * 3.14159 / 180)) * 127)
        pixels.append((r, g, b))
    
    frame = Frame(pixels=pixels, duration_ms=50)
    pattern.frames.append(frame)

# Save
pattern.save_project('rainbow.ledproj')
```

---

### Example 3: Custom Uploader Registration

```python
from uploaders.base import BaseUploader
from uploaders.uploader_registry import UploaderRegistry
from typing import Dict

class CustomChipUploader(BaseUploader):
    def build(self, pattern, config) -> Dict:
        print(f"Building for custom chip: {pattern.name}")
        # Your build logic here
        return {
            'success': True,
            'firmware_path': '/path/to/firmware.bin',
            'binary_size': 12345
        }
    
    def upload(self, firmware_path, upload_config) -> Dict:
        print(f"Uploading to {upload_config['port']}")
        # Your upload logic here
        return {'success': True, 'message': 'Uploaded successfully'}
    
    def get_specs(self) -> Dict:
        return {
            'name': 'CustomChip',
            'family': 'Custom',
            'flash_size': 65536,
            'ram_size': 8192,
            'max_leds': 500
        }

# Register
registry = UploaderRegistry.instance()
registry.register_uploader('custom_chip', CustomChipUploader())

# Use
uploader = registry.get_uploader('custom_chip')
result = uploader.build(pattern, {'gpio_pin': 3})
```

---

### Example 4: File Format Detection

```python
from parsers.parser_registry import ParserRegistry

# Get registry
registry = ParserRegistry.instance()

# Read file
with open('unknown_format.dat', 'rb') as f:
    content = f.read()

# Detect format
detected_format = registry.detect_format('unknown_format.dat', content)
print(f"Detected: {detected_format['format']}")
print(f"Confidence: {detected_format['confidence']}%")
print(f"Recommended parser: {detected_format['parser']}")
```

---

### Example 5: Pattern Transformation Pipeline

```python
from core.pattern import Pattern
from parsers.parser_registry import ParserRegistry

# Load
pattern = ParserRegistry.instance().parse_pattern_file('input.bin', 100, 200)

# Transform 1: Adjust brightness
pattern.metadata.brightness = 0.8
pattern.metadata.brightness_curve = 'gamma_corrected'

# Transform 2: Slow down
pattern.metadata.fps = pattern.metadata.fps * 0.7

# Transform 3: Change color order
pattern.metadata.color_order = 'GRB'  # For WS2812 LEDs

# Transform 4: Create copy with modifications
pattern_copy = pattern.copy()
pattern_copy.metadata.brightness = 0.5
pattern_copy.name = 'Dim Version'

# Save both
pattern.save_project('original.ledproj')
pattern_copy.save_project('dim_version.ledproj')
```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'PySide6'"

**Solution**:
```bash
# Install missing dependencies
pip install -r requirements.txt

# Or install PySide6 directly
pip install PySide6
```

---

### Problem: "Arduino CLI not found"

**Solution**:
```bash
# Windows: Download and add to PATH
# https://arduino.github.io/arduino-cli/

# macOS:
brew install arduino-cli

# Linux:
sudo apt install arduino-cli

# Then install ESP cores:
arduino-cli core install esp8266:esp8266
arduino-cli core install esp32:esp32
```

---

### Problem: "esptool not found"

**Solution**:
```bash
pip install esptool

# Verify installation
esptool.py version
```

---

### Problem: "Device not found on COM port"

**Solutions**:
1. Check physical connection
2. Install CH340 drivers (for NodeMCU): https://ch340.com/
3. Install FTDI drivers (for other boards)
4. Try different USB cable (data cable, not power-only)
5. Check port in Device Manager (Windows) or `/dev/tty*` (Linux/Mac)

---

### Problem: "Upload timeout"

**Solutions**:
1. Hold GPIO0 LOW before uploading (for ESP8266)
2. Reduce baud rate: `115200` → `74880`
3. Add delay in upload: `--before=default_reset --after=hard_reset`
4. Check power supply (may be insufficient current)

---

### Problem: "Pattern file not recognized"

**Solutions**:
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Try specifying format explicitly
from parsers.raw_rgb_parser import RawRGBParser
parser = RawRGBParser()
pattern = parser.parse('file.bin', led_count=76, frame_count=400)

# Check file format manually
with open('file.bin', 'rb') as f:
    header = f.read(4)
    print(f"First 4 bytes: {header.hex()}")
    print(f"File size: {os.path.getsize('file.bin')} bytes")
```

---

### Problem: "Memory constraint on ESP8266"

**Solutions**:
```python
# Check pattern memory usage
print(pattern.estimate_memory_bytes())

# Reduce pattern to fit
# ESP8266 has ~1MB flash, ~80KB useful for pattern storage

# Option 1: Fewer LEDs
pattern.metadata.width = 50  # Instead of 100

# Option 2: Fewer frames
pattern.frames = pattern.frames[:200]  # First 200 frames only

# Option 3: Lower resolution
pattern.metadata.fps = pattern.metadata.fps / 2

# Option 4: Use external storage (SPIFFS)
# Upload pattern to SPIFFS instead of PROGMEM
```

---

## Performance Tips

### Tip 1: Optimize LED Count

```python
# For ESP8266, maximum ~150 LEDs (WS2812)
# For ESP32, maximum ~400 LEDs
# For STM32, maximum ~200 LEDs

# Check compatibility before building
spec = registry.get_chip_spec('esp8266')
if pattern.led_count > spec['max_leds']:
    print(f"Warning: Pattern exceeds max LEDs")
    pattern.metadata.width = spec['max_leds']
```

---

### Tip 2: Cache Pattern Data

```python
# Patterns are heavy to load - cache them
from functools import lru_cache

@lru_cache(maxsize=5)
def load_cached_pattern(filename):
    return ParserRegistry.instance().parse_pattern_file(
        filename, None, None
    )

# Multiple calls are fast
pattern1 = load_cached_pattern('pattern.bin')
pattern2 = load_cached_pattern('pattern.bin')  # Cached!
```

---

### Tip 3: Batch Operations

```python
# Instead of flashing one at a time
for pattern_file in pattern_files:
    flash_single(pattern_file)  # Slow!

# Use batch flasher
flasher = BatchFlasher()
for pattern_file in pattern_files:
    flasher.add_pattern(pattern_file, ...)
results = flasher.flash_all()  # Optimized!
```

---

### Tip 4: Reduce Frame Interpolation Overhead

```python
# Interpolation looks smooth but uses CPU
pattern.metadata.interpolation_enabled = True
pattern.metadata.interpolation_factor = 2.0

# For fast playback, disable:
pattern.metadata.interpolation_enabled = False

# Use brightness curves instead (GPU accelerated)
pattern.metadata.brightness_curve = 'gamma_corrected'
```

---

### Tip 5: Optimize Brightness Calculations

```python
# Pre-calculate brightness LUT for maximum performance
def create_brightness_lut(curve_type, points=256):
    lut = []
    for i in range(points):
        value = i / points
        if curve_type == 'gamma':
            # Gamma correction: value^2.2
            adjusted = value ** 2.2
        elif curve_type == 'linear':
            adjusted = value
        lut.append(int(adjusted * 255))
    return lut

# Use LUT
brightness_lut = create_brightness_lut('gamma')
adjusted_value = brightness_lut[original_value]
```

---

## Testing Guide

### Test 1: Unit Test Pattern Model

```python
from core.pattern import Pattern, PatternMetadata, Frame

def test_pattern_creation():
    # Create pattern
    metadata = PatternMetadata(width=10, height=1)
    pattern = Pattern(name='Test', metadata=metadata)
    
    # Add frame
    pixels = [(255, 0, 0)] * 10  # All red
    frame = Frame(pixels=pixels, duration_ms=50)
    pattern.frames.append(frame)
    
    # Assertions
    assert pattern.led_count == 10
    assert pattern.frame_count == 1
    assert pattern.average_fps == 20.0
    assert pattern.duration_ms == 50
    
    print("✅ Pattern creation test passed")

# Run test
test_pattern_creation()
```

---

### Test 2: Parser Verification

```python
from parsers.parser_registry import ParserRegistry

def test_parser():
    registry = ParserRegistry.instance()
    
    # Test with known file
    pattern = registry.parse_pattern_file(
        'patterns/test_pattern.bin',
        led_count=76,
        frame_count=400
    )
    
    # Verify results
    assert pattern.led_count == 76
    assert pattern.frame_count == 400
    assert pattern.frames[0].pixels is not None
    assert len(pattern.frames[0].pixels) == 76
    
    print("✅ Parser test passed")

# Run test
test_parser()
```

---

### Test 3: Upload Simulation

```python
from uploaders.uploader_registry import UploaderRegistry

def test_uploader_build():
    registry = UploaderRegistry.instance()
    uploader = registry.get_uploader('esp8266')
    
    # Load pattern
    pattern = ParserRegistry.instance().parse_pattern_file(
        'patterns/test_pattern.bin', 76, 400
    )
    
    # Build firmware
    result = uploader.build(pattern, {'gpio_pin': 3})
    
    # Verify
    assert result['success'] == True
    assert result['firmware_path'] is not None
    assert result['binary_size'] > 0
    
    print("✅ Uploader build test passed")

# Run test
test_uploader_build()
```

---

### Test 4: File Format Detection

```python
from parsers.parser_registry import ParserRegistry

def test_format_detection():
    registry = ParserRegistry.instance()
    
    # Test different formats
    test_files = [
        'patterns/standard.bin',    # Should detect standard format
        'patterns/raw_rgb.bin',     # Should detect raw RGB
        'patterns/pattern.hex',     # Should detect Intel HEX
    ]
    
    for test_file in test_files:
        detected = registry.detect_format(test_file)
        print(f"{test_file}: {detected['format']} (confidence: {detected['confidence']}%)")
        assert detected['confidence'] > 50, f"Low confidence for {test_file}"
    
    print("✅ Format detection test passed")

# Run test
test_format_detection()
```

---

## Quick Commands

```bash
# Launch GUI
python main.py

# Launch CLI
python flash_cli.py

# Run tests
pytest

# Format code
black .

# Check code quality
flake8 .

# Generate build
python create_final_package.py

# Install dependencies
pip install -r requirements.txt

# Install build tools
python install_tools.py
```

---

## Useful File Locations

| What | Where |
|------|-------|
| Pattern examples | `patterns/` |
| Source code | `core/`, `parsers/`, `uploaders/`, `ui/` |
| Firmware templates | `firmware/templates/` |
| Configuration | `config/chip_database.yaml` |
| Build output | `build/` |
| Tests | `test_*.py` |
| Documentation | `*.md` |

---

## Key Classes & Methods

### ParserRegistry
```python
parse_pattern_file(path, led_count, frame_count)  # Main entry
detect_format(path, content)                       # Format detection
get_parser(name)                                   # Get specific parser
register_parser(name, parser)                      # Register custom
```

### UploaderRegistry
```python
get_uploader(chip_name)                            # Get uploader
list_supported_chips()                             # List all
get_chip_spec(chip_name)                           # Get specs
register_uploader(name, uploader)                  # Register custom
```

### Pattern
```python
save_project(path)                                 # Save as .ledproj
load_project(path)                                 # Load from .ledproj
estimate_memory_bytes()                            # Memory estimate
copy()                                             # Deep copy
```

### FirmwareBuilder
```python
build(pattern, chip, config)                       # Build firmware
```

---

This guide should help you quickly find what you need! Happy coding! 🚀
