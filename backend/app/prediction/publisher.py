"""
Prediction publisher service.
Caches generated directional predictions in Redis and dispatches events.
"""

from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.events import BaseEvent, EventPublisher
from app.prediction.models.prediction import Prediction


class PredictionPublisher:
    """
    Handles caching of Prediction objects in Redis and publication of event notifications.
    """
    def __init__(self, redis_client: Redis = None, event_publisher: EventPublisher = None) -> None:
        self._redis_client = redis_client
        self.publisher = event_publisher or EventPublisher()

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def publish(self, prediction: Prediction) -> bool:
        """
        Saves Prediction in Redis and publishes PredictionCreatedEvent to the Event Bus.
        Key structure: prediction:{timeframe}:{symbol}
        TTL: 24 hours (86400 seconds)
        """
        # Try caching to Redis, but proceed to publish event even if it fails
        from app.config.settings import settings
        if not settings.BACKTEST_SPEED_MODE:
            try:
                redis_key = f"prediction:{prediction.timeframe}:{prediction.symbol}"
                pred_json = prediction.model_dump_json()
                await self.redis.set(
                    name=redis_key,
                    value=pred_json,
                    ex=86400,  # 24 hours
                )
                logger.info(f"Cached Prediction to Redis: {redis_key}")
            except Exception as e:
                logger.error(f"Failed to cache Prediction for {prediction.symbol} ({prediction.timeframe}) to Redis: {e}")
        else:
            logger.debug(f"Speed mode enabled. Bypassing Redis cache for prediction: {prediction.symbol}")

        try:
            # 2. Publish event to the central Event Bus
            event = BaseEvent(
                event_name="PredictionCreatedEvent",
                source="PredictionPublisher",
                payload=prediction,
            )
            await self.publisher.publish(event)
            logger.info(
                f"Published PredictionCreatedEvent: {prediction.symbol} "
                f"({prediction.direction} | Prob: {prediction.probability:.2f})"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to dispatch PredictionCreatedEvent for {prediction.symbol} "
                f"({prediction.timeframe}): {e}"
            )
            return False
