"""
Event subscriber registry.
Tracks subscribers and automates their registration with the central EventBus on startup.
"""

from typing import List
from loguru import logger

from app.events.event_bus import event_bus, EventBus
from app.events.subscriber import EventSubscriber


class EventRegistry:
    """
    Registry coordinator holding instantiated subscribers, subscribing them during startup hooks.
    """
    def __init__(self, bus: EventBus = event_bus) -> None:
        self._bus = bus
        self._subscribers: List[EventSubscriber] = []

    def register(self, subscriber: EventSubscriber) -> None:
        """
        Stores and registers a subscriber handler with the central EventBus.
        """
        self._bus.subscribe(subscriber.event_name, subscriber.handle)
        self._subscribers.append(subscriber)
        logger.info(f"Registered subscriber: {subscriber.__class__.__name__} to event: {subscriber.event_name}")

    def unregister_all(self) -> None:
        """
        Unsubscribes all stored handlers from the EventBus, clearing the list.
        """
        for sub in self._subscribers:
            self._bus.unsubscribe(sub.event_name, sub.handle)
            logger.info(f"Unregistered subscriber: {sub.__class__.__name__} from event: {sub.event_name}")
        self._subscribers.clear()


# Centralized application EventRegistry singleton
event_registry = EventRegistry()
