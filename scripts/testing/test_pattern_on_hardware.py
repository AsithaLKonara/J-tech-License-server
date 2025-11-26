#!/usr/bin/env python3
"""
Test Pattern on Hardware - Tests pattern on connected hardware

This script is used by CI/CD workflows to test patterns on actual hardware.
"""

import argparse
import sys
from pathlib import Path
import time

from uploaders.adapter_registry import get_adapter
from core.project import load_project


def main():
    parser = argparse.ArgumentParser(description='Test pattern on hardware')
    parser.add_argument('--chip', required=True, help='Chip identifier')
    parser.add_argument('--port', help='Serial port')
    parser.add_argument('--pattern', required=True, type=Path, help='Pattern file')
    
    args = parser.parse_args()
    
    if not args.pattern.exists():
        print(f"ERROR: Pattern file not found: {args.pattern}", file=sys.stderr)
        sys.exit(1)
    
    # Load pattern
    pattern, _ = load_project(args.pattern)
    
    # Get adapter
    adapter = get_adapter(args.chip)
    if not adapter:
        print(f"ERROR: Chip {args.chip} not found", file=sys.stderr)
        sys.exit(1)
    
    # Detect device
    device_info = adapter.detect_device(args.port)
    if not device_info:
        print(f"ERROR: Device not detected on port {args.port}", file=sys.stderr)
        sys.exit(1)
    
    # Build firmware
    firmware_path = Path("build") / f"test_firmware_{args.chip}.bin"
    firmware_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = adapter.build_firmware(pattern, firmware_path)
    if not result.success:
        print(f"ERROR: Firmware build failed: {result.error}", file=sys.stderr)
        sys.exit(1)
    
    # Flash firmware
    flash_result = adapter.flash_firmware(firmware_path, device_info)
    if flash_result.value != "SUCCESS":
        print(f"ERROR: Firmware flash failed: {flash_result.value}", file=sys.stderr)
        sys.exit(1)
    
    # Wait for pattern to play
    print(f"SUCCESS: Pattern flashed, waiting 5 seconds for playback...")
    time.sleep(5)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

