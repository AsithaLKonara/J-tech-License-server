"""
Performance tests for service layer.

Tests service performance under various loads and conditions.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch

from core.pattern import Pattern, PatternMetadata, Frame
from core.services.pattern_service import PatternService
from core.services.export_service import ExportService
from core.repositories.pattern_repository import PatternRepository


@pytest.fixture
def large_pattern():
    """Create a large pattern for performance testing."""
    metadata = PatternMetadata(width=72, height=1)
    frames = []
    for i in range(1000):  # 1000 frames
        pixels = [(i % 255, 0, 0)] * 72
        frames.append(Frame(pixels=pixels, duration_ms=50))
    return Pattern(name="Large Pattern", metadata=metadata, frames=frames)


@pytest.fixture
def clean_repository():
    """Reset repository before each test."""
    PatternRepository.clear_pattern()
    PatternRepository._instance = None
    yield
    PatternRepository.clear_pattern()
    PatternRepository._instance = None


class TestPatternServicePerformance:
    """Performance tests for PatternService."""
    
    def test_create_pattern_performance(self, clean_repository):
        """Test pattern creation performance."""
        service = PatternService()
        
        start = time.time()
        for i in range(100):
            service.create_pattern(name=f"Pattern {i}", width=72, height=1)
        elapsed = time.time() - start
        
        # Should complete 100 creations in under 1 second
        assert elapsed < 1.0
        print(f"Created 100 patterns in {elapsed:.3f}s ({elapsed/100*1000:.2f}ms per pattern)")
    
    def test_validate_pattern_performance(self, large_pattern, clean_repository):
        """Test pattern validation performance."""
        service = PatternService()
        
        start = time.time()
        for _ in range(10):
            service.validate_pattern(large_pattern)
        elapsed = time.time() - start
        
        # Should complete 10 validations in under 0.5 seconds
        assert elapsed < 0.5
        print(f"Validated pattern 10 times in {elapsed:.3f}s ({elapsed/10*1000:.2f}ms per validation)")
    
    def test_duplicate_pattern_performance(self, large_pattern, clean_repository):
        """Test pattern duplication performance."""
        service = PatternService()
        
        start = time.time()
        for _ in range(10):
            service.duplicate_pattern(large_pattern)
        elapsed = time.time() - start
        
        # Should complete 10 duplications in under 2 seconds
        assert elapsed < 2.0
        print(f"Duplicated pattern 10 times in {elapsed:.3f}s ({elapsed/10*1000:.2f}ms per duplication)")


class TestExportServicePerformance:
    """Performance tests for ExportService."""
    
    @patch('core.services.export_service.PatternExporter')
    def test_export_validation_performance(self, mock_exporter_class, large_pattern):
        """Test export validation performance."""
        service = ExportService()
        
        with patch('core.services.export_service.generate_export_preview') as mock_preview:
            mock_preview.return_value = Mock()
            
            start = time.time()
            for _ in range(10):
                service.validate_export(large_pattern, "bin")
            elapsed = time.time() - start
            
            # Should complete 10 validations in under 1 second
            assert elapsed < 1.0
            print(f"Validated export 10 times in {elapsed:.3f}s ({elapsed/10*1000:.2f}ms per validation)")


class TestRepositoryPerformance:
    """Performance tests for PatternRepository."""
    
    def test_repository_access_performance(self, clean_repository, large_pattern):
        """Test repository access performance."""
        PatternRepository.set_current_pattern(large_pattern)
        
        start = time.time()
        for _ in range(1000):
            pattern = PatternRepository.get_current_pattern()
            assert pattern is not None
        elapsed = time.time() - start
        
        # Should complete 1000 accesses in under 0.1 seconds
        assert elapsed < 0.1
        print(f"Accessed repository 1000 times in {elapsed:.3f}s ({elapsed/1000*1000000:.2f}μs per access)")
    
    def test_repository_signal_performance(self, clean_repository, large_pattern, qtbot):
        """Test repository signal emission performance."""
        repo = PatternRepository.instance()
        signal_count = [0]
        
        def handler(pattern: Pattern):
            signal_count[0] += 1
        
        repo.pattern_changed.connect(handler)
        
        start = time.time()
        for i in range(100):
            PatternRepository.set_current_pattern(large_pattern)
        elapsed = time.time() - start
        
        # Should complete 100 signal emissions in under 0.5 seconds
        assert elapsed < 0.5
        assert signal_count[0] == 100
        print(f"Emitted 100 signals in {elapsed:.3f}s ({elapsed/100*1000:.2f}ms per signal)")


class TestEventBusPerformance:
    """Performance tests for EventBus."""
    
    def test_event_publish_performance(self, large_pattern):
        """Test event publishing performance."""
        from core.events import get_event_bus, PatternCreatedEvent
        
        bus = get_event_bus()
        event_count = [0]
        
        def handler(event):
            event_count[0] += 1
        
        bus.subscribe(PatternCreatedEvent, handler)
        
        start = time.time()
        for _ in range(1000):
            bus.publish(PatternCreatedEvent(large_pattern))
        elapsed = time.time() - start
        
        # Should complete 1000 publishes in under 0.5 seconds
        assert elapsed < 0.5
        assert event_count[0] == 1000
        print(f"Published 1000 events in {elapsed:.3f}s ({elapsed/1000*1000000:.2f}μs per event)")

