"""
Integration tests for service layer integration.

Tests how services work together with the repository and UI components.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

from core.pattern import Pattern, PatternMetadata, Frame
from core.repositories.pattern_repository import PatternRepository
from core.services.pattern_service import PatternService
from core.services.export_service import ExportService
from core.services.flash_service import FlashService


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for Qt-dependent tests."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def clean_repository():
    """Reset repository state before each test."""
    PatternRepository.clear_pattern()
    PatternRepository._instance = None
    yield
    PatternRepository.clear_pattern()
    PatternRepository._instance = None


class TestPatternServiceRepositoryIntegration:
    """Test PatternService integration with PatternRepository."""
    
    def test_load_pattern_updates_repository(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that loading pattern updates repository."""
        service = PatternService()
        
        # Mock parser registry
        with patch.object(service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            
            test_file = tmp_path / "test.bin"
            test_file.write_bytes(b"test")
            
            service.load_pattern(str(test_file))
            
            # Verify repository was updated
            assert PatternRepository.get_current_pattern() == sample_pattern
            assert PatternRepository.get_current_file() == str(test_file)
            assert PatternRepository.is_dirty() is False
    
    def test_save_pattern_updates_repository(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that saving pattern updates repository."""
        service = PatternService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        test_file = tmp_path / "output.bin"
        
        with patch.object(sample_pattern, 'save_to_file') as mock_save:
            service.save_pattern(sample_pattern, str(test_file))
            
            # Verify repository was updated
            assert PatternRepository.get_current_file() == str(test_file)
            assert PatternRepository.is_dirty() is False
    
    def test_create_pattern_updates_repository(self, clean_repository, qapp):
        """Test that creating pattern updates repository."""
        service = PatternService()
        
        pattern = service.create_pattern(name="New Pattern", width=16, height=16)
        
        # Verify repository was updated
        assert PatternRepository.get_current_pattern() == pattern
        assert PatternRepository.get_current_file() is None
    
    def test_pattern_service_repository_signals(self, clean_repository, qapp, sample_pattern, qtbot):
        """Test that repository signals are emitted when using service."""
        service = PatternService()
        repo = PatternRepository.instance()
        
        # Track signal emissions
        pattern_changed_calls = []
        repo.pattern_changed.connect(lambda p: pattern_changed_calls.append(p))
        
        # Create pattern via service
        with qtbot.waitSignal(repo.pattern_changed, timeout=1000):
            service.create_pattern(name="Test", width=8, height=8)
        
        assert len(pattern_changed_calls) == 1


class TestExportServicePatternRepositoryIntegration:
    """Test ExportService integration with PatternRepository."""
    
    def test_export_uses_repository_pattern(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that export can use pattern from repository."""
        service = ExportService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        # Mock exporter
        with patch.object(service.exporter, 'export_binary') as mock_export:
            mock_export.return_value = tmp_path / "output.bin"
            
            output_file = tmp_path / "output.bin"
            service.export_pattern(sample_pattern, str(output_file), "bin")
            
            mock_export.assert_called_once()
    
    def test_export_validation_with_repository_pattern(self, clean_repository, qapp, sample_pattern):
        """Test export validation with repository pattern."""
        service = ExportService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        with patch('core.services.export_service.generate_export_preview') as mock_preview:
            mock_preview.return_value = Mock()
            
            is_valid, error, preview = service.validate_export(sample_pattern, "bin")
            
            assert is_valid is True
            assert error is None


class TestFlashServicePatternRepositoryIntegration:
    """Test FlashService integration with PatternRepository."""
    
    @patch('core.services.flash_service.get_uploader')
    def test_build_firmware_uses_repository_pattern(self, mock_get_uploader, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that firmware build can use pattern from repository."""
        service = FlashService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        mock_uploader = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.firmware_path = tmp_path / "firmware.bin"
        mock_uploader.build_firmware.return_value = mock_result
        mock_get_uploader.return_value = mock_uploader
        
        result = service.build_firmware(sample_pattern, "esp8266")
        
        assert result.success is True
        mock_uploader.build_firmware.assert_called_once()


class TestServiceWorkflowIntegration:
    """Test complete workflows using multiple services."""
    
    def test_create_load_export_workflow(self, clean_repository, qapp, tmp_path):
        """Test complete workflow: create -> load -> export."""
        pattern_service = PatternService()
        export_service = ExportService()
        
        # Step 1: Create pattern
        pattern = pattern_service.create_pattern(name="Workflow Test", width=8, height=8)
        assert PatternRepository.get_current_pattern() == pattern
        
        # Step 2: Add a frame (simulate editing)
        frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
        pattern.frames.append(frame)
        PatternRepository.set_dirty(True)
        assert PatternRepository.is_dirty() is True
        
        # Step 3: Export pattern
        with patch.object(export_service.exporter, 'export_binary') as mock_export:
            mock_export.return_value = tmp_path / "export.bin"
            output_file = tmp_path / "export.bin"
            result = export_service.export_pattern(pattern, str(output_file), "bin")
            
            assert result == tmp_path / "export.bin"
            mock_export.assert_called_once()
    
    def test_load_validate_export_workflow(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test workflow: load -> validate -> export."""
        pattern_service = PatternService()
        export_service = ExportService()
        
        # Step 1: Load pattern
        with patch.object(pattern_service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            test_file = tmp_path / "input.bin"
            test_file.write_bytes(b"test")
            
            pattern, format_name = pattern_service.load_pattern(str(test_file))
            assert pattern == sample_pattern
        
        # Step 2: Validate export
        with patch('core.services.export_service.generate_export_preview') as mock_preview:
            mock_preview.return_value = Mock()
            is_valid, error, preview = export_service.validate_export(pattern, "bin")
            assert is_valid is True
        
        # Step 3: Export
        with patch.object(export_service.exporter, 'export_binary') as mock_export:
            mock_export.return_value = tmp_path / "output.bin"
            output_file = tmp_path / "output.bin"
            result = export_service.export_pattern(pattern, str(output_file), "bin")
            assert result == tmp_path / "output.bin"


class TestRepositorySignalIntegration:
    """Test repository signal integration with services."""
    
    def test_pattern_changed_signal_on_load(self, clean_repository, qapp, sample_pattern, qtbot, tmp_path):
        """Test that pattern_changed signal is emitted when loading via service."""
        service = PatternService()
        repo = PatternRepository.instance()
        
        with patch.object(service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            test_file = tmp_path / "test.bin"
            test_file.write_bytes(b"test")
            
            with qtbot.waitSignal(repo.pattern_changed, timeout=1000) as blocker:
                service.load_pattern(str(test_file))
            
            assert blocker.args == [sample_pattern]
    
    def test_pattern_changed_signal_on_create(self, clean_repository, qapp, qtbot):
        """Test that pattern_changed signal is emitted when creating via service."""
        service = PatternService()
        repo = PatternRepository.instance()
        
        with qtbot.waitSignal(repo.pattern_cleared, timeout=1000):
            PatternRepository.clear_pattern()
        
        with qtbot.waitSignal(repo.pattern_changed, timeout=1000) as blocker:
            pattern = service.create_pattern(name="Signal Test", width=8, height=8)
        
        assert blocker.args == [pattern]
    
    def test_multiple_services_receive_signals(self, clean_repository, qapp, sample_pattern, qtbot, tmp_path):
        """Test that multiple services can receive repository signals."""
        pattern_service = PatternService()
        export_service = ExportService()
        repo = PatternRepository.instance()
        
        # Track signal emissions
        pattern_changed_calls = []
        repo.pattern_changed.connect(lambda p: pattern_changed_calls.append(p))
        
        # Load pattern via service
        with patch.object(pattern_service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            test_file = tmp_path / "test.bin"
            test_file.write_bytes(b"test")
            
            with qtbot.waitSignal(repo.pattern_changed, timeout=1000):
                pattern_service.load_pattern(str(test_file))
        
        # Verify signal was received
        assert len(pattern_changed_calls) == 1
        assert pattern_changed_calls[0] == sample_pattern


class TestServiceErrorHandlingIntegration:
    """Test error handling across service boundaries."""
    
    def test_load_error_does_not_update_repository(self, clean_repository, qapp, tmp_path):
        """Test that load errors don't update repository."""
        service = PatternService()
        original_pattern = PatternRepository.get_current_pattern()
        
        with patch.object(service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.side_effect = FileNotFoundError("File not found")
            
            with pytest.raises(FileNotFoundError):
                service.load_pattern("/nonexistent/file.bin")
            
            # Repository should remain unchanged
            assert PatternRepository.get_current_pattern() == original_pattern
    
    def test_export_error_handling(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test export error handling."""
        service = ExportService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        with patch.object(service.exporter, 'export_binary') as mock_export:
            mock_export.side_effect = IOError("Write failed")
            
            with pytest.raises(IOError):
                service.export_pattern(sample_pattern, str(tmp_path / "output.bin"), "bin")
    
    def test_build_error_handling(self, clean_repository, qapp, sample_pattern):
        """Test firmware build error handling."""
        service = FlashService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        with patch('core.services.flash_service.get_uploader') as mock_get:
            mock_uploader = Mock()
            mock_uploader.build_firmware.side_effect = Exception("Build failed")
            mock_get.return_value = mock_uploader
            
            with pytest.raises(RuntimeError, match="build failed"):
                service.build_firmware(sample_pattern, "esp8266")


class TestServiceStateConsistency:
    """Test state consistency across services."""
    
    def test_repository_state_consistent_across_services(self, clean_repository, qapp, sample_pattern):
        """Test that repository state is consistent when accessed from multiple services."""
        pattern_service = PatternService()
        export_service = ExportService()
        
        # Set pattern via repository
        PatternRepository.set_current_pattern(sample_pattern)
        
        # Both services should see the same pattern
        pattern_from_service = pattern_service.get_current_pattern()
        pattern_from_repo = PatternRepository.get_current_pattern()
        
        assert pattern_from_service == pattern_from_repo == sample_pattern
    
    def test_dirty_state_consistency(self, clean_repository, qapp, sample_pattern):
        """Test that dirty state is consistent across services."""
        pattern_service = PatternService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        # Mark as dirty via service
        pattern_service.set_dirty(True)
        assert PatternRepository.is_dirty() is True
        
        # Mark as clean via repository
        PatternRepository.set_dirty(False)
        assert pattern_service.is_dirty() is False

