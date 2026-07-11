"""
Market stream processing service.
Receives, parses, validates raw events into MarketTick schemas, and caches them in Redis.
"""

import asyncio
from datetime import datetime, timezone
import json
from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.market.schemas.market_tick import MarketTick


from app.events import BaseEvent, EventPublisher


class MarketStreamService:
    """
    Service responsible for converting raw market events into structured ticks,
    persisting them in the cache, and publishing tick events to the Event Bus.
    """
    def __init__(self, redis_client: Redis = None, publisher: EventPublisher = None) -> None:
        # Dependency-injectable client with fallback to global helper
        self._redis_client = redis_client
        # Dependency-injectable publisher
        self.publisher = publisher or EventPublisher()

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def handle_raw_message(self, message: dict) -> None:
        """
        Processes incoming payload. Extracts raw tick data depending on wrapper formatting.
        """
        # If multiplexed combined stream format, extract 'data' segment
        if "stream" in message and "data" in message:
            raw_tick = message["data"]
        else:
            raw_tick = message

        # Basic fields verification
        required_fields = {"s", "c", "b", "a", "v", "E"}
        if not required_fields.issubset(raw_tick.keys()):
            logger.warning(f"Skipping incomplete market event payload: {message}")
            return

        try:
            # Parse event time (from milliseconds)
            event_dt = datetime.fromtimestamp(raw_tick["E"] / 1000.0, tz=timezone.utc)
            
            # Map raw fields to structured Pydantic model
            tick = MarketTick(
                symbol=raw_tick["s"].upper(),
                price=float(raw_tick["c"]),
                best_bid=float(raw_tick["b"]),
                best_ask=float(raw_tick["a"]),
                volume=float(raw_tick["v"]),
                event_time=event_dt,
                receive_time=datetime.now(timezone.utc),
            )
            
            # Cache the tick in Redis
            await self._cache_tick(tick)

            # Publish event to the asynchronous Event Bus
            event = BaseEvent(
                event_name="MarketTickReceivedEvent",
                source="MarketStreamService",
                payload=tick,
            )
            await self.publisher.publish(event)
            
        except ValueError as ve:
            logger.error(f"Error parsing field data types in tick message: {ve} | Payload: {raw_tick}")
        except Exception as e:
            logger.error(f"Unexpected error processing tick: {e} | Message: {message}")

    async def _cache_tick(self, tick: MarketTick) -> None:
        """
        Persists the MarketTick in Redis.
        Key structure: market:{symbol} (e.g. market:BTCUSDT)
        TTL: 5 minutes (300 seconds)
        """
        try:
            redis_key = f"market:{tick.symbol}"
            # Serialize model to JSON using Pydantic serializer
            tick_json = tick.model_dump_json()
            
            await self.redis.set(
                name=redis_key,
                value=tick_json,
                ex=300,  # 5 minutes TTL
            )
        except Exception as e:
            logger.error(f"Failed to cache tick for {tick.symbol} to Redis: {e}")
