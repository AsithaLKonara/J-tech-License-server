#!/usr/bin/env python3
"""
Run Pattern Compatibility Test
Tests all patterns in the patterns/ folder for compatibility with upload bridge
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_pattern_compatibility import PatternCompatibilityTester


def main():
    """Main test function"""
    print("=" * 80)
    print("LED MATRIX STUDIO - PATTERN COMPATIBILITY TEST")
    print("=" * 80)
    print()
    
    # Check if patterns directory exists
    patterns_dir = Path("patterns")
    if not patterns_dir.exists():
        print("❌ Patterns directory not found!")
        print("Please ensure the 'patterns' directory exists and contains pattern files.")
        return 1
    
    # Count pattern files
    pattern_files = []
    for ext in ['*.bin', '*.hex', '*.dat', '*.leds', '*.ledadmin', '*.ledproj', '*.json', '*.csv', '*.txt']:
        pattern_files.extend(patterns_dir.glob(ext))
    
    if not pattern_files:
        print("❌ No pattern files found in 'patterns' directory!")
        print("Please add some pattern files to test.")
        return 1
    
    print(f"📁 Found {len(pattern_files)} pattern files to test")
    print()
    
    # Initialize tester
    print("🔧 Initializing pattern compatibility tester...")
    tester = PatternCompatibilityTester()
    
    # Run tests
    print("🧪 Running compatibility tests...")
    print("-" * 40)
    
    start_time = time.time()
    results = tester.test_all_patterns("patterns")
    end_time = time.time()
    
    print(f"\n⏱️  Tests completed in {end_time - start_time:.2f} seconds")
    print()
    
    # Generate report
    print("📊 Generating compatibility report...")
    report = tester.generate_report(results)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print()
    
    print(f"📈 Total files tested: {results['total_files']}")
    print(f"✅ Successfully parsed: {results['successful_parses']}")
    print(f"❌ Failed to parse: {results['failed_parses']}")
    print(f"🔌 ESP-01 compatible: {results['esp01_compatible']}")
    print(f"⚠️  ESP-01 incompatible: {results['esp01_incompatible']}")
    print()
    
    # Calculate success rates
    if results['total_files'] > 0:
        parse_rate = (results['successful_parses'] / results['total_files']) * 100
        print(f"📊 Parse success rate: {parse_rate:.1f}%")
        
        if results['successful_parses'] > 0:
            esp01_rate = (results['esp01_compatible'] / results['successful_parses']) * 100
            print(f"🔌 ESP-01 compatibility rate: {esp01_rate:.1f}%")
        else:
            print("🔌 ESP-01 compatibility rate: N/A (no successful parses)")
    
    print()
    
    # Show detailed results
    print("📋 DETAILED RESULTS:")
    print("-" * 40)
    
    for detail in results['details']:
        status = "✅" if detail['parse_success'] else "❌"
        esp01_status = "🔌" if detail['esp01_compatible'] else "⚠️"
        
        print(f"\n{status} {detail['filename']}")
        print(f"   Size: {detail['file_size']:,} bytes")
        
        if detail['parse_success'] and detail['pattern_info']:
            info = detail['pattern_info']
            print(f"   LEDs: {info['led_count']}")
            print(f"   Frames: {info['frame_count']}")
            print(f"   Duration: {info['duration_ms'] / 1000:.2f}s")
            print(f"   FPS: {info['average_fps']:.1f}")
            print(f"   Size: {info['estimated_size_kb']:.1f}KB")
            print(f"   ESP-01: {esp01_status} {'Compatible' if detail['esp01_compatible'] else 'Incompatible'}")
            
            if detail['esp01_error']:
                print(f"   Error: {detail['esp01_error']}")
            
            if detail['recommendations']:
                print(f"   Recommendations:")
                for rec in detail['recommendations']:
                    print(f"     • {rec}")
        else:
            print(f"   Parse error: {detail['parse_error']}")
    
    # Save report
    report_file = "pattern_compatibility_report.txt"
    tester.save_report(results, report_file)
    print(f"\n💾 Full report saved to: {report_file}")
    
    # Final status
    print("\n" + "=" * 80)
    if results['successful_parses'] == results['total_files']:
        print("🎉 ALL PATTERNS SUCCESSFULLY PARSED!")
    elif results['successful_parses'] > 0:
        print(f"⚠️  {results['successful_parses']}/{results['total_files']} patterns successfully parsed")
    else:
        print("❌ NO PATTERNS SUCCESSFULLY PARSED!")
    
    if results['esp01_compatible'] > 0:
        print(f"🔌 {results['esp01_compatible']} patterns are ESP-01 compatible")
    else:
        print("⚠️  No patterns are ESP-01 compatible")
    
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
