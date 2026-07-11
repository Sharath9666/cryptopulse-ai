"""
Asynchronous session factory module.
Initializes the async_sessionmaker bound to the async engine.
"""

from sqlalchemy.ext.asyncio import async_sessionmaker
from app.database.engine import engine

# Async session factory used to generate new database sessions.
# Configured to prevent auto-flushing and committing without explicit control.
async_session_factory = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Keep instances usable after commit
)
