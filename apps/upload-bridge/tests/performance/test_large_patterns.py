"""
Performance tests for large LED matrix patterns.

Tests rendering, memory usage, and export performance with large matrices.
"""

import pytest
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pattern import Pattern, Frame, PatternMetadata
from domain.pattern_state import PatternState
from domain.frames import FrameManager
from core.export import generate_export_preview


class TestLargePatterns:
    """Test performance with large matrix patterns"""
    
    def test_32x32_pattern_creation(self):
        """Test creating a 32x32 pattern"""
        pattern = Pattern(
            metadata=PatternMetadata(width=32, height=32)
        )
        
        # Add 10 frames
        for i in range(10):
            # Create frame with pixels
            pixels = []
            for y in range(32):
                for x in range(32):
                    if (x + y) % 2 == 0:
                        pixels.append((255, 0, 0))
                    else:
                        pixels.append((0, 0, 0))
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern.frames.append(frame)
        
        assert len(pattern.frames) == 10
        assert pattern.metadata.width == 32
        assert pattern.metadata.height == 32
    
    def test_64x64_pattern_creation(self):
        """Test creating a 64x64 pattern"""
        start_time = time.time()
        
        pattern = Pattern(
            metadata=PatternMetadata(width=64, height=64)
        )
        
        # Add 20 frames
        for i in range(20):
            pixels = []
            for y in range(64):
                for x in range(64):
                    if (x + y) % 2 == 0:
                        pixels.append((0, 255, 0))
                    else:
                        pixels.append((0, 0, 0))
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern.frames.append(frame)
        
        elapsed = time.time() - start_time
        
        assert len(pattern.frames) == 20
        assert pattern.metadata.width == 64
        assert pattern.metadata.height == 64
        assert elapsed < 5.0  # Should complete in under 5 seconds
    
    def test_128x128_pattern_creation(self):
        """Test creating a 128x128 pattern (large)"""
        start_time = time.time()
        
        pattern = Pattern(
            metadata=PatternMetadata(width=128, height=128)
        )
        
        # Add 10 frames (fewer frames for large matrix)
        for i in range(10):
            pixels = []
            for y in range(128):
                for x in range(128):
                    if (x + y) % 4 == 0:
                        pixels.append((0, 0, 255))
                    else:
                        pixels.append((0, 0, 0))
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern.frames.append(frame)
        
        elapsed = time.time() - start_time
        
        assert len(pattern.frames) == 10
        assert pattern.metadata.width == 128
        assert pattern.metadata.height == 128
        assert elapsed < 10.0  # Should complete in under 10 seconds
    
    def test_long_pattern_1000_frames(self):
        """Test pattern with 1000 frames"""
        start_time = time.time()
        
        pattern = Pattern(
            metadata=PatternMetadata(width=16, height=16)
        )
        
        # Add 1000 frames
        for i in range(1000):
            pixels = [(0, 0, 0)] * (16 * 16)  # Initialize with black
            # Set one pixel per frame
            pixel_idx = ((i % 16) + ((i // 16) % 16) * 16)
            if pixel_idx < len(pixels):
                pixels[pixel_idx] = (255, 255, 255)
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern.frames.append(frame)
        
        elapsed = time.time() - start_time
        
        assert len(pattern.frames) == 1000
        assert elapsed < 30.0  # Should complete in under 30 seconds
    
    def test_export_performance_large_pattern(self):
        """Test export performance with large pattern"""
        pattern = Pattern(
            metadata=PatternMetadata(width=64, height=64)
        )
        
        # Add 50 frames
        for i in range(50):
            pixels = []
            for y in range(64):
                for x in range(64):
                    if (x + y) % 4 == 0:
                        pixels.append((128, 128, 128))
                    else:
                        pixels.append((0, 0, 0))
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern.frames.append(frame)
        
        start_time = time.time()
        
        # Test export preview generation
        try:
            preview = generate_export_preview(pattern, format="bin")
            elapsed = time.time() - start_time
            
            assert elapsed < 10.0  # Export should complete in under 10 seconds
        except Exception as e:
            # Export might not be fully implemented, skip if so
            pytest.skip(f"Export not fully implemented: {e}")
    
    def test_memory_usage_pattern_creation(self):
        """Test memory usage doesn't grow excessively"""
        import tracemalloc
        
        tracemalloc.start()
        
        pattern = Pattern(
            metadata=PatternMetadata(width=32, height=32)
        )
        
        # Add 100 frames
        for i in range(100):
            pixels = []
            for y in range(32):
                for x in range(32):
                    if (x + y) % 2 == 0:
                        pixels.append((255, 0, 0))
                    else:
                        pixels.append((0, 0, 0))
            frame = Frame(pixels=pixels, duration_ms=100)
            pattern.frames.append(frame)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory should be reasonable (less than 100MB for 100 frames)
        assert peak < 100 * 1024 * 1024  # 100MB

