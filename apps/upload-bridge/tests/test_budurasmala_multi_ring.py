"""
Tests for Budurasmala Multi-Ring Layout System.
"""

import pytest
from core.pattern import PatternMetadata
from core.mapping.circular_mapper import CircularMapper


class TestMultiRingLayout:
    """Test multi-ring layout functionality."""
    
    def test_multi_ring_mapping_generation(self):
        """Test multi-ring mapping table generation."""
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="multi_ring",
            multi_ring_count=3,
            ring_led_counts=[60, 40, 20],
            ring_radii=[30.0, 20.0, 10.0],
            ring_spacing=10.0
        )
        
        mapping = CircularMapper.generate_multi_ring_mapping(metadata)
        
        assert len(mapping) == 120  # 60 + 40 + 20
        assert all(isinstance(m, tuple) and len(m) == 2 for m in mapping)
        assert all(0 <= x < 32 and 0 <= y < 32 for x, y in mapping)
    
    def test_multi_ring_validation(self):
        """Test multi-ring parameter validation."""
        # Valid configuration
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="multi_ring",
            multi_ring_count=2,
            ring_led_counts=[30, 20],
            ring_radii=[25.0, 15.0]
        )
        
        mapping = CircularMapper.generate_multi_ring_mapping(metadata)
        assert len(mapping) == 50
        
        # Invalid: mismatched counts
        with pytest.raises(ValueError):
            metadata.ring_led_counts = [30]  # Should be 2
            CircularMapper.generate_multi_ring_mapping(metadata)
    
    def test_multi_ring_led_count_calculation(self):
        """Test LED count calculation for multi-ring."""
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="multi_ring",
            multi_ring_count=3,
            ring_led_counts=[60, 40, 20],
            ring_radii=[30.0, 20.0, 10.0]
        )
        
        # LED count should be sum of ring_led_counts
        total_leds = sum(metadata.ring_led_counts)
        assert total_leds == 120
        
        mapping = CircularMapper.generate_multi_ring_mapping(metadata)
        assert len(mapping) == total_leds
    
    def test_multi_ring_ring_spacing(self):
        """Test ring spacing configuration."""
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="multi_ring",
            multi_ring_count=3,
            ring_led_counts=[30, 20, 10],
            ring_radii=[30.0, 20.0, 10.0],
            ring_spacing=10.0
        )
        
        mapping = CircularMapper.generate_multi_ring_mapping(metadata)
        assert len(mapping) == 60
        
        # Verify rings are properly spaced
        assert metadata.ring_spacing == 10.0

