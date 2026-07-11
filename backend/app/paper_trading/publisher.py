"""
Paper trading publisher service.
Persists trades in Redis and dispatches completed trade notifications to the Event Bus.
"""

from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.events import BaseEvent, EventPublisher
from app.paper_trading.models.trade import Trade


class PaperTradingPublisher:
    """
    Handles publishing of simulated trading event notifications and caching.
    """
    def __init__(self, redis_client: Redis = None, event_publisher: EventPublisher = None) -> None:
        self._redis_client = redis_client
        self.publisher = event_publisher or EventPublisher()

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def publish_trade_close(self, trade: Trade) -> bool:
        # Try caching to Redis, but proceed to publish event even if it fails
        from app.config.settings import settings
        if not settings.BACKTEST_SPEED_MODE:
            try:
                redis_key = f"paper_trade:{trade.trade_id}"
                trade_json = trade.model_dump_json()
                await self.redis.set(
                    name=redis_key,
                    value=trade_json,
                    ex=604800,  # 7 days
                )
                logger.info(f"Cached Trade details to Redis: {redis_key}")
            except Exception as e:
                logger.error(f"Failed to cache closed trade {trade.trade_id} to Redis: {e}")
        else:
            logger.debug(f"Speed mode enabled. Bypassing Redis cache for closed trade: {trade.trade_id}")

        try:
            # 2. Publish event to the central Event Bus
            event = BaseEvent(
                event_name="TradeCompletedEvent",
                source="PaperTradingPublisher",
                payload=trade,
            )
            await self.publisher.publish(event)
            logger.info(f"Published TradeCompletedEvent: {trade.symbol} (PnL: {trade.profit_loss:.2f} USDT)")
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch TradeCompletedEvent for trade {trade.trade_id}: {e}")
            return False

    async def cache_open_trade(self, trade: Trade) -> bool:
        """
        Saves open Trade details in Redis with a 7-day TTL.
        """
        from app.config.settings import settings
        if not settings.BACKTEST_SPEED_MODE:
            try:
                redis_key = f"paper_trade:{trade.trade_id}"
                trade_json = trade.model_dump_json()
                await self.redis.set(
                    name=redis_key,
                    value=trade_json,
                    ex=604800,  # 7 days
                )
                return True
            except Exception as e:
                logger.error(f"Failed to cache open trade {trade.trade_id}: {e}")
                return False
        else:
            logger.debug(f"Speed mode enabled. Bypassing Redis cache for open trade: {trade.trade_id}")
            return True
