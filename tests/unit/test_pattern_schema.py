"""
Unit tests for Pattern JSON Schema v1.0

Tests schema validation, conversion, RLE encoding, and migration.
"""

import pytest
import json
import uuid
from pathlib import Path
from datetime import datetime

from core.pattern import Pattern, Frame, PatternMetadata
from core.schemas.pattern_schema_v1 import (
    PATTERN_SCHEMA_V1,
    validate_pattern_json,
    PatternSchemaError,
)
from core.schemas.pattern_converter import (
    PatternConverter,
    encode_pixels_rle,
    decode_pixels_rle,
)
from core.schemas.migration import (
    SchemaMigrator,
    migrate_pattern_json,
    get_schema_version,
    needs_migration,
)


class TestPatternSchemaValidation:
    """Test JSON schema validation"""
    
    def test_valid_schema_v1_0(self):
        """Test that valid v1.0 schema passes validation"""
        valid_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Test Pattern",
            "description": "A test pattern",
            "tags": ["test", "animation"],
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "modified_at": datetime.utcnow().isoformat() + 'Z',
            "matrix": {
                "width": 16,
                "height": 16,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB"
            },
            "frames": [
                {
                    "index": 0,
                    "duration_ms": 100,
                    "layers": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": "base",
                            "opacity": 1.0,
                            "blend_mode": "normal",
                            "visible": True,
                            "pixels": [[255, 0, 0], [0, 255, 0]],
                            "encoding": "raw+rgb8"
                        }
                    ]
                }
            ],
            "effects": [],
            "metadata": {
                "author": "Test Author",
                "approx_memory_bytes": 768
            }
        }
        
        assert validate_pattern_json(valid_pattern) is True
    
    def test_invalid_schema_version(self):
        """Test that invalid schema version fails"""
        invalid_pattern = {
            "schema_version": "2.0",  # Invalid version
            "id": str(uuid.uuid4()),
            "name": "Test",
            "matrix": {"width": 16, "height": 16},
            "frames": []
        }
        
        with pytest.raises(PatternSchemaError):
            validate_pattern_json(invalid_pattern)
    
    def test_missing_required_fields(self):
        """Test that missing required fields fail validation"""
        invalid_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            # Missing name, matrix, frames
        }
        
        with pytest.raises(PatternSchemaError):
            validate_pattern_json(invalid_pattern)
    
    def test_invalid_matrix_dimensions(self):
        """Test that invalid matrix dimensions fail"""
        invalid_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Test",
            "matrix": {
                "width": 0,  # Invalid
                "height": 16
            },
            "frames": []
        }
        
        with pytest.raises(PatternSchemaError):
            validate_pattern_json(invalid_pattern)
    
    def test_circular_layout_schema(self):
        """Test that circular layout fields pass validation"""
        circular_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Circular Pattern",
            "description": "A circular layout pattern",
            "tags": ["circular", "budurasmala"],
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "modified_at": datetime.utcnow().isoformat() + 'Z',
            "matrix": {
                "width": 32,
                "height": 32,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB",
                "layout_type": "circle",
                "circular_led_count": 60,
                "circular_radius": 15.0,
                "circular_start_angle": 0.0,
                "circular_end_angle": 360.0,
                "circular_mapping_table": [[16, 16], [17, 15], [18, 14]]  # Sample mapping
            },
            "frames": [
                {
                    "index": 0,
                    "duration_ms": 100,
                    "layers": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": "base",
                            "opacity": 1.0,
                            "blend_mode": "normal",
                            "visible": True,
                            "pixels": [[255, 0, 0]] * 1024,
                            "encoding": "raw+rgb8"
                        }
                    ]
                }
            ],
            "effects": [],
            "metadata": {}
        }
        
        assert validate_pattern_json(circular_pattern) is True
    
    def test_multi_ring_layout_schema(self):
        """Test that multi-ring layout fields pass validation"""
        multi_ring_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Multi-Ring Pattern",
            "matrix": {
                "width": 40,
                "height": 40,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB",
                "layout_type": "multi_ring",
                "multi_ring_count": 3,
                "ring_led_counts": [24, 36, 48],
                "ring_radii": [8.0, 12.0, 16.0],
                "ring_spacing": 4.0
            },
            "frames": [
                {
                    "index": 0,
                    "duration_ms": 100,
                    "layers": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": "base",
                            "opacity": 1.0,
                            "blend_mode": "normal",
                            "visible": True,
                            "pixels": [[0, 255, 0]] * 1600,
                            "encoding": "raw+rgb8"
                        }
                    ]
                }
            ],
            "effects": [],
            "metadata": {}
        }
        
        assert validate_pattern_json(multi_ring_pattern) is True
    
    def test_radial_rays_layout_schema(self):
        """Test that radial rays layout fields pass validation"""
        radial_rays_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Radial Rays Pattern",
            "matrix": {
                "width": 30,
                "height": 30,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB",
                "layout_type": "radial_rays",
                "ray_count": 8,
                "leds_per_ray": 10,
                "ray_spacing_angle": 45.0
            },
            "frames": [
                {
                    "index": 0,
                    "duration_ms": 100,
                    "layers": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": "base",
                            "opacity": 1.0,
                            "blend_mode": "normal",
                            "visible": True,
                            "pixels": [[0, 0, 255]] * 900,
                            "encoding": "raw+rgb8"
                        }
                    ]
                }
            ],
            "effects": [],
            "metadata": {}
        }
        
        assert validate_pattern_json(radial_rays_pattern) is True
    
    def test_custom_positions_layout_schema(self):
        """Test that custom LED positions layout fields pass validation"""
        custom_positions_pattern = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Custom Positions Pattern",
            "matrix": {
                "width": 20,
                "height": 20,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB",
                "layout_type": "custom_positions",
                "custom_led_positions": [[10.0, 10.0], [12.0, 10.0], [14.0, 10.0]],
                "led_position_units": "mm",
                "custom_position_center_x": 10.0,
                "custom_position_center_y": 10.0
            },
            "frames": [
                {
                    "index": 0,
                    "duration_ms": 100,
                    "layers": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": "base",
                            "opacity": 1.0,
                            "blend_mode": "normal",
                            "visible": True,
                            "pixels": [[255, 255, 0]] * 400,
                            "encoding": "raw+rgb8"
                        }
                    ]
                }
            ],
            "effects": [],
            "metadata": {}
        }
        
        assert validate_pattern_json(custom_positions_pattern) is True


