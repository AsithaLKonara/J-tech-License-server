"""
Pattern Compatibility Test Script
Tests all patterns in the patterns/ folder for compatibility
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pattern import Pattern
from parsers.parser_registry import ParserRegistry
from uploaders.esp01_uploader import ESP01Uploader


class PatternCompatibilityTester:
    """
    Comprehensive pattern compatibility tester
    """
    
    def __init__(self):
        self.parser_registry = ParserRegistry()
        self.esp01_uploader = ESP01Uploader()
        self.results = []
    
    def test_all_patterns(self, patterns_dir: str = "patterns") -> Dict:
        """
        Test all patterns in the specified directory
        
        Args:
            patterns_dir: Directory containing pattern files
            
        Returns:
            Dictionary with test results
        """
        patterns_path = Path(patterns_dir)
        
        if not patterns_path.exists():
            print(f"Patterns directory not found: {patterns_path}")
            return {"error": "Patterns directory not found"}
        
        # Find all pattern files
        pattern_files = []
        for ext in ['*.bin', '*.hex', '*.dat', '*.leds', '*.ledadmin', '*.ledproj', '*.json', '*.csv', '*.txt']:
            pattern_files.extend(patterns_path.glob(ext))
        
        print(f"Found {len(pattern_files)} pattern files")
        
        # Test each pattern
        results = {
            'total_files': len(pattern_files),
            'successful_parses': 0,
            'failed_parses': 0,
            'esp01_compatible': 0,
            'esp01_incompatible': 0,
            'details': []
        }
        
        for pattern_file in pattern_files:
            print(f"\nTesting: {pattern_file.name}")
            result = self.test_single_pattern(pattern_file)
            results['details'].append(result)
            
            if result['parse_success']:
                results['successful_parses'] += 1
            else:
                results['failed_parses'] += 1
            
            if result['esp01_compatible']:
                results['esp01_compatible'] += 1
            else:
                results['esp01_incompatible'] += 1
        
        return results
    
    def test_single_pattern(self, pattern_file: Path) -> Dict:
        """
        Test a single pattern file
        
        Args:
            pattern_file: Path to pattern file
            
        Returns:
            Dictionary with test results
        """
        result = {
            'filename': pattern_file.name,
            'file_size': pattern_file.stat().st_size,
            'parse_success': False,
            'parse_error': None,
            'pattern_info': None,
            'esp01_compatible': False,
            'esp01_error': None,
            'recommendations': []
        }
        
        try:
            # Test parsing
            print(f"  Parsing {pattern_file.name}...")
            pattern, format_name = self.parser_registry.parse_file(str(pattern_file))
            
            result['parse_success'] = True
            result['pattern_info'] = {
                'name': pattern.name,
                'led_count': pattern.led_count,
                'frame_count': pattern.frame_count,
                'duration_ms': pattern.duration_ms,
                'average_fps': pattern.average_fps,
                'estimated_size_kb': pattern.estimate_memory_bytes() / 1024.0
            }
            
            print(f"    ✓ Parsed successfully: {pattern.led_count} LEDs, {pattern.frame_count} frames")
            
            # Test ESP-01 compatibility
            print(f"  Testing ESP-01 compatibility...")
            is_compatible, error_msg = self.esp01_uploader.validate_pattern(pattern)
            
            result['esp01_compatible'] = is_compatible
            if not is_compatible:
                result['esp01_error'] = error_msg
                print(f"    ✗ ESP-01 incompatible: {error_msg}")
            else:
                print(f"    ✓ ESP-01 compatible")
            
            # Generate recommendations
            result['recommendations'] = self.generate_recommendations(pattern)
            
        except Exception as e:
            result['parse_error'] = str(e)
            print(f"    ✗ Parse failed: {e}")
        
        return result
    
    def generate_recommendations(self, pattern: Pattern) -> List[str]:
        """
        Generate recommendations for pattern optimization
        
        Args:
            pattern: Pattern object
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # LED count recommendations
        if pattern.led_count > 300:
            recommendations.append(f"Consider reducing LED count from {pattern.led_count} to 300 or less for ESP-01")
        elif pattern.led_count > 150:
            recommendations.append(f"LED count ({pattern.led_count}) is high for ESP-01, consider optimization")
        
        # Frame count recommendations
        if pattern.frame_count > 10000:
            recommendations.append(f"Consider reducing frame count from {pattern.frame_count} to 10000 or less")
        elif pattern.frame_count > 5000:
            recommendations.append(f"Frame count ({pattern.frame_count}) is high, consider reducing for better performance")
        
        # Duration recommendations
        if pattern.duration_ms > 300000:  # 5 minutes
            recommendations.append(f"Pattern duration ({pattern.duration_ms / 1000:.1f}s) is very long, consider shortening")
        
        # FPS recommendations
        if pattern.average_fps > 60:
            recommendations.append(f"High FPS ({pattern.average_fps:.1f}) may cause performance issues on ESP-01")
        elif pattern.average_fps < 10:
            recommendations.append(f"Low FPS ({pattern.average_fps:.1f}) may appear choppy, consider increasing")
        
        # Size recommendations
        size_kb = pattern.estimate_memory_bytes() / 1024.0
        if size_kb > 800:
            recommendations.append(f"Pattern size ({size_kb:.1f}KB) is large for ESP-01 (1MB flash), consider optimization")
        elif size_kb > 400:
            recommendations.append(f"Pattern size ({size_kb:.1f}KB) is moderate, monitor memory usage")
        
        # Matrix recommendations
        if pattern.metadata.is_matrix:
            width = pattern.metadata.width
            height = pattern.metadata.height
            if width > 20 or height > 20:
                recommendations.append(f"Large matrix ({width}×{height}) may be challenging for ESP-01")
            elif width > 10 or height > 10:
                recommendations.append(f"Matrix size ({width}×{height}) is moderate for ESP-01")
        
        return recommendations
    
    def generate_report(self, results: Dict) -> str:
        """
        Generate a comprehensive test report
        
        Args:
            results: Test results dictionary
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("PATTERN COMPATIBILITY TEST REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total files tested: {results['total_files']}")
        report.append(f"  Successfully parsed: {results['successful_parses']}")
        report.append(f"  Failed to parse: {results['failed_parses']}")
        report.append(f"  ESP-01 compatible: {results['esp01_compatible']}")
        report.append(f"  ESP-01 incompatible: {results['esp01_incompatible']}")
        report.append("")
        
        # Success rate
        if results['total_files'] > 0:
            parse_rate = (results['successful_parses'] / results['total_files']) * 100
            esp01_rate = (results['esp01_compatible'] / results['successful_parses']) * 100 if results['successful_parses'] > 0 else 0
            
            report.append("SUCCESS RATES:")
            report.append(f"  Parse success rate: {parse_rate:.1f}%")
            report.append(f"  ESP-01 compatibility rate: {esp01_rate:.1f}%")
            report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        report.append("-" * 40)
        
        for detail in results['details']:
            report.append(f"\nFile: {detail['filename']}")
            report.append(f"  Size: {detail['file_size']:,} bytes")
            
            if detail['parse_success'] and detail['pattern_info']:
                info = detail['pattern_info']
                report.append(f"  ✓ Parsed successfully")
                report.append(f"    LEDs: {info['led_count']}")
                report.append(f"    Frames: {info['frame_count']}")
                report.append(f"    Duration: {info['duration_ms'] / 1000:.2f}s")
                report.append(f"    FPS: {info['average_fps']:.1f}")
                report.append(f"    Size: {info['estimated_size_kb']:.1f}KB")
                
                if detail['esp01_compatible']:
                    report.append(f"  ✓ ESP-01 compatible")
                else:
                    report.append(f"  ✗ ESP-01 incompatible: {detail['esp01_error']}")
                
                if detail['recommendations']:
                    report.append(f"  Recommendations:")
                    for rec in detail['recommendations']:
                        report.append(f"    - {rec}")
            else:
                report.append(f"  ✗ Parse failed: {detail['parse_error']}")
        
        return "\n".join(report)
    
    def save_report(self, results: Dict, output_file: str = "pattern_compatibility_report.txt"):
        """
        Save test report to file
        
        Args:
            results: Test results dictionary
            output_file: Output file path
        """
        report = self.generate_report(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nReport saved to: {output_file}")


def main():
    """Main test function"""
    print("Pattern Compatibility Tester")
    print("=" * 40)
    
    # Initialize tester
    tester = PatternCompatibilityTester()
    
    # Test patterns
    print("Testing patterns in 'patterns/' directory...")
    results = tester.test_all_patterns("patterns")
    
    # Generate and save report
    report = tester.generate_report(results)
    print("\n" + report)
    
    # Save report to file
    tester.save_report(results)
    
    # Print summary
    print(f"\nSUMMARY:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Parse success: {results['successful_parses']}/{results['total_files']}")
    print(f"  ESP-01 compatible: {results['esp01_compatible']}/{results['successful_parses']}")
    
    if results['successful_parses'] > 0:
        success_rate = (results['successful_parses'] / results['total_files']) * 100
        esp01_rate = (results['esp01_compatible'] / results['successful_parses']) * 100
        print(f"  Parse success rate: {success_rate:.1f}%")
        print(f"  ESP-01 compatibility rate: {esp01_rate:.1f}%")


if __name__ == "__main__":
    main()
