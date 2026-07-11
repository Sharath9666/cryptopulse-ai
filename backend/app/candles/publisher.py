"""
Candle publishing service.
Responsible for serializing completed OHLCV candles and storing them in Redis.
"""

from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.candles.models.candle import Candle


from app.events import BaseEvent, EventPublisher


class CandlePublisher:
    """
    Publisher class to cache completed candles in Redis and publish events to the Event Bus.
    """
    def __init__(self, redis_client: Redis = None, publisher: EventPublisher = None) -> None:
        self._redis_client = redis_client
        self.publisher = publisher or EventPublisher()

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def publish(self, candle: Candle) -> bool:
        """
        Serializes and stores a completed Candle in Redis and publishes the event.
        Key structure: candle:{timeframe}:{symbol} (e.g. candle:1m:BTCUSDT)
        TTL: 24 hours (86400 seconds)
        """
        # Try caching to Redis, but proceed to publish event even if it fails
        from app.config.settings import settings
        if not settings.BACKTEST_SPEED_MODE:
            try:
                redis_key = f"candle:{candle.timeframe}:{candle.symbol}"
                candle_json = candle.model_dump_json()
                await self.redis.set(
                    name=redis_key,
                    value=candle_json,
                    ex=86400,  # 24 hours
                )
                logger.info(f"Published completed candle to Redis: {redis_key}")
            except Exception as e:
                logger.error(f"Failed to cache candle for {candle.symbol} ({candle.timeframe}) to Redis: {e}")
        else:
            logger.debug(f"Speed mode enabled. Bypassing Redis cache for candle: {candle.symbol}")

        # Persist to PostgreSQL permanent history
        try:
            from app.database.session import async_session_factory
            from app.database.models import MarketCandle
            from app.database.repositories.candle_repository import CandleRepository
            
            db_candle = MarketCandle(
                symbol=candle.symbol,
                timeframe=candle.timeframe,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                start_time=candle.start_time,
                end_time=candle.end_time
            )
            async with async_session_factory() as session:
                async with session.begin():
                    await CandleRepository.save_batch(session, [db_candle])
            logger.info(f"Persisted completed candle for {candle.symbol} to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to persist completed candle for {candle.symbol} to PostgreSQL: {e}")

        try:
            # Publish event to the asynchronous Event Bus
            event = BaseEvent(
                event_name="CompletedCandleEvent",
                source="CandlePublisher",
                payload=candle,
            )
            await self.publisher.publish(event)
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch CompletedCandleEvent for {candle.symbol} ({candle.timeframe}): {e}")
            return False
