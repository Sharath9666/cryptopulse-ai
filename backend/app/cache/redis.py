"""
Redis helper module.
Provides centralized access to the active Redis client and contains placeholder caching operations.
"""

from redis.asyncio import Redis
from app.cache.client import redis_manager


def get_redis_client() -> Redis:
    """
    Utility function to retrieve the active Redis client.
    Can be used in contexts where FastAPI dependency injection is not available.
    
    Returns:
        Redis: The active Redis client instance.
    """
    return redis_manager.client
