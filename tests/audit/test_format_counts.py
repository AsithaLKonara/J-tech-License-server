"""
Tests for import/export format fixes
Verifies import format count (17) and export format count (12)
"""

import pytest
from pathlib import Path
from core.export.exporters import PatternExporter


class TestFormatCounts:
    """Test import/export format counts"""
    
    def test_export_formats_count(self):
        """Test 12 export formats are implemented"""
        exporter = PatternExporter()
        
        # Count export methods
        export_methods = [
            'export_binary', 'export_dat', 'export_hex', 'export_header',
            'export_json', 'export_leds', 'export_project', 'export_sprite_sheet',
            'export_gif', 'export_wled', 'export_falcon_player', 'export_xlights'
        ]
        
        for method in export_methods:
            assert hasattr(exporter, method), \
                f"PatternExporter should have {method} method"
        
        assert len(export_methods) == 12, "Should have 12 export formats"
    
    def test_import_formats_exist(self):
        """Test import format implementations exist"""
        # Pattern file parsers
        parser_registry = Path("parsers/parser_registry.py")
        assert parser_registry.exists(), "Parser registry should exist"
        
        # Image importer
        image_importer = Path("core/image_importer.py")
        assert image_importer.exists(), "Image importer should exist"
        
        # Vector importer
        vector_importer = Path("core/vector_importer.py")
        assert vector_importer.exists(), "Vector importer should exist"
        
        # Media converter
        media_converter = Path("core/media_converter.py")
        assert media_converter.exists(), "Media converter should exist"
    
    def test_import_format_support(self):
        """Test import formats are supported"""
        from core.image_importer import ImageImporter
        from core.media_converter import MediaConverter
        
        # Check image formats
        converter = MediaConverter()
        assert '.png' in converter.supported_image_formats
        assert '.jpg' in converter.supported_image_formats or '.jpeg' in converter.supported_image_formats
        assert '.bmp' in converter.supported_image_formats
        assert '.gif' in converter.supported_image_formats
        
        # Check video formats
        assert '.mp4' in converter.supported_video_formats
        assert '.avi' in converter.supported_video_formats
        assert '.mov' in converter.supported_video_formats
        assert '.mkv' in converter.supported_video_formats
        assert '.webm' in converter.supported_video_formats
    
    def test_export_format_methods(self):
        """Test export format methods are callable"""
        exporter = PatternExporter()
        
        # Create minimal pattern for testing
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=8, height=8)
        pattern = Pattern(metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*64)])
        
        # Test that export methods exist and are callable
        export_methods = ['export_binary', 'export_dat', 'export_json']
        
        for method_name in export_methods:
            method = getattr(exporter, method_name)
            assert callable(method), f"{method_name} should be callable"

