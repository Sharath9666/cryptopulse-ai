"""
Candle aggregation engine manager.
Coordinates startup, registration with the market streams feed, and cleanup.
"""

from typing import Union
from loguru import logger

from app.market.manager import market_manager
from app.candles.publisher import CandlePublisher
from app.candles.services.candle_aggregator import CandleAggregator


class CandleManager:
    """
    Manager class coordinating the lifecycle of the Candle Aggregation Engine.
    """
    def __init__(self) -> None:
        self.publisher: Union[CandlePublisher, None] = None
        self.aggregator: Union[CandleAggregator, None] = None

    def start(self) -> None:
        """
        Initializes the publisher and aggregator, and hooks into the Market Data streams.
        """
        logger.info("Initializing Candle Aggregation Manager...")
        self.publisher = CandlePublisher()
        self.aggregator = CandleAggregator(
            on_candle_complete=self.publisher.publish,
            timeframes=["1m"]
        )

        # Instantiate subscriber and register with central Event Registry
        from app.events.registry import event_registry
        from app.candles.subscribers import MarketTickSubscriber
        
        self.subscriber = MarketTickSubscriber(self.aggregator)
        event_registry.register(self.subscriber)
        logger.info("Candle aggregator registered with EventRegistry for MarketTickReceivedEvent.")

    def stop(self) -> None:
        """
        Cleans up resources and shuts down the Candle Aggregator.
        """
        logger.info("Stopping Candle Aggregation Manager...")
        # Since active candles are in-memory, we can log active ones or save them if required,
        # but the spec only asks for graceful shutdown.
        logger.info("Candle Aggregation Manager stopped.")


# Singleton manager instance for integration with lifespan events
candle_manager = CandleManager()
