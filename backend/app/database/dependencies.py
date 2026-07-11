"""
FastAPI dependencies for database operations.
Provides scope-controlled database session generators.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for obtaining an asynchronous database session.
    Automatically manages commits, rollbacks on error, and ensures the session is closed.
    
    Yields:
        AsyncSession: An active SQLAlchemy async session.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
