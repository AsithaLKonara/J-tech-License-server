"""
Unit tests for ExportService.

Tests the business logic service for pattern export operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from core.pattern import Pattern, PatternMetadata, Frame
from core.services.export_service import ExportService
from core.export_options import ExportOptions
from core.export.validator import ExportValidationError


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def export_service():
    """Create an ExportService instance."""
    return ExportService()


class TestExportServiceInitialization:
    """Test service initialization."""
    
    def test_init_default(self, export_service):
        """Test that service initializes with default options."""
        assert export_service.exporter is not None
        assert export_service.options is not None
    
    def test_init_with_options(self):
        """Test that service initializes with custom options."""
        options = ExportOptions()
        service = ExportService(options)
        assert service.options == options


class TestExportServiceGetAvailableFormats:
    """Test getting available export formats."""
    
    def test_get_available_formats(self, export_service):
        """Test getting list of available formats."""
        formats = export_service.get_available_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'bin' in formats
        assert 'hex' in formats
        assert 'json' in formats
    
    def test_get_available_formats_returns_copy(self, export_service):
        """Test that returned list is a copy."""
        formats1 = export_service.get_available_formats()
        formats2 = export_service.get_available_formats()
        
        assert formats1 is not formats2  # Should be different objects


class TestExportServiceExportPattern:
    """Test pattern export operations."""
    
    @patch('core.services.export_service.PatternExporter')
    def test_export_pattern_bin(self, mock_exporter_class, export_service, sample_pattern, tmp_path):
        """Test exporting pattern as binary."""
        mock_exporter = Mock()
        mock_exporter.export_binary.return_value = tmp_path / "output.bin"
        export_service.exporter = mock_exporter
        
        output_file = tmp_path / "output.bin"
        result = export_service.export_pattern(sample_pattern, str(output_file), "bin")
        
        assert result == tmp_path / "output.bin"
        mock_exporter.export_binary.assert_called_once()
    
    @patch('core.services.export_service.PatternExporter')
    def test_export_pattern_hex(self, mock_exporter_class, export_service, sample_pattern, tmp_path):
        """Test exporting pattern as hex."""
        mock_exporter = Mock()
        mock_exporter.export_hex.return_value = tmp_path / "output.hex"
        export_service.exporter = mock_exporter
        
        output_file = tmp_path / "output.hex"
        result = export_service.export_pattern(sample_pattern, str(output_file), "hex")
        
        assert result == tmp_path / "output.hex"
        mock_exporter.export_hex.assert_called_once()
    
    @patch('core.services.export_service.PatternExporter')
    def test_export_pattern_json(self, mock_exporter_class, export_service, sample_pattern, tmp_path):
        """Test exporting pattern as JSON."""
        mock_exporter = Mock()
        mock_exporter.export_json.return_value = tmp_path / "output.json"
        export_service.exporter = mock_exporter
        
        output_file = tmp_path / "output.json"
        result = export_service.export_pattern(sample_pattern, str(output_file), "json")
        
        assert result == tmp_path / "output.json"
        mock_exporter.export_json.assert_called_once()
    
    def test_export_pattern_unsupported_format(self, export_service, sample_pattern, tmp_path):
        """Test exporting with unsupported format raises error."""
        output_file = tmp_path / "output.xyz"
        
        with pytest.raises(ValueError, match="Unsupported"):
            export_service.export_pattern(sample_pattern, str(output_file), "xyz")
    
    def test_export_pattern_case_insensitive(self, export_service, sample_pattern, tmp_path):
        """Test that format is case-insensitive."""
        with patch.object(export_service.exporter, 'export_binary') as mock_export:
            mock_export.return_value = tmp_path / "output.bin"
            output_file = tmp_path / "output.bin"
            
            export_service.export_pattern(sample_pattern, str(output_file), "BIN")
            export_service.export_pattern(sample_pattern, str(output_file), "Bin")
            
            assert mock_export.call_count == 2


class TestExportServiceValidateExport:
    """Test export validation."""
    
    @patch('core.services.export_service.generate_export_preview')
    def test_validate_export_success(self, mock_preview, export_service, sample_pattern):
        """Test validating a valid export."""
        mock_preview_result = Mock()
        mock_preview.return_value = mock_preview_result
        
        is_valid, error, preview = export_service.validate_export(sample_pattern, "bin")
        
        assert is_valid is True
        assert error is None
        assert preview == mock_preview_result
    
    @patch('core.services.export_service.generate_export_preview')
    def test_validate_export_validation_error(self, mock_preview, export_service, sample_pattern):
        """Test validating export with validation error."""
        mock_preview.side_effect = ExportValidationError("Invalid pattern")
        
        is_valid, error, preview = export_service.validate_export(sample_pattern, "bin")
        
        assert is_valid is False
        assert error == "Invalid pattern"
        assert preview is None
    
    @patch('core.services.export_service.generate_export_preview')
    def test_validate_export_general_exception(self, mock_preview, export_service, sample_pattern):
        """Test validating export with general exception."""
        mock_preview.side_effect = Exception("Unexpected error")
        
        is_valid, error, preview = export_service.validate_export(sample_pattern, "bin")
        
        assert is_valid is False
        assert "Validation failed" in error
        assert preview is None
    
    def test_validate_export_unsupported_format(self, export_service, sample_pattern):
        """Test validating unsupported format."""
        is_valid, error, preview = export_service.validate_export(sample_pattern, "xyz")
        
        assert is_valid is False
        assert "Unsupported" in error
        assert preview is None


class TestExportServiceGetExportPreview:
    """Test getting export preview."""
    
    @patch('core.services.export_service.generate_export_preview')
    def test_get_export_preview_success(self, mock_preview, export_service, sample_pattern):
        """Test getting export preview successfully."""
        mock_preview_result = Mock()
        mock_preview.return_value = mock_preview_result
        
        preview = export_service.get_export_preview(sample_pattern, "bin")
        
        assert preview == mock_preview_result
    
    @patch('core.services.export_service.generate_export_preview')
    def test_get_export_preview_failure(self, mock_preview, export_service, sample_pattern):
        """Test getting export preview with error."""
        mock_preview.side_effect = Exception("Preview error")
        
        preview = export_service.get_export_preview(sample_pattern, "bin")
        
        assert preview is None


class TestExportServiceSetExportOptions:
    """Test setting export options."""
    
    def test_set_export_options(self, export_service):
        """Test updating export options."""
        new_options = ExportOptions()
        new_options.rgb_order = "BGR"
        
        export_service.set_export_options(new_options)
        
        assert export_service.options == new_options
        assert export_service.exporter is not None  # Should create new exporter

