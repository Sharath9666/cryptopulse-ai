"""
Market data engine lifecycle manager.
Binds clients and services together and manages their initialization and cleanup
during application lifespan transitions.
"""

from typing import Union
from loguru import logger

from app.config.settings import settings
from app.market.clients.binance_client import BinanceWebSocketClient
from app.market.services.market_stream_service import MarketStreamService


class MarketDataManager:
    """
    Coordination manager starting the streaming services and ensuring cleanup on shutdown.
    """
    def __init__(self) -> None:
        self.service: Union[MarketStreamService, None] = None
        self.client: Union[BinanceWebSocketClient, None] = None

    def start(self) -> None:
        """
        Instantiates services, binds message handlers, and starts streaming tasks.
        """
        logger.info("Initializing Market Data Manager...")
        self.service = MarketStreamService()
        
        # Instantiate Binance Client with injected message handling callback
        self.client = BinanceWebSocketClient(
            symbols=settings.MARKET_SYMBOLS,
            on_message=self.service.handle_raw_message,
        )
        self.client.start()
        logger.info("Market Data Manager started successfully.")

    async def stop(self) -> None:
        """
        Cleans up connection clients and terminates background tasks.
        """
        if self.client:
            logger.info("Stopping Market Data Manager client...")
            await self.client.stop()
        logger.info("Market Data Manager stopped.")


# Singleton manager instance for integration with lifespan events
market_manager = MarketDataManager()
