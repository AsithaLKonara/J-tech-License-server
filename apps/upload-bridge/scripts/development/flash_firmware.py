#!/usr/bin/env python3
"""
Flash Firmware Script - Flashes firmware to connected device

This script is used by CI/CD workflows to flash firmware to hardware.
"""

import argparse
import sys
from pathlib import Path

from uploaders.adapter_registry import get_adapter
from uploaders.types import DeviceInfo


def main():
    parser = argparse.ArgumentParser(description='Flash firmware to device')
    parser.add_argument('--chip', required=True, help='Chip identifier')
    parser.add_argument('--port', help='Serial port (auto-detect if not provided)')
    parser.add_argument('--firmware', required=True, type=Path, help='Firmware file')
    
    args = parser.parse_args()
    
    if not args.firmware.exists():
        print(f"ERROR: Firmware file not found: {args.firmware}", file=sys.stderr)
        sys.exit(1)
    
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
    
    # Flash firmware
    result = adapter.flash_firmware(args.firmware, device_info)
    
    if result.value == "SUCCESS":
        print(f"SUCCESS: Firmware flashed to {device_info.port}")
        sys.exit(0)
    else:
        print(f"ERROR: Firmware flash failed: {result.value}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

