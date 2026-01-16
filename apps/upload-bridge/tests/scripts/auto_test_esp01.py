#!/usr/bin/env python3
"""
Automated ESP01 Test - Run test and fix in loop
"""

import sys
import os
import time
import subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_tools():
    """Check if required tools are available"""
    print("Checking tools...")
    
    try:
        import esptool
        print(f"  ✓ esptool {esptool.__version__}")
    except ImportError:
        print("  ❌ esptool not found")
        return False
    
    try:
        result = subprocess.run(['arduino-cli', 'version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ arduino-cli: {result.stdout.strip()}")
        else:
            print("  ❌ arduino-cli not working")
            return False
    except FileNotFoundError:
        print("  ❌ arduino-cli not found")
        return False
    
    return True

def check_esp_on_com4():
    """Check if ESP01 is connected on COM4"""
    print("\nChecking COM4 for ESP01...")
    
    try:
        import serial
        ser = serial.Serial('COM4', 115200, timeout=1)
        ser.close()
        print("  ✓ COM4 is available")
        return True
    except Exception as e:
        print(f"  ❌ COM4 error: {e}")
        return False

def create_minimal_pattern():
    """Create a minimal test pattern"""
    print("\nCreating test pattern...")
    
    from core.pattern import create_test_pattern
    
    pattern = create_test_pattern(led_count=76, frame_count=20)
    print(f"  ✓ Created: {pattern.led_count} LEDs, {pattern.frame_count} frames")
    
    return pattern

def build_firmware(pattern):
    """Build firmware for ESP8266"""
    print("\nBuilding firmware...")
    
    from firmware.builder import FirmwareBuilder
    
    builder = FirmwareBuilder()
    output_dir = os.path.join(os.path.dirname(__file__), 'build', 'test_esp01')
    os.makedirs(output_dir, exist_ok=True)
    
    build_result = builder.build(
        pattern=pattern,
        chip_id='esp8266',
        build_opts={
            'output_dir': output_dir,
            'gpio_pin': 3,
            'optimize_level': 1
        }
    )
    
    if not build_result.success:
        print(f"  ❌ Build failed: {build_result.error_message}")
        return None
    
    print(f"  ✓ Built: {build_result.firmware_path}")
    print(f"     Size: {build_result.size_bytes} bytes")
    
    return build_result

def flash_firmware(firmware_path, max_attempts=3):
    """Attempt to flash firmware to ESP01 on COM4"""
    print(f"\nAttempting flash to COM4 (max {max_attempts} attempts)...")
    
    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt}/{max_attempts}...")
        
        try:
            # Use esptool to erase flash
            print("  Erasing flash...")
            result = subprocess.run([
                'python', '-m', 'esptool',
                '--port', 'COM4',
                '--chip', 'esp8266',
                'erase_flash'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"  ⚠ Erase failed: {result.stderr}")
            
            # Upload firmware
            print("  Uploading firmware...")
            result = subprocess.run([
                'python', '-m', 'esptool',
                '--port', 'COM4',
                '--baud', '115200',
                '--chip', 'esp8266',
                'write_flash',
                '0x0', firmware_path
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("  ✓ Flash successful!")
                print(f"  Output: {result.stdout}")
                return True
            else:
                print(f"  ❌ Flash failed:")
                print(f"  Stdout: {result.stdout}")
                print(f"  Stderr: {result.stderr}")
                
                if attempt < max_attempts:
                    print("  Retrying in 2 seconds...")
                    time.sleep(2)
                    
        except subprocess.TimeoutExpired:
            print(f"  ❌ Flash timeout on attempt {attempt}")
            if attempt < max_attempts:
                print("  Retrying...")
                time.sleep(2)
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            if attempt < max_attempts:
                print("  Retrying...")
                time.sleep(2)
    
    return False

def main():
    """Main test loop"""
    print("=" * 60)
    print("ESP01 AUTOMATED TEST")
    print("=" * 60)
    
    # Step 1: Check tools
    if not check_tools():
        print("\n❌ Required tools missing. Please install:")
        print("  - pip install esptool")
        print("  - Install Arduino CLI")
        return False
    
    # Step 2: Check COM port
    if not check_esp_on_com4():
        print("\n⚠ Make sure ESP01 is connected to COM4")
        print("  Press ENTER to continue anyway, or Ctrl+C to cancel...")
        try:
            input()
        except KeyboardInterrupt:
            return False
    
    # Step 3: Create pattern
    pattern = create_minimal_pattern()
    
    # Step 4: Build firmware
    build_result = build_firmware(pattern)
    if not build_result:
        print("\n❌ Build failed")
        return False
    
    # Step 5: Flash firmware
    firmware_path = build_result.firmware_path
    success = flash_firmware(firmware_path)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TEST SUCCESSFUL!")
        print("=" * 60)
        print("\nESP01 has been flashed with test pattern.")
        print("The pattern should be running on your LEDs now.")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Make sure ESP01 is in flash mode (GPIO0 to GND)")
        print("2. Check COM port connection")
        print("3. Try pressing reset button on ESP01")
        print("4. Check baud rate settings")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




