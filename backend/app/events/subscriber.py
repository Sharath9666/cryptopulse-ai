"""
Abstract base subscriber definitions.
All custom event subscribers must inherit from this module interface.
"""

from abc import ABC, abstractmethod
from app.events.base_event import BaseEvent


class EventSubscriber(ABC):
    """
    Abstract Base Class for an event listener/subscriber.
    Defines signature metrics required by registers.
    """
    @property
    @abstractmethod
    def event_name(self) -> str:
        """
        The name of the event type this subscriber handles.
        """
        pass

    @abstractmethod
    async def handle(self, event: BaseEvent) -> None:
        """
        Processes the captured event payload.
        """
        pass
