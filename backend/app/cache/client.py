"""
Redis connection client manager.
Handles connection pool creation, client retrieval, and graceful lifecycle shutdown.
"""

from typing import Union
from redis.asyncio import ConnectionPool, Redis
from loguru import logger
from app.config.settings import settings


class RedisClientManager:
    """
    Manager class responsible for initializing and closing the Redis connection pool.
    Exposes properties to access the client and connection pool safely.
    """
    def __init__(self) -> None:
        self.pool: Union[ConnectionPool, None] = None
        self._redis_client: Union[Redis, None] = None

    def init_pool(self) -> None:
        """
        Initializes the async Redis connection pool.
        Connection pooling optimizes resources and manages open sockets efficiently.
        """
        if self.pool is not None:
            logger.warning("Redis connection pool is already initialized.")
            return

        logger.info("Initializing Redis connection pool...")
        self.pool = ConnectionPool.from_url(
            url=settings.ASYNC_REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,  # Limits maximum concurrent connections to prevent socket exhaustion
            socket_timeout=0.1,
            socket_connect_timeout=0.1,
        )
        self._redis_client = Redis(connection_pool=self.pool)
        logger.info("Redis connection pool initialized successfully.")

    async def close_pool(self) -> None:
        """
        Gracefully disconnects and shuts down the connection pool, clearing allocated resources.
        """
        if self.pool is None:
            logger.warning("Redis connection pool is not initialized. Skipping shutdown.")
            return

        logger.info("Closing Redis connection pool...")
        if self._redis_client:
            await self._redis_client.aclose()
        await self.pool.disconnect()
        self.pool = None
        self._redis_client = None
        logger.info("Redis connection pool closed successfully.")

    @property
    def client(self) -> Redis:
        """
        Retrieves the initialized Redis client instance.
        
        Raises:
            RuntimeError: If connection pool has not been initialized.
        """
        if self._redis_client is None:
            raise RuntimeError("Redis connection pool is not initialized. Call init_pool() first.")
        return self._redis_client


# Singleton manager instance for application-wide cache sharing
redis_manager = RedisClientManager()
