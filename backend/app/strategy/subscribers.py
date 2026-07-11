"""
Strategy engine event subscribers.
Subscribes to feature engineering outputs to trigger strategy updates.
"""

from loguru import logger

from app.events.subscriber import EventSubscriber
from app.events.base_event import BaseEvent
from app.features.models.feature_vector import FeatureVector
from app.strategy.services.strategy_engine import strategy_engine


class FeatureVectorCreatedSubscriber(EventSubscriber):
    """
    Subscribes to 'FeatureVectorCreatedEvent' and forwards payloads to the Strategy Engine.
    """
    def __init__(self, engine=strategy_engine) -> None:
        self._engine = engine

    @property
    def event_name(self) -> str:
        return "FeatureVectorCreatedEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Processes FeatureVectorCreatedEvent by passing payload to strategy engine.
        """
        features = event.payload
        if isinstance(features, FeatureVector):
            await self._engine.process_features(features)
        else:
            logger.warning(f"FeatureVectorCreatedSubscriber received unexpected payload format: {type(features)}")
            if isinstance(features, dict):
                try:
                    feat_model = FeatureVector(**features)
                    await self._engine.process_features(feat_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to FeatureVector in strategy subscriber: {e}")
