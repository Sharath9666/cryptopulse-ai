"""
Candle aggregator service.
Ingests live MarketTick events, maintains active in-memory candles,
detects candle completion, and forwards completed candles to the publisher.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Coroutine, Dict, List
from loguru import logger

from app.market.schemas.market_tick import MarketTick
from app.candles.models.candle import Candle
from app.candles.health import candle_health_tracker


class CandleAggregator:
    """
    Stateful aggregator converting MarketTick streams into OHLCV Candles.
    Designed to easily support multiple timeframes (default: 1m).
    """
    def __init__(
        self,
        on_candle_complete: Callable[[Candle], Coroutine[Any, Any, None]],
        timeframes: List[str] = None
    ) -> None:
        self.on_candle_complete = on_candle_complete
        self.timeframes = timeframes or ["1m"]
        # Map storing active candles: { "timeframe:symbol": { active_candle_state } }
        self.active_candles: Dict[str, Dict[str, Any]] = {}
        candle_health_tracker.update_active_count(0)

    def _get_timeframe_delta(self, timeframe: str) -> timedelta:
        """
        Translates timeframe string into a timedelta.
        Extensible to other timeframes (e.g. 5m, 15m, 1h).
        """
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        if unit == "m":
            return timedelta(minutes=value)
        elif unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        else:
            raise ValueError(f"Unsupported timeframe unit: {unit}")

    def _get_candle_bounds(self, event_time: datetime, timeframe: str) -> tuple[datetime, datetime]:
        """
        Truncates the event_time to align with the starting bound of the timeframe.
        """
        delta = self._get_timeframe_delta(timeframe)
        
        # Ensure timezone-aware comparison
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
            
        if timeframe.endswith("m"):
            minutes = int(timeframe[:-1])
            # Align start time to the nearest block of minutes
            start_minute = (event_time.minute // minutes) * minutes
            start_time = event_time.replace(minute=start_minute, second=0, microsecond=0)
        elif timeframe.endswith("h"):
            hours = int(timeframe[:-1])
            start_hour = (event_time.hour // hours) * hours
            start_time = event_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        else:
            # Default fallback to day truncation
            start_time = event_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
        return start_time, start_time + delta

    async def ingest_tick(self, tick: MarketTick) -> None:
        """
        Ingests a new MarketTick and updates all supported active candles for the symbol.
        """
        for timeframe in self.timeframes:
            key = f"{timeframe}:{tick.symbol}"
            start_time, end_time = self._get_candle_bounds(tick.event_time, timeframe)
            
            # Retrieve active candle
            active = self.active_candles.get(key)
            
            if active is None:
                # 1. No active candle exists. Start a new one.
                self.active_candles[key] = {
                    "symbol": tick.symbol,
                    "timeframe": timeframe,
                    "open": tick.price,
                    "high": tick.price,
                    "low": tick.price,
                    "close": tick.price,
                    "start_24h_volume": tick.volume,  # Store initial volume to compute delta
                    "volume": 0.0,
                    "start_time": start_time,
                    "end_time": end_time,
                }
                logger.info(f"New {timeframe} candle started for {tick.symbol} starting at {start_time}")
                candle_health_tracker.update_active_count(len(self.active_candles))
                continue

            # 2. Check if the tick belongs to a new candle period
            if tick.event_time >= active["end_time"]:
                # The current candle is completed!
                completed_candle = Candle(
                    symbol=active["symbol"],
                    timeframe=active["timeframe"],
                    open=active["open"],
                    high=active["high"],
                    low=active["low"],
                    close=active["close"],
                    volume=active["volume"],
                    start_time=active["start_time"],
                    end_time=active["end_time"],
                )
                logger.info(f"Completed {timeframe} candle for {tick.symbol} ending at {active['end_time']}")
                
                # Update health tracker
                candle_health_tracker.record_completed(completed_candle)
                
                # Trigger complete callback (save to Redis)
                await self.on_candle_complete(completed_candle)
                
                # Start a new candle period using the current tick
                self.active_candles[key] = {
                    "symbol": tick.symbol,
                    "timeframe": timeframe,
                    "open": tick.price,
                    "high": tick.price,
                    "low": tick.price,
                    "close": tick.price,
                    "start_24h_volume": tick.volume,
                    "volume": 0.0,
                    "start_time": start_time,
                    "end_time": end_time,
                }
                logger.info(f"New {timeframe} candle started for {tick.symbol} starting at {start_time}")
            else:
                # 3. Update existing candle metrics
                active["high"] = max(active["high"], tick.price)
                active["low"] = min(active["low"], tick.price)
                active["close"] = tick.price
                # Calculate candle-scoped volume delta using 24h volume shifts
                active["volume"] = max(0.0, tick.volume - active["start_24h_volume"])
                
        candle_health_tracker.update_active_count(len(self.active_candles))
