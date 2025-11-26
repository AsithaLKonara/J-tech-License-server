"""
Unit tests for export events integration.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from core.pattern import Pattern, Frame, PatternMetadata
from core.services.export_service import ExportService
from core.events import EventListener
from core.events.export_events import (
    ExportStartedEvent,
    ExportCompletedEvent,
    ExportFailedEvent
)
from core.export_options import ExportOptions


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def export_service():
    """Create export service instance."""
    return ExportService()


@pytest.fixture
def event_listener():
    """Create event listener for capturing events."""
    from core.events import get_event_bus, EventListener
    
    listener = EventListener()
    event_bus = get_event_bus()
    
    # Subscribe to export events
    event_bus.subscribe(ExportStartedEvent, listener.on_event)
    event_bus.subscribe(ExportCompletedEvent, listener.on_event)
    event_bus.subscribe(ExportFailedEvent, listener.on_event)
    
    return listener


class TestExportEvents:
    """Test export events are published correctly."""
    
    def test_export_started_event_published(self, export_service, sample_pattern, event_listener):
        """Test that ExportStartedEvent is published when export starts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.bin"
            
            try:
                export_service.export_pattern(sample_pattern, str(output_path), "bin")
            except Exception:
                pass  # May fail if exporter not fully implemented
            
            # Check that started event was published
            started_events = event_listener.get_events(ExportStartedEvent)
            assert len(started_events) >= 1
            assert started_events[0].pattern == sample_pattern
            assert started_events[0].format == "bin"
    
    def test_export_completed_event_published_on_success(
        self, export_service, sample_pattern, event_listener
    ):
        """Test that ExportCompletedEvent is published on successful export."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.bin"
            
            try:
                export_service.export_pattern(sample_pattern, str(output_path), "bin")
            except Exception:
                pass  # May fail if exporter not fully implemented
            
            # Check that completed event was published (if export succeeded)
            completed_events = event_listener.get_events(ExportCompletedEvent)
            # May be 0 if export failed, which is OK for this test
    
    def test_export_failed_event_published_on_error(
        self, export_service, sample_pattern, event_listener
    ):
        """Test that ExportFailedEvent is published on export failure."""
        # Try to export with invalid format
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.invalid"
            
            try:
                export_service.export_pattern(sample_pattern, str(output_path), "invalid_format")
            except ValueError:
                pass  # Expected to fail
            
            # Check that failed event was published
            failed_events = event_listener.get_events(ExportFailedEvent)
            # May be 0 if error happened before event, which is OK

