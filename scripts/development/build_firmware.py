#!/usr/bin/env python3
"""
Build Firmware Script - Builds firmware for specified chip

This script is used by CI/CD workflows to build firmware for different chips.
"""

import argparse
import sys
from pathlib import Path

from uploaders.adapter_registry import get_adapter
from core.pattern import Pattern, Frame, PatternMetadata


def main():
    parser = argparse.ArgumentParser(description='Build firmware for chip')
    parser.add_argument('--chip', required=True, help='Chip identifier')
    parser.add_argument('--output', required=True, type=Path, help='Output firmware file')
    parser.add_argument('--pattern', type=Path, help='Pattern file (optional, uses default if not provided)')
    
    args = parser.parse_args()
    
    # Get adapter
    adapter = get_adapter(args.chip)
    if not adapter:
        print(f"ERROR: Chip {args.chip} not found", file=sys.stderr)
        sys.exit(1)
    
    # Load or create pattern
    if args.pattern and args.pattern.exists():
        from core.project import load_project
        pattern, _ = load_project(args.pattern)
    else:
        # Create default test pattern
        metadata = PatternMetadata(
            width=16,
            height=16,
            color_order="RGB",
            wiring_mode="Row-major",
            data_in_corner="LT"
        )
        pattern = Pattern(
            id="test_pattern",
            name="Test Pattern",
            metadata=metadata,
            frames=[Frame(pixels=[(255, 0, 0)] * 256, duration_ms=100)]
        )
    
    # Build firmware
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = adapter.build_firmware(pattern, args.output)
    
    if result.success:
        print(f"SUCCESS: Firmware built: {args.output}")
        sys.exit(0)
    else:
        print(f"ERROR: Firmware build failed: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

