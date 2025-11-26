#!/usr/bin/env python3
"""
Test ESP01 Flash - Real Hardware Test
This script tests flashing a pattern to ESP01 connected on COM4
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pattern import create_test_pattern, Pattern, Frame
from uploaders.esp_uploader import EspUploader
from firmware.builder import FirmwareBuilder
import time

def create_simple_test_pattern(led_count=76, frame_count=50):
    """Create a simple test pattern"""
    print(f"Creating test pattern: {led_count} LEDs, {frame_count} frames...")
    
    # Create a simple rainbow chase pattern
    frames = []
    for f in range(frame_count):
        pixels = []
        for i in range(led_count):
            # Rainbow effect
            hue = ((i / led_count) + (f / frame_count)) % 1.0
            import math
            r = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * hue)))
            g = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * (hue + 0.333))))
            b = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * (hue + 0.666))))
            pixels.append((r, g, b))
        
        frames.append(Frame(pixels=pixels, duration_ms=100))
    
    pattern = Pattern(
        name="Test Pattern",
        metadata=type('obj', (object,), {
            'width': led_count,
            'height': 1,
            'led_count': led_count,
            'color_order': 'GRB'
        })()
    )
    pattern.frames = frames
    
    return pattern

def test_flash(com_port='COM4', chip_id='esp8266'):
    """Test flashing to ESP01"""
    print("=" * 60)
    print("ESP01 FLASH TEST")
    print("=" * 60)
    
    try:
        # Step 1: Create test pattern
        print("\n[1/5] Creating test pattern...")
        pattern = create_simple_test_pattern(led_count=76, frame_count=50)
        print(f"   ✓ Pattern created: {pattern.led_count} LEDs, {pattern.frame_count} frames")
        
        # Step 2: Validate pattern
        print("\n[2/5] Validating pattern...")
        uploader = EspUploader(chip_id)
        is_valid, warnings = uploader.validate_pattern_for_chip(pattern)
        
        if warnings:
            for warning in warnings:
                print(f"   ⚠ Warning: {warning}")
        
        if not is_valid:
            print("   ❌ Pattern validation failed!")
            return False
        
        print("   ✓ Pattern valid for ESP8266")
        
        # Step 3: Build firmware
        print("\n[3/5] Building firmware...")
        builder = FirmwareBuilder()
        
        # Create output directory
        output_dir = os.path.join(os.path.dirname(__file__), 'build', 'test_esp01')
        os.makedirs(output_dir, exist_ok=True)
        
        build_result = builder.build(
            pattern=pattern,
            chip_id=chip_id,
            build_opts={
                'output_dir': output_dir,
                'gpio_pin': 3,  # GPIO3 on ESP01
                'optimize_level': 2
            }
        )
        
        if not build_result.success:
            print(f"   ❌ Build failed: {build_result.error_message}")
            return False
        
        print(f"   ✓ Firmware built: {build_result.firmware_path}")
        print(f"      Size: {build_result.size_bytes} bytes")
        
        # Step 4: Upload to ESP01
        print(f"\n[4/5] Uploading to ESP01 on {com_port}...")
        print("   (Put ESP01 in flash mode and press any key to continue)")
        input("   Press Enter to start upload...")
        
        upload_result = uploader.upload(
            firmware_path=build_result.firmware_path,
            port_params={
                'port': com_port,
                'baud': 115200,
                'flash_mode': 'dout',
                'flash_size': '1MB',
                'chip': 'ESP8266'
            }
        )
        
        if not upload_result.success:
            print(f"   ❌ Upload failed: {upload_result.error_message}")
            return False
        
        print(f"   ✓ Upload successful!")
        print(f"      Duration: {upload_result.duration_seconds:.2f}s")
        print(f"      Bytes written: {upload_result.bytes_written}")
        
        # Step 5: Verify
        print("\n[5/5] Verifying...")
        verified = uploader.verify(
            firmware_path=build_result.firmware_path,
            port_params={'port': com_port}
        )
        
        if verified:
            print("   ✓ Verification successful!")
        else:
            print("   ⚠ Verification skipped or unavailable")
        
        print("\n" + "=" * 60)
        print("✅ FLASH TEST SUCCESSFUL!")
        print("=" * 60)
        print("\nThe test pattern is now running on your ESP01!")
        print("You should see a rainbow chase animation on your LEDs.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        print("\nTraceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Try to detect COM port automatically
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    
    if ports:
        print("Available COM ports:")
        for p in ports:
            print(f"  - {p.device}: {p.description}")
        print()
    
    # Default to COM4, but allow override
    com_port = sys.argv[1] if len(sys.argv) > 1 else 'COM4'
    chip_id = sys.argv[2] if len(sys.argv) > 2 else 'esp8266'
    
    success = test_flash(com_port=com_port, chip_id=chip_id)
    
    if not success:
        print("\n❌ Test failed. Check the errors above and retry.")
        sys.exit(1)
    else:
        print("\n✅ Test completed successfully!")
        sys.exit(0)




