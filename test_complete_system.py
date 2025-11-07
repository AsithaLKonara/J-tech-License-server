#!/usr/bin/env python3
"""
Complete System Test - ESP8266 on COM4
Tests the entire pipeline from pattern loading to firmware upload
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.pattern import Pattern
from parsers.parser_registry import ParserRegistry
from firmware.builder import FirmwareBuilder
from uploaders.esp_uploader import EspUploader

def test_pattern_loading():
    """Test pattern loading from SamplePatterns folder"""
    print("🧪 Testing Pattern Loading")
    print("=" * 40)
    
    sample_patterns_dir = Path("C:/Users/asith/Documents/LEDMatrixStudioSource/SamplePatterns")
    
    # Find all .leds files
    leds_files = list(sample_patterns_dir.glob("*.leds"))
    
    if not leds_files:
        print("❌ No .leds files found in SamplePatterns folder")
        return None
    
    # Get the last file (alphabetically)
    last_file = sorted(leds_files)[-1]
    print(f"📁 Loading pattern: {last_file.name}")
    print(f"   Size: {last_file.stat().st_size:,} bytes")
    
    try:
        # Use parser registry to load the pattern
        registry = ParserRegistry()
        is_valid, message, info = registry.validate_file(str(last_file))
        
        if not is_valid:
            print(f"❌ Invalid pattern file: {message}")
            return None
        
        print(f"✅ Pattern validation successful")
        print(f"   LEDs: {info.get('leds', 'Unknown')}")
        print(f"   Frames: {info.get('frames', 'Unknown')}")
        
        # Load the pattern
        pattern = registry.parse_file(str(last_file))
        if pattern:
            print(f"✅ Pattern loaded successfully: {pattern.name}")
            print(f"   LEDs: {pattern.led_count}")
            print(f"   Frames: {pattern.frame_count}")
            print(f"   FPS: {pattern.metadata.fps}")
            return pattern
        else:
            print("❌ Failed to parse pattern file")
            return None
            
    except Exception as e:
        print(f"❌ Error loading pattern: {e}")
        return None

def test_firmware_building(pattern):
    """Test firmware building for ESP8266"""
    print(f"\n🔨 Testing Firmware Building")
    print("=" * 40)
    
    # Create firmware builder
    builder = FirmwareBuilder()
    
    # Build firmware for ESP8266
    print("📱 Building firmware for ESP8266...")
    result = builder.build_universal_firmware(
        pattern, 
        "esp8266", 
        {"gpio_pin": 2}
    )
    
    if result.success:
        print(f"✅ Firmware built successfully")
        print(f"   File: {result.firmware_path}")
        print(f"   Size: {result.size_bytes:,} bytes")
        print(f"   Type: {result.binary_type}")
        
        # Check if firmware file exists and is readable
        firmware_path = Path(result.firmware_path)
        if firmware_path.exists():
            print(f"✅ Firmware file verified")
            return result.firmware_path
        else:
            print(f"❌ Firmware file not found: {firmware_path}")
            return None
    else:
        print(f"❌ Firmware build failed: {result.error_message}")
        return None

def test_esp8266_connection():
    """Test ESP8266 connection on COM4"""
    print(f"\n🔌 Testing ESP8266 Connection")
    print("=" * 40)
    
    try:
        # Create ESP uploader
        uploader = EspUploader()
        
        # Test connection
        print("🔍 Checking COM4 connection...")
        ports = uploader.list_ports()
        
        if "COM4" in ports:
            print(f"✅ COM4 found in available ports")
            print(f"   Available ports: {ports}")
            return True
        else:
            print(f"❌ COM4 not found in available ports")
            print(f"   Available ports: {ports}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking connection: {e}")
        return False

def test_firmware_upload(firmware_path):
    """Test firmware upload to ESP8266"""
    print(f"\n🚀 Testing Firmware Upload")
    print("=" * 40)
    
    try:
        # Create ESP uploader
        uploader = EspUploader()
        
        # Upload configuration
        upload_config = {
            'port': 'COM4',
            'baud_rate': 115200,
            'chip': 'esp8266',
            'firmware_path': firmware_path
        }
        
        print("📤 Starting upload to ESP8266 on COM4...")
        print("⚠️  Make sure ESP8266 is in bootloader mode:")
        print("   1. Hold GPIO0 LOW")
        print("   2. Press RESET")
        print("   3. Release GPIO0")
        print("   4. Release RESET")
        print("\n⏳ Uploading in 5 seconds...")
        
        # Give user time to prepare
        for i in range(5, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Attempt upload
        result = uploader.upload_firmware(upload_config)
        
        if result.success:
            print(f"✅ Upload successful!")
            print(f"   Firmware: {result.firmware_path}")
            print(f"   Size: {result.size_bytes:,} bytes")
            print(f"   Time: {result.upload_time:.2f}s")
            return True
        else:
            print(f"❌ Upload failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False

def test_complete_system():
    """Test the complete system pipeline"""
    print("🎨 Upload Bridge - Complete System Test")
    print("=" * 60)
    print("Testing ESP8266 on COM4 with sample pattern")
    print("=" * 60)
    
    # Step 1: Load pattern
    pattern = test_pattern_loading()
    if not pattern:
        print("\n❌ SYSTEM TEST FAILED: Pattern loading failed")
        return False
    
    # Step 2: Build firmware
    firmware_path = test_firmware_building(pattern)
    if not firmware_path:
        print("\n❌ SYSTEM TEST FAILED: Firmware building failed")
        return False
    
    # Step 3: Test connection
    connection_ok = test_esp8266_connection()
    if not connection_ok:
        print("\n⚠️  WARNING: COM4 connection test failed")
        print("   Proceeding with upload attempt anyway...")
    
    # Step 4: Upload firmware
    upload_ok = test_firmware_upload(firmware_path)
    if not upload_ok:
        print("\n❌ SYSTEM TEST FAILED: Firmware upload failed")
        return False
    
    # Success!
    print(f"\n🎉 COMPLETE SYSTEM TEST PASSED!")
    print("=" * 60)
    print(f"✅ Pattern loaded: {pattern.name}")
    print(f"✅ Firmware built: {firmware_path}")
    print(f"✅ ESP8266 connected: COM4")
    print(f"✅ Firmware uploaded successfully")
    print(f"\n💡 Your ESP8266 should now be running the pattern!")
    print(f"   LEDs: {pattern.led_count}")
    print(f"   Frames: {pattern.frame_count}")
    print(f"   FPS: {pattern.metadata.fps}")
    
    return True

def main():
    """Main function"""
    try:
        success = test_complete_system()
        return success
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)













