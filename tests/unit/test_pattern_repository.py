"""
Unit tests for PatternRepository.

Tests the singleton pattern repository that manages the current pattern state.
"""

import pytest
from PySide6.QtCore import QObject

from core.pattern import Pattern, PatternMetadata, Frame
from core.repositories.pattern_repository import PatternRepository


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def clean_repository():
    """Reset repository state before each test."""
    # Clear any existing pattern
    PatternRepository.clear_pattern()
    # Reset singleton instance
    PatternRepository._instance = None
    yield
    # Cleanup after test
    PatternRepository.clear_pattern()
    PatternRepository._instance = None


class TestPatternRepositorySingleton:
    """Test singleton behavior."""
    
    def test_singleton_instance(self, clean_repository):
        """Test that instance() returns the same singleton."""
        instance1 = PatternRepository.instance()
        instance2 = PatternRepository.instance()
        assert instance1 is instance2
    
    def test_direct_instantiation_raises_error(self, clean_repository):
        """Test that direct instantiation raises RuntimeError."""
        PatternRepository.instance()  # Create instance first
        with pytest.raises(RuntimeError, match="singleton"):
            PatternRepository()


class TestPatternRepositoryPatternManagement:
    """Test pattern get/set operations."""
    
    def test_get_current_pattern_initially_none(self, clean_repository):
        """Test that get_current_pattern returns None initially."""
        assert PatternRepository.get_current_pattern() is None
    
    def test_set_current_pattern(self, clean_repository, sample_pattern):
        """Test setting the current pattern."""
        PatternRepository.set_current_pattern(sample_pattern)
        assert PatternRepository.get_current_pattern() == sample_pattern
    
    def test_set_current_pattern_with_file_path(self, clean_repository, sample_pattern):
        """Test setting pattern with file path."""
        file_path = "/path/to/pattern.bin"
        PatternRepository.set_current_pattern(sample_pattern, file_path)
        assert PatternRepository.get_current_pattern() == sample_pattern
        assert PatternRepository.get_current_file() == file_path
    
    def test_set_current_pattern_type_check(self, clean_repository):
        """Test that set_current_pattern validates pattern type."""
        with pytest.raises(TypeError, match="Pattern"):
            PatternRepository.set_current_pattern("not a pattern")
    
    def test_clear_pattern(self, clean_repository, sample_pattern):
        """Test clearing the current pattern."""
        PatternRepository.set_current_pattern(sample_pattern)
        PatternRepository.clear_pattern()
        assert PatternRepository.get_current_pattern() is None
        assert PatternRepository.get_current_file() is None


class TestPatternRepositoryFileManagement:
    """Test file path management."""
    
    def test_get_current_file_initially_none(self, clean_repository):
        """Test that get_current_file returns None initially."""
        assert PatternRepository.get_current_file() is None
    
    def test_set_current_file(self, clean_repository, sample_pattern):
        """Test setting the file path."""
        PatternRepository.set_current_pattern(sample_pattern)
        file_path = "/path/to/pattern.bin"
        PatternRepository.set_current_file(file_path)
        assert PatternRepository.get_current_file() == file_path
    
    def test_set_current_file_to_none(self, clean_repository, sample_pattern):
        """Test clearing the file path."""
        PatternRepository.set_current_pattern(sample_pattern, "/path/to/file.bin")
        PatternRepository.set_current_file(None)
        assert PatternRepository.get_current_file() is None


class TestPatternRepositoryDirtyState:
    """Test dirty state management."""
    
    def test_is_dirty_initially_false(self, clean_repository):
        """Test that is_dirty returns False initially."""
        assert PatternRepository.is_dirty() is False
    
    def test_set_dirty(self, clean_repository, sample_pattern):
        """Test marking pattern as dirty."""
        PatternRepository.set_current_pattern(sample_pattern)
        PatternRepository.set_dirty(True)
        assert PatternRepository.is_dirty() is True
    
    def test_set_dirty_false(self, clean_repository, sample_pattern):
        """Test marking pattern as clean."""
        PatternRepository.set_current_pattern(sample_pattern)
        PatternRepository.set_dirty(True)
        PatternRepository.set_dirty(False)
        assert PatternRepository.is_dirty() is False
    
    def test_set_pattern_clears_dirty(self, clean_repository, sample_pattern):
        """Test that setting pattern clears dirty state."""
        PatternRepository.set_current_pattern(sample_pattern)
        PatternRepository.set_dirty(True)
        PatternRepository.set_current_pattern(sample_pattern)
        assert PatternRepository.is_dirty() is False


class TestPatternRepositorySignals:
    """Test Qt signal emissions."""
    
    def test_pattern_changed_signal(self, clean_repository, sample_pattern, qtbot):
        """Test that pattern_changed signal is emitted."""
        repo = PatternRepository.instance()
        with qtbot.waitSignal(repo.pattern_changed, timeout=1000) as blocker:
            PatternRepository.set_current_pattern(sample_pattern)
        assert blocker.args == [sample_pattern]
    
    def test_pattern_cleared_signal(self, clean_repository, sample_pattern, qtbot):
        """Test that pattern_cleared signal is emitted."""
        PatternRepository.set_current_pattern(sample_pattern)
        repo = PatternRepository.instance()
        with qtbot.waitSignal(repo.pattern_cleared, timeout=1000):
            PatternRepository.clear_pattern()


class TestPatternRepositoryHasPattern:
    """Test has_pattern method."""
    
    def test_has_pattern_initially_false(self, clean_repository):
        """Test that has_pattern returns False initially."""
        assert PatternRepository.has_pattern() is False
    
    def test_has_pattern_after_set(self, clean_repository, sample_pattern):
        """Test that has_pattern returns True after setting pattern."""
        PatternRepository.set_current_pattern(sample_pattern)
        assert PatternRepository.has_pattern() is True
    
    def test_has_pattern_after_clear(self, clean_repository, sample_pattern):
        """Test that has_pattern returns False after clearing."""
        PatternRepository.set_current_pattern(sample_pattern)
        PatternRepository.clear_pattern()
        assert PatternRepository.has_pattern() is False

