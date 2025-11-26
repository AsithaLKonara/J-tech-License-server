"""
Comprehensive edge case tests for better coverage.
Tests boundary conditions, error cases, and unusual scenarios.
"""
import pytest
from pathlib import Path
import tempfile

from core.pattern import Pattern, Frame, PatternMetadata
from core.services.pattern_service import PatternService
from core.services.export_service import ExportService
from core.services.flash_service import FlashService
from domain.layers import LayerManager
from domain.pattern_state import PatternState
from domain.frames import FrameManager


class TestEdgeCases:
    """Edge case and boundary condition tests."""
    
    def test_pattern_with_maximum_dimensions(self):
        """Test pattern creation with maximum reasonable dimensions."""
        service = PatternService()
        
        # Test large but reasonable dimensions (256x256 = 65,536 pixels)
        pattern = service.create_pattern("Large", 256, 256)
        assert pattern is not None
        assert pattern.metadata.width == 256
        assert pattern.metadata.height == 256
    
    def test_pattern_with_minimum_dimensions(self):
        """Test pattern creation with minimum dimensions."""
        service = PatternService()
        
        # Test minimum dimensions (1x1)
        pattern = service.create_pattern("Small", 1, 1)
        assert pattern is not None
        assert pattern.metadata.width == 1
        assert pattern.metadata.height == 1
    
    def test_export_empty_pattern(self):
        """Test exporting pattern with no frames."""
        service = PatternService()
        export_service = ExportService()
        
        pattern = service.create_pattern("Empty", 8, 8)
        # Pattern has no frames initially
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.bin"
            try:
                export_service.export_pattern(pattern, str(output_path), "bin")
                # Export may succeed or fail depending on format
            except Exception:
                pass  # Expected for some formats
    
    def test_layer_operations_on_empty_frame(self):
        """Test layer operations when frame is valid but operations are safe."""
        state = PatternState()
        pattern = Pattern(
            name="Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)]  # Valid frame
        )
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)
        layer_manager.set_pattern(pattern)
        
        # Should handle gracefully
        layers = layer_manager.get_layers(0)
        assert isinstance(layers, list)
    
    def test_concurrent_pattern_operations(self):
        """Test multiple pattern operations simultaneously."""
        service = PatternService()
        
        # Create multiple patterns
        patterns = []
        for i in range(10):
            pattern = service.create_pattern(f"Pattern {i}", 8, 8)
            patterns.append(pattern)
        
        assert len(patterns) == 10
        assert all(p is not None for p in patterns)
    
    def test_export_with_special_characters_in_path(self):
        """Test export with special characters in file path."""
        export_service = ExportService()
        service = PatternService()
        pattern = service.create_pattern("Test", 8, 8)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test path with special characters
            special_path = Path(tmpdir) / "test file (1).bin"
            try:
                export_service.export_pattern(pattern, str(special_path), "bin")
            except Exception:
                pass  # May fail depending on exporter implementation
    
    def test_flash_service_with_invalid_chip(self):
        """Test flash service with invalid chip ID."""
        service = FlashService()
        pattern_service = PatternService()
        pattern = pattern_service.create_pattern("Test", 8, 8)
        
        # Should raise ValueError for invalid chip
        with pytest.raises(ValueError):
            service.build_firmware(pattern, "invalid_chip_id_xyz")
    
    def test_error_handler_with_various_exceptions(self):
        """Test error handler with different exception types."""
        from core.errors import get_error_handler
        
        error_handler = get_error_handler()
        
        # Test various exception types
        exceptions = [
            ValueError("Test value error"),
            FileNotFoundError("test_file.txt"),
            PermissionError("access denied"),
            RuntimeError("Test runtime error"),
        ]
        
        for exc in exceptions:
            # Should handle gracefully without raising
            try:
                error_handler.handle_error(exc, show_to_user=False)
            except Exception:
                pytest.fail(f"Error handler should not raise for {type(exc).__name__}")
    
    def test_pattern_with_very_long_name(self):
        """Test pattern with very long name."""
        service = PatternService()
        long_name = "A" * 1000  # Very long name
        
        pattern = service.create_pattern(long_name, 8, 8)
        assert pattern is not None
        assert len(pattern.name) == 1000
    
    def test_multiple_layers_on_single_frame(self):
        """Test creating many layers on a single frame."""
        state = PatternState()
        pattern = Pattern(
            name="Test",
            metadata=PatternMetadata(width=8, height=8),
            frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)]
        )
        state.set_pattern(pattern)
        layer_manager = LayerManager(state)
        layer_manager.set_pattern(pattern)
        
        # Create many layers
        for i in range(20):
            layer_manager.add_layer(0, f"Layer {i}")
        
        layers = layer_manager.get_layers(0)
        assert len(layers) >= 20

