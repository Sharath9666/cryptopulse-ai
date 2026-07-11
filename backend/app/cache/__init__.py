"""
Cache package initialization.
Exposes connection manager, dependency provider, and health verification helpers.
"""

from app.cache.client import redis_manager
from app.cache.redis import get_redis_client
from app.cache.dependencies import get_redis
from app.cache.health import check_redis_health, verify_redis_connection

__all__ = [
    "redis_manager",
    "get_redis_client",
    "get_redis",
    "check_redis_health",
    "verify_redis_connection",
]
