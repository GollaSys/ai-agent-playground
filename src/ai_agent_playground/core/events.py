"""Event system for the simulator."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Optional
from enum import Enum
import uuid
from datetime import datetime


class EventType(Enum):
    """Types of events in the simulation."""
    AGENT_SPAWN = "agent_spawn"
    AGENT_DEATH = "agent_death"
    AGENT_MOVE = "agent_move"
    AGENT_INTERACT = "agent_interact"
    ENVIRONMENT_CHANGE = "environment_change"
    COLLISION = "collision"
    CUSTOM = "custom"


@dataclass
class Event:
    """Base event class."""
    event_type: EventType
    timestamp: datetime
    source_id: str
    target_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """Handle an event."""
        pass


class EventManager:
    """Manages event publishing and subscription."""
    
    def __init__(self) -> None:
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history: int = 10000
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers."""
        self._event_history.append(event)
        
        # Maintain history size
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Notify handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    handler.handle_event(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def get_event_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type is None:
            return self._event_history.copy()
        return [event for event in self._event_history if event.event_type == event_type]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()