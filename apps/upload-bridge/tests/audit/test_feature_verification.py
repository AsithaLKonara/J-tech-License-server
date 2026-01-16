"""
Tests for feature verification
Verifies features from FEATURE_INVENTORY.md have implementation files
"""

import pytest
from pathlib import Path
import re


class TestFeatureVerification:
    """Test feature implementation files exist"""
    
    def test_feature_inventory_exists(self):
        """Test FEATURE_INVENTORY.md exists"""
        inventory = Path("docs/FEATURE_INVENTORY.md")
        assert inventory.exists(), "FEATURE_INVENTORY.md should exist"
    
    def test_drawing_tools_exist(self):
        """Test all 8 drawing tools are implemented"""
        tools_file = Path("domain/drawing/tools.py")
        assert tools_file.exists(), "domain/drawing/tools.py should exist"
        
        content = tools_file.read_text(encoding='utf-8')
        
        # Check for all 8 tool classes
        tools = ['PixelTool', 'RectangleTool', 'CircleTool', 'LineTool', 
                'FillTool', 'GradientTool', 'RandomSprayTool', 'TextTool']
        
        for tool in tools:
            assert tool in content, f"{tool} should be in tools.py"
    
    def test_effects_library_exists(self):
        """Test effects library is implemented"""
        effects_lib = Path("domain/effects/library.py")
        assert effects_lib.exists(), "domain/effects/library.py should exist"
    
    def test_export_formats_exist(self):
        """Test export formats are implemented"""
        exporters = Path("core/export/exporters.py")
        assert exporters.exists(), "core/export/exporters.py should exist"
        
        content = exporters.read_text(encoding='utf-8')
        
        # Check for export methods
        export_methods = ['export_binary', 'export_dat', 'export_hex', 
                         'export_json', 'export_wled', 'export_gif']
        
        for method in export_methods:
            assert method in content, f"{method} should be in exporters.py"
    
    def test_import_formats_exist(self):
        """Test import formats are implemented"""
        # Check image importer
        image_importer = Path("core/image_importer.py")
        assert image_importer.exists(), "core/image_importer.py should exist"
        
        # Check media converter
        media_converter = Path("core/media_converter.py")
        assert media_converter.exists(), "core/media_converter.py should exist"
        
        # Check parser registry
        parser_registry = Path("parsers/parser_registry.py")
        assert parser_registry.exists(), "parsers/parser_registry.py should exist"

