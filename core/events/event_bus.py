"""
Event Bus - Central event dispatcher for domain events.

The event bus provides a centralized way to publish and subscribe to events,
enabling decoupled communication between components.
"""

from typing import Dict, List, Callable, Type, Optional, Any
import logging
from threading import Lock

from core.events.base import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event bus for domain events.
    
    The event bus follows the publish-subscribe pattern, allowing components
    to communicate without direct dependencies.
    
    Usage:
        # Subscribe to events
        event_bus.subscribe(PatternCreatedEvent, handler_function)
        
        # Publish events
        event_bus.publish(PatternCreatedEvent(pattern=pattern))
        
        # Unsubscribe
        event_bus.unsubscribe(PatternCreatedEvent, handler_function)
    """
    
    # Singleton instance
    _instance: Optional['EventBus'] = None
    _lock = Lock()
    
    def __init__(self):
        """Initialize the event bus."""
        if EventBus._instance is not None:
            raise RuntimeError("EventBus is a singleton. Use EventBus.instance() instead.")
        
        self._subscribers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}
        self._global_subscribers: List[Callable[[DomainEvent], None]] = []
        self._event_history: List[DomainEvent] = []
        self._max_history = 1000  # Limit history size
        EventBus._instance = self
    
    @classmethod
    def instance(cls) -> 'EventBus':
        """
        Get the singleton instance of EventBus.
        
        Returns:
            EventBus: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None],
        global_subscriber: bool = False
    ) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: Callback function that will be called when event is published
            global_subscriber: If True, subscribe to all events regardless of type
        """
        if global_subscriber:
            if handler not in self._global_subscribers:
                self._global_subscribers.append(handler)
                logger.debug(f"Added global subscriber: {handler.__name__}")
        else:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")
    
    def unsubscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed {handler.__name__} from {event_type.__name__}")
    
    def unsubscribe_global(self, handler: Callable[[DomainEvent], None]) -> None:
        """
        Unsubscribe a global subscriber.
        
        Args:
            handler: The global handler to remove
        """
        if handler in self._global_subscribers:
            self._global_subscribers.remove(handler)
            logger.debug(f"Removed global subscriber: {handler.__name__}")
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The domain event to publish
        """
        logger.debug(f"Publishing event: {event}")
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify specific subscribers
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)
        
        # Notify global subscribers
        for handler in self._global_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in global event handler {handler.__name__}: {e}", exc_info=True)
    
    def get_event_history(
        self,
        event_type: Optional[Type[DomainEvent]] = None,
        limit: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
            limit: Optional limit on number of events to return
        
        Returns:
            List of events
        """
        events = self._event_history
        if event_type is not None:
            events = [e for e in events if isinstance(e, event_type)]
        
        if limit is not None:
            events = events[-limit:]
        
        return events.copy()
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
    
    def get_subscriber_count(self, event_type: Optional[Type[DomainEvent]] = None) -> int:
        """
        Get the number of subscribers for a given event type.
        
        Args:
            event_type: Optional event type to check
        
        Returns:
            Number of subscribers
        """
        if event_type is None:
            return len(self._global_subscribers)
        
        return len(self._subscribers.get(event_type, []))


def get_event_bus() -> EventBus:
    """
    Get the singleton event bus instance.
    
    Returns:
        EventBus: The singleton event bus
    """
    return EventBus.instance()