class TestPatternConverter:
    """Test Pattern ↔ JSON conversion"""
    
    def test_pattern_to_json_basic(self):
        """Test basic pattern to JSON conversion"""
        pattern = Pattern(
            id="test-id",
            name="Test Pattern",
            metadata=PatternMetadata(width=8, height=8),
            frames=[
                Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100),
                Frame(pixels=[(0, 255, 0)] * 64, duration_ms=100)
            ]
        )
        
        json_data = PatternConverter.pattern_to_json(pattern, use_rle=False)
        
        assert json_data["schema_version"] == "1.0"
        assert json_data["id"] == "test-id"
        assert json_data["name"] == "Test Pattern"
        assert json_data["matrix"]["width"] == 8
        assert json_data["matrix"]["height"] == 8
        assert len(json_data["frames"]) == 2
        assert json_data["frames"][0]["duration_ms"] == 100
    
    def test_pattern_from_json_basic(self):
        """Test basic JSON to pattern conversion"""
        json_data = {
            "schema_version": "1.0",
            "id": "test-id",
            "name": "Test Pattern",
            "description": "",
            "tags": [],
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "modified_at": datetime.utcnow().isoformat() + 'Z',
            "matrix": {
                "width": 8,
                "height": 8,
                "layout": "row_major",
                "wiring": "linear",
                "default_color_order": "RGB"
            },
            "frames": [
                {
                    "index": 0,
                    "duration_ms": 100,
                    "layers": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": "base",
                            "opacity": 1.0,
                            "blend_mode": "normal",
                            "visible": True,
                            "pixels": [[255, 0, 0]] * 64,
                            "encoding": "raw+rgb8"
                        }
                    ]
                }
            ],
            "effects": [],
            "metadata": {}
        }
        
        pattern = PatternConverter.pattern_from_json(json_data)
        
        assert pattern.id == "test-id"
        assert pattern.name == "Test Pattern"
        assert pattern.metadata.width == 8
        assert pattern.metadata.height == 8
        assert len(pattern.frames) == 1
        assert pattern.frames[0].duration_ms == 100
        assert len(pattern.frames[0].pixels) == 64
    
    def test_round_trip_conversion(self):
        """Test that pattern → JSON → pattern preserves data"""
        original_pattern = Pattern(
            id="round-trip-id",
            name="Round Trip Test",
            metadata=PatternMetadata(width=4, height=4, color_order="GRB"),
            frames=[
                Frame(pixels=[(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)] * 4, duration_ms=150),
                Frame(pixels=[(0, 255, 255), (255, 0, 255), (128, 128, 128), (64, 64, 64)] * 4, duration_ms=200)
            ]
        )
        
        # Convert to JSON and back
        json_data = PatternConverter.pattern_to_json(original_pattern, use_rle=False)
        converted_pattern = PatternConverter.pattern_from_json(json_data)
        
        # Verify round-trip
        assert converted_pattern.id == original_pattern.id
        assert converted_pattern.name == original_pattern.name
        assert converted_pattern.metadata.width == original_pattern.metadata.width
        assert converted_pattern.metadata.height == original_pattern.metadata.height
        assert converted_pattern.metadata.color_order == original_pattern.metadata.color_order
        assert len(converted_pattern.frames) == len(original_pattern.frames)
        
        for orig_frame, conv_frame in zip(original_pattern.frames, converted_pattern.frames):
            assert conv_frame.duration_ms == orig_frame.duration_ms
            assert conv_frame.pixels == orig_frame.pixels
    
    def test_rle_encoding_decoding(self):
        """Test RLE encoding and decoding"""
        # Create pixels with runs
        pixels = [(255, 0, 0)] * 10 + [(0, 255, 0)] * 5 + [(0, 0, 255)] * 3
        
        encoded = encode_pixels_rle(pixels)
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        
        decoded = decode_pixels_rle(encoded, len(pixels))
        assert decoded == pixels
    
    def test_rle_with_pattern(self):
        """Test pattern conversion with RLE encoding"""
        pattern = Pattern(
            metadata=PatternMetadata(width=2, height=2),
            frames=[
                Frame(pixels=[(255, 0, 0)] * 4, duration_ms=100)
            ]
        )
        
        json_data = PatternConverter.pattern_to_json(pattern, use_rle=True)
        
        # Check that pixels are encoded as string (RLE)
        layer = json_data["frames"][0]["layers"][0]
        assert isinstance(layer["pixels"], str)
        assert layer["encoding"] == "rle+rgba8"
        
        # Decode and verify
        decoded_pattern = PatternConverter.pattern_from_json(json_data)
        assert decoded_pattern.frames[0].pixels == pattern.frames[0].pixels
    
    def test_circular_layout_round_trip(self):
        """Test that circular layout patterns round-trip correctly"""
        from core.mapping.circular_mapper import CircularMapper
        
        # Create a circular pattern with mapping table
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="circle",
            circular_led_count=60,
            circular_radius=15.0
        )
        
        # Generate mapping table
        mapping_table = CircularMapper.generate_mapping_table(metadata)
        metadata.circular_mapping_table = mapping_table
        
        original_pattern = Pattern(
            id="circular-round-trip-id",
            name="Circular Round Trip",
            metadata=metadata,
            frames=[
                Frame(pixels=[(255, 0, 0)] * (32 * 32), duration_ms=100)
            ]
        )
        
        # Convert to JSON and back
        json_data = PatternConverter.pattern_to_json(original_pattern, use_rle=False)
        converted_pattern = PatternConverter.pattern_from_json(json_data)
        
        # Verify circular layout fields are preserved
        assert converted_pattern.metadata.layout_type == "circle"
        assert converted_pattern.metadata.circular_led_count == 60
        assert converted_pattern.metadata.circular_radius == 15.0
        assert converted_pattern.metadata.circular_mapping_table is not None
        assert len(converted_pattern.metadata.circular_mapping_table) == 60


