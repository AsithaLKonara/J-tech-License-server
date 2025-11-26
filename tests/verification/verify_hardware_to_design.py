"""
Verify hardware_to_design_order() function works for all 16 combinations
Tests round-trip conversion: design → hardware → design (should match original)
"""

from core.wiring_mapper import WiringMapper
from core.pattern_converter import hardware_to_design_order, _build_hardware_to_design_map
from core.pattern import Pattern, Frame, PatternMetadata
import hashlib

def test_round_trip_conversion():
    """Test that design → hardware → design produces identical output"""
    
    width, height = 4, 3
    total_leds = width * height
    
    # Original design order pixels
    design_pixels = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255),
        (255, 0, 255), (255, 255, 0), (0, 255, 255), (255, 128, 0),
        (128, 0, 128), (0, 128, 128), (128, 128, 0), (64, 64, 64),
    ]
    
    wiring_modes = ["Row-major", "Serpentine", "Column-major", "Column-serpentine"]
    corners = ["LT", "LB", "RT", "RB"]
    
    print("="*80)
    print("ROUND-TRIP CONVERSION TEST")
    print("="*80)
    print("Testing: Design → Hardware → Design (should match original)")
    print(f"Matrix: {width}×{height}")
    print()
    
    all_passed = True
    
    for wiring in wiring_modes:
        for corner in corners:
            print(f"\nTesting: {wiring:20s} + {corner:2s}...", end=" ")
            
            # Step 1: Design → Hardware
            mapper = WiringMapper(width, height, wiring, corner)
            hardware_pixels = mapper.design_to_hardware(design_pixels)
            
            # Step 2: Hardware → Design
            try:
                hw_to_design_map = _build_hardware_to_design_map(width, height, wiring, corner)
                
                # Apply reverse mapping
                recovered_pixels = [None] * total_leds
                for hw_idx, design_idx in enumerate(hw_to_design_map):
                    recovered_pixels[design_idx] = hardware_pixels[hw_idx]
                
                # Step 3: Compare with original
                if recovered_pixels == design_pixels:
                    print("✓ PASS (perfect round-trip)")
                else:
                    print("❌ FAIL (pixels don't match)")
                    # Show first mismatch
                    for i in range(total_leds):
                        if recovered_pixels[i] != design_pixels[i]:
                            print(f"   First mismatch at index {i}:")
                            print(f"     Original:  {design_pixels[i]}")
                            print(f"     Recovered: {recovered_pixels[i]}")
                            break
                    all_passed = False
                    
            except NotImplementedError as e:
                print(f"⚠️  NOT IMPLEMENTED: {e}")
                all_passed = False
            except Exception as e:
                print(f"❌ ERROR: {e}")
                all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL 16 COMBINATIONS PASSED ROUND-TRIP TEST")
    else:
        print("❌ SOME COMBINATIONS FAILED - Check pattern_converter.py implementation")
    print("="*80)
    
    return all_passed

if __name__ == "__main__":
    success = test_round_trip_conversion()
    exit(0 if success else 1)

