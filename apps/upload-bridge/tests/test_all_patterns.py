#!/usr/bin/env python3
"""Test metadata detection for all patterns in the patterns directory."""

import sys
from pathlib import Path
from parsers.parser_registry import ParserRegistry
from core.file_format_detector import detect_file_format

def test_pattern_file(filepath: Path):
    """Test a single pattern file and return results."""
    try:
        registry = ParserRegistry()
        pattern, format_name = registry.parse_file(str(filepath))
        
        # Detect wiring format
        wiring_mode, data_in_corner = detect_file_format(pattern)
        
        return {
            'success': True,
            'format': format_name,
            'width': pattern.metadata.width,
            'height': pattern.metadata.height,
            'led_count': pattern.led_count,
            'frame_count': pattern.frame_count,
            'wiring_mode': wiring_mode,
            'data_in_corner': data_in_corner,
            'dimension_source': pattern.metadata.dimension_source,
            'dimension_confidence': pattern.metadata.dimension_confidence,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'format': None,
            'width': None,
            'height': None,
            'led_count': None,
            'frame_count': None,
            'wiring_mode': None,
            'data_in_corner': None,
            'dimension_source': None,
            'dimension_confidence': None
        }

def main():
    patterns_dir = Path("patterns")
    if not patterns_dir.exists():
        print(f"ERROR: Patterns directory not found: {patterns_dir}")
        return 1
    
    # Collect all pattern files
    pattern_files = []
    
    # Root level files
    for ext in ['.bin', '.dat', '.leds', '.hex']:
        pattern_files.extend(patterns_dir.glob(f"*{ext}"))
    
    # 15x6 directory
    if (patterns_dir / "15x6").exists():
        for ext in ['.bin', '.dat', '.leds', '.hex']:
            pattern_files.extend((patterns_dir / "15x6").glob(f"*{ext}"))
    
    # 12x6 patterns directory
    if (patterns_dir / "12x6 patterns").exists():
        for ext in ['.bin', '.dat', '.leds', '.hex']:
            pattern_files.extend((patterns_dir / "12x6 patterns").glob(f"*{ext}"))
        # Also check correct subdirectory
        correct_dir = patterns_dir / "12x6 patterns" / "correct"
        if correct_dir.exists():
            for ext in ['.bin', '.dat', '.leds', '.hex']:
                pattern_files.extend(correct_dir.glob(f"*{ext}"))
    
    # Sort for consistent output
    pattern_files.sort()
    
    print("=" * 100)
    print("PATTERN METADATA DETECTION TEST RESULTS")
    print("=" * 100)
    print()
    
    results = []
    for filepath in pattern_files:
        # Get relative path for display
        try:
            rel_path = filepath.relative_to(patterns_dir.parent)
        except (ValueError, AttributeError):
            rel_path = filepath
        print(f"Testing: {rel_path}")
        result = test_pattern_file(filepath)
        result['filepath'] = rel_path
        results.append(result)
        
        if result['success']:
            print(f"  ✓ Format: {result['format']}")
            print(f"  ✓ Dimensions: {result['width']}x{result['height']} = {result['led_count']} LEDs")
            print(f"  ✓ Frames: {result['frame_count']}")
            print(f"  ✓ Wiring: {result['wiring_mode']} ({result['data_in_corner']})")
            print(f"  ✓ Dimension source: {result['dimension_source']} (confidence: {result['dimension_confidence']:.2f})")
        else:
            print(f"  ✗ ERROR: {result['error']}")
        print()
    
    # Summary
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    print(f"Total files tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()
    
    # Group by expected dimensions
    print("Grouped by detected dimensions:")
    dim_groups = {}
    for r in results:
        if r['success']:
            key = f"{r['width']}x{r['height']}"
            if key not in dim_groups:
                dim_groups[key] = []
            dim_groups[key].append(r)
    
    for dim, group in sorted(dim_groups.items()):
        print(f"\n  {dim} ({len(group)} files):")
        for r in group:
            wiring_info = f"{r['wiring_mode']} {r['data_in_corner']}"
            fp = r['filepath']
            name = fp.name if hasattr(fp, 'name') else str(fp).split('/')[-1].split('\\')[-1]
            print(f"    - {name}: {wiring_info}")
    
    # Check for specific issues
    print()
    print("=" * 100)
    print("SPECIFIC CHECKS")
    print("=" * 100)
    
    # Check 15x6 patterns
    print("\n15x6 patterns:")
    for r in results:
        fp_str = str(r['filepath'])
        if r['success'] and '15x6' in fp_str:
            expected_wiring = "Column-serpentine" if "alternate" in fp_str.lower() else "Column-major" if "column" in fp_str.lower() else "Row-major"
            status = "✓" if r['wiring_mode'] == expected_wiring or (expected_wiring == "Column-serpentine" and r['wiring_mode'] == "Column-major") else "✗"
            name = r['filepath'].name if hasattr(r['filepath'], 'name') else fp_str.split('/')[-1].split('\\')[-1]
            print(f"  {status} {name}: {r['wiring_mode']} {r['data_in_corner']} (expected: {expected_wiring})")
    
    # Check 12x6 patterns
    print("\n12x6 patterns:")
    for r in results:
        fp_str = str(r['filepath'])
        if r['success'] and ('12x6' in fp_str or '12.6' in fp_str):
            expected_wiring = "Column-serpentine" if "alternate" in fp_str.lower() or "down up" in fp_str.lower() or "up down" in fp_str.lower() else "Row-major" if "row" in fp_str.lower() else None
            name = r['filepath'].name if hasattr(r['filepath'], 'name') else fp_str.split('/')[-1].split('\\')[-1]
            if expected_wiring:
                status = "✓" if r['wiring_mode'] == expected_wiring or (expected_wiring == "Column-serpentine" and r['wiring_mode'] == "Column-major") else "✗"
                print(f"  {status} {name}: {r['wiring_mode']} {r['data_in_corner']} (expected: {expected_wiring})")
            else:
                print(f"  ? {name}: {r['wiring_mode']} {r['data_in_corner']}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
