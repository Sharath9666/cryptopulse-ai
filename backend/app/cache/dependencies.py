"""
FastAPI dependency injection provider for Redis.
Yields the active Redis client connection to endpoints.
"""

from typing import AsyncGenerator
from redis.asyncio import Redis
from app.cache.client import redis_manager


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency function yielding the active Redis client.
    Used for injecting Redis capabilities into FastAPI path operation endpoints.
    
    Yields:
        Redis: The active Redis connection client.
    """
    yield redis_manager.client
