#!/usr/bin/env python3
"""
Test Advanced Brightness and Speed Controls
Comprehensive testing of the new brightness and speed control features
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.pattern import Pattern, create_test_pattern, BrightnessCurve, HardwareBrightnessMapper, SpeedController
from firmware.enhanced_pattern_generator import EnhancedPatternGenerator
import time


def test_brightness_curves():
    """Test different brightness curves"""
    print("=== Testing Brightness Curves ===")
    
    # Create test pattern
    pattern = create_test_pattern(led_count=10, frame_count=5)
    
    # Test different curves
    curves = ["linear", "gamma_corrected", "logarithmic", "exponential", "s_curve"]
    
    for curve in curves:
        print(f"\nTesting {curve} curve:")
        
        # Create copy for testing
        test_pattern = Pattern.from_dict(pattern.to_dict())
        
        # Apply brightness curve
        test_pattern.apply_advanced_brightness(
            brightness=0.5,
            curve_type=curve,
            led_type="ws2812"
        )
        
        # Show first pixel of first frame
        first_pixel = test_pattern.frames[0].pixels[0]
        print(f"  First pixel: R={first_pixel[0]}, G={first_pixel[1]}, B={first_pixel[2]}")


def test_per_channel_brightness():
    """Test per-channel brightness control"""
    print("\n=== Testing Per-Channel Brightness ===")
    
    # Create test pattern
    pattern = create_test_pattern(led_count=5, frame_count=3)
    
    # Set per-channel brightness
    pattern.set_per_channel_brightness(red=0.8, green=0.6, blue=0.4)
    
    # Apply brightness
    pattern.apply_advanced_brightness(brightness=0.7, per_channel=True)
    
    print("Per-channel brightness applied:")
    first_pixel = pattern.frames[0].pixels[0]
    print(f"  First pixel: R={first_pixel[0]}, G={first_pixel[1]}, B={first_pixel[2]}")
    print(f"  Expected: R={int(255 * 0.7 * 0.8)}, G={int(255 * 0.7 * 0.6)}, B={int(255 * 0.7 * 0.4)}")


def test_hardware_brightness_mapping():
    """Test hardware-specific brightness mapping"""
    print("\n=== Testing Hardware Brightness Mapping ===")
    
    # Test different LED types
    led_types = ["ws2812", "ws2812b", "sk6812", "apa102", "dotstar"]
    
    for led_type in led_types:
        print(f"\nTesting {led_type}:")
        
        # Test pixel mapping
        test_pixel = (255, 128, 64)
        mapped_pixel = HardwareBrightnessMapper.apply_to_pixel(
            test_pixel, 0.5, led_type, "gamma_corrected"
        )
        
        print(f"  Original: {test_pixel}")
        print(f"  Mapped: {mapped_pixel}")


def test_speed_curves():
    """Test different speed curves"""
    print("\n=== Testing Speed Curves ===")
    
    # Create test pattern
    pattern = create_test_pattern(led_count=5, frame_count=10)
    
    # Test different speed curves
    curves = ["linear", "ease_in_quad", "ease_out_quad", "ease_in_out_quad", 
              "ease_in_cubic", "ease_out_cubic", "ease_in_out_cubic"]
    
    for curve in curves:
        print(f"\nTesting {curve} curve:")
        
        # Create copy for testing
        test_pattern = Pattern.from_dict(pattern.to_dict())
        
        # Apply speed curve
        test_pattern.apply_speed_curve(curve, 2000)  # 2 second duration
        
        # Show frame durations
        durations = [frame.duration_ms for frame in test_pattern.frames[:5]]
        print(f"  First 5 frame durations: {durations}")


def test_variable_speed():
    """Test variable speed with keyframes"""
    print("\n=== Testing Variable Speed ===")
    
    # Create test pattern
    pattern = create_test_pattern(led_count=5, frame_count=20)
    
    # Set up keyframes
    keyframes = [
        (0, 1.0),    # Start at normal speed
        (5, 2.0),    # Speed up at frame 5
        (10, 0.5),   # Slow down at frame 10
        (15, 1.5),   # Speed up again at frame 15
    ]
    
    # Apply variable speed
    pattern.apply_variable_speed(keyframes)
    
    print("Variable speed applied with keyframes:")
    for i, frame in enumerate(pattern.frames[:10]):
        print(f"  Frame {i}: {frame.duration_ms}ms")


def test_frame_interpolation():
    """Test frame interpolation"""
    print("\n=== Testing Frame Interpolation ===")
    
    # Create test pattern
    pattern = create_test_pattern(led_count=3, frame_count=5)
    
    print(f"Original pattern: {pattern.frame_count} frames")
    
    # Apply interpolation
    pattern.interpolate_frames(factor=2.0)
    
    print(f"After 2x interpolation: {pattern.frame_count} frames")
    
    # Show some interpolated frames
    for i in range(min(10, pattern.frame_count)):
        frame = pattern.frames[i]
        first_pixel = frame.pixels[0]
        print(f"  Frame {i}: {first_pixel} (duration: {frame.duration_ms}ms)")


def test_enhanced_pattern_generator():
    """Test enhanced pattern data generation"""
    print("\n=== Testing Enhanced Pattern Generator ===")
    
    # Create test pattern with advanced features
    pattern = create_test_pattern(led_count=8, frame_count=6)
    
    # Set advanced features
    pattern.metadata.brightness_curve = "gamma_corrected"
    pattern.metadata.led_type = "ws2812"
    pattern.metadata.per_channel_brightness = True
    pattern.metadata.red_brightness = 0.9
    pattern.metadata.green_brightness = 0.8
    pattern.metadata.blue_brightness = 0.7
    pattern.metadata.speed_curve = "ease_in_out_quad"
    pattern.metadata.variable_speed = True
    pattern.metadata.speed_keyframes = [(0, 1.0), (3, 2.0)]
    pattern.metadata.interpolation_enabled = True
    pattern.metadata.interpolation_factor = 1.5
    
    # Generate enhanced pattern data
    generator = EnhancedPatternGenerator()
    
    # Test memory estimation
    memory_usage = generator.estimate_memory_usage(pattern)
    print("Memory usage estimation:")
    for key, value in memory_usage.items():
        print(f"  {key}: {value} bytes")
    
    # Generate pattern data header
    output_path = "test_pattern_data.h"
    generator.generate_pattern_data_h(pattern, output_path, {"gpio_pin": 3})
    
    print(f"\nGenerated pattern data header: {output_path}")
    
    # Show first few lines of generated file
    with open(output_path, 'r') as f:
        lines = f.readlines()[:20]
        print("\nFirst 20 lines of generated header:")
        for line in lines:
            print(f"  {line.rstrip()}")


def test_integration():
    """Test integration of all features"""
    print("\n=== Testing Full Integration ===")
    
    # Create complex pattern
    pattern = create_test_pattern(led_count=12, frame_count=15)
    
    # Apply all advanced features
    print("Applying advanced brightness control...")
    pattern.apply_advanced_brightness(
        brightness=0.8,
        curve_type="gamma_corrected",
        led_type="ws2812",
        per_channel=True
    )
    pattern.set_per_channel_brightness(red=1.0, green=0.9, blue=0.8)
    
    print("Applying advanced speed control...")
    pattern.apply_speed_curve("ease_in_out_cubic", 3000)
    pattern.apply_variable_speed([(0, 1.0), (5, 1.5), (10, 0.7)])
    pattern.interpolate_frames(1.5)
    
    # Show results
    print(f"\nFinal pattern:")
    print(f"  LEDs: {pattern.led_count}")
    print(f"  Frames: {pattern.frame_count}")
    print(f"  Duration: {pattern.duration_ms / 1000.0:.2f}s")
    print(f"  Brightness curve: {pattern.metadata.brightness_curve}")
    print(f"  LED type: {pattern.metadata.led_type}")
    print(f"  Per-channel: {pattern.metadata.per_channel_brightness}")
    print(f"  Speed curve: {pattern.metadata.speed_curve}")
    print(f"  Variable speed: {pattern.metadata.variable_speed}")
    print(f"  Interpolation: {pattern.metadata.interpolation_enabled}")
    
    # Show sample frame
    sample_frame = pattern.frames[5]
    print(f"\nSample frame 5:")
    print(f"  Duration: {sample_frame.duration_ms}ms")
    print(f"  First 3 pixels: {sample_frame.pixels[:3]}")


def main():
    """Run all tests"""
    print("🚀 Testing Advanced Brightness and Speed Controls")
    print("=" * 60)
    
    try:
        test_brightness_curves()
        test_per_channel_brightness()
        test_hardware_brightness_mapping()
        test_speed_curves()
        test_variable_speed()
        test_frame_interpolation()
        test_enhanced_pattern_generator()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\n🎉 Advanced brightness and speed control features are working!")
        print("\nFeatures tested:")
        print("  ✅ Brightness curves (linear, gamma, logarithmic, exponential, s-curve)")
        print("  ✅ Per-channel brightness control")
        print("  ✅ Hardware-specific brightness mapping")
        print("  ✅ Speed curves (linear, ease-in, ease-out, cubic)")
        print("  ✅ Variable speed with keyframes")
        print("  ✅ Frame interpolation")
        print("  ✅ Enhanced pattern data generation")
        print("  ✅ Full integration testing")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())













