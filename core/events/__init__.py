"""
Domain Events - Event-driven architecture for decoupled communication.

This module provides a domain event system that allows components to communicate
without direct dependencies, improving maintainability and testability.
"""

from core.events.event_bus import EventBus, get_event_bus
from core.events.base import DomainEvent, EventHandler, EventListener
from core.events.pattern_events import (
    PatternCreatedEvent,
    PatternLoadedEvent,
    PatternSavedEvent,
    PatternModifiedEvent,
    PatternClearedEvent,
    PatternDuplicatedEvent
)
from core.events.frame_events import (
    FrameAddedEvent,
    FrameDeletedEvent,
    FrameDuplicatedEvent,
    FrameMovedEvent,
    FrameSelectedEvent,
    FrameDurationChangedEvent
)
from core.events.export_events import (
    ExportStartedEvent,
    ExportCompletedEvent,
    ExportFailedEvent
)
from core.events.flash_events import (
    FirmwareBuildStartedEvent,
    FirmwareBuildCompletedEvent,
    FirmwareBuildFailedEvent,
    FirmwareUploadStartedEvent,
    FirmwareUploadCompletedEvent,
    FirmwareUploadFailedEvent
)

__all__ = [
    'EventBus',
    'get_event_bus',
    'DomainEvent',
    'EventHandler',
    'EventListener',
    'PatternCreatedEvent',
    'PatternLoadedEvent',
    'PatternSavedEvent',
    'PatternModifiedEvent',
    'PatternClearedEvent',
    'PatternDuplicatedEvent',
    'FrameAddedEvent',
    'FrameDeletedEvent',
    'FrameDuplicatedEvent',
    'FrameMovedEvent',
    'FrameSelectedEvent',
    'FrameDurationChangedEvent',
    'ExportStartedEvent',
    'ExportCompletedEvent',
    'ExportFailedEvent',
    'FirmwareBuildStartedEvent',
    'FirmwareBuildCompletedEvent',
    'FirmwareBuildFailedEvent',
    'FirmwareUploadStartedEvent',
    'FirmwareUploadCompletedEvent',
    'FirmwareUploadFailedEvent',
]

