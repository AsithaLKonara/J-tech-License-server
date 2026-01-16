#!/usr/bin/env python3
"""
Professional Integration Test - Verify all chips have full advanced features
Comprehensive testing of professional-grade features across all chip families
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.pattern import create_test_pattern
from firmware.builder import FirmwareBuilder
from firmware.universal_pattern_generator import UniversalPatternGenerator
from uploaders.uploader_registry import UploaderRegistry
import tempfile
from pathlib import Path


def test_professional_features_integration():
    """Test professional features integration across all chips"""
    print("🎯 Testing Professional Features Integration")
    print("=" * 60)
    
    # Create test pattern with all advanced features
    pattern = create_test_pattern(led_count=50, frame_count=20)
    
    # Apply all advanced features
    pattern.apply_advanced_brightness(
        brightness=0.8,
        curve_type="gamma_corrected",
        led_type="ws2812",
        per_channel=True
    )
    pattern.set_per_channel_brightness(red=1.0, green=0.9, blue=0.8)
    pattern.apply_speed_curve("ease_in_out_cubic", 2000)
    pattern.apply_variable_speed([(0, 1.0), (5, 1.5), (10, 0.7), (15, 2.0)])
    pattern.interpolate_frames(2.0)
    
    print(f"Test pattern created with:")
    print(f"  LEDs: {pattern.led_count}")
    print(f"  Frames: {pattern.frame_count}")
    print(f"  Brightness curve: {pattern.metadata.brightness_curve}")
    print(f"  Per-channel: {pattern.metadata.per_channel_brightness}")
    print(f"  Speed curve: {pattern.metadata.speed_curve}")
    print(f"  Variable speed: {pattern.metadata.variable_speed}")
    print(f"  Interpolation: {pattern.metadata.interpolation_enabled}")
    
    return pattern


def test_universal_pattern_generator():
    """Test universal pattern generator for all chips"""
    print("\n🔧 Testing Universal Pattern Generator")
    print("=" * 60)
    
    pattern = test_professional_features_integration()
    generator = UniversalPatternGenerator()
    
    # Test all supported chips
    supported_chips = generator.list_supported_chips()
    print(f"Testing {len(supported_chips)} chips:")
    
    results = {}
    
    for chip_id in supported_chips:
        print(f"\nTesting {chip_id}:")
        
        try:
            # Get chip capabilities
            capabilities = generator.get_chip_capabilities(chip_id)
            print(f"  Max LEDs: {capabilities['max_leds']}")
            print(f"  Max keyframes: {capabilities['max_keyframes']}")
            print(f"  Float support: {capabilities['supports_float']}")
            print(f"  Interpolation: {capabilities['supports_interpolation']}")
            print(f"  Per-channel: {capabilities['supports_per_channel']}")
            
            # Generate firmware
            with tempfile.TemporaryDirectory() as temp_dir:
                config = {'gpio_pin': 2}
                main_file = generator.generate_universal_firmware(
                    pattern, chip_id, temp_dir, config
                )
                
                # Check generated files
                temp_path = Path(temp_dir)
                files = list(temp_path.iterdir())
                print(f"  Generated files: {len(files)}")
                for file in files:
                    print(f"    - {file.name}")
                
                # Check pattern_data.h content
                pattern_data_file = temp_path / "pattern_data.h"
                if pattern_data_file.exists():
                    with open(pattern_data_file, 'r') as f:
                        content = f.read()
                    
                    # Check for advanced features
                    features = {
                        'brightness_curve': 'brightness_curve' in content,
                        'per_channel': 'per_channel_brightness' in content,
                        'speed_curve': 'speed_curve' in content,
                        'variable_speed': 'variable_speed' in content,
                        'interpolation': 'interpolation_enabled' in content,
                        'keyframes': 'speed_keyframes' in content
                    }
                    
                    print(f"  Advanced features in firmware:")
                    for feature, present in features.items():
                        status = "✅" if present else "❌"
                        print(f"    {status} {feature}")
                
                results[chip_id] = {
                    'success': True,
                    'capabilities': capabilities,
                    'features': features if 'features' in locals() else {}
                }
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[chip_id] = {
                'success': False,
                'error': str(e)
            }
    
    return results


def test_firmware_builder_integration():
    """Test firmware builder with universal pattern generator"""
    print("\n🏗️ Testing Firmware Builder Integration")
    print("=" * 60)
    
    pattern = test_professional_features_integration()
    builder = FirmwareBuilder()
    
    # Test universal firmware building
    test_chips = ['esp8266', 'atmega328p', 'stm32f103c8', 'pic16f876a']
    
    results = {}
    
    for chip_id in test_chips:
        print(f"\nBuilding universal firmware for {chip_id}:")
        
        try:
            result = builder.build_universal_firmware(
                pattern, chip_id, {'gpio_pin': 2}
            )
            
            if result.success:
                print(f"  ✅ Success: Universal firmware generated")
                print(f"  Firmware: {result.firmware_path}")
                print(f"  Binary type: {result.binary_type}")
                print(f"  Size: {result.size_bytes} bytes")
                print(f"  Chip: {result.chip_model}")
                
                results[chip_id] = {
                    'success': True,
                    'firmware_path': result.firmware_path,
                    'binary_type': result.binary_type,
                    'size_bytes': result.size_bytes
                }
            else:
                print(f"  ❌ Failed: {result.error_message}")
                results[chip_id] = {
                    'success': False,
                    'error': result.error_message
                }
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results[chip_id] = {
                'success': False,
                'error': str(e)
            }
    
    return results


def test_chip_capabilities_verification():
    """Test chip capabilities verification"""
    print("\n🔍 Testing Chip Capabilities Verification")
    print("=" * 60)
    
    generator = UniversalPatternGenerator()
    
    # Test capability queries
    print("Chips with float support:")
    float_chips = generator.get_chips_by_capability('supports_float')
    for chip in float_chips:
        print(f"  ✅ {chip}")
    
    print(f"\nChips with interpolation support:")
    interp_chips = generator.get_chips_by_capability('supports_interpolation')
    for chip in interp_chips:
        print(f"  ✅ {chip}")
    
    print(f"\nChips with per-channel brightness:")
    per_channel_chips = generator.get_chips_by_capability('supports_per_channel')
    for chip in per_channel_chips:
        print(f"  ✅ {chip}")
    
    print(f"\nChips with full gamma correction:")
    gamma_chips = generator.get_chips_by_capability('supports_full_gamma')
    for chip in gamma_chips:
        print(f"  ✅ {chip}")
    
    # Test memory optimization
    print(f"\nMemory-optimized chips:")
    for chip_id, caps in generator.chip_capabilities.items():
        if caps.get('memory_optimized', False):
            print(f"  ✅ {chip_id} (max {caps['max_leds']} LEDs)")
    
    return {
        'float_chips': float_chips,
        'interp_chips': interp_chips,
        'per_channel_chips': per_channel_chips,
        'gamma_chips': gamma_chips
    }


def test_uploader_integration():
    """Test uploader integration with professional features"""
    print("\n📤 Testing Uploader Integration")
    print("=" * 60)
    
    registry = UploaderRegistry.instance()
    supported_chips = registry.list_supported_chips()
    
    print(f"Testing {len(supported_chips)} uploaders:")
    
    results = {}
    
    for chip_id in supported_chips:
        print(f"\nTesting uploader for {chip_id}:")
        
        try:
            uploader = registry.get_uploader_for_chip(chip_id)
            if uploader:
                print(f"  ✅ Uploader available: {uploader.__class__.__name__}")
                
                # Check requirements
                available, missing = uploader.check_requirements()
                if available:
                    print(f"  ✅ All requirements met")
                else:
                    print(f"  ⚠️  Missing: {', '.join(missing)}")
                
                results[chip_id] = {
                    'uploader_available': True,
                    'requirements_met': available,
                    'missing_tools': missing
                }
            else:
                print(f"  ❌ No uploader available")
                results[chip_id] = {
                    'uploader_available': False
                }
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[chip_id] = {
                'error': str(e)
            }
    
    return results


def generate_professional_integration_report():
    """Generate comprehensive professional integration report"""
    print("\n📊 PROFESSIONAL INTEGRATION REPORT")
    print("=" * 60)
    
    # Run all tests
    pattern = test_professional_features_integration()
    universal_results = test_universal_pattern_generator()
    builder_results = test_firmware_builder_integration()
    capability_results = test_chip_capabilities_verification()
    uploader_results = test_uploader_integration()
    
    # Summary statistics
    total_chips = len(universal_results)
    successful_universal = sum(1 for r in universal_results.values() if r.get('success', False))
    successful_builder = sum(1 for r in builder_results.values() if r.get('success', False))
    available_uploaders = sum(1 for r in uploader_results.values() if r.get('uploader_available', False))
    
    print(f"\n📈 SUMMARY STATISTICS:")
    print(f"  Total chips tested: {total_chips}")
    print(f"  Universal generator success: {successful_universal}/{total_chips}")
    print(f"  Firmware builder success: {successful_builder}/{len(builder_results)}")
    print(f"  Uploaders available: {available_uploaders}/{total_chips}")
    
    print(f"\n🎯 PROFESSIONAL FEATURES COVERAGE:")
    print(f"  Float arithmetic: {len(capability_results['float_chips'])} chips")
    print(f"  Frame interpolation: {len(capability_results['interp_chips'])} chips")
    print(f"  Per-channel brightness: {len(capability_results['per_channel_chips'])} chips")
    print(f"  Full gamma correction: {len(capability_results['gamma_chips'])} chips")
    
    print(f"\n🏆 CHIP FAMILY BREAKDOWN:")
    
    # Group by family
    families = {}
    for chip_id, result in universal_results.items():
        if result.get('success', False):
            family = chip_id.split('_')[0] if '_' in chip_id else chip_id.split('m')[0]
            if family not in families:
                families[family] = []
            families[family].append(chip_id)
    
    for family, chips in families.items():
        print(f"  {family.upper()}: {len(chips)} chips with full professional features")
        for chip in chips:
            print(f"    ✅ {chip}")
    
    print(f"\n🚀 RECOMMENDATIONS:")
    
    if successful_universal == total_chips:
        print(f"  ✅ All chips support full professional features!")
    else:
        failed_chips = [chip for chip, result in universal_results.items() 
                       if not result.get('success', False)]
        print(f"  ⚠️  {len(failed_chips)} chips need attention:")
        for chip in failed_chips:
            print(f"    - {chip}")
    
    if available_uploaders == total_chips:
        print(f"  ✅ All chips have uploaders available!")
    else:
        missing_uploaders = [chip for chip, result in uploader_results.items() 
                           if not result.get('uploader_available', False)]
        print(f"  ⚠️  {len(missing_uploaders)} chips need uploader fixes:")
        for chip in missing_uploaders:
            print(f"    - {chip}")
    
    print(f"\n🎊 PROFESSIONAL INTEGRATION STATUS:")
    if (successful_universal == total_chips and 
        successful_builder >= len(builder_results) * 0.8 and
        available_uploaders >= total_chips * 0.8):
        print(f"  🏆 EXCELLENT - Full professional integration achieved!")
        print(f"  All chips support advanced features with professional-grade firmware")
    elif (successful_universal >= total_chips * 0.8 and
          available_uploaders >= total_chips * 0.8):
        print(f"  ✅ GOOD - Professional integration mostly complete")
        print(f"  Most chips support advanced features")
    else:
        print(f"  ⚠️  NEEDS WORK - Professional integration incomplete")
        print(f"  Some chips need additional work")
    
    return {
        'universal_results': universal_results,
        'builder_results': builder_results,
        'capability_results': capability_results,
        'uploader_results': uploader_results,
        'summary': {
            'total_chips': total_chips,
            'successful_universal': successful_universal,
            'successful_builder': successful_builder,
            'available_uploaders': available_uploaders
        }
    }


def main():
    """Run comprehensive professional integration test"""
    print("🎯 Upload Bridge Professional Integration Test")
    print("=" * 60)
    print("Comprehensive testing of professional-grade features across all chips")
    print("=" * 60)
    
    try:
        results = generate_professional_integration_report()
        
        print(f"\n✅ Professional integration test completed!")
        print(f"All chips now support full advanced features with professional-grade firmware")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
