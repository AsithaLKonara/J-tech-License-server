#!/usr/bin/env python3
"""
Advanced Controls Demo - Quick demonstration of new features
Shows how to use the comprehensive brightness and speed control system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.pattern import Pattern, create_test_pattern
from firmware.enhanced_pattern_generator import EnhancedPatternGenerator


def demo_brightness_controls():
    """Demonstrate advanced brightness controls"""
    print("🎨 Advanced Brightness Controls Demo")
    print("=" * 50)
    
    # Create a test pattern
    pattern = create_test_pattern(led_count=20, frame_count=10)
    print(f"Created test pattern: {pattern.led_count} LEDs, {pattern.frame_count} frames")
    
    # 1. Basic brightness control
    print("\n1. Basic Brightness Control:")
    pattern.apply_advanced_brightness(brightness=0.7)
    first_pixel = pattern.frames[0].pixels[0]
    print(f"   Applied 70% brightness: {first_pixel}")
    
    # 2. Hardware-specific curves
    print("\n2. Hardware-Specific Brightness Curves:")
    curves = ["linear", "gamma_corrected", "logarithmic", "exponential", "s_curve"]
    
    for curve in curves:
        test_pattern = Pattern.from_dict(pattern.to_dict())
        test_pattern.apply_advanced_brightness(
            brightness=0.5, 
            curve_type=curve, 
            led_type="ws2812"
        )
        pixel = test_pattern.frames[0].pixels[0]
        print(f"   {curve:15}: {pixel}")
    
    # 3. Per-channel brightness
    print("\n3. Per-Channel Brightness Control:")
    pattern.set_per_channel_brightness(red=1.0, green=0.8, blue=0.6)
    pattern.apply_advanced_brightness(brightness=0.8, per_channel=True)
    pixel = pattern.frames[0].pixels[0]
    print(f"   Per-channel (R:1.0, G:0.8, B:0.6): {pixel}")


def demo_speed_controls():
    """Demonstrate advanced speed controls"""
    print("\n⚡ Advanced Speed Controls Demo")
    print("=" * 50)
    
    # Create a test pattern
    pattern = create_test_pattern(led_count=15, frame_count=8)
    print(f"Created test pattern: {pattern.frame_count} frames")
    
    # 1. Basic speed control
    print("\n1. Basic Speed Control:")
    original_duration = pattern.duration_ms
    pattern.scale_speed(2.0)  # 2x faster
    print(f"   Original duration: {original_duration}ms")
    print(f"   After 2x speed: {pattern.duration_ms}ms")
    
    # 2. Speed curves
    print("\n2. Speed Curves:")
    curves = ["linear", "ease_in_quad", "ease_out_quad", "ease_in_out_quad"]
    
    for curve in curves:
        test_pattern = Pattern.from_dict(pattern.to_dict())
        test_pattern.apply_speed_curve(curve, 2000)  # 2 second duration
        durations = [f.duration_ms for f in test_pattern.frames[:3]]
        print(f"   {curve:15}: First 3 frames {durations}ms")
    
    # 3. Variable speed with keyframes
    print("\n3. Variable Speed with Keyframes:")
    pattern.apply_variable_speed([
        (0, 1.0),   # Normal start
        (2, 2.0),   # Speed up 2x
        (4, 0.5),   # Slow down 0.5x
        (6, 1.5),   # Speed up 1.5x
    ])
    durations = [f.duration_ms for f in pattern.frames]
    print(f"   Frame durations: {durations}ms")
    
    # 4. Frame interpolation
    print("\n4. Frame Interpolation:")
    original_frames = pattern.frame_count
    pattern.interpolate_frames(2.0)  # Double frames
    print(f"   Original frames: {original_frames}")
    print(f"   After 2x interpolation: {pattern.frame_count}")


def demo_integration():
    """Demonstrate full integration"""
    print("\n🚀 Full Integration Demo")
    print("=" * 50)
    
    # Create a complex pattern
    pattern = create_test_pattern(led_count=25, frame_count=12)
    pattern.name = "Advanced Demo Pattern"
    
    print(f"Created pattern: {pattern.name}")
    print(f"  LEDs: {pattern.led_count}, Frames: {pattern.frame_count}")
    
    # Apply all advanced features
    print("\nApplying advanced features...")
    
    # Brightness features
    pattern.apply_advanced_brightness(
        brightness=0.85,
        curve_type="gamma_corrected",
        led_type="ws2812",
        per_channel=True
    )
    pattern.set_per_channel_brightness(red=1.0, green=0.9, blue=0.8)
    print("  ✅ Advanced brightness applied")
    
    # Speed features
    pattern.apply_speed_curve("ease_in_out_cubic", 4000)  # 4 second duration
    pattern.apply_variable_speed([
        (0, 1.0), (3, 1.8), (6, 0.6), (9, 1.2)
    ])
    pattern.interpolate_frames(1.5)
    print("  ✅ Advanced speed control applied")
    
    # Show results
    print(f"\nFinal pattern properties:")
    print(f"  Duration: {pattern.duration_ms / 1000.0:.2f}s")
    print(f"  Brightness curve: {pattern.metadata.brightness_curve}")
    print(f"  LED type: {pattern.metadata.led_type}")
    print(f"  Per-channel: {pattern.metadata.per_channel_brightness}")
    print(f"  Speed curve: {pattern.metadata.speed_curve}")
    print(f"  Variable speed: {pattern.metadata.variable_speed}")
    print(f"  Interpolation: {pattern.metadata.interpolation_enabled}")
    
    # Generate enhanced firmware data
    print(f"\nGenerating enhanced firmware data...")
    generator = EnhancedPatternGenerator()
    
    # Estimate memory usage
    memory = generator.estimate_memory_usage(pattern)
    print(f"  Memory usage: {memory['total']} bytes")
    
    # Generate pattern data header
    output_file = "demo_pattern_data.h"
    generator.generate_pattern_data_h(pattern, output_file, {"gpio_pin": 2})
    print(f"  Generated: {output_file}")
    
    # Show sample data
    print(f"\nSample pattern data:")
    sample_frame = pattern.frames[3]
    print(f"  Frame 3 duration: {sample_frame.duration_ms}ms")
    print(f"  First 3 pixels: {sample_frame.pixels[:3]}")


def demo_gui_usage():
    """Demonstrate GUI usage"""
    print("\n🖥️ GUI Usage Demo")
    print("=" * 50)
    
    print("To use the advanced controls in the GUI:")
    print("\n1. Launch Upload Bridge:")
    print("   python main.py")
    
    print("\n2. Load your pattern:")
    print("   File > Open Pattern > Select your .bin or .ledproj file")
    
    print("\n3. Use Advanced Brightness Controller:")
    print("   - Basic tab: Adjust brightness slider and LED type")
    print("   - Advanced tab: Select brightness curve and visualize")
    print("   - Per-Channel tab: Enable per-channel control")
    
    print("\n4. Use Advanced Speed Controller:")
    print("   - Basic tab: Adjust speed and duration")
    print("   - Variable Speed tab: Add keyframes for dynamic speed")
    print("   - Interpolation tab: Enable frame interpolation")
    print("   - Speed Curves tab: Select easing functions")
    
    print("\n5. Preview and Flash:")
    print("   - Watch real-time preview in LED simulator")
    print("   - Go to Flash tab to upload to your device")
    
    print("\n6. Save Project:")
    print("   - File > Save Project to preserve all settings")


def main():
    """Run the complete demo"""
    print("🎛️ Upload Bridge Advanced Controls Demo")
    print("=" * 60)
    print("Demonstrating comprehensive brightness and speed control features")
    print("=" * 60)
    
    try:
        demo_brightness_controls()
        demo_speed_controls()
        demo_integration()
        demo_gui_usage()
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("\n🎉 Advanced controls are ready to use!")
        print("\nNext steps:")
        print("  1. Run: python test_advanced_controls.py")
        print("  2. Launch: python main.py")
        print("  3. Load your pattern and explore the controls")
        print("  4. Check ADVANCED_CONTROLS_GUIDE.md for detailed usage")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())













