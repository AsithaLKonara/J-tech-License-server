"""
Base classes for domain events.

Provides the foundation for the event-driven architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class DomainEvent(ABC):
    """
    Base class for all domain events.
    
    Domain events represent something that has happened in the domain.
    They are immutable and contain all the information needed to handle the event.
    """
    
    def __init__(self, source: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a domain event.
        
        Args:
            source: Optional identifier for the event source
            metadata: Optional additional metadata
        """
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.source = source
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        """String representation of the event."""
        return f"{self.__class__.__name__}(id={self.event_id[:8]}, source={self.source})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata,
            'event_type': self.__class__.__name__
        }


class EventHandler(ABC):
    """
    Base class for event handlers.
    
    Event handlers process domain events. They should be stateless
    and idempotent when possible.
    """
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """
        Handle a domain event.
        
        Args:
            event: The domain event to handle
        """
        pass
    
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can handle the given event.
        
        Args:
            event: The domain event to check
        
        Returns:
            True if this handler can handle the event
        """
        return True


class EventListener:
    """
    Simple event listener that can be used for testing or simple cases.
    
    Usage:
        listener = EventListener()
        event_bus.subscribe(PatternCreatedEvent, listener.on_event)
        # ... later ...
        events = listener.get_events(PatternCreatedEvent)
    """
    
    def __init__(self):
        """Initialize the event listener."""
        self._events: list[DomainEvent] = []
    
    def on_event(self, event: DomainEvent) -> None:
        """
        Handle an event (callback for event bus).
        
        Args:
            event: The domain event
        """
        self._events.append(event)
    
    def get_events(self, event_type: type[DomainEvent] = None) -> list[DomainEvent]:
        """
        Get all captured events, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
        
        Returns:
            List of captured events
        """
        if event_type is None:
            return self._events.copy()
        return [e for e in self._events if isinstance(e, event_type)]
    
    def clear(self) -> None:
        """Clear all captured events."""
        self._events.clear()
    
    def count(self, event_type: type[DomainEvent] = None) -> int:
        """
        Count captured events, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
        
        Returns:
            Number of captured events
        """
        return len(self.get_events(event_type))

