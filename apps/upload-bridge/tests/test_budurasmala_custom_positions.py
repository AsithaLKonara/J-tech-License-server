"""
Tests for Budurasmala Custom LED Position Support.
"""

import pytest
from pathlib import Path
import tempfile
from core.pattern import PatternMetadata
from core.mapping.circular_mapper import CircularMapper
from core.io.custom_position_importer import (
    import_positions_from_csv,
    import_positions_from_json,
    detect_units_from_filename
)


class TestCustomLEDPositions:
    """Test custom LED position functionality."""
    
    def test_custom_position_mapping(self):
        """Test custom position mapping generation."""
        positions = [
            (10.0, 20.0),
            (15.0, 25.0),
            (20.0, 30.0),
            (25.0, 35.0)
        ]
        
        metadata = PatternMetadata(
            width=32,
            height=32,
            layout_type="custom_positions",
            custom_led_positions=positions,
            led_position_units="mm"
        )
        
        mapping = CircularMapper.generate_custom_position_mapping(metadata)
        
        assert len(mapping) == len(positions)
        assert all(isinstance(m, tuple) and len(m) == 2 for m in mapping)
    
    def test_csv_import(self):
        """Test CSV position import."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("x,y\n")
            f.write("10.0,20.0\n")
            f.write("15.0,25.0\n")
            f.write("20.0,30.0\n")
            temp_path = Path(f.name)
        
        try:
            positions = import_positions_from_csv(
                temp_path,
                x_column=0,
                y_column=1,
                skip_header=True
            )
            
            assert len(positions) == 3
            assert positions[0] == (10.0, 20.0)
            assert positions[1] == (15.0, 25.0)
            assert positions[2] == (20.0, 30.0)
        finally:
            temp_path.unlink()
    
    def test_json_import(self):
        """Test JSON position import."""
        import json
        
        data = {
            "positions": [
                {"x": 10.0, "y": 20.0},
                {"x": 15.0, "y": 25.0},
                {"x": 20.0, "y": 30.0}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)
        
        try:
            positions = import_positions_from_json(temp_path)
            
            assert len(positions) == 3
            assert positions[0] == (10.0, 20.0)
            assert positions[1] == (15.0, 25.0)
            assert positions[2] == (20.0, 30.0)
        finally:
            temp_path.unlink()
    
    def test_units_detection(self):
        """Test unit detection from filename."""
        assert detect_units_from_filename(Path("leds_mm.csv")) == "mm"
        assert detect_units_from_filename(Path("leds_inches.csv")) == "inches"
        assert detect_units_from_filename(Path("leds.csv")) == "mm"  # Default

