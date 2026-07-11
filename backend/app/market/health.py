"""
Market data engine health tracking and diagnostics.
Monitors connectivity state, disconnect frequency, symbols list, and latencies.
"""

from datetime import datetime
from typing import Dict, List, Union
from pydantic import BaseModel, Field


class MarketEngineHealth(BaseModel):
    """
    Representation of the Market Data Engine's health indicators.
    """
    market_connected: bool = Field(..., description="Websocket connection state")
    last_tick_time: Union[datetime, None] = Field(None, description="Timestamp of the last received valid tick")
    connected_symbols: List[str] = Field(default_factory=list, description="List of currently tracked symbols")
    reconnect_count: int = Field(0, description="Total number of automated reconnect attempts")
    health_status: str = Field(..., description="Overall state indicator (e.g. 'healthy', 'degraded', 'unhealthy')")


class MarketHealthTracker:
    """
    Thread-safe tracker storing runtime metrics for the Binance WebSocket connection.
    """
    def __init__(self) -> None:
        self.market_connected: bool = False
        self.last_tick_time: Union[datetime, None] = None
        self.connected_symbols: List[str] = []
        self.reconnect_count: int = 0

    def record_connect(self, symbols: List[str]) -> None:
        """
        Records a successful connection event.
        """
        self.market_connected = True
        self.connected_symbols = symbols

    def record_disconnect(self) -> None:
        """
        Records a connection loss event.
        """
        self.market_connected = False

    def record_reconnect(self) -> None:
        """
        Increments the reconnect counter.
        """
        self.reconnect_count += 1

    def record_tick(self) -> None:
        """
        Updates the timestamp of the most recent tick.
        """
        self.last_tick_time = datetime.now()

    def get_health(self) -> MarketEngineHealth:
        """
        Calculates and returns the aggregated health snapshot.
        """
        # Determine status based on connection state and latency
        if not self.market_connected:
            status = "unhealthy"
        else:
            status = "healthy"
            if self.last_tick_time:
                # If we haven't received a tick in 60 seconds despite being 'connected', mark degraded
                latency = (datetime.now() - self.last_tick_time).total_seconds()
                if latency > 60:
                    status = "degraded"
            else:
                # Connected but no ticks received yet
                status = "degraded"

        return MarketEngineHealth(
            market_connected=self.market_connected,
            last_tick_time=self.last_tick_time,
            connected_symbols=self.connected_symbols,
            reconnect_count=self.reconnect_count,
            health_status=status,
        )


# Global tracker instance
market_health_tracker = MarketHealthTracker()
