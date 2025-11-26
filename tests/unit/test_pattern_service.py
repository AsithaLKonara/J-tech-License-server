"""
Unit tests for PatternService.

Tests the business logic service for pattern operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from core.pattern import Pattern, PatternMetadata, Frame
from core.services.pattern_service import PatternService
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
    PatternRepository.clear_pattern()
    PatternRepository._instance = None
    yield
    PatternRepository.clear_pattern()
    PatternRepository._instance = None


@pytest.fixture
def pattern_service(clean_repository):
    """Create a PatternService instance."""
    return PatternService()


class TestPatternServiceInitialization:
    """Test service initialization."""
    
    def test_init(self, pattern_service):
        """Test that service initializes correctly."""
        assert pattern_service.parser_registry is not None
        assert pattern_service.repository is not None


class TestPatternServiceLoadPattern:
    """Test pattern loading."""
    
    @patch('core.services.pattern_service.ParserRegistry')
    def test_load_pattern_success(self, mock_registry_class, pattern_service, sample_pattern, tmp_path):
        """Test loading a pattern successfully."""
        # Setup mock
        mock_registry = Mock()
        mock_registry.parse_file.return_value = (sample_pattern, "bin")
        pattern_service.parser_registry = mock_registry
        
        # Create test file
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")
        
        # Load pattern
        pattern, format_name = pattern_service.load_pattern(str(test_file))
        
        # Verify
        assert pattern == sample_pattern
        assert format_name == "bin"
        mock_registry.parse_file.assert_called_once()
        assert PatternRepository.get_current_pattern() == sample_pattern
    
    @patch('core.services.pattern_service.ParserRegistry')
    def test_load_pattern_file_not_found(self, mock_registry_class, pattern_service):
        """Test loading a non-existent file."""
        mock_registry = Mock()
        mock_registry.parse_file.side_effect = FileNotFoundError("File not found")
        pattern_service.parser_registry = mock_registry
        
        with pytest.raises(FileNotFoundError):
            pattern_service.load_pattern("/nonexistent/file.bin")
    
    @patch('core.services.pattern_service.ParserRegistry')
    def test_load_pattern_with_hints(self, mock_registry_class, pattern_service, sample_pattern, tmp_path):
        """Test loading pattern with LED and frame hints."""
        mock_registry = Mock()
        mock_registry.parse_file.return_value = (sample_pattern, "bin")
        pattern_service.parser_registry = mock_registry
        
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"test data")
        
        pattern_service.load_pattern(str(test_file), suggested_leds=64, suggested_frames=1)
        
        mock_registry.parse_file.assert_called_once_with(
            str(test_file),
            suggested_leds=64,
            suggested_frames=1
        )


class TestPatternServiceSavePattern:
    """Test pattern saving."""
    
    def test_save_pattern(self, pattern_service, sample_pattern, tmp_path):
        """Test saving a pattern."""
        test_file = tmp_path / "output.bin"
        
        # Mock pattern.save_to_file
        with patch.object(sample_pattern, 'save_to_file') as mock_save:
            pattern_service.save_pattern(sample_pattern, str(test_file))
            
            mock_save.assert_called_once_with(str(test_file))
            assert PatternRepository.get_current_pattern() == sample_pattern
            assert PatternRepository.get_current_file() == str(test_file)
            assert PatternRepository.is_dirty() is False


class TestPatternServiceCreatePattern:
    """Test pattern creation."""
    
    def test_create_pattern_default(self, pattern_service, clean_repository):
        """Test creating a pattern with default values."""
        pattern = pattern_service.create_pattern()
        
        assert pattern.name == "Untitled Pattern"
        assert pattern.metadata.width == 72
        assert pattern.metadata.height == 1
        assert len(pattern.frames) == 0
        assert PatternRepository.get_current_pattern() == pattern
    
    def test_create_pattern_custom(self, pattern_service, clean_repository):
        """Test creating a pattern with custom values."""
        pattern = pattern_service.create_pattern(
            name="Custom Pattern",
            width=16,
            height=16
        )
        
        assert pattern.name == "Custom Pattern"
        assert pattern.metadata.width == 16
        assert pattern.metadata.height == 16
        assert len(pattern.frames) == 0
    
    def test_create_pattern_with_metadata(self, pattern_service, clean_repository):
        """Test creating a pattern with custom metadata."""
        metadata = PatternMetadata(width=10, height=10)
        pattern = pattern_service.create_pattern(metadata=metadata)
        
        assert pattern.metadata == metadata


class TestPatternServiceDuplicatePattern:
    """Test pattern duplication."""
    
    def test_duplicate_pattern(self, pattern_service, sample_pattern):
        """Test duplicating a pattern."""
        duplicated = pattern_service.duplicate_pattern(sample_pattern)
        
        assert duplicated.name == f"{sample_pattern.name} (Copy)"
        assert duplicated.metadata.width == sample_pattern.metadata.width
        assert duplicated.metadata.height == sample_pattern.metadata.height
        assert duplicated.id != sample_pattern.id
    
    def test_duplicate_pattern_custom_name(self, pattern_service, sample_pattern):
        """Test duplicating with custom name."""
        duplicated = pattern_service.duplicate_pattern(sample_pattern, "New Name")
        
        assert duplicated.name == "New Name"


class TestPatternServiceValidatePattern:
    """Test pattern validation."""
    
    def test_validate_pattern_valid(self, pattern_service, sample_pattern):
        """Test validating a valid pattern."""
        is_valid, error = pattern_service.validate_pattern(sample_pattern)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_pattern_no_frames(self, pattern_service):
        """Test validating a pattern with no frames."""
        metadata = PatternMetadata(width=8, height=8)
        pattern = Pattern(name="Empty", metadata=metadata, frames=[])
        
        is_valid, error = pattern_service.validate_pattern(pattern)
        
        assert is_valid is False
        assert "no frames" in error.lower()
    
    def test_validate_pattern_invalid_dimensions(self, pattern_service):
        """Test validating a pattern with invalid dimensions."""
        metadata = PatternMetadata(width=0, height=0)
        frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
        pattern = Pattern(name="Invalid", metadata=metadata, frames=[frame])
        
        is_valid, error = pattern_service.validate_pattern(pattern)
        
        assert is_valid is False
        assert "dimensions" in error.lower()
    
    def test_validate_pattern_frame_led_mismatch(self, pattern_service):
        """Test validating a pattern with frame LED count mismatch."""
        metadata = PatternMetadata(width=8, height=8)  # 64 LEDs
        frame = Frame(pixels=[(255, 0, 0)] * 32, duration_ms=100)  # 32 LEDs
        pattern = Pattern(name="Mismatch", metadata=metadata, frames=[frame])
        
        is_valid, error = pattern_service.validate_pattern(pattern)
        
        assert is_valid is False
        assert "frame" in error.lower()


class TestPatternServiceRepositoryAccess:
    """Test repository access methods."""
    
    def test_get_current_pattern(self, pattern_service, sample_pattern):
        """Test getting current pattern from repository."""
        PatternRepository.set_current_pattern(sample_pattern)
        
        pattern = pattern_service.get_current_pattern()
        assert pattern == sample_pattern
    
    def test_set_current_pattern(self, pattern_service, sample_pattern):
        """Test setting current pattern in repository."""
        pattern_service.set_current_pattern(sample_pattern, "/path/to/file.bin")
        
        assert PatternRepository.get_current_pattern() == sample_pattern
        assert PatternRepository.get_current_file() == "/path/to/file.bin"
    
    def test_clear_pattern(self, pattern_service, sample_pattern):
        """Test clearing pattern from repository."""
        PatternRepository.set_current_pattern(sample_pattern)
        pattern_service.clear_pattern()
        
        assert PatternRepository.get_current_pattern() is None
    
    def test_is_dirty(self, pattern_service, sample_pattern):
        """Test checking dirty state."""
        PatternRepository.set_current_pattern(sample_pattern)
        PatternRepository.set_dirty(True)
        
        assert pattern_service.is_dirty() is True
    
    def test_set_dirty(self, pattern_service, sample_pattern):
        """Test setting dirty state."""
        PatternRepository.set_current_pattern(sample_pattern)
        pattern_service.set_dirty(True)
        
        assert PatternRepository.is_dirty() is True

