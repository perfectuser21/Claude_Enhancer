"""
Claude Enhancer v2.0 - Event System
====================================

Event bus and event handling for the core system.
"""

from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event object"""
    name: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "core"


class EventBus:
    """
    Event bus for inter-component communication

    Implements a publish-subscribe pattern for loose coupling
    between components.
    """

    # Core events
    EVENTS = {
        'workflow.phase_changed',
        'workflow.phase_completed',
        'workflow.phase_failed',
        'hook.validation_failed',
        'hook.validation_passed',
        'agent.selected',
        'agent.execution_started',
        'agent.execution_completed',
        'feature.enabled',
        'feature.disabled',
        'config.loaded',
        'config.updated',
        'state.saved',
        'state.loaded',
    }

    def __init__(self):
        """Initialize event bus"""
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000

        logger.debug("EventBus initialized")

    def emit(self, event_name: str, event: Event):
        """
        Emit an event

        Args:
            event_name: Name of the event
            event: Event object with data
        """
        logger.debug("Emitting event: %s", event_name)

        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Call handlers
        handlers = self._handlers.get(event_name, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.exception("Error in event handler for %s: %s", event_name, e)

    def on(self, event_name: str, handler: Callable):
        """
        Register event handler

        Args:
            event_name: Name of the event to listen for
            handler: Callable to handle the event
        """
        if event_name not in self._handlers:
            self._handlers[event_name] = []

        self._handlers[event_name].append(handler)
        logger.debug("Registered handler for event: %s", event_name)

    def off(self, event_name: str, handler: Callable):
        """
        Unregister event handler

        Args:
            event_name: Name of the event
            handler: Handler to remove
        """
        if event_name in self._handlers:
            try:
                self._handlers[event_name].remove(handler)
                logger.debug("Unregistered handler for event: %s", event_name)
            except ValueError:
                logger.warning("Handler not found for event: %s", event_name)

    def get_history(self, event_name: str = None, limit: int = 100) -> List[Event]:
        """
        Get event history

        Args:
            event_name: Optional event name to filter by
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        if event_name:
            events = [e for e in self._event_history if e.name == event_name]
        else:
            events = self._event_history

        return events[-limit:]

    def clear_history(self):
        """Clear event history"""
        self._event_history = []
        logger.debug("Event history cleared")
