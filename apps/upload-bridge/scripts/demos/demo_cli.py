#!/usr/bin/env python3
"""
Upload Bridge - Command-Line Demo
Demonstrates core functionality WITHOUT GUI
Works 100% - No graphics needed!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print(" 🚀 Upload Bridge v3.0 - CLI Demo")
print(" (Core functionality - No GUI required)")
print("="*70)
print()

# Demo 1: Create and manipulate pattern
print("[ DEMO 1: Pattern System ]")
print()

from core.pattern import create_test_pattern

# Create pattern matching your p1.bin specs
print("Creating pattern: 76 LEDs × 400 frames...")
pattern = create_test_pattern(led_count=76, frame_count=400)

print(f"✅ Pattern created!")
print(f"   LEDs: {pattern.led_count}")
print(f"   Frames: {pattern.frame_count}")
print(f"   Duration: {pattern.duration_ms/1000:.1f}s")
print(f"   FPS: {pattern.average_fps:.1f}")
print(f"   Size: {pattern.estimate_memory_bytes()/1024:.1f}KB")
print()

# Modify it
print("Modifying pattern...")
pattern.set_global_fps(60)
print(f"✅ Changed to 60 FPS (was {pattern.average_fps:.1f})")

pattern.apply_brightness(200)
print(f"✅ Applied 80% brightness")
print()

# Save/Load
print("Testing save/load...")
pattern.save_to_file("demo_pattern.ledproj")
print(f"✅ Saved to demo_pattern.ledproj")

from core.pattern import Pattern
loaded = Pattern.load_from_file("demo_pattern.ledproj")
print(f"✅ Loaded: {loaded.frame_count} frames")
print()

# Demo 2: Generate firmware data
print("[ DEMO 2: Firmware Generation ]")
print()

from uploaders.esp_uploader import EspUploader

uploader = EspUploader("esp8266")
print(f"✅ Created ESP8266 uploader")

header = uploader._generate_pattern_header(pattern, gpio_pin=3)
print(f"✅ Generated pattern_data.h ({len(header):,} bytes)")

# Save it
with open("demo_pattern_data.h", "w") as f:
    f.write(header)
print(f"✅ Saved to demo_pattern_data.h")
print()

# Show snippet
print("Header snippet:")
print("-"*70)
lines = header.split('\n')
for line in lines[:20]:
    print(line)
print("...")
print("-"*70)
print()

# Demo 3: Check chip database
print("[ DEMO 3: Chip Database ]")
print()

from uploaders.uploader_registry import UploaderRegistry

registry = UploaderRegistry.instance()
chips = registry.list_supported_chips()

print(f"✅ Loaded chip database: {len(chips)} chips")
print()
print("Supported chips:")

families = registry.get_all_families()
for family in families:
    family_chips = registry.get_chips_by_family(family)
    print(f"\n{family.upper()} Family ({len(family_chips)} chips):")
    for chip in family_chips[:5]:  # First 5
        spec = registry.get_chip_spec(chip)
        flash_kb = spec.get('flash_size', 0) // 1024
        print(f"  ├─ {chip:15s} {flash_kb:4d}KB flash")
    if len(family_chips) > 5:
        print(f"  └─ ... and {len(family_chips)-5} more")

print()

# Demo 4: Validate pattern for chips
print("[ DEMO 4: Multi-Chip Validation ]")
print()

print(f"Your pattern size: {pattern.estimate_memory_bytes()/1024:.1f}KB")
print()

test_chips = ["esp8266", "esp32", "atmega328p", "atmega2560", "stm32f103c8"]

print("Checking which chips can fit this pattern:")
for chip_id in test_chips:
    uploader = registry.get_uploader_for_chip(chip_id)
    if uploader:
        is_valid, warnings = uploader.validate_pattern_for_chip(pattern)
        status = "✅" if is_valid else "⚠️"
        spec = registry.get_chip_spec(chip_id)
        flash_kb = spec.get('flash_size', 0) // 1024
        print(f"{status} {chip_id:15s} ({flash_kb:4d}KB) - {'OK' if is_valid else 'Too large'}")

print()

# Summary
print("="*70)
print(" 🎉 DEMO COMPLETE")
print("="*70)
print()
print("✅ Pattern system: WORKING")
print("✅ Firmware generation: WORKING")  
print("✅ Chip database: WORKING")
print("✅ Multi-chip validation: WORKING")
print()
print("NEXT: Try the GUI version:")
print("  python main.py")
print()
print("Or continue with CLI upload (if you have Arduino CLI + esptool):")
print("  python demo_build_and_flash.py")
print()
print("="*70)
print()

# Cleanup
import os
try:
    os.remove("demo_pattern.ledproj")
    os.remove("demo_pattern_data.h")
except:
    pass

