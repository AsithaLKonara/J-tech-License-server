"""
Integration tests for UI and service layer integration.

Tests how UI components interact with services and repository.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QObject, Signal

from core.pattern import Pattern, PatternMetadata, Frame
from core.repositories.pattern_repository import PatternRepository
from core.services.pattern_service import PatternService
from core.services.export_service import ExportService


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


class MockUITab(QWidget):
    """Mock UI tab that subscribes to repository signals."""
    
    pattern_loaded = Signal(Pattern)
    
    def __init__(self):
        super().__init__()
        self.loaded_patterns = []
        self.cleared_count = 0
        
        # Subscribe to repository signals
        repo = PatternRepository.instance()
        repo.pattern_changed.connect(self.on_pattern_changed)
        repo.pattern_cleared.connect(self.on_pattern_cleared)
    
    def on_pattern_changed(self, pattern: Pattern):
        """Handle pattern changed signal."""
        self.loaded_patterns.append(pattern)
        self.pattern_loaded.emit(pattern)
    
    def on_pattern_cleared(self):
        """Handle pattern cleared signal."""
        self.cleared_count += 1


class TestMainWindowServiceIntegration:
    """Test MainWindow integration with services."""
    
    def test_mainwindow_uses_pattern_service(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that MainWindow can use PatternService for loading."""
        service = PatternService()
        
        with patch.object(service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            test_file = tmp_path / "test.bin"
            test_file.write_bytes(b"test")
            
            # Simulate MainWindow loading pattern
            pattern, format_name = service.load_pattern(str(test_file))
            
            # Verify pattern is in repository
            assert PatternRepository.get_current_pattern() == sample_pattern
            assert PatternRepository.get_current_file() == str(test_file)
    
    def test_mainwindow_uses_export_service(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that MainWindow can use ExportService for exporting."""
        service = ExportService()
        PatternRepository.set_current_pattern(sample_pattern)
        
        with patch.object(service.exporter, 'export_binary') as mock_export:
            mock_export.return_value = tmp_path / "output.bin"
            output_file = tmp_path / "output.bin"
            
            # Simulate MainWindow exporting pattern
            result = service.export_pattern(sample_pattern, str(output_file), "bin")
            
            assert result == tmp_path / "output.bin"
            mock_export.assert_called_once()


class TestTabRepositorySignalIntegration:
    """Test how tabs receive repository signals."""
    
    def test_tab_receives_pattern_changed_signal(self, clean_repository, qapp, sample_pattern, qtbot):
        """Test that tab receives pattern_changed signal."""
        tab = MockUITab()
        service = PatternService()
        
        # Create pattern via service
        with qtbot.waitSignal(tab.pattern_loaded, timeout=1000) as blocker:
            pattern = service.create_pattern(name="Signal Test", width=8, height=8)
        
        # Verify tab received signal
        assert len(tab.loaded_patterns) == 1
        assert tab.loaded_patterns[0] == pattern
        assert blocker.args == [pattern]
    
    def test_tab_receives_pattern_cleared_signal(self, clean_repository, qapp, sample_pattern, qtbot):
        """Test that tab receives pattern_cleared signal."""
        tab = MockUITab()
        PatternRepository.set_current_pattern(sample_pattern)
        
        # Clear pattern
        with qtbot.waitSignal(PatternRepository.instance().pattern_cleared, timeout=1000):
            PatternRepository.clear_pattern()
        
        # Verify tab received signal
        assert tab.cleared_count == 1
    
    def test_multiple_tabs_receive_signals(self, clean_repository, qapp, sample_pattern, qtbot):
        """Test that multiple tabs receive repository signals."""
        tab1 = MockUITab()
        tab2 = MockUITab()
        service = PatternService()
        
        # Create pattern via service
        with qtbot.waitSignal(tab1.pattern_loaded, timeout=1000):
            pattern = service.create_pattern(name="Multi Tab Test", width=8, height=8)
        
        # Both tabs should receive signal
        assert len(tab1.loaded_patterns) == 1
        assert len(tab2.loaded_patterns) == 1
        assert tab1.loaded_patterns[0] == pattern
        assert tab2.loaded_patterns[0] == pattern


class TestTabServiceWorkflow:
    """Test complete workflows from tab perspective."""
    
    def test_tab_load_export_workflow(self, clean_repository, qapp, sample_pattern, tmp_path, qtbot):
        """Test workflow: tab loads pattern, user exports."""
        tab = MockUITab()
        pattern_service = PatternService()
        export_service = ExportService()
        
        # Step 1: Load pattern (simulates user opening file)
        with patch.object(pattern_service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            test_file = tmp_path / "input.bin"
            test_file.write_bytes(b"test")
            
            with qtbot.waitSignal(tab.pattern_loaded, timeout=1000):
                pattern, format_name = pattern_service.load_pattern(str(test_file))
            
            # Tab should have received signal
            assert len(tab.loaded_patterns) == 1
        
        # Step 2: Export pattern (simulates user exporting)
        with patch.object(export_service.exporter, 'export_binary') as mock_export:
            mock_export.return_value = tmp_path / "output.bin"
            output_file = tmp_path / "output.bin"
            result = export_service.export_pattern(pattern, str(output_file), "bin")
            
            assert result == tmp_path / "output.bin"
    
    def test_tab_create_modify_workflow(self, clean_repository, qapp, qtbot):
        """Test workflow: tab creates pattern, user modifies."""
        tab = MockUITab()
        pattern_service = PatternService()
        
        # Step 1: Create pattern
        with qtbot.waitSignal(tab.pattern_loaded, timeout=1000):
            pattern = pattern_service.create_pattern(name="New Pattern", width=8, height=8)
        
        # Step 2: Modify pattern (simulates user editing)
        frame = Frame(pixels=[(0, 255, 0)] * 64, duration_ms=200)
        pattern.frames.append(frame)
        
        # Mark as dirty
        pattern_service.set_dirty(True)
        assert PatternRepository.is_dirty() is True
        
        # Pattern should still be in repository
        assert PatternRepository.get_current_pattern() == pattern


class TestServiceBackwardCompatibility:
    """Test backward compatibility with legacy UI code."""
    
    def test_legacy_pattern_reference_still_works(self, clean_repository, qapp, sample_pattern):
        """Test that legacy pattern references still work."""
        # Simulate legacy code that uses self.pattern
        class LegacyTab:
            def __init__(self):
                self.pattern = None
                repo = PatternRepository.instance()
                repo.pattern_changed.connect(self.on_pattern_changed)
            
            def on_pattern_changed(self, pattern: Pattern):
                """Sync legacy reference."""
                self.pattern = pattern
        
        tab = LegacyTab()
        service = PatternService()
        
        # Create pattern via service
        pattern = service.create_pattern(name="Legacy Test", width=8, height=8)
        
        # Legacy reference should be synced
        assert tab.pattern == pattern
    
    def test_legacy_file_reference_still_works(self, clean_repository, qapp, sample_pattern, tmp_path):
        """Test that legacy file references still work."""
        # Simulate legacy code that uses self.current_file
        class LegacyTab:
            def __init__(self):
                self.current_file = None
                repo = PatternRepository.instance()
                # In real code, would connect to pattern_changed to sync
        
        tab = LegacyTab()
        service = PatternService()
        
        # Load pattern via service
        with patch.object(service.parser_registry, 'parse_file') as mock_parse:
            mock_parse.return_value = (sample_pattern, "bin")
            test_file = tmp_path / "test.bin"
            test_file.write_bytes(b"test")
            
            service.load_pattern(str(test_file))
            
            # Legacy code can still access file path
            tab.current_file = PatternRepository.get_current_file()
            assert tab.current_file == str(test_file)

