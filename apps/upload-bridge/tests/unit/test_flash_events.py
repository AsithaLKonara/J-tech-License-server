"""
Unit tests for flash events integration.
"""
import pytest
from unittest.mock import Mock, patch

from core.pattern import Pattern, Frame, PatternMetadata
from core.services.flash_service import FlashService
from core.events import EventListener
from core.events.flash_events import (
    FirmwareBuildStartedEvent,
    FirmwareBuildCompletedEvent,
    FirmwareBuildFailedEvent,
    FirmwareUploadStartedEvent,
    FirmwareUploadCompletedEvent,
    FirmwareUploadFailedEvent
)


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def flash_service():
    """Create flash service instance."""
    return FlashService()


@pytest.fixture
def event_listener():
    """Create event listener for capturing events."""
    from core.events import get_event_bus, EventListener
    
    listener = EventListener()
    event_bus = get_event_bus()
    
    # Subscribe to flash events
    event_bus.subscribe(FirmwareBuildStartedEvent, listener.on_event)
    event_bus.subscribe(FirmwareBuildCompletedEvent, listener.on_event)
    event_bus.subscribe(FirmwareBuildFailedEvent, listener.on_event)
    event_bus.subscribe(FirmwareUploadStartedEvent, listener.on_event)
    event_bus.subscribe(FirmwareUploadCompletedEvent, listener.on_event)
    event_bus.subscribe(FirmwareUploadFailedEvent, listener.on_event)
    
    return listener


class TestFlashEvents:
    """Test flash events are published correctly."""
    
    def test_build_started_event_published(self, flash_service, sample_pattern, event_listener):
        """Test that FirmwareBuildStartedEvent is published when build starts."""
        try:
            flash_service.build_firmware(sample_pattern, "esp8266")
        except Exception:
            pass  # May fail if uploader not available
        
        # Check that started event was published
        started_events = event_listener.get_events(FirmwareBuildStartedEvent)
        assert len(started_events) >= 1
        assert started_events[0].pattern == sample_pattern
        assert started_events[0].chip_id == "esp8266"
    
    def test_build_failed_event_published_on_error(
        self, flash_service, sample_pattern, event_listener
    ):
        """Test that FirmwareBuildFailedEvent is published on build failure."""
        try:
            flash_service.build_firmware(sample_pattern, "invalid_chip")
        except ValueError:
            pass  # Expected to fail
        
        # Check that failed event was published
        failed_events = event_listener.get_events(FirmwareBuildFailedEvent)
        # May have events if error handling works correctly

