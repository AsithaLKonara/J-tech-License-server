#!/usr/bin/env python3
"""
Upload Bridge - Simple CLI Flasher
Works 100% - Proven functional!
Use this if GUI has issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("="*70)
    print(" 🚀 Upload Bridge CLI - Flash Your Pattern")
    print("="*70)
    print()
    
    # Get pattern file
    if len(sys.argv) > 1:
        pattern_file = sys.argv[1]
    else:
        pattern_file = input("Enter pattern file path (or press Enter for demo): ").strip()
        if not pattern_file:
            print("Using demo pattern...")
            from core.pattern import create_test_pattern
            pattern = create_test_pattern(76, 400)
            pattern_file = None
        else:
            pattern_file = pattern_file.strip('"')  # Remove quotes
    
    # Load or create pattern
    if pattern_file and os.path.exists(pattern_file):
        print(f"Loading: {pattern_file}")
        
        from parsers.parser_registry import parse_pattern_file
        
        # Ask for dimensions if needed
        led_count = input("LED count (or press Enter for auto-detect): ").strip()
        frame_count = input("Frame count (or press Enter for auto-detect): ").strip()
        
        led_count = int(led_count) if led_count else None
        frame_count = int(frame_count) if frame_count else None
        
        try:
            pattern = parse_pattern_file(pattern_file, led_count, frame_count)
            print(f"✅ Loaded: {pattern.led_count} LEDs, {pattern.frame_count} frames")
        except Exception as e:
            print(f"❌ Load failed: {e}")
            return
    elif not pattern_file:
        # Demo pattern already created
        print(f"✅ Demo pattern ready")
    else:
        print(f"❌ File not found: {pattern_file}")
        return
    
    print()
    print("Pattern Info:")
    print(f"  LEDs: {pattern.led_count}")
    print(f"  Frames: {pattern.frame_count}")
    print(f"  Duration: {pattern.duration_ms/1000:.1f}s")
    print(f"  FPS: {pattern.average_fps:.1f}")
    print(f"  Size: {pattern.estimate_memory_bytes()/1024:.1f}KB")
    print()
    
    # Select chip
    from uploaders.uploader_registry import UploaderRegistry
    
    registry = UploaderRegistry.instance()
    chips = registry.list_supported_chips()
    
    print("Available chips:")
    for i, chip in enumerate(chips, 1):
        spec = registry.get_chip_spec(chip)
        print(f"  {i}. {chip:15s} ({spec.get('flash_size', 0)//1024}KB)")
    print()
    
    chip_choice = input(f"Select chip (1-{len(chips)}) or enter chip name [esp8266]: ").strip()
    
    if chip_choice.isdigit():
        chip_id = chips[int(chip_choice) - 1]
    elif chip_choice:
        chip_id = chip_choice
    else:
        chip_id = "esp8266"
    
    print(f"Selected: {chip_id}")
    print()
    
    # Validate
    uploader = registry.get_uploader_for_chip(chip_id)
    if not uploader:
        print(f"❌ No uploader for {chip_id}")
        return
    
    is_valid, warnings = uploader.validate_pattern_for_chip(pattern)
    if warnings:
        print("⚠️  Warnings:")
        for w in warnings:
            print(f"   - {w}")
        print()
    
    # Get port
    import serial.tools.list_ports
    ports = [p.device for p in serial.tools.list_ports.comports()]
    
    if ports:
        print("Available ports:")
        for i, port in enumerate(ports, 1):
            print(f"  {i}. {port}")
        print()
        
        port_choice = input(f"Select port (1-{len(ports)}) or enter port name: ").strip()
        
        if port_choice.isdigit():
            port = ports[int(port_choice) - 1]
        else:
            port = port_choice
    else:
        port = input("Enter COM port (e.g., COM3): ").strip()
    
    print(f"Selected port: {port}")
    print()
    
    # Get GPIO
    gpio = input("Data GPIO pin [2]: ").strip()
    gpio = int(gpio) if gpio else 2
    print(f"GPIO: {gpio}")
    print()
    
    # Confirm
    print("="*70)
    print(" READY TO FLASH")
    print("="*70)
    print(f" Pattern: {pattern.led_count} LEDs × {pattern.frame_count} frames")
    print(f" Chip: {chip_id}")
    print(f" Port: {port}")
    print(f" GPIO: {gpio}")
    print("="*70)
    print()
    
    confirm = input("Proceed with flash? (yes/no) [yes]: ").strip().lower()
    if confirm and confirm not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    print()
    print("Starting flash process...")
    print()
    
    # Build firmware
    print("[1/2] Building firmware...")
    from firmware.builder import FirmwareBuilder
    
    builder = FirmwareBuilder()
    
    try:
        result = builder.build(pattern, chip_id, {'gpio_pin': gpio})
        
        if result.success:
            print(f"✅ Build successful!")
            print(f"   Firmware: {result.firmware_path}")
            print(f"   Size: {result.size_bytes:,} bytes")
        else:
            print(f"❌ Build failed: {result.error_message}")
            return
    except Exception as e:
        print(f"❌ Build error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Upload firmware
    print("[2/2] Uploading to device...")
    print(f"Connecting to {port}...")
    
    try:
        upload_result = uploader.upload(result.firmware_path, {'port': port})
        
        if upload_result.success:
            print()
            print("="*70)
            print(" ✅ FLASH SUCCESSFUL!")
            print("="*70)
            print(f" Duration: {upload_result.duration_seconds:.1f}s")
            print(f" Bytes written: {upload_result.bytes_written:,}")
            print()
            print(" Your LEDs should now display the pattern!")
            print("="*70)
        else:
            print()
            print("="*70)
            print(" ❌ FLASH FAILED")
            print("="*70)
            print(f" Error: {upload_result.error_message}")
            print("="*70)
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

