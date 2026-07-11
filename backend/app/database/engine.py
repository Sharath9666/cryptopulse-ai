"""
Database engine configuration using SQLAlchemy 2.x Async.
Sets up the asynchronous engine with optimized connection pooling.
"""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from app.config.settings import settings
import sys

# For testing, use NullPool to prevent event loop closed errors on connection termination
pool_class = NullPool if "pytest" in sys.modules else None

kwargs = {
    "url": settings.ASYNC_DATABASE_URL,
    "echo": settings.DB_ECHO,
    "pool_pre_ping": True,
}

if pool_class is not None:
    kwargs["poolclass"] = pool_class
else:
    kwargs["pool_size"] = settings.DB_POOL_SIZE
    kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

# Create the asynchronous database engine.
# Uses asyncpg driver under the hood.
engine = create_async_engine(**kwargs)
