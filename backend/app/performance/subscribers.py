"""
Performance tracking engine event subscribers.
Subscribes to prediction events to track directional accuracy.
"""

from loguru import logger

from app.events.subscriber import EventSubscriber
from app.events.base_event import BaseEvent
from app.prediction.models.prediction import Prediction
from app.performance.services.prediction_tracker import prediction_tracker


class PredictionCreatedSubscriber(EventSubscriber):
    """
    Subscribes to 'PredictionCreatedEvent' and forwards payloads to the performance tracker.
    """
    def __init__(self, tracker=prediction_tracker) -> None:
        self._tracker = tracker

    @property
    def event_name(self) -> str:
        return "PredictionCreatedEvent"

    async def handle(self, event: BaseEvent) -> None:
        """
        Processes PredictionCreatedEvent by passing payload to tracker.
        """
        prediction = event.payload
        if isinstance(prediction, Prediction):
            await self._tracker.track_prediction(prediction)
        else:
            logger.warning(f"PredictionCreatedSubscriber received unexpected payload format: {type(prediction)}")
            if isinstance(prediction, dict):
                try:
                    pred_model = Prediction(**prediction)
                    await self._tracker.track_prediction(pred_model)
                except Exception as e:
                    logger.error(f"Failed parsing dict payload to Prediction in subscriber: {e}")
