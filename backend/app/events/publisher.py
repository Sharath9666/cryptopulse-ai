"""
Generic event publishing interface.
Encapsulates publisher tasks, permitting swap out to external systems in future.
"""

from app.events.base_event import BaseEvent
from app.events.event_bus import event_bus, EventBus


class EventPublisher:
    """
    Publisher manager delivering events to the event bus.
    Can be inherited or initialized locally.
    """
    def __init__(self, bus: EventBus = event_bus) -> None:
        self._bus = bus

    async def publish(self, event: BaseEvent) -> None:
        """
        Publishes the event to the configured event routing bus.
        """
        await self._bus.publish(event)
