#!/usr/bin/env python3
"""
Quick Test - Fast pattern loading and firmware building
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def quick_test():
    """Quick test of pattern loading and firmware building"""
    print("🚀 Quick Test - ESP8266 on COM4")
    print("=" * 40)
    
    try:
        # Import required modules
        from core.pattern import Pattern
        from parsers.parser_registry import ParserRegistry
        from firmware.builder import FirmwareBuilder
        
        print("✅ Modules imported successfully")
        
        # Find the last .leds file
        sample_dir = Path("C:/Users/asith/Documents/LEDMatrixStudioSource/SamplePatterns")
        leds_files = list(sample_dir.glob("*.leds"))
        
        if not leds_files:
            print("❌ No .leds files found")
            return False
        
        last_file = sorted(leds_files)[-1]
        print(f"📁 Loading: {last_file.name}")
        
        # Load pattern
        registry = ParserRegistry()
        pattern = registry.parse_file(str(last_file))
        
        if pattern:
            print(f"✅ Pattern loaded: {pattern.led_count} LEDs, {pattern.frame_count} frames")
            
            # Build firmware
            builder = FirmwareBuilder()
            result = builder.build_universal_firmware(pattern, "esp8266", {"gpio_pin": 2})
            
            if result.success:
                print(f"✅ Firmware built: {result.firmware_path}")
                print(f"✅ Size: {result.size_bytes:,} bytes")
                print(f"\n🎯 Ready for upload to ESP8266 on COM4!")
                print(f"   Use the Upload Bridge app to flash: {result.firmware_path}")
                return True
            else:
                print(f"❌ Firmware build failed: {result.error_message}")
                return False
        else:
            print("❌ Pattern loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    quick_test()













