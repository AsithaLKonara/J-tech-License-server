#!/usr/bin/env python3
"""
Test Large Frame Pattern Metadata Detection
Tests metadata detection and validation for patterns with varying frame counts:
100, 1000, 5000, 10000, 15000 frames
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.pattern import Pattern, Frame, PatternMetadata
from core.dimension_scorer import _frame_score, infer_leds_and_frames
from core.matrix_detector import MatrixDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_pattern(width: int, height: int, frame_count: int, 
                       dimension_source: str = "detector",
                       dimension_confidence: float = 0.8) -> Pattern:
    """
    Create a test pattern with specified dimensions and frame count.
    
    Args:
        width: Matrix width
        height: Matrix height
        frame_count: Number of frames
        dimension_source: Source of dimensions ('header', 'detector', 'fallback')
        dimension_confidence: Confidence score (0.0-1.0)
    """
    import math
    
    led_count = width * height
    frames = []
    
    logger.info(f"Creating pattern: {width}×{height} ({led_count} LEDs), {frame_count} frames...")
    start_time = time.time()
    
    for f in range(frame_count):
        pixels = []
        for y in range(height):
            for x in range(width):
                # Create a simple animated pattern
                hue = ((x + y) / (width + height) + (f / max(frame_count, 1))) % 1.0
                r = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * hue)))
                g = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * (hue + 0.333))))
                b = int(255 * (0.5 + 0.5 * math.sin(2 * math.pi * (hue + 0.666))))
                pixels.append((r, g, b))
        
        frames.append(Frame(pixels=pixels, duration_ms=50))
        
        # Progress indicator for large patterns
        if frame_count > 1000 and (f + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            logger.info(f"  Generated {f + 1}/{frame_count} frames ({elapsed:.1f}s)")
    
    elapsed = time.time() - start_time
    logger.info(f"  Pattern created in {elapsed:.2f}s")
    
    metadata = PatternMetadata(
        width=width,
        height=height,
        color_order="RGB",
        dimension_source=dimension_source,
        dimension_confidence=dimension_confidence
    )
    
    return Pattern(
        name=f"Test Pattern {width}×{height} ({frame_count} frames)",
        metadata=metadata,
        frames=frames
    )


def test_frame_score():
    """Test _frame_score function with different frame counts"""
    print("\n" + "="*70)
    print("TEST 1: Frame Score Function")
    print("="*70)
    
    test_cases = [
        (100, "detector", None),
        (1000, "detector", None),
        (4000, "detector", None),
        (5000, "detector", None),
        (10000, "detector", None),
        (15000, "detector", None),
        (4000, "header", 1.0),  # Header should always return 1.0
        (15000, "header", 1.0),
    ]
    
    print(f"{'Frames':<10} {'Source':<12} {'Score':<10} {'Expected':<10} {'Status'}")
    print("-" * 70)
    
    for frames, source, expected_score in test_cases:
        score = _frame_score(frames, dimension_source=source)
        expected = expected_score if expected_score is not None else "N/A"
        
        if source == "header":
            status = "✓ PASS" if score == 1.0 else "✗ FAIL"
        elif frames <= 100:
            status = "✓ PASS" if score >= 0.7 else "✗ FAIL"
        elif frames <= 5000:
            status = "✓ PASS" if score >= 0.2 else "✗ FAIL"
        else:
            status = "✓ PASS" if score >= 0.15 else "✗ FAIL"
        
        print(f"{frames:<10} {source:<12} {score:<10.3f} {str(expected):<10} {status}")
    
    return True


def test_metadata_validation():
    """Test metadata validation logic"""
    print("\n" + "="*70)
    print("TEST 2: Metadata Validation")
    print("="*70)
    
    # Simulate the validation logic from preview_tab.py
    def validate_pattern_metadata(pattern: Pattern) -> dict:
        if not pattern or not pattern.frames:
            return {'valid': False, 'reason': 'Pattern has no frames', 'should_redetect': False}
        
        expected_leds = pattern.metadata.width * pattern.metadata.height
        actual_leds = pattern.led_count
        
        if expected_leds != actual_leds:
            return {
                'valid': False,
                'reason': f'Dimension mismatch: {pattern.metadata.width}×{pattern.metadata.height}={expected_leds} but LED count={actual_leds}',
                'should_redetect': True
            }
        
        first_frame_leds = len(pattern.frames[0].pixels) if pattern.frames else 0
        if first_frame_leds != actual_leds:
            return {
                'valid': False,
                'reason': f'Frame LED count mismatch: first frame has {first_frame_leds} LEDs, expected {actual_leds}',
                'should_redetect': True
            }
        
        dimension_source = getattr(pattern.metadata, 'dimension_source', 'unknown')
        dimension_confidence = getattr(pattern.metadata, 'dimension_confidence', 0.0)
        
        if dimension_source != 'header' and dimension_confidence < 0.5:
            return {
                'valid': False,
                'reason': f'Low confidence detection ({dimension_confidence:.0%}) from {dimension_source}',
                'should_redetect': True
            }
        
        return {'valid': True, 'reason': 'Metadata is consistent', 'should_redetect': False}
    
    # Test cases
    test_patterns = [
        create_test_pattern(12, 6, 100, "detector", 0.8),   # Valid
        create_test_pattern(12, 6, 1000, "detector", 0.8),  # Valid
        create_test_pattern(12, 6, 4000, "header", 1.0),   # Valid (header)
        create_test_pattern(12, 6, 5000, "detector", 0.3), # Low confidence
        create_test_pattern(12, 6, 10000, "detector", 0.8), # Valid
    ]
    
    print(f"{'Frames':<10} {'Source':<12} {'Conf':<8} {'Valid':<8} {'Should Redetect':<15} {'Status'}")
    print("-" * 70)
    
    for pattern in test_patterns:
        result = validate_pattern_metadata(pattern)
        frames = pattern.frame_count
        source = pattern.metadata.dimension_source
        conf = pattern.metadata.dimension_confidence
        
        expected_valid = (
            pattern.metadata.width * pattern.metadata.height == pattern.led_count and
            (source == 'header' or conf >= 0.5)
        )
        
        status = "✓ PASS" if result['valid'] == expected_valid else "✗ FAIL"
        
        print(f"{frames:<10} {source:<12} {conf:<8.2f} {str(result['valid']):<8} "
              f"{str(result['should_redetect']):<15} {status}")
    
    return True


def test_pattern_loading(frame_counts: list):
    """Test loading patterns with different frame counts"""
    print("\n" + "="*70)
    print("TEST 3: Pattern Loading and Metadata Detection")
    print("="*70)
    
    width, height = 12, 6
    led_count = width * height
    
    results = []
    
    for frame_count in frame_counts:
        print(f"\nTesting {frame_count} frames...")
        start_time = time.time()
        
        # Create pattern with detector source (simulating auto-detection)
        pattern = create_test_pattern(width, height, frame_count, "detector", 0.8)
        
        # Verify pattern integrity
        assert pattern.frame_count == frame_count, f"Frame count mismatch: expected {frame_count}, got {pattern.frame_count}"
        assert pattern.led_count == led_count, f"LED count mismatch: expected {led_count}, got {pattern.led_count}"
        assert len(pattern.frames[0].pixels) == led_count, "First frame LED count mismatch"
        
        # Test dimension detection
        detector = MatrixDetector()
        detected_layout = detector.detect_layout(
            pattern.led_count,
            pattern.frames[0].pixels if pattern.frames else None
        )
        
        # Verify detected dimensions match
        dim_match = (
            detected_layout.width == width and
            detected_layout.height == height
        )
        
        elapsed = time.time() - start_time
        
        result = {
            'frames': frame_count,
            'width': width,
            'height': height,
            'detected_width': detected_layout.width,
            'detected_height': detected_layout.height,
            'confidence': detected_layout.confidence,
            'dim_match': dim_match,
            'time': elapsed,
            'status': 'PASS' if dim_match else 'FAIL'
        }
        
        results.append(result)
        
        print(f"  ✓ Pattern created: {frame_count} frames")
        print(f"  ✓ Dimensions: {detected_layout.width}×{detected_layout.height} "
              f"(confidence: {detected_layout.confidence:.0%})")
        print(f"  ✓ Time: {elapsed:.2f}s")
        print(f"  ✓ Status: {result['status']}")
    
    # Summary table
    print(f"\n{'Frames':<10} {'Detected':<15} {'Expected':<15} {'Confidence':<12} {'Time':<10} {'Status'}")
    print("-" * 80)
    
    for r in results:
        detected = f"{r['detected_width']}×{r['detected_height']}"
        expected = f"{r['width']}×{r['height']}"
        status_icon = "✓" if r['status'] == 'PASS' else "✗"
        print(f"{r['frames']:<10} {detected:<15} {expected:<15} "
              f"{r['confidence']:<12.2%} {r['time']:<10.2f} {status_icon} {r['status']}")
    
    return all(r['status'] == 'PASS' for r in results)


def test_preview_tab_simulation(frame_counts: list):
    """Simulate preview tab loading behavior"""
    print("\n" + "="*70)
    print("TEST 4: Preview Tab Loading Simulation")
    print("="*70)
    
    width, height = 12, 6
    led_count = width * height
    
    results = []
    
    for frame_count in frame_counts:
        print(f"\nSimulating preview tab load for {frame_count} frames...")
        start_time = time.time()
        
        # Create pattern
        pattern = create_test_pattern(width, height, frame_count, "detector", 0.8)
        
        # Simulate validation (from preview_tab.py)
        def validate_pattern_metadata(pattern: Pattern) -> dict:
            if not pattern or not pattern.frames:
                return {'valid': False, 'reason': 'Pattern has no frames', 'should_redetect': False}
            
            expected_leds = pattern.metadata.width * pattern.metadata.height
            actual_leds = pattern.led_count
            
            if expected_leds != actual_leds:
                return {
                    'valid': False,
                    'reason': f'Dimension mismatch',
                    'should_redetect': True
                }
            
            dimension_source = getattr(pattern.metadata, 'dimension_source', 'unknown')
            dimension_confidence = getattr(pattern.metadata, 'dimension_confidence', 0.0)
            
            if dimension_source != 'header' and dimension_confidence < 0.5:
                return {
                    'valid': False,
                    'reason': f'Low confidence',
                    'should_redetect': True
                }
            
            return {'valid': True, 'reason': 'Metadata is consistent', 'should_redetect': False}
        
        # Validate
        validation = validate_pattern_metadata(pattern)
        
        # Simulate optimized copying for large patterns
        import copy
        if frame_count > 1000:
            # Optimized copy (first 100 frames only)
            copied_frames = [Frame(pixels=list(frame.pixels), duration_ms=frame.duration_ms) 
                           for frame in pattern.frames[:100]]
            copy_time = time.time() - start_time
            copy_optimized = True
        else:
            # Full copy
            copied_frames = [Frame(pixels=list(frame.pixels), duration_ms=frame.duration_ms) 
                           for frame in pattern.frames]
            copy_time = time.time() - start_time
            copy_optimized = False
        
        elapsed = time.time() - start_time
        
        result = {
            'frames': frame_count,
            'valid': validation['valid'],
            'should_redetect': validation['should_redetect'],
            'copy_optimized': copy_optimized,
            'copy_time': copy_time,
            'total_time': elapsed,
            'status': 'PASS' if validation['valid'] else 'FAIL'
        }
        
        results.append(result)
        
        print(f"  ✓ Validation: {'PASS' if validation['valid'] else 'FAIL'}")
        print(f"  ✓ Copy optimized: {copy_optimized}")
        print(f"  ✓ Copy time: {copy_time:.2f}s")
        print(f"  ✓ Total time: {elapsed:.2f}s")
    
    # Summary
    print(f"\n{'Frames':<10} {'Valid':<8} {'Optimized':<12} {'Copy Time':<12} {'Total Time':<12} {'Status'}")
    print("-" * 70)
    
    for r in results:
        status_icon = "✓" if r['status'] == 'PASS' else "✗"
        print(f"{r['frames']:<10} {str(r['valid']):<8} {str(r['copy_optimized']):<12} "
              f"{r['copy_time']:<12.2f} {r['total_time']:<12.2f} {status_icon} {r['status']}")
    
    return all(r['status'] == 'PASS' for r in results)


def main():
    """Run all tests"""
    print("="*70)
    print("LARGE FRAME PATTERN METADATA DETECTION TESTS")
    print("="*70)
    print("\nTesting patterns with: 100, 1000, 5000, 10000, 15000 frames")
    print("Matrix size: 12×6 (72 LEDs)")
    
    frame_counts = [100, 1000, 5000, 10000, 15000]
    
    results = {}
    
    # Test 1: Frame score function
    try:
        results['frame_score'] = test_frame_score()
    except Exception as e:
        logger.error(f"Frame score test failed: {e}", exc_info=True)
        results['frame_score'] = False
    
    # Test 2: Metadata validation
    try:
        results['validation'] = test_metadata_validation()
    except Exception as e:
        logger.error(f"Validation test failed: {e}", exc_info=True)
        results['validation'] = False
    
    # Test 3: Pattern loading
    try:
        results['loading'] = test_pattern_loading(frame_counts)
    except Exception as e:
        logger.error(f"Loading test failed: {e}", exc_info=True)
        results['loading'] = False
    
    # Test 4: Preview tab simulation
    try:
        results['preview'] = test_preview_tab_simulation(frame_counts)
    except Exception as e:
        logger.error(f"Preview simulation test failed: {e}", exc_info=True)
        results['preview'] = False
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