class TestSchemaMigration:
    """Test schema migration utilities"""
    
    def test_get_schema_version(self):
        """Test getting schema version from JSON"""
        data = {"schema_version": "1.0"}
        assert get_schema_version(data) == "1.0"
        
        data_no_version = {"name": "Test"}
        assert get_schema_version(data_no_version) is None
    
    def test_needs_migration(self):
        """Test migration detection"""
        data_v1 = {"schema_version": "1.0"}
        assert needs_migration(data_v1) is False
        
        data_no_version = {"name": "Test"}
        assert needs_migration(data_no_version) is True
    
    def test_migrate_from_legacy(self):
        """Test migration from legacy format"""
        legacy_data = {
            "name": "Legacy Pattern",
            "metadata": {
                "width": 16,
                "height": 16,
                "color_order": "RGB"
            },
            "frames": [
                {
                    "pixels": [[255, 0, 0]] * 256,
                    "duration_ms": 100
                }
            ]
        }
        
        migrated = migrate_pattern_json(legacy_data, target_version="1.0")
        
        assert migrated["schema_version"] == "1.0"
        assert migrated["name"] == "Legacy Pattern"
        assert migrated["matrix"]["width"] == 16
        assert len(migrated["frames"]) == 1
    
    def test_migrate_already_current(self):
        """Test that current version doesn't migrate"""
        current_data = {
            "schema_version": "1.0",
            "id": str(uuid.uuid4()),
            "name": "Current",
            "matrix": {"width": 8, "height": 8},
            "frames": []
        }
        
        migrated = migrate_pattern_json(current_data)
        assert migrated == current_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

