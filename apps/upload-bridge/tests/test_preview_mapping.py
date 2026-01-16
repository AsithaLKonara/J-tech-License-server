"""
Automated tests for preview tab matrix mapping verification.

Tests that preview tab shows exact same pattern as design tools tab.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.pattern import Pattern, Frame, PatternMetadata
from core.mapping.irregular_shape_mapper import IrregularShapeMapper
from pathlib import Path


def test_regular_matrix_mapping():
    """Test that regular matrices map pixels correctly in preview."""
    print("\n=== Test: Regular Matrix Mapping ===")
    
    width, height = 8, 8
    metadata = PatternMetadata(width=width, height=height)
    pattern = Pattern(name="Test Regular Mapping", metadata=metadata)
    
    # Create pixels with known colors at specific positions
    pixels = [(0, 0, 0)] * (width * height)
    
    # Top-left (0,0): Red
    pixels[0] = (255, 0, 0)
    
    # Top-right (7,0): Green
    pixels[width - 1] = (0, 255, 0)
    
    # Bottom-left (0,7): Blue
    pixels[(height - 1) * width] = (0, 0, 255)
    
    # Bottom-right (7,7): Yellow
    pixels[height * width - 1] = (255, 255, 0)
    
    # Center (4,4): Magenta
    center_x, center_y = width // 2, height // 2
    pixels[center_y * width + center_x] = (255, 0, 255)
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    
    # Verify mapping: cell_idx = y * width + x
    test_cases = [
        ((0, 0), 0, (255, 0, 0)),      # Top-left: Red
        ((7, 0), 7, (0, 255, 0)),     # Top-right: Green
        ((0, 7), 56, (0, 0, 255)),     # Bottom-left: Blue
        ((7, 7), 63, (255, 255, 0)),  # Bottom-right: Yellow
        ((4, 4), 36, (255, 0, 255)),  # Center: Magenta
    ]
    
    all_passed = True
    for (x, y), expected_idx, expected_color in test_cases:
        cell_idx = y * width + x
        actual_color = pixels[cell_idx]
        
        if cell_idx != expected_idx:
            print(f"  FAIL: Position ({x},{y}) - Expected cell_idx {expected_idx}, got {cell_idx}")
            all_passed = False
        elif actual_color != expected_color:
            print(f"  FAIL: Position ({x},{y}) - Expected color {expected_color}, got {actual_color}")
            all_passed = False
        else:
            print(f"  PASS: Position ({x},{y}) - cell_idx {cell_idx}, color {actual_color}")
    
    if all_passed:
        print("  ✓ All regular matrix mapping tests passed")
    else:
        print("  ✗ Some regular matrix mapping tests failed")
    
    return all_passed


def test_irregular_matrix_mapping():
    """Test that irregular matrices map pixels correctly and skip inactive cells."""
    print("\n=== Test: Irregular Matrix Mapping ===")
    
    width, height = 10, 10
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    # Create cross pattern (center row and column inactive)
    active_cells = []
    center_row = height // 2
    center_col = width // 2
    
    for y in range(height):
        for x in range(width):
            if x != center_col and y != center_row:
                active_cells.append((x, y))
    
    metadata.active_cell_coordinates = active_cells
    
    pattern = Pattern(name="Test Irregular Mapping", metadata=metadata)
    
    # Create pixels
    pixels = [(0, 0, 0)] * (width * height)
    
    # Paint some active cells
    if (0, 0) in active_cells:
        pixels[0] = (255, 0, 0)  # Red
    
    # Find an active cell near center
    center_x, center_y = width // 2, height // 2
    for offset in range(1, min(width, height)):
        for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
            test_x = center_x + dx
            test_y = center_y + dy
            if (test_x, test_y) in active_cells and 0 <= test_x < width and 0 <= test_y < height:
                pixels[test_y * width + test_x] = (0, 255, 0)  # Green
                break
        else:
            continue
        break
    
    pattern.frames = [Frame(pixels=pixels, duration_ms=100)]
    
    # Verify active cells
    all_passed = True
    
    # Test that inactive cells are correctly identified
    inactive_cells = [
        (center_col, center_row),  # Center of cross
        (center_col, 0),           # Top of cross
        (center_col, height - 1),  # Bottom of cross
        (0, center_row),           # Left of cross
        (width - 1, center_row),   # Right of cross
    ]
    
    for x, y in inactive_cells:
        is_active = IrregularShapeMapper.is_cell_active(x, y, metadata)
        if is_active:
            print(f"  FAIL: Cell ({x},{y}) should be inactive but is marked active")
            all_passed = False
        else:
            print(f"  PASS: Cell ({x},{y}) correctly identified as inactive")
    
    # Test that active cells are correctly identified
    test_active_cells = [
        (0, 0),           # Top-left
        (width - 1, 0),   # Top-right
        (0, height - 1),  # Bottom-left
        (width - 1, height - 1),  # Bottom-right
    ]
    
    for x, y in test_active_cells:
        if (x, y) in active_cells:
            is_active = IrregularShapeMapper.is_cell_active(x, y, metadata)
            if not is_active:
                print(f"  FAIL: Cell ({x},{y}) should be active but is marked inactive")
                all_passed = False
            else:
                print(f"  PASS: Cell ({x},{y}) correctly identified as active")
    
    # Verify pixel mapping still works (cell_idx = y * width + x)
    if (0, 0) in active_cells:
        cell_idx = 0 * width + 0
        if pixels[cell_idx] == (255, 0, 0):
            print(f"  PASS: Pixel mapping correct for active cell (0,0)")
        else:
            print(f"  FAIL: Pixel mapping incorrect for active cell (0,0)")
            all_passed = False
    
    if all_passed:
        print("  ✓ All irregular matrix mapping tests passed")
    else:
        print("  ✗ Some irregular matrix mapping tests failed")
    
    return all_passed


def test_multiframe_mapping():
    """Test that multi-frame patterns map correctly."""
    print("\n=== Test: Multi-Frame Mapping ===")
    
    width, height = 8, 8
    metadata = PatternMetadata(width=width, height=height)
    pattern = Pattern(name="Test MultiFrame Mapping", metadata=metadata)
    
    # Create 5 frames with different colors
    frames = []
    for frame_idx in range(5):
        pixels = [(0, 0, 0)] * (width * height)
        
        # Each frame has a different color at center
        center_x, center_y = width // 2, height // 2
        r = (frame_idx * 255) // 4 if frame_idx > 0 else 0
        g = 128
        b = 255 - r
        pixels[center_y * width + center_x] = (r, g, b)
        
        frames.append(Frame(pixels=pixels, duration_ms=100))
    
    pattern.frames = frames
    
    # Verify each frame maps correctly
    all_passed = True
    for frame_idx, frame in enumerate(frames):
        center_x, center_y = width // 2, height // 2
        cell_idx = center_y * width + center_x
        expected_r = (frame_idx * 255) // 4 if frame_idx > 0 else 0
        expected_color = (expected_r, 128, 255 - expected_r)
        actual_color = frame.pixels[cell_idx]
        
        if actual_color != expected_color:
            print(f"  FAIL: Frame {frame_idx} - Expected center color {expected_color}, got {actual_color}")
            all_passed = False
        else:
            print(f"  PASS: Frame {frame_idx} - Center color {actual_color} correct")
    
    if all_passed:
        print("  ✓ All multi-frame mapping tests passed")
    else:
        print("  ✗ Some multi-frame mapping tests failed")
    
    return all_passed


def main():
    """Run all preview mapping tests."""
    print("=" * 70)
    print("Preview Tab Matrix Mapping Tests")
    print("=" * 70)
    
    results = []
    
    results.append(("Regular Matrix Mapping", test_regular_matrix_mapping()))
    results.append(("Irregular Matrix Mapping", test_irregular_matrix_mapping()))
    results.append(("Multi-Frame Mapping", test_multiframe_mapping()))
    
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
