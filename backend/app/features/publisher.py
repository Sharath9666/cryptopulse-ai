"""
Feature vector publisher service.
Persists engineered features in Redis and triggers EventBus notifications.
"""

from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.events import BaseEvent, EventPublisher
from app.features.models.feature_vector import FeatureVector


class FeaturePublisher:
    """
    Publisher class caching FeatureVectors in Redis and notifying subscribers.
    """
    def __init__(self, redis_client: Redis = None, event_publisher: EventPublisher = None) -> None:
        self._redis_client = redis_client
        self.publisher = event_publisher or EventPublisher()

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def publish(self, feature_vector: FeatureVector) -> bool:
        """
        Saves FeatureVector in Redis and publishes FeatureVectorCreatedEvent to the Event Bus.
        Key structure: feature:{timeframe}:{symbol}
        TTL: 24 hours (86400 seconds)
        """
        # Try caching to Redis, but proceed to publish event even if it fails
        from app.config.settings import settings
        if not settings.BACKTEST_SPEED_MODE:
            try:
                 redis_key = f"feature:{feature_vector.timeframe}:{feature_vector.symbol}"
                 fv_json = feature_vector.model_dump_json()
                 await self.redis.set(
                     name=redis_key,
                     value=fv_json,
                     ex=86400,  # 24 hours
                 )
                 logger.info(f"Cached FeatureVector to Redis: {redis_key}")
            except Exception as e:
                 logger.error(f"Failed to cache FeatureVector for {feature_vector.symbol} ({feature_vector.timeframe}) to Redis: {e}")
        else:
            logger.debug(f"Speed mode enabled. Bypassing Redis cache for features: {feature_vector.symbol}")

        try:
             # 2. Publish event to the central Event Bus
             event = BaseEvent(
                 event_name="FeatureVectorCreatedEvent",
                 source="FeaturePublisher",
                 payload=feature_vector,
             )
             await self.publisher.publish(event)
             logger.info(f"Published FeatureVectorCreatedEvent to EventBus: {feature_vector.symbol}")
             return True
        except Exception as e:
             logger.error(
                 f"Failed to dispatch FeatureVectorCreatedEvent for {feature_vector.symbol} "
                 f"({feature_vector.timeframe}): {e}"
             )
             return False
class_name = "FeaturePublisher"
