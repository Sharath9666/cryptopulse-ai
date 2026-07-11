"""
Event Bus health checker.
Exposes statistics on event rates, subscriber metrics, queue depths, and errors.
"""

from pydantic import BaseModel, Field
from app.events.event_bus import event_bus


class EventBusHealth(BaseModel):
    """
    Representation of the Event Bus's health indicators.
    """
    subscriber_count: int = Field(..., description="Total active event subscriber bindings")
    published_events: int = Field(..., description="Total count of successfully published events")
    failed_events: int = Field(..., description="Total count of failed subscriber handle actions")
    queue_size: int = Field(..., description="Current count of events waiting in the dispatch queue")


def get_event_bus_health() -> EventBusHealth:
    """
    Constructs and returns a snapshot representation of EventBus metrics.
    """
    return EventBusHealth(
        subscriber_count=event_bus.subscriber_count,
        published_events=event_bus.published_count,
        failed_events=event_bus.failed_count,
        queue_size=event_bus.queue_size,
    )
