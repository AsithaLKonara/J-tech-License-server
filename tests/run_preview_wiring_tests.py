"""
Comprehensive test runner for preview mapping and irregular wiring.

This script runs automated tests and provides manual testing instructions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path


def run_automated_tests():
    """Run automated test suites."""
    print("=" * 70)
    print("Running Automated Tests")
    print("=" * 70)
    
    results = []
    
    # Import and run preview mapping tests
    try:
        from tests.test_preview_mapping import main as test_preview_main
        print("\n1. Running Preview Mapping Tests...")
        result = test_preview_main()
        results.append(("Preview Mapping", result == 0))
    except Exception as e:
        print(f"  ERROR: Failed to run preview mapping tests: {e}")
        results.append(("Preview Mapping", False))
    
    # Import and run irregular wiring tests
    try:
        from tests.test_irregular_wiring import main as test_wiring_main
        print("\n2. Running Irregular Wiring Tests...")
        result = test_wiring_main()
        results.append(("Irregular Wiring", result == 0))
    except Exception as e:
        print(f"  ERROR: Failed to run irregular wiring tests: {e}")
        results.append(("Irregular Wiring", False))
    
    return results


def print_manual_testing_instructions():
    """Print manual testing instructions."""
    print("\n" + "=" * 70)
    print("Manual Testing Instructions")
    print("=" * 70)
    
    print("""
To complete comprehensive testing, please perform the following manual tests:

1. PREVIEW TAB MATRIX MAPPING VERIFICATION
   ----------------------------------------
   a) Regular Matrices:
      - Create 8×8 regular matrix in design tools
      - Paint distinct colors at corners and center:
        * Top-left (0,0): Red
        * Top-right (7,0): Green
        * Bottom-left (0,7): Blue
        * Bottom-right (7,7): Yellow
        * Center (4,4): Magenta
      - Switch to preview tab
      - Verify: Pixels appear at exact same positions with exact same colors
      - Repeat for 16×16 and 32×8 matrices
   
   b) Irregular Matrices:
      - Create 10×10 irregular matrix
      - Enable irregular shape mode
      - Create cross pattern (center row/column inactive)
      - Paint colors on active cells only
      - Switch to preview tab
      - Verify: Active cells show correct colors, inactive cells are transparent (not black)
      - Test with border pattern and checkerboard pattern

2. IRREGULAR MATRIX WIRING SYSTEM
   -------------------------------
   For each wiring mode (Row-major, Serpentine, Column-major, Column-serpentine):
     For each data-in corner (LT, LB, RT, RB):
       - Create irregular matrix with cross pattern
       - Enable wiring overlay in design tools
       - Verify:
         * Wiring path only connects active cells
         * No wiring lines through inactive cells
         * LED numbers only appear on active cells
         * Wiring order follows selected mode correctly
   
   Total: 16 combinations (4 modes × 4 corners)

3. REGRESSION TESTING
   -------------------
   - Test regular rectangular matrices with all wiring modes (should work as before)
   - Test circular layouts (should still work correctly)
   - Verify no performance degradation
   - Verify no crashes or errors

4. EDGE CASES
   -----------
   - Single active cell: Create 8×8 matrix with only center cell active
   - Sparse pattern: Create 10×10 matrix with only 5-10 scattered active cells
   - All cells active: Create irregular matrix but mark all cells as active
   - Large matrix: Test 64×64 irregular matrix for performance
   - Empty active cells: Test with empty active_cell_coordinates list

TEST PATTERNS:
   Test patterns can be created using the application UI:
   - Regular matrices: Use "New Pattern" → Set dimensions → Paint test colors
   - Irregular matrices: Use "New Pattern" → Enable "Irregular Shape" → 
     Toggle cells to create patterns → Paint test colors

EXPECTED RESULTS:
   ✓ Preview tab shows identical pattern to design tools
   ✓ Inactive cells are transparent in preview (not black)
   ✓ Wiring overlay only traverses active cells
   ✓ All 16 wiring combinations work correctly
   ✓ No regressions in regular matrices or circular layouts
""")


def main():
    """Main test runner."""
    print("=" * 70)
    print("Preview Mapping and Irregular Wiring - Comprehensive Test Suite")
    print("=" * 70)
    
    # Run automated tests
    results = run_automated_tests()
    
    # Print summary
    print("\n" + "=" * 70)
    print("Automated Test Results Summary")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    # Print manual testing instructions
    print_manual_testing_instructions()
    
    # Final summary
    print("\n" + "=" * 70)
    print("Next Steps")
    print("=" * 70)
    if all_passed:
        print("✓ Automated tests passed!")
        print("  → Proceed with manual testing using the instructions above")
    else:
        print("✗ Some automated tests failed!")
        print("  → Review test output above and fix issues before manual testing")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
