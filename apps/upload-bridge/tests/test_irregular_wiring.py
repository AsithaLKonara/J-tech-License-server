"""
Automated tests for irregular matrix wiring system.

Tests that wiring only traverses active cells for irregular matrices.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.wiring_mapper import WiringMapper
from core.pattern import PatternMetadata
from core.mapping.irregular_shape_mapper import IrregularShapeMapper


def create_test_irregular_metadata(width=8, height=8, pattern_type="cross"):
    """Create test irregular matrix metadata."""
    metadata = PatternMetadata(
        width=width,
        height=height,
        layout_type="irregular",
        irregular_shape_enabled=True
    )
    
    if pattern_type == "cross":
        # Cross pattern (center row and column inactive)
        active_cells = []
        center_row = height // 2
        center_col = width // 2
        
        for y in range(height):
            for x in range(width):
                if x != center_col and y != center_row:
                    active_cells.append((x, y))
    
    elif pattern_type == "border":
        # Border pattern (outer cells inactive)
        active_cells = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                active_cells.append((x, y))
    
    elif pattern_type == "sparse":
        # Sparse pattern (few scattered cells)
        import random
        random.seed(42)
        all_cells = [(x, y) for y in range(height) for x in range(width)]
        active_cells = random.sample(all_cells, min(8, len(all_cells)))
    
    elif pattern_type == "single":
        # Single cell
        center_x = width // 2
        center_y = height // 2
        active_cells = [(center_x, center_y)]
    
    else:
        active_cells = [(x, y) for y in range(height) for x in range(width)]
    
    metadata.active_cell_coordinates = active_cells
    return metadata


def test_wiring_only_active_cells(wiring_mode, data_in_corner, pattern_type="cross"):
    """Test that wiring only includes active cells."""
    metadata = create_test_irregular_metadata(8, 8, pattern_type)
    active_cells_set = set(metadata.active_cell_coordinates)
    
    mapper = WiringMapper(
        width=metadata.width,
        height=metadata.height,
        wiring_mode=wiring_mode,
        data_in_corner=data_in_corner,
        active_cell_coordinates=metadata.active_cell_coordinates
    )
    
    mapping = mapper._build_mapping_table()
    
    # Convert mapping indices back to (x, y) coordinates
    wiring_path = []
    for design_idx in mapping:
        x = design_idx % metadata.width
        y = design_idx // metadata.width
        wiring_path.append((x, y))
    
    # Verify all cells in wiring path are active
    all_active = True
    inactive_in_path = []
    for x, y in wiring_path:
        if (x, y) not in active_cells_set:
            inactive_in_path.append((x, y))
            all_active = False
    
    if not all_active:
        print(f"    FAIL: Wiring path includes inactive cells: {inactive_in_path[:5]}")
        return False
    
    # Verify wiring path length matches active cell count
    if len(wiring_path) != len(active_cells_set):
        print(f"    FAIL: Wiring path length {len(wiring_path)} != active cell count {len(active_cells_set)}")
        return False
    
    return True


def test_wiring_modes_all_corners():
    """Test all wiring modes with all corners."""
    print("\n=== Test: Wiring Modes with All Corners ===")
    
    wiring_modes = ["Row-major", "Serpentine", "Column-major", "Column-serpentine"]
    corners = ["LT", "LB", "RT", "RB"]
    pattern_types = ["cross", "border", "sparse", "single"]
    
    all_passed = True
    total_tests = 0
    passed_tests = 0
    
    for pattern_type in pattern_types:
        print(f"\n  Pattern: {pattern_type}")
        for wiring_mode in wiring_modes:
            for corner in corners:
                total_tests += 1
                test_name = f"{wiring_mode} × {corner}"
                passed = test_wiring_only_active_cells(wiring_mode, corner, pattern_type)
                
                if passed:
                    passed_tests += 1
                    print(f"    PASS: {test_name}")
                else:
                    all_passed = False
                    print(f"    FAIL: {test_name}")
    
    print(f"\n  Results: {passed_tests}/{total_tests} tests passed")
    
    if all_passed:
        print("  ✓ All wiring mode tests passed")
    else:
        print("  ✗ Some wiring mode tests failed")
    
    return all_passed


def test_wiring_order_preservation():
    """Test that wiring order is preserved for active cells."""
    print("\n=== Test: Wiring Order Preservation ===")
    
    metadata = create_test_irregular_metadata(8, 8, "cross")
    
    # Test Row-major LT
    mapper = WiringMapper(
        width=metadata.width,
        height=metadata.height,
        wiring_mode="Row-major",
        data_in_corner="LT",
        active_cell_coordinates=metadata.active_cell_coordinates
    )
    
    mapping = mapper._build_mapping_table()
    
    # Convert to (x, y) coordinates
    wiring_path = []
    for design_idx in mapping:
        x = design_idx % metadata.width
        y = design_idx // metadata.width
        wiring_path.append((x, y))
    
    # For Row-major LT, should traverse rows left-to-right, top-to-bottom
    # But only active cells
    all_passed = True
    
    # Check that rows are traversed in order (top to bottom)
    prev_y = -1
    for x, y in wiring_path:
        if y < prev_y:
            print(f"    FAIL: Row order violated - y={y} after y={prev_y}")
            all_passed = False
            break
        prev_y = y
    
    if all_passed:
        print("  ✓ Wiring order preserved correctly")
    else:
        print("  ✗ Wiring order violated")
    
    return all_passed


def test_regular_matrix_regression():
    """Test that regular matrices still work (regression test)."""
    print("\n=== Test: Regular Matrix Regression ===")
    
    # Create regular matrix (all cells active)
    metadata = PatternMetadata(width=8, height=8)
    
    # Test with and without active_cell_coordinates
    all_passed = True
    
    # Without active_cell_coordinates (regular matrix)
    mapper1 = WiringMapper(
        width=metadata.width,
        height=metadata.height,
        wiring_mode="Row-major",
        data_in_corner="LT"
    )
    mapping1 = mapper1._build_mapping_table()
    
    # With all cells as active_cell_coordinates (should be same)
    all_cells = [(x, y) for y in range(8) for x in range(8)]
    mapper2 = WiringMapper(
        width=metadata.width,
        height=metadata.height,
        wiring_mode="Row-major",
        data_in_corner="LT",
        active_cell_coordinates=all_cells
    )
    mapping2 = mapper2._build_mapping_table()
    
    if mapping1 == mapping2:
        print("  ✓ Regular matrix behavior unchanged")
    else:
        print("  ✗ Regular matrix behavior changed (regression!)")
        all_passed = False
    
    # Verify mapping length
    if len(mapping1) == 64:
        print("  ✓ Regular matrix mapping length correct (64 cells)")
    else:
        print(f"  ✗ Regular matrix mapping length incorrect: {len(mapping1)} (expected 64)")
        all_passed = False
    
    return all_passed


def main():
    """Run all irregular wiring tests."""
    print("=" * 70)
    print("Irregular Matrix Wiring System Tests")
    print("=" * 70)
    
    results = []
    
    results.append(("Wiring Modes All Corners", test_wiring_modes_all_corners()))
    results.append(("Wiring Order Preservation", test_wiring_order_preservation()))
    results.append(("Regular Matrix Regression", test_regular_matrix_regression()))
    
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
