"""
Feature engine subscribers.
Listens to completed candle events to run feature calculations.
"""

from loguru import logger

from app.events.subscriber import EventSubscriber
from app.events.base_event import BaseEvent
from app.candles.models.candle import Candle
from app.features.services.feature_engine import feature_engine


class CompletedCandleSubscriber(EventSubscriber):
    """
    Subscribes to 'CompletedCandleEvent' to forward completed candles to the FeatureEngine.
    """
    def __init__(self, engine=feature_engine) -> None:
        self._engine = engine

    @property
    def event_name(self) -> str:
        return "CompletedCandleEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Processes CompletedCandleEvent by delegating candle to feature calculation methods.
        """
        candle = event.payload
        if isinstance(candle, Candle):
            await self._engine.process_candle(candle)
        else:
            logger.warning(f"CompletedCandleSubscriber received unexpected payload: {type(candle)}")
            if isinstance(candle, dict):
                try:
                    candle_model = Candle(**candle)
                    await self._engine.process_candle(candle_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to Candle in subscriber: {e}")
