"""
Pydantic schemas for database records (Candles, Predictions, Trades) for API serialization.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MarketCandleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique candle identifier")
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Candle period timeframe (e.g. '1m')")
    start_time: datetime = Field(..., description="Candle start timestamp")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: float = Field(..., description="Trading volume")
    created_at: datetime = Field(..., description="Record creation timestamp")


class PredictionRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique record identifier")
    prediction_id: str = Field(..., description="Semantic prediction ID")
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Candle timeframe (e.g. '1m')")
    direction: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    confidence: str = Field(..., description="HIGH, MEDIUM, or LOW")
    predicted_move: float = Field(..., description="Predicted percentage move")
    entry_price: float = Field(..., description="Asset price at prediction entry")
    actual_price: Optional[float] = Field(None, description="Asset price at prediction evaluation")
    actual_move: Optional[float] = Field(None, description="Actual percentage move realized")
    correct: Optional[bool] = Field(None, description="Whether prediction direction matched price move")
    prediction_time: datetime = Field(..., description="Timestamp when prediction was generated")
    evaluation_time: Optional[datetime] = Field(None, description="Timestamp when evaluation was executed")
    created_at: datetime = Field(..., description="Record creation timestamp")


class TradeRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique record identifier")
    trade_id: str = Field(..., description="Simulated trade UUID")
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    direction: str = Field(..., description="Simulated position direction (LONG)")
    entry_price: float = Field(..., description="Asset price at entry")
    exit_price: Optional[float] = Field(None, description="Asset price at exit")
    quantity: float = Field(..., description="Simulated position size/quantity")
    profit_loss: float = Field(..., description="Realized PnL in USDT")
    status: str = Field(..., description="Position status: OPEN or CLOSED")
    opened_at: datetime = Field(..., description="Position open timestamp")
    closed_at: Optional[datetime] = Field(None, description="Position close timestamp")
    created_at: datetime = Field(..., description="Record creation timestamp")
