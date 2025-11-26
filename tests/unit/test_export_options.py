"""
Unit tests for advanced export options.
"""

import pytest
from core.export_options import ExportOptions

RGB = tuple[int, int, int]


class TestExportOptions:
    """Test ExportOptions functionality."""
    
    def test_default_options(self):
        """Test default export options."""
        opts = ExportOptions()
        assert opts.bit_order_msb_lsb == "MSB"
        assert opts.bit_order_position == "Top"
        assert opts.scan_direction == "Rows"
        assert opts.scan_order == "LeftToRight"
        assert opts.serpentine is False
        assert opts.rgb_order == "RGB"
        assert opts.color_space == "RGB888"
        assert opts.bytes_per_line == 0
        assert opts.number_format == "Hex"
    
    def test_rgb_ordering(self):
        """Test all RGB channel orderings."""
        pixel: RGB = (255, 128, 64)
        opts = ExportOptions()
        
        # RGB
        opts.rgb_order = "RGB"
        assert opts.reorder_color_channels(pixel) == (255, 128, 64)
        
        # BGR
        opts.rgb_order = "BGR"
        assert opts.reorder_color_channels(pixel) == (64, 128, 255)
        
        # GRB
        opts.rgb_order = "GRB"
        assert opts.reorder_color_channels(pixel) == (128, 255, 64)
        
        # BRG
        opts.rgb_order = "BRG"
        assert opts.reorder_color_channels(pixel) == (64, 255, 128)
        
        # RBG
        opts.rgb_order = "RBG"
        assert opts.reorder_color_channels(pixel) == (255, 64, 128)
        
        # GBR
        opts.rgb_order = "GBR"
        assert opts.reorder_color_channels(pixel) == (128, 64, 255)
    
    def test_pixel_reordering_rows(self):
        """Test pixel reordering for row scanning."""
        width, height = 4, 3
        pixels = [(i % 256, (i + 1) % 256, (i + 2) % 256) for i in range(width * height)]
        
        opts = ExportOptions()
        opts.scan_direction = "Rows"
        opts.scan_order = "LeftToRight"
        
        reordered = opts.reorder_pixels(pixels, width, height)
        assert len(reordered) == width * height
        assert reordered == pixels  # Should be same for default
    
    def test_pixel_reordering_columns(self):
        """Test pixel reordering for column scanning."""
        width, height = 4, 3
        pixels = [(i % 256, (i + 1) % 256, (i + 2) % 256) for i in range(width * height)]
        
        opts = ExportOptions()
        opts.scan_direction = "Columns"
        opts.scan_order = "TopToBottom"
        
        reordered = opts.reorder_pixels(pixels, width, height)
        assert len(reordered) == width * height
    
    def test_serpentine_wiring(self):
        """Test serpentine wiring reordering."""
        width, height = 4, 3
        pixels = [(i % 256, (i + 1) % 256, (i + 2) % 256) for i in range(width * height)]
        
        opts = ExportOptions()
        opts.serpentine = True
        opts.scan_direction = "Rows"
        
        reordered = opts.reorder_pixels(pixels, width, height)
        assert len(reordered) == width * height
    
    def test_color_space_rgb565(self):
        """Test RGB565 color space conversion."""
        opts = ExportOptions()
        opts.color_space = "RGB565"
        
        # Test conversion
        pixel: RGB = (255, 128, 64)
        result = opts.convert_color_space(pixel)
        assert isinstance(result, tuple)
        assert len(result) == 1
        assert isinstance(result[0], int)
        assert 0 <= result[0] <= 0xFFFF
    
    def test_color_space_rgb888(self):
        """Test RGB888 color space (no conversion)."""
        opts = ExportOptions()
        opts.color_space = "RGB888"
        
        pixel: RGB = (255, 128, 64)
        result = opts.convert_color_space(pixel)
        assert result == pixel
    
    def test_bit_depth_trimming(self):
        """Test bit depth trimming."""
        opts = ExportOptions()
        opts.bits_per_channel = (5, 6, 5)  # RGB565-like
        
        pixel: RGB = (255, 255, 255)
        trimmed = opts.trim_to_bit_depth(pixel)
        assert len(trimmed) == 3
        assert all(0 <= c <= 255 for c in trimmed)
    
    def test_number_formatting(self):
        """Test number formatting."""
        opts = ExportOptions()
        
        # Hex
        opts.number_format = "Hex"
        assert opts.format_number(255) == "0xFF"
        assert opts.format_number(4095, 2) == "0x0FFF"
        
        # Decimal
        opts.number_format = "Decimal"
        assert opts.format_number(255) == "255"
        
        # Binary
        opts.number_format = "Binary"
        result = opts.format_number(255)
        assert result.startswith("1")  # Should be binary string
        assert len(result) == 8  # 8 bits
    
    def test_bytes_per_line(self):
        """Test bytes per line setting."""
        opts = ExportOptions()
        assert opts.bytes_per_line == 0
        
        opts.bytes_per_line = 16
        assert opts.bytes_per_line == 16

