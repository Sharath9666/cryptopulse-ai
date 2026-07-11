"""
Pydantic model representing a completed OHLCV candle.
Defines candle properties and validation requirements.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class Candle(BaseModel):
    """
    Standard schema for a completed OHLCV candle.
    Used for analytical aggregation and strategies.
    """
    symbol: str = Field(..., description="The trading symbol (e.g., BTCUSDT)")
    timeframe: str = Field(..., description="The candle timeframe duration (e.g., '1m')")
    open: float = Field(..., description="The opening price of the candle")
    high: float = Field(..., description="The highest price achieved during the candle timeframe")
    low: float = Field(..., description="The lowest price achieved during the candle timeframe")
    close: float = Field(..., description="The closing price of the candle")
    volume: float = Field(..., description="Total volume traded within the candle timeframe")
    start_time: datetime = Field(..., description="Candle start timestamp (inclusive)")
    end_time: datetime = Field(..., description="Candle end timestamp (exclusive)")
