#!/usr/bin/env python3
"""
Verify Firmware Script - Verifies flashed firmware

This script is used by CI/CD workflows to verify flashed firmware.
"""

import argparse
import sys
from pathlib import Path

from uploaders.adapter_registry import get_adapter
from uploaders.verification import verify_firmware_hash


def main():
    parser = argparse.ArgumentParser(description='Verify flashed firmware')
    parser.add_argument('--chip', required=True, help='Chip identifier')
    parser.add_argument('--port', help='Serial port')
    parser.add_argument('--firmware', required=True, type=Path, help='Firmware file')
    parser.add_argument('--expected-hash', help='Expected hash (optional)')
    
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
    
    # Verify firmware
    result, actual_hash = verify_firmware_hash(
        firmware_path=args.firmware,
        device_info=device_info,
        adapter=adapter,
        expected_hash=args.expected_hash
    )
    
    if result.value == "SUCCESS":
        print(f"SUCCESS: Firmware verification passed (hash: {actual_hash})")
        sys.exit(0)
    else:
        print(f"ERROR: Firmware verification failed: {result.value}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

