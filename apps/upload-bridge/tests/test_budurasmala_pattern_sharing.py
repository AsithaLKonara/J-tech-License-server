"""
Tests for Budurasmala Pattern Sharing Service.
"""

import pytest
from pathlib import Path
import tempfile
from core.services.pattern_sharing import PatternSharingService, SharedPattern


class TestPatternSharing:
    """Test pattern sharing functionality."""
    
    def test_sharing_service_initialization(self):
        """Test pattern sharing service initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = PatternSharingService(storage_path=Path(tmpdir))
            
            assert service.storage_path == Path(tmpdir)
            assert len(service._patterns) == 0
    
    def test_upload_pattern(self):
        """Test pattern upload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = PatternSharingService(storage_path=Path(tmpdir))
            
            pattern_data = b"test_pattern_data"
            pattern_id = service.upload_pattern(
                pattern_data=pattern_data,
                name="Test Pattern",
                author="Test Author",
                description="Test description",
                category="Vesak",
                tags=["test", "pattern"]
            )
            
            assert pattern_id is not None
            assert pattern_id.startswith("pattern_")
            
            # Verify pattern was saved
            pattern = service.download_pattern(pattern_id)
            assert pattern is not None
            assert pattern.name == "Test Pattern"
            assert pattern.author == "Test Author"
            assert pattern.category == "Vesak"
    
    def test_download_pattern(self):
        """Test pattern download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = PatternSharingService(storage_path=Path(tmpdir))
            
            pattern_id = service.upload_pattern(
                pattern_data=b"test_data",
                name="Test",
                author="Author"
            )
            
            pattern = service.download_pattern(pattern_id)
            assert pattern is not None
            assert pattern.pattern_data == b"test_data"
            assert pattern.downloads == 1  # Downloads incremented
    
    def test_search_patterns(self):
        """Test pattern search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = PatternSharingService(storage_path=Path(tmpdir))
            
            # Upload test patterns
            service.upload_pattern(
                pattern_data=b"data1",
                name="Vesak Pattern",
                author="Author1",
                category="Vesak",
                tags=["vesak", "festival"]
            )
            
            service.upload_pattern(
                pattern_data=b"data2",
                name="Buddhist Pattern",
                author="Author2",
                category="Buddhist",
                tags=["buddhist", "symbol"]
            )
            
            # Search by category
            results = service.search_patterns(category="Vesak")
            assert len(results) == 1
            assert results[0].name == "Vesak Pattern"
            
            # Search by query
            results = service.search_patterns(query="Vesak")
            assert len(results) >= 1
    
    def test_rate_pattern(self):
        """Test pattern rating."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = PatternSharingService(storage_path=Path(tmpdir))
            
            pattern_id = service.upload_pattern(
                pattern_data=b"test",
                name="Test",
                author="Author"
            )
            
            # Rate pattern
            assert service.rate_pattern(pattern_id, 5.0) is True
            assert service.rate_pattern(pattern_id, 4.0) is True
            
            pattern = service.download_pattern(pattern_id)
            assert pattern.rating > 0
            assert pattern.rating_count == 2
    
    def test_get_popular_patterns(self):
        """Test getting popular patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = PatternSharingService(storage_path=Path(tmpdir))
            
            # Upload multiple patterns
            for i in range(5):
                service.upload_pattern(
                    pattern_data=b"data",
                    name=f"Pattern {i}",
                    author="Author"
                )
            
            # Download some to increase popularity
            all_patterns = list(service._patterns.values())
            if all_patterns:
                service.download_pattern(all_patterns[0].pattern_id)
                service.download_pattern(all_patterns[0].pattern_id)
            
            popular = service.get_popular_patterns(limit=3)
            assert len(popular) <= 3

