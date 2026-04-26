"""
Event Bus implementing Observer pattern.

Enables loosely-coupled event-driven architecture for notifications.
"""
import logging
from typing import Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types in the system."""
    LICENSE_OPTIMIZED = "license_optimized"
    USER_DEACTIVATED = "user_deactivated"
    SECURITY_ALERT = "security_alert"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    REPORT_GENERATED = "report_generated"
    SAVINGS_ACHIEVED = "savings_achieved"


@dataclass
class Event:
    """Event object."""
    type: EventType
    data: dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventBus:
    """
    Event Bus implementing Observer pattern.
    
    Allows components to publish events and subscribe to events
    without tight coupling.
    
    Usage:
        bus = EventBus()
        bus.subscribe(EventType.SECURITY_ALERT, my_handler)
        bus.publish(Event(EventType.SECURITY_ALERT, {"user": "john"}))
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize event bus."""
        if self._initialized:
            return
        
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        
        self._initialized = True
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callable that takes Event as argument
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.info(f"Handler subscribed to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.info(f"Handler unsubscribed from {event_type.value}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type.value}")
    
    async def publish(self, event: Event):
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        logger.info(f"Publishing event: {event.type.value}")
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify subscribers
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    # Support both sync and async handlers
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in event handler for {event.type.value}: {e}",
                        exc_info=True
                    )
    
    def get_history(self, event_type: EventType = None, limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of Event objects
        """
        history = self._event_history
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        return history[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Singleton instance
import asyncio
event_bus = EventBus()
