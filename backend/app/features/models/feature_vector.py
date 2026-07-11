"""
Feature vector schema definitions.
Represents a collection of technical indicators computed for a given symbol and timeframe.
"""

from datetime import datetime
from typing import Dict, Union
from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    """
    Standard model representing the full engineered technical indicator set.
    """
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Candle period timeframe (e.g. '1m')")
    timestamp: datetime = Field(..., description="Indicator calculation event execution timestamp")
    
    # Trend Indicators
    ema_9: Union[float, None] = Field(None, description="9-period Exponential Moving Average")
    ema_20: Union[float, None] = Field(None, description="20-period Exponential Moving Average")
    ema_50: Union[float, None] = Field(None, description="50-period Exponential Moving Average")
    ema_200: Union[float, None] = Field(None, description="200-period Exponential Moving Average")
    
    # Momentum Indicators
    rsi_14: Union[float, None] = Field(None, description="14-period Relative Strength Index")
    macd: Union[float, None] = Field(None, description="Moving Average Convergence Divergence line")
    macd_signal: Union[float, None] = Field(None, description="MACD signal line (9-period EMA of MACD)")
    macd_hist: Union[float, None] = Field(None, description="MACD histogram difference")
    stoch_rsi: Union[float, None] = Field(None, description="Stochastic Relative Strength Index")
    
    # Volatility Indicators
    atr_14: Union[float, None] = Field(None, description="14-period Average True Range")
    bb_upper: Union[float, None] = Field(None, description="Bollinger Band upper boundary")
    bb_middle: Union[float, None] = Field(None, description="Bollinger Band middle boundary (20-period SMA)")
    bb_lower: Union[float, None] = Field(None, description="Bollinger Band lower boundary")
    bb_width: Union[float, None] = Field(None, description="Bollinger Band width (Upper - Lower) / Middle")
    
    # Volume Indicators
    vwap: Union[float, None] = Field(None, description="Volume Weighted Average Price")
    obv: Union[float, None] = Field(None, description="On Balance Volume")
