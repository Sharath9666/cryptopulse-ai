"""
Redis health checking and verification utilities.
Enables runtime ping verification and startup connectivity assertions.
"""

from loguru import logger
from app.cache.client import redis_manager


async def check_redis_health() -> bool:
    """
    Executes a PING command against Redis to verify connection health.
    
    Returns:
        bool: True if connection is responsive and responds to PING, False otherwise.
    """
    try:
        # Retrieve client and send PING command
        client = redis_manager.client
        # ping() is async and returns True on SUCCESS
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


async def verify_redis_connection() -> None:
    """
    Tests the Redis connection during application startup.
    Warns in logs if Redis is unavailable but does not crash startup
    to support graceful service degradation.
    """
    logger.info("Initializing Redis connection verification...")
    is_healthy = await check_redis_health()
    if is_healthy:
        logger.info("Redis connection verified successfully.")
    else:
        logger.warning(
            "Redis cache is unavailable. The application will start, "
            "but caching capabilities will be offline. "
            "Please check connection settings and Redis status."
        )
