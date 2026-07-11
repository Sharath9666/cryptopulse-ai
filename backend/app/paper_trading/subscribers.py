"""
Paper trading subscribers.
Listens to prediction creation events and live ticker updates.
"""

from loguru import logger

from app.events.subscriber import EventSubscriber
from app.events.base_event import BaseEvent
from app.prediction.models.prediction import Prediction
from app.market.schemas.market_tick import MarketTick
from app.paper_trading.services.paper_trading_engine import paper_trading_engine


class PredictionSubscriber(EventSubscriber):
    """
    Subscribes to 'PredictionCreatedEvent' to trigger trade entries.
    """
    def __init__(self, engine=paper_trading_engine) -> None:
        self._engine = engine

    @property
    def event_name(self) -> str:
        return "PredictionCreatedEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Forwards incoming Prediction payloads to paper trading engine logic.
        """
        prediction = event.payload
        if isinstance(prediction, Prediction):
            await self._engine.handle_prediction(prediction)
        else:
            logger.warning(f"PredictionSubscriber received unexpected payload: {type(prediction)}")
            if isinstance(prediction, dict):
                try:
                    pred_model = Prediction(**prediction)
                    await self._engine.handle_prediction(pred_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to Prediction in subscriber: {e}")


class TickSubscriber(EventSubscriber):
    """
    Subscribes to 'MarketTickReceivedEvent' to track and close open positions.
    """
    def __init__(self, engine=paper_trading_engine) -> None:
        self._engine = engine

    @property
    def event_name(self) -> str:
        return "MarketTickReceivedEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Forwards incoming tick payloads to paper trading engine monitoring logic.
        """
        tick = event.payload
        if isinstance(tick, MarketTick):
            await self._engine.handle_tick(tick)
        else:
            logger.warning(f"TickSubscriber received unexpected payload: {type(tick)}")
            if isinstance(tick, dict):
                try:
                    tick_model = MarketTick(**tick)
                    await self._engine.handle_tick(tick_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to MarketTick in subscriber: {e}")
