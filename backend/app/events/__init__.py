"""
Events infrastructure package initialization.
Exposes BaseEvent, EventBus, Publisher, Subscriber, Registry, and health metrics.
"""

from app.events.base_event import BaseEvent
from app.events.event_bus import event_bus, EventBus
from app.events.publisher import EventPublisher
from app.events.subscriber import EventSubscriber
from app.events.registry import event_registry, EventRegistry
from app.events.health import get_event_bus_health, EventBusHealth

__all__ = [
    "BaseEvent",
    "event_bus",
    "EventBus",
    "EventPublisher",
    "EventSubscriber",
    "event_registry",
    "EventRegistry",
    "get_event_bus_health",
    "EventBusHealth",
]
