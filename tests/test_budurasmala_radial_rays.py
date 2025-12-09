"""
Tests for Budurasmala Radial Ray Pattern.
"""

import pytest
from core.pattern import PatternMetadata
from core.mapping.circular_mapper import CircularMapper


class TestRadialRayPattern:
    """Test radial ray pattern functionality."""
    
    def test_radial_ray_mapping_generation(self):
        """Test radial ray mapping table generation."""
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="radial_rays",
            ray_count=8,
            leds_per_ray=10,
            ray_spacing_angle=45.0
        )
        
        mapping = CircularMapper.generate_radial_ray_mapping(metadata)
        
        assert len(mapping) == 80  # 8 rays * 10 LEDs
        assert all(isinstance(m, tuple) and len(m) == 2 for m in mapping)
        assert all(0 <= x < 32 and 0 <= y < 32 for x, y in mapping)
    
    def test_radial_ray_validation(self):
        """Test radial ray parameter validation."""
        # Valid configuration
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="radial_rays",
            ray_count=12,
            leds_per_ray=15,
            ray_spacing_angle=30.0
        )
        
        mapping = CircularMapper.generate_radial_ray_mapping(metadata)
        assert len(mapping) == 180  # 12 * 15
        
        # Invalid: missing ray_count
        with pytest.raises(ValueError):
            metadata.ray_count = None
            CircularMapper.generate_radial_ray_mapping(metadata)
    
    def test_radial_ray_led_count_calculation(self):
        """Test LED count calculation for radial rays."""
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="radial_rays",
            ray_count=8,
            leds_per_ray=10,
            ray_spacing_angle=45.0
        )
        
        # LED count should be ray_count * leds_per_ray
        total_leds = metadata.ray_count * metadata.leds_per_ray
        assert total_leds == 80
        
        mapping = CircularMapper.generate_radial_ray_mapping(metadata)
        assert len(mapping) == total_leds
    
    def test_radial_ray_angle_spacing(self):
        """Test ray angle spacing."""
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="radial_rays",
            ray_count=8,
            leds_per_ray=10,
            ray_spacing_angle=45.0
        )
        
        # 8 rays with 45° spacing = 360° / 8 = 45° ✓
        expected_spacing = 360.0 / metadata.ray_count
        assert metadata.ray_spacing_angle == expected_spacing

