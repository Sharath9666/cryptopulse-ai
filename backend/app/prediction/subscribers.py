"""
Prediction engine subscribers.
Subscribes to feature vectors to generate direction predictions.
"""

from loguru import logger

from app.events.subscriber import EventSubscriber
from app.events.base_event import BaseEvent
from app.strategy.publisher import StrategySignal
from app.prediction.services.prediction_engine import prediction_engine


class FeatureVectorSubscriber(EventSubscriber):
    """
    Subscribes to 'StrategySignalCreatedEvent' and forwards signals to the prediction engine.
    """
    def __init__(self, engine=prediction_engine) -> None:
        self._engine = engine

    @property
    def event_name(self) -> str:
        return "StrategySignalCreatedEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Processes StrategySignalCreatedEvent by passing it to prediction service.
        """
        signal = event.payload
        if isinstance(signal, StrategySignal):
            await self._engine.generate_prediction_from_signal(signal)
        else:
            logger.warning(f"FeatureVectorSubscriber received unexpected payload: {type(signal)}")
            if isinstance(signal, dict):
                try:
                    signal_model = StrategySignal(**signal)
                    await self._engine.generate_prediction_from_signal(signal_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to StrategySignal in subscriber: {e}")
