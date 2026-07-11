"""
Market replay service.
Translates historical OHLCV candles into sequential Tick events and pushes to Event Bus.
"""

import asyncio
from typing import List
from loguru import logger

from app.backtesting.models.historical_candle import HistoricalCandle
from app.market.schemas.market_tick import MarketTick
from app.events import BaseEvent, event_bus


class MarketReplayEngine:
    """
    Simulates live tick feeds by streaming historical data series sequentially through the EventBus.
    """
    def __init__(self) -> None:
        self.bus = event_bus

    async def replay(self, candles: List[HistoricalCandle]) -> None:
        """
        Loops through candles, converting and publishing tick events with simulated delays.
        """
        logger.info(f"Starting historical replay of {len(candles)} candles...")
        
        for index, candle in enumerate(candles):
            # Map historical close as trade price
            tick = MarketTick(
                symbol=candle.symbol,
                price=candle.close,
                best_bid=candle.close,
                best_ask=candle.close,
                volume=candle.volume,
                event_time=candle.end_time,
                receive_time=candle.end_time,
            )

            # Create event envelope
            event = BaseEvent(
                event_name="MarketTickReceivedEvent",
                source="MarketReplayEngine",
                payload=tick,
            )

            # Publish tick event to central Event Bus
            await self.bus.publish(event)
            
            # Conditionally sleep based on settings
            from app.config.settings import settings
            if settings.BACKTEST_SPEED_MODE:
                await asyncio.sleep(0)
            else:
                await asyncio.sleep(0.002)

            if (index + 1) % 100 == 0:
                logger.info(f"Replayed {index + 1}/{len(candles)} candle ticks...")

        logger.info("Market replay completed.")
