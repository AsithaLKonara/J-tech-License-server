#!/usr/bin/env python3
"""
Clean Build Test - Generate clean firmware without redefinition errors
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def clean_build_test():
    """Generate a clean firmware build"""
    print("🧹 Clean Build Test")
    print("=" * 30)
    
    try:
        from core.pattern import create_test_pattern
        from firmware.builder import FirmwareBuilder
        
        # Create a simple test pattern
        pattern = create_test_pattern(8, 5)
        print(f"✅ Created test pattern: {pattern.led_count} LEDs, {pattern.frame_count} frames")
        
        # Build firmware
        builder = FirmwareBuilder()
        result = builder.build_universal_firmware(pattern, "esp8266", {"gpio_pin": 2})
        
        if result.success:
            print(f"✅ Firmware built: {result.firmware_path}")
            print(f"✅ Size: {result.size_bytes:,} bytes")
            
            # Check for duplicate definitions
            firmware_path = Path(result.firmware_path)
            if firmware_path.exists():
                with open(firmware_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                setup_count = content.count('void setup()')
                loop_count = content.count('void loop()')
                crgb_count = content.count('CRGB leds[')
                
                print(f"\n🔍 Checking for duplicates:")
                print(f"   void setup(): {setup_count}")
                print(f"   void loop(): {loop_count}")
                print(f"   CRGB leds[: {crgb_count}")
                
                if setup_count == 1 and loop_count == 1 and crgb_count == 1:
                    print("✅ No duplicate definitions found!")
                    print(f"\n🎯 Ready for upload to ESP8266 on COM4!")
                    return True
                else:
                    print("❌ Duplicate definitions found!")
                    return False
            else:
                print("❌ Firmware file not found")
                return False
        else:
            print(f"❌ Build failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    clean_build_test()













