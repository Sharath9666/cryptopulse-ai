"""
Pydantic schemas representing parsed and validated market ticks.
Provides datatype validation and transformation helpers.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class MarketTick(BaseModel):
    """
    Standard schema for a normalized cryptocurrency market tick.
    Maps to raw streaming data from source feeds (e.g., Binance).
    """
    symbol: str = Field(..., description="The trading symbol (e.g., BTCUSDT)")
    price: float = Field(..., description="The last traded transaction price")
    best_bid: float = Field(..., description="The current best bid/buy price")
    best_ask: float = Field(..., description="The current best ask/sell price")
    volume: float = Field(..., description="The 24h total traded volume")
    event_time: datetime = Field(..., description="Event generation timestamp from feed source")
    receive_time: datetime = Field(..., description="Timestamp when engine received and processed the event")
