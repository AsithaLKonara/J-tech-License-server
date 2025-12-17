"""
Test script to verify radial_rays mapping fix.

This script verifies that:
1. LED 0 maps to row 0 (top/outer circle)
2. LED 3 maps to row 3 (bottom/inner circle)
3. Position generation uses correct radius calculation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.pattern import PatternMetadata
from core.mapping.circular_mapper import CircularMapper


def test_radial_rays_mapping():
    """Test that radial_rays mapping table is correct."""
    print("=" * 60)
    print("Testing Radial Rays Mapping Fix")
    print("=" * 60)
    
    # Create metadata for 4 rows × 6 columns radial_rays layout
    metadata = PatternMetadata(
        width=6,   # columns = ray count
        height=4,   # rows = LEDs per ray
        layout_type="radial_rays",
        ray_count=6,
        leds_per_ray=4
    )
    
    # Generate mapping table
    mapping_table = CircularMapper.generate_mapping_table(metadata)
    
    print(f"\nMapping table generated: {len(mapping_table)} LEDs")
    print(f"Expected: 6 rays × 4 LEDs = 24 LEDs")
    
    # Verify LED 0 maps to row 0 (top/outer)
    led_0_x, led_0_y = mapping_table[0]
    print(f"\nLED 0 → grid({led_0_x}, {led_0_y})")
    print(f"Expected: grid(0, 0) - Row 0 (top/outer)")
    
    if led_0_x == 0 and led_0_y == 0:
        print("✅ LED 0 correctly maps to row 0 (top/outer)")
    else:
        print(f"❌ ERROR: LED 0 maps to ({led_0_x}, {led_0_y}), expected (0, 0)")
        return False
    
    # Verify LED 3 maps to row 3 (bottom/inner)
    led_3_x, led_3_y = mapping_table[3]
    print(f"\nLED 3 → grid({led_3_x}, {led_3_y})")
    print(f"Expected: grid(0, 3) - Row 3 (bottom/inner)")
    
    if led_3_x == 0 and led_3_y == 3:
        print("✅ LED 3 correctly maps to row 3 (bottom/inner)")
    else:
        print(f"❌ ERROR: LED 3 maps to ({led_3_x}, {led_3_y}), expected (0, 3)")
        return False
    
    # Verify first ray (LEDs 0-3) maps to rows 0-3
    print(f"\nFirst ray (LEDs 0-3):")
    for led_idx in range(4):
        grid_x, grid_y = mapping_table[led_idx]
        print(f"  LED {led_idx} → grid({grid_x}, {grid_y}) = row {grid_y}")
        if grid_x != 0:
            print(f"  ❌ ERROR: LED {led_idx} should be in ray 0 (col 0)")
            return False
        if grid_y != led_idx:
            print(f"  ❌ ERROR: LED {led_idx} should map to row {led_idx}")
            return False
    
    print("✅ First ray correctly maps to rows 0-3")
    
    # Verify second ray (LEDs 4-7) maps to rows 0-3
    print(f"\nSecond ray (LEDs 4-7):")
    for led_idx in range(4, 8):
        grid_x, grid_y = mapping_table[led_idx]
        expected_row = led_idx - 4
        print(f"  LED {led_idx} → grid({grid_x}, {grid_y}) = row {grid_y}")
        if grid_x != 1:
            print(f"  ❌ ERROR: LED {led_idx} should be in ray 1 (col 1)")
            return False
        if grid_y != expected_row:
            print(f"  ❌ ERROR: LED {led_idx} should map to row {expected_row}")
            return False
    
    print("✅ Second ray correctly maps to rows 0-3")
    
    return True


def test_position_generation():
    """Test that position generation uses correct radius calculation."""
    print("\n" + "=" * 60)
    print("Testing Position Generation")
    print("=" * 60)
    
    metadata = PatternMetadata(
        width=6,
        height=4,
        layout_type="radial_rays",
        ray_count=6,
        leds_per_ray=4
    )
    
    # Generate positions
    center_x, center_y = 100.0, 100.0
    max_radius = 50.0
    
    positions = CircularMapper.generate_led_positions_for_preview(
        metadata=metadata,
        center_x=center_x,
        center_y=center_y,
        max_radius=max_radius
    )
    
    print(f"\nGenerated {len(positions)} positions")
    
    # Calculate expected radii
    outer_radius = max_radius * 0.8  # 40.0
    inner_radius = outer_radius * 0.15  # 6.0
    radius_delta = (outer_radius - inner_radius) / 3  # ~11.33
    
    print(f"\nExpected radii:")
    print(f"  Outer radius (row 0): {outer_radius:.2f}")
    print(f"  Inner radius (row 3): {inner_radius:.2f}")
    print(f"  Radius delta: {radius_delta:.2f}")
    
    # Check first ray positions
    print(f"\nFirst ray positions (LEDs 0-3):")
    for led_idx in range(4):
        x, y = positions[led_idx]
        # Calculate distance from center
        import math
        distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
        
        # Expected radius for this LED
        row = led_idx  # LED 0 → row 0, LED 3 → row 3
        inverted_row = 4 - 1 - row  # row 0 → 3, row 3 → 0
        expected_radius = inner_radius + radius_delta * inverted_row
        
        print(f"  LED {led_idx} (row {row}): distance={distance:.2f}, expected={expected_radius:.2f}")
        
        # Allow small tolerance for floating point
        if abs(distance - expected_radius) > 0.1:
            print(f"    ❌ ERROR: Distance {distance:.2f} doesn't match expected {expected_radius:.2f}")
            return False
    
    print("✅ Position generation uses correct radius calculation")
    
    # Verify LED 0 (row 0) has larger radius than LED 3 (row 3)
    led_0_pos = positions[0]
    led_3_pos = positions[3]
    import math
    radius_0 = math.sqrt((led_0_pos[0] - center_x)**2 + (led_0_pos[1] - center_y)**2)
    radius_3 = math.sqrt((led_3_pos[0] - center_x)**2 + (led_3_pos[1] - center_y)**2)
    
    print(f"\nRadius comparison:")
    print(f"  LED 0 (row 0, outer): {radius_0:.2f}")
    print(f"  LED 3 (row 3, inner): {radius_3:.2f}")
    
    if radius_0 > radius_3:
        print("✅ LED 0 has larger radius than LED 3 (correct: outer > inner)")
        return True
    else:
        print("❌ ERROR: LED 0 should have larger radius than LED 3")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RADIAL RAYS FIX VERIFICATION")
    print("=" * 60)
    
    mapping_ok = test_radial_rays_mapping()
    position_ok = test_position_generation()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Mapping table: {'✅ PASS' if mapping_ok else '❌ FAIL'}")
    print(f"Position generation: {'✅ PASS' if position_ok else '❌ FAIL'}")
    
    if mapping_ok and position_ok:
        print("\n✅ All tests passed! Fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)
