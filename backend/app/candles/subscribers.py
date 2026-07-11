"""
Candle aggregation engine subscribers.
Subscribes to market tick events to feed the candle aggregator.
"""

from loguru import logger

from app.events.subscriber import EventSubscriber
from app.events.base_event import BaseEvent
from app.market.schemas.market_tick import MarketTick
from app.candles.services.candle_aggregator import CandleAggregator


class MarketTickSubscriber(EventSubscriber):
    """
    Subscribes to 'MarketTickReceivedEvent' and forwards ticks to the CandleAggregator.
    """
    def __init__(self, aggregator: CandleAggregator) -> None:
        self._aggregator = aggregator

    @property
    def event_name(self) -> str:
        return "MarketTickReceivedEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Extracts MarketTick from event payload and pushes it to aggregator.
        """
        tick = event.payload
        if isinstance(tick, MarketTick):
            await self._aggregator.ingest_tick(tick)
        else:
            logger.warning(f"MarketTickSubscriber received unexpected payload format: {type(tick)}")
            # Try to parse if it's dictionary representation
            if isinstance(tick, dict):
                try:
                    tick_model = MarketTick(**tick)
                    await self._aggregator.ingest_tick(tick_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to MarketTick in subscriber: {e}")
