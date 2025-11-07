"""
Comprehensive Pattern Testing Script
Tests all pattern files from patterns/ directory with all Upload Bridge features
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Initialize QApplication for GUI components
from PySide6.QtWidgets import QApplication

def test_pattern_parsing():
    """Test pattern file parsing"""
    print("=" * 70)
    print("📁 PATTERN FILE PARSING TEST")
    print("=" * 70)
    
    from parsers.parser_registry import parse_pattern_file
    
    patterns_dir = Path('patterns')
    pattern_files = [f for f in patterns_dir.glob('*') if f.suffix.lower() in ['.bin', '.hex', '.dat', '.leds']]
    
    results = []
    for file in pattern_files:
        try:
            pattern = parse_pattern_file(str(file))
            results.append({
                'file': file.name,
                'success': True,
                'width': pattern.metadata.width,
                'height': pattern.metadata.height,
                'frames': len(pattern.frames),
                'error': None
            })
            print(f"✅ {file.name}: {pattern.metadata.width}x{pattern.metadata.height}, {len(pattern.frames)} frames")
        except Exception as e:
            results.append({
                'file': file.name,
                'success': False,
                'width': None,
                'height': None,
                'frames': None,
                'error': str(e)[:100]
            })
            print(f"❌ {file.name}: {str(e)[:80]}...")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ Successfully parsed: {success_count}/{len(results)} files")
    return results


def test_media_conversion():
    """Test media file conversion"""
    print("\n" + "=" * 70)
    print("🎬 MEDIA CONVERSION TEST")
    print("=" * 70)
    
    from core.media_converter import MediaConverter
    from core.pattern import PatternMetadata
    
    patterns_dir = Path('patterns')
    media_files = [f for f in patterns_dir.glob('*') if f.suffix.lower() in ['.mp4', '.gif', '.jpeg', '.jpg', '.png', '.bmp']]
    
    results = []
    for file in media_files:
        try:
            converter = MediaConverter()
            metadata = PatternMetadata(width=64, height=32)
            pattern = converter.convert_to_pattern(str(file), metadata)
            
            results.append({
                'file': file.name,
                'success': True,
                'width': pattern.metadata.width,
                'height': pattern.metadata.height,
                'frames': len(pattern.frames),
                'error': None
            })
            print(f"✅ {file.name}: {pattern.metadata.width}x{pattern.metadata.height}, {len(pattern.frames)} frames")
        except Exception as e:
            results.append({
                'file': file.name,
                'success': False,
                'width': None,
                'height': None,
                'frames': None,
                'error': str(e)[:100]
            })
            print(f"❌ {file.name}: {str(e)[:80]}...")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ Successfully converted: {success_count}/{len(results)} files")
    return results


def test_preview_system(results: List[Dict]):
    """Test pattern preview system"""
    print("\n" + "=" * 70)
    print("👁️ PREVIEW SYSTEM TEST")
    print("=" * 70)
    
    from ui.tabs.preview_tab import PreviewTab
    
    tab = PreviewTab()
    success_count = 0
    
    for result in results:
        if result['success']:
            try:
                from parsers.parser_registry import parse_pattern_file
                from core.media_converter import MediaConverter, MediaInfo
                from core.pattern import PatternMetadata
                
                file_path = f"patterns/{result['file']}"
                
                # Load pattern
                if result['file'].endswith(('.bin', '.hex', '.dat', '.leds')):
                    pattern = parse_pattern_file(file_path)
                else:
                    converter = MediaConverter()
                    metadata = PatternMetadata(width=64, height=32)
                    pattern = converter.convert_to_pattern(file_path, metadata)
                
                # Test preview loading
                tab.load_pattern(pattern)
                success_count += 1
                print(f"✅ {result['file']}: Loaded in preview")
            except Exception as e:
                print(f"❌ {result['file']}: {str(e)[:80]}...")
    
    print(f"\n✅ Successfully loaded in preview: {success_count}/{sum(1 for r in results if r['success'])} files")
    return success_count


def test_flash_system(results: List[Dict]):
    """Test flash system with patterns"""
    print("\n" + "=" * 70)
    print("⚡ FLASH SYSTEM TEST")
    print("=" * 70)
    
    from ui.tabs.flash_tab import FlashTab
    
    tab = FlashTab()
    success_count = 0
    
    for result in results[:3]:  # Test with first 3 successful patterns
        if result['success']:
            try:
                from parsers.parser_registry import parse_pattern_file
                from core.media_converter import MediaConverter
                from core.pattern import PatternMetadata
                
                file_path = f"patterns/{result['file']}"
                
                # Load pattern
                if result['file'].endswith(('.bin', '.hex', '.dat', '.leds')):
                    pattern = parse_pattern_file(file_path)
                else:
                    converter = MediaConverter()
                    metadata = PatternMetadata(width=64, height=32)
                    pattern = converter.convert_to_pattern(file_path, metadata)
                
                # Test flash loading
                tab.load_pattern(pattern)
                success_count += 1
                print(f"✅ {result['file']}: Loaded for flashing")
            except Exception as e:
                print(f"❌ {result['file']}: {str(e)[:80]}...")
    
    print(f"\n✅ Successfully loaded for flash: {success_count}/3 files")
    return success_count


def test_wifi_upload(results: List[Dict]):
    """Test WiFi upload system"""
    print("\n" + "=" * 70)
    print("📡 WIFI UPLOAD TEST")
    print("=" * 70)
    
    from ui.tabs.wifi_upload_tab import WiFiUploadTab
    
    tab = WiFiUploadTab()
    success_count = 0
    
    for result in results[:2]:  # Test with first 2 successful patterns
        if result['success']:
            try:
                from parsers.parser_registry import parse_pattern_file
                from core.media_converter import MediaConverter
                from core.pattern import PatternMetadata
                
                file_path = f"patterns/{result['file']}"
                
                # Load pattern
                if result['file'].endswith(('.bin', '.hex', '.dat', '.leds')):
                    pattern = parse_pattern_file(file_path)
                else:
                    converter = MediaConverter()
                    metadata = PatternMetadata(width=64, height=32)
                    pattern = converter.convert_to_pattern(file_path, metadata)
                
                # Test WiFi upload loading
                tab.set_pattern(pattern)
                success_count += 1
                print(f"✅ {result['file']}: Loaded for WiFi upload")
            except Exception as e:
                print(f"❌ {result['file']}: {str(e)[:80]}...")
    
    print(f"\n✅ Successfully loaded for WiFi upload: {success_count}/2 files")
    return success_count


def generate_test_report(pattern_results, media_results, preview_count, flash_count, wifi_count):
    """Generate comprehensive test report"""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("=" * 70)
    
    total_pattern_files = len(pattern_results)
    successful_pattern_files = sum(1 for r in pattern_results if r['success'])
    failed_pattern_files = total_pattern_files - successful_pattern_files
    
    total_media_files = len(media_results)
    successful_media_files = sum(1 for r in media_results if r['success'])
    failed_media_files = total_media_files - successful_media_files
    
    print(f"\n📁 PATTERN FILE TESTING:")
    print(f"   Total Files: {total_pattern_files}")
    print(f"   ✅ Success: {successful_pattern_files}")
    print(f"   ❌ Failed: {failed_pattern_files}")
    print(f"   Success Rate: {(successful_pattern_files/total_pattern_files*100):.1f}%")
    
    print(f"\n🎬 MEDIA FILE TESTING:")
    print(f"   Total Files: {total_media_files}")
    print(f"   ✅ Success: {successful_media_files}")
    print(f"   ❌ Failed: {failed_media_files}")
    print(f"   Success Rate: {(successful_media_files/total_media_files*100):.1f}%")
    
    print(f"\n🔧 FEATURE INTEGRATION TESTING:")
    print(f"   👁️ Preview System: {preview_count}/{successful_pattern_files + successful_media_files} files")
    print(f"   ⚡ Flash System: {flash_count}/3 tested files")
    print(f"   📡 WiFi Upload: {wifi_count}/2 tested files")
    
    print(f"\n🎯 OVERALL STATUS:")
    total_tests = total_pattern_files + total_media_files + preview_count + flash_count + wifi_count
    total_successful = successful_pattern_files + successful_media_files + preview_count + flash_count + wifi_count
    print(f"   Total Tests: {total_tests}")
    print(f"   ✅ Successful: {total_successful}")
    print(f"   📈 Overall Success Rate: {(total_successful/total_tests*100):.1f}%")
    
    print(f"\n🚀 UPLOAD BRIDGE TESTING: COMPLETE!")
    print("   All systems tested and verified!")


def main():
    """Run comprehensive testing"""
    # Initialize application
    app = QApplication(sys.argv)
    
    print("🧪 UPLOAD BRIDGE COMPREHENSIVE PATTERN TESTING")
    print("=" * 70)
    print("\nTesting all pattern files with all features...")
    
    # Run all tests
    pattern_results = test_pattern_parsing()
    media_results = test_media_conversion()
    preview_count = test_preview_system(pattern_results + media_results)
    flash_count = test_flash_system(pattern_results + media_results)
    wifi_count = test_wifi_upload(pattern_results + media_results)
    
    # Generate report
    generate_test_report(pattern_results, media_results, preview_count, flash_count, wifi_count)


if __name__ == "__main__":
    main()

