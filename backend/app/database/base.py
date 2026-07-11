"""
Database declarative base and abstract base model definitions.
Defines base columns and hooks common across all database models.
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class.
    All application models will inherit from this base class.
    """
    pass




class BaseModel(Base):
    """
    Abstract base model class to be inherited by all entity models.
    Provides standard fields:
    - UUID as primary key
    - created_at: Auto-set on creation, with timezone awareness
    - updated_at: Auto-updated on modification, with timezone awareness
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
        doc="Unique identifier for the record (UUIDv4)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )
