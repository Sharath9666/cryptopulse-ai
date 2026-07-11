"""
Strategy Signal Publisher.
Publishes compiled StrategySignalCreatedEvent signals to the Event Bus.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from loguru import logger

from app.events import BaseEvent, event_bus
from app.strategy.health import strategy_health_tracker


class StrategySignal(BaseModel):
    """
    Model representing an output trading signal generated from a strategy run.
    """
    symbol: str = Field(..., description="Target pair symbol")
    direction: str = Field(..., description="Target direction: BULLISH, BEARISH, or NEUTRAL")
    confidence: float = Field(..., description="Confidence rating coefficient")
    reasoning: str = Field(..., description="Text explanations confirming signal flags")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Signal timestamp")


class StrategySignalPublisher:
    """
    Publishes StrategySignalCreatedEvent to the Event Bus.
    """
    def __init__(self) -> None:
        self.bus = event_bus

    async def publish_signal(self, symbol: str, direction: str, confidence: float, reasoning: str) -> None:
        """
        Constructs and publishes StrategySignal.
        """
        signal = StrategySignal(
            symbol=symbol.upper(),
            direction=direction.upper(),
            confidence=confidence,
            reasoning=reasoning
        )
        
        event = BaseEvent(
            event_name="StrategySignalCreatedEvent",
            source="StrategyEngine",
            payload=signal
        )
        
        await self.bus.publish(event)
        strategy_health_tracker.increment_signals()
        logger.info(f"Published StrategySignalCreatedEvent for {symbol} Direction: {direction}")
