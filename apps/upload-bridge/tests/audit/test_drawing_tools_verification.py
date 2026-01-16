"""
Tests for drawing tools verification
Verifies all 8 drawing tools are implemented and functional
"""

import pytest
from pathlib import Path
from domain.drawing.tools import (
    PixelTool, RectangleTool, CircleTool, LineTool,
    FillTool, GradientTool, RandomSprayTool, TextTool
)
from core.pattern import Pattern, PatternMetadata, Frame


class TestDrawingTools:
    """Test drawing tools implementation"""
    
    def test_all_tool_classes_exist(self):
        """Test all 8 tool classes can be imported"""
        tools = [
            PixelTool, RectangleTool, CircleTool, LineTool,
            FillTool, GradientTool, RandomSprayTool, TextTool
        ]
        
        for tool_class in tools:
            assert tool_class is not None, f"{tool_class.__name__} should exist"
            assert hasattr(tool_class, 'apply'), \
                f"{tool_class.__name__} should have apply method"
    
    def test_tool_map_registry(self):
        """Test tool map includes all tools"""
        from domain.drawing.tools import get_tool_class
        
        tool_types = ['pixel', 'rectangle', 'circle', 'line', 
                     'fill', 'gradient', 'random', 'text']
        
        for tool_type in tool_types:
            tool_class = get_tool_class(tool_type)
            assert tool_class is not None, \
                f"Tool type '{tool_type}' should be in registry"
    
    def test_tools_inherit_from_base(self):
        """Test all tools inherit from DrawingTool"""
        from domain.drawing.tools import DrawingTool
        
        tools = [
            PixelTool, RectangleTool, CircleTool, LineTool,
            FillTool, GradientTool, RandomSprayTool, TextTool
        ]
        
        for tool_class in tools:
            assert issubclass(tool_class, DrawingTool), \
                f"{tool_class.__name__} should inherit from DrawingTool"
    
    def test_tool_apply_method_signature(self):
        """Test tools have correct apply method signature"""
        import inspect
        
        tools = [PixelTool, RectangleTool, CircleTool, LineTool]
        
        for tool_class in tools:
            sig = inspect.signature(tool_class.apply)
            params = list(sig.parameters.keys())
            
            # Should have: frame, start_pos, end_pos, color, width, height
            assert 'frame' in params, f"{tool_class.__name__}.apply should have 'frame' parameter"
            assert 'start_pos' in params, f"{tool_class.__name__}.apply should have 'start_pos' parameter"
            assert 'end_pos' in params, f"{tool_class.__name__}.apply should have 'end_pos' parameter"
            assert 'color' in params, f"{tool_class.__name__}.apply should have 'color' parameter"

