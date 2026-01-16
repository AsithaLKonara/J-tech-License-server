"""
Unit tests for EventBus.

Tests the event bus functionality for domain events.
"""

import pytest
from core.events.event_bus import EventBus
from core.events.base import DomainEvent
from core.events.pattern_events import PatternCreatedEvent, PatternLoadedEvent
from core.pattern import Pattern, PatternMetadata, Frame


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing."""
    metadata = PatternMetadata(width=8, height=8)
    frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)
    return Pattern(name="Test Pattern", metadata=metadata, frames=[frame])


@pytest.fixture
def clean_event_bus():
    """Reset event bus before each test."""
    EventBus._instance = None
    yield
    EventBus._instance = None


class TestEventBusSingleton:
    """Test singleton behavior."""
    
    def test_singleton_instance(self, clean_event_bus):
        """Test that instance() returns the same singleton."""
        bus1 = EventBus.instance()
        bus2 = EventBus.instance()
        assert bus1 is bus2
    
    def test_direct_instantiation_raises_error(self, clean_event_bus):
        """Test that direct instantiation raises RuntimeError."""
        EventBus.instance()  # Create instance first
        with pytest.raises(RuntimeError, match="singleton"):
            EventBus()


class TestEventBusSubscribe:
    """Test event subscription."""
    
    def test_subscribe_to_event_type(self, clean_event_bus, sample_pattern):
        """Test subscribing to a specific event type."""
        bus = EventBus.instance()
        handler_called = []
        
        def handler(event: DomainEvent):
            handler_called.append(event)
        
        bus.subscribe(PatternCreatedEvent, handler)
        
        # Publish event
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)
        
        assert len(handler_called) == 1
        assert handler_called[0] == event
    
    def test_subscribe_global(self, clean_event_bus, sample_pattern):
        """Test subscribing to all events."""
        bus = EventBus.instance()
        handler_called = []
        
        def handler(event: DomainEvent):
            handler_called.append(event)
        
        bus.subscribe(PatternCreatedEvent, handler, global_subscriber=True)
        
        # Publish different event types
        event1 = PatternCreatedEvent(sample_pattern)
        event2 = PatternLoadedEvent(sample_pattern, "/path/to/file.bin")
        
        bus.publish(event1)
        bus.publish(event2)
        
        assert len(handler_called) == 2
    
    def test_multiple_subscribers(self, clean_event_bus, sample_pattern):
        """Test multiple subscribers to same event type."""
        bus = EventBus.instance()
        handler1_called = []
        handler2_called = []
        
        def handler1(event: DomainEvent):
            handler1_called.append(event)
        
        def handler2(event: DomainEvent):
            handler2_called.append(event)
        
        bus.subscribe(PatternCreatedEvent, handler1)
        bus.subscribe(PatternCreatedEvent, handler2)
        
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)
        
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1


class TestEventBusUnsubscribe:
    """Test event unsubscription."""
    
    def test_unsubscribe(self, clean_event_bus, sample_pattern):
        """Test unsubscribing from events."""
        bus = EventBus.instance()
        handler_called = []
        
        def handler(event: DomainEvent):
            handler_called.append(event)
        
        bus.subscribe(PatternCreatedEvent, handler)
        
        # Publish event - should be handled
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)
        assert len(handler_called) == 1
        
        # Unsubscribe
        bus.unsubscribe(PatternCreatedEvent, handler)
        
        # Publish again - should not be handled
        bus.publish(event)
        assert len(handler_called) == 1  # Still 1, not 2


class TestEventBusPublish:
    """Test event publishing."""
    
    def test_publish_event(self, clean_event_bus, sample_pattern):
        """Test publishing an event."""
        bus = EventBus.instance()
        handler_called = []
        
        def handler(event: DomainEvent):
            handler_called.append(event)
        
        bus.subscribe(PatternCreatedEvent, handler)
        
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)
        
        assert len(handler_called) == 1
        assert handler_called[0] == event
    
    def test_publish_adds_to_history(self, clean_event_bus, sample_pattern):
        """Test that published events are added to history."""
        bus = EventBus.instance()
        
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)
        
        history = bus.get_event_history()
        assert len(history) == 1
        assert history[0] == event
    
    def test_publish_handles_handler_errors(self, clean_event_bus, sample_pattern):
        """Test that handler errors don't stop event processing."""
        bus = EventBus.instance()
        handler1_called = []
        handler2_called = []
        
        def handler1(event: DomainEvent):
            raise Exception("Handler error")
        
        def handler2(event: DomainEvent):
            handler2_called.append(event)
        
        bus.subscribe(PatternCreatedEvent, handler1)
        bus.subscribe(PatternCreatedEvent, handler2)
        
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)  # Should not raise
        
        # Handler2 should still be called
        assert len(handler2_called) == 1


class TestEventBusHistory:
    """Test event history."""
    
    def test_get_event_history(self, clean_event_bus, sample_pattern):
        """Test getting event history."""
        bus = EventBus.instance()
        
        event1 = PatternCreatedEvent(sample_pattern)
        event2 = PatternLoadedEvent(sample_pattern, "/path/to/file.bin")
        
        bus.publish(event1)
        bus.publish(event2)
        
        history = bus.get_event_history()
        assert len(history) == 2
    
    def test_get_event_history_filtered(self, clean_event_bus, sample_pattern):
        """Test getting filtered event history."""
        bus = EventBus.instance()
        
        event1 = PatternCreatedEvent(sample_pattern)
        event2 = PatternLoadedEvent(sample_pattern, "/path/to/file.bin")
        
        bus.publish(event1)
        bus.publish(event2)
        
        history = bus.get_event_history(PatternCreatedEvent)
        assert len(history) == 1
        assert history[0] == event1
    
    def test_clear_history(self, clean_event_bus, sample_pattern):
        """Test clearing event history."""
        bus = EventBus.instance()
        
        event = PatternCreatedEvent(sample_pattern)
        bus.publish(event)
        
        assert len(bus.get_event_history()) == 1
        
        bus.clear_history()
        assert len(bus.get_event_history()) == 0

