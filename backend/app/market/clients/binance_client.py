"""
Binance WebSocket client.
Manages low-level WebSocket connection, subscription multiplexing, keepalives,
automated reconnection with exponential backoff, and robust error recovery.
"""

import asyncio
import json
from typing import Any, Callable, Coroutine, List, Union
import websockets
from loguru import logger

from app.config.settings import settings
from app.market.health import market_health_tracker


class BinanceWebSocketClient:
    """
    Asynchronous WebSocket client dedicated to streaming live tick data from Binance.
    """
    def __init__(
        self,
        symbols: List[str],
        on_message: Callable[[dict], Coroutine[Any, Any, None]],
        ws_url: str = settings.BINANCE_WS_URL
    ) -> None:
        self.symbols = [s.upper() for s in symbols]
        self.on_message = on_message
        self.ws_url = ws_url
        self._websocket: Union[websockets.WebSocketClientProtocol, None] = None
        self._running: bool = False
        self._task: Union[asyncio.Task, None] = None

    def _build_connection_url(self) -> str:
        """
        Constructs the multiplexed WebSocket stream URL.
        Example: wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/ethusdt@ticker
        """
        streams = "/".join(f"{s.lower()}@ticker" for s in self.symbols)
        return f"{self.ws_url}?streams={streams}"

    def start(self) -> None:
        """
        Spawns the background task executing the connection and listen loop.
        """
        if self._running:
            logger.warning("Binance client is already running.")
            return

        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("Binance WebSocket stream worker started.")

    async def stop(self) -> None:
        """
        Triggers graceful connection closure and shuts down background workers.
        """
        if not self._running:
            logger.warning("Binance client is not running.")
            return

        logger.info("Stopping Binance WebSocket client...")
        self._running = False
        if self._websocket:
            await self._websocket.close()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        market_health_tracker.record_disconnect()
        logger.info("Binance WebSocket client shut down cleanly.")

    async def _listen_loop(self) -> None:
        """
        Perpetual connection manager loop. Reconnects with backoff if disconnected.
        """
        url = self._build_connection_url()
        backoff = 1.0  # Starting reconnect retry delay in seconds
        max_backoff = 60.0

        while self._running:
            try:
                logger.info(f"Connecting to Binance WebSocket: {url}")
                async with websockets.connect(
                    url,
                    ping_interval=20,  # Built-in heartbeat: send ping every 20s
                    ping_timeout=20,   # Expect pong within 20s or close connection
                ) as ws:
                    self._websocket = ws
                    backoff = 1.0  # Reset backoff on successful connection
                    market_health_tracker.record_connect(self.symbols)
                    logger.info("Successfully established connection to Binance WebSocket.")

                    while self._running:
                        message = await ws.recv()
                        # Increment tick tracker internally
                        market_health_tracker.record_tick()
                        
                        try:
                            data = json.loads(message)
                            # Handle incoming payload on callback
                            await self.on_message(data)
                        except json.JSONDecodeError as jde:
                            logger.error(f"Malformed message received (JSON decoding failed): {jde}")
                        except Exception as e:
                            logger.error(f"Error handling streaming packet: {e}")

            except websockets.exceptions.ConnectionClosed as cc:
                logger.warning(f"WebSocket connection closed unexpectedly by remote peer: {cc}")
            except Exception as e:
                logger.error(f"WebSocket client loop encountered connection error: {e}")

            self._websocket = None
            market_health_tracker.record_disconnect()

            if self._running:
                logger.warning(f"Attempting reconnection in {backoff:.1f} seconds...")
                market_health_tracker.record_reconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, max_backoff)
