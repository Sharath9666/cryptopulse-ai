"""
Base event model definitions.
All system events must inherit from BaseEvent or instantiate it.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """
    Core schema for internal application events.
    Holds metadata and generic payload payloads.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique event identifier")
    event_name: str = Field(..., description="The name characterizing the event type")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when event was initialized"
    )
    source: str = Field(..., description="Module naming indicating event generator")
    payload: Any = Field(..., description="Event payload contents")
