#!/usr/bin/env python3
"""
Test Firmware Generation - Debug compilation errors
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.pattern import create_test_pattern
from firmware.builder import FirmwareBuilder

def test_firmware_generation():
    """Test firmware generation to debug compilation errors"""
    print("🧪 Testing Firmware Generation")
    print("=" * 50)
    
    # Create a simple test pattern
    pattern = create_test_pattern(8, 5)
    print(f"Created test pattern: {pattern.led_count} LEDs, {pattern.frame_count} frames")
    
    # Create firmware builder
    builder = FirmwareBuilder()
    
    # Test ESP8266 firmware generation
    print("\n📱 Testing ESP8266 firmware generation:")
    result = builder.build_universal_firmware(pattern, "esp8266", {"gpio_pin": 2})
    
    if result.success:
        print(f"✅ Success: {result.firmware_path}")
        print(f"   Size: {result.size_bytes} bytes")
        
        # Check the generated files
        firmware_path = Path(result.firmware_path)
        if firmware_path.exists():
            print(f"\n📄 Generated files in {firmware_path.parent}:")
            for file in firmware_path.parent.iterdir():
                print(f"   - {file.name} ({file.stat().st_size} bytes)")
                
            # Check for duplicate definitions
            print(f"\n🔍 Checking for duplicate definitions in {firmware_path.name}:")
            with open(firmware_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Count occurrences
            setup_count = content.count('void setup()')
            loop_count = content.count('void loop()')
            crgb_count = content.count('CRGB leds[')
            
            print(f"   - void setup(): {setup_count} occurrences")
            print(f"   - void loop(): {loop_count} occurrences")
            print(f"   - CRGB leds[: {crgb_count} occurrences")
            
            if setup_count > 1 or loop_count > 1 or crgb_count > 1:
                print("   ❌ DUPLICATE DEFINITIONS FOUND!")
                
                # Find line numbers
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'void setup()' in line:
                        print(f"     Line {i}: {line.strip()}")
                    elif 'void loop()' in line:
                        print(f"     Line {i}: {line.strip()}")
                    elif 'CRGB leds[' in line:
                        print(f"     Line {i}: {line.strip()}")
            else:
                print("   ✅ No duplicate definitions found")
                
        else:
            print(f"❌ Firmware file not found: {firmware_path}")
    else:
        print(f"❌ Failed: {result.error_message}")

if __name__ == "__main__":
    test_firmware_generation()













