"""
Historical candle model definitions.
Represents OHLCV historical candle data fetched from Binance.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class HistoricalCandle(BaseModel):
    """
    Model representing a single OHLCV interval bar.
    """
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Timeframe interval (e.g. '1m')")
    open: float = Field(..., description="Opening price of the interval")
    high: float = Field(..., description="Highest price during the interval")
    low: float = Field(..., description="Lowest price during the interval")
    close: float = Field(..., description="Closing price of the interval")
    volume: float = Field(..., description="Trading volume during the interval")
    start_time: datetime = Field(..., description="Interval start timestamp")
    end_time: datetime = Field(..., description="Interval end timestamp")
