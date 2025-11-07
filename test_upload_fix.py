#!/usr/bin/env python3
"""
Test script to verify the upload fix
"""

import sys
from pathlib import Path
from core.pattern import create_test_pattern
from uploaders.esp_uploader import EspUploader
from uploaders.base import UploadError

def test_upload_fix():
    """Test that the upload process no longer fails with WinError 2"""
    print("🧪 Testing Upload Fix")
    print("=" * 40)

    # Create test pattern
    pattern = create_test_pattern(led_count=8, frame_count=5)
    print(f"✅ Created test pattern: {pattern.led_count} LEDs, {pattern.frame_count} frames")

    # Create ESP uploader
    uploader = EspUploader("esp8266")

    # Test build (this should work)
    try:
        result = uploader.build_firmware(
            pattern=pattern,
            build_opts={
                "gpio_pin": 2,
                "output_dir": "build/test_upload_fix"
            }
        )

        print(f"✅ Build successful: {result.firmware_path}")
        print(f"   Size: {result.size_bytes} bytes")

        # Test upload (this will fail due to no device, but shouldn't be WinError 2)
        try:
            upload_result = uploader.upload(
                firmware_path=result.firmware_path,
                port_params={
                    "port": "COM4",
                    "baud": 115200
                }
            )
            print("✅ Upload successful!")
        except UploadError as e:
            if "WinError 2" in str(e):
                print(f"❌ Still getting WinError 2: {e}")
                return False
            else:
                print(f"✅ Upload failed as expected (no device): {e}")
                print("   This is normal - the important thing is it's not WinError 2!")

    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False

    print("\n🎉 Upload fix verified! WinError 2 is resolved.")
    return True

if __name__ == "__main__":
    success = test_upload_fix()
    sys.exit(0 if success else 1)













