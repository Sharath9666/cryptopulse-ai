"""
Prediction performance record model definition.
Represents a recorded prediction and its subsequent evaluation outcome.
"""

from datetime import datetime
from typing import Union
from pydantic import BaseModel, Field


class PredictionRecord(BaseModel):
    """
    Data model tracking prediction outcomes and accuracy evaluations.
    """
    prediction_id: str = Field(..., description="Unique prediction identifier matching prediction event")
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Simulated timeframe interval")
    direction: str = Field(..., description="Predicted direction: BULLISH, BEARISH, or NEUTRAL")
    confidence: str = Field(..., description="Confidence grade: HIGH, MEDIUM, or LOW")
    predicted_move: float = Field(..., description="Expected/predicted movement percent")
    entry_price: float = Field(..., description="Market price at the time of prediction entry")
    prediction_time: datetime = Field(..., description="Timestamp when prediction was registered")
    
    # Evaluation fields populated later
    evaluation_time: Union[datetime, None] = Field(None, description="Timestamp when evaluation was executed")
    actual_price: Union[float, None] = Field(None, description="Actual market price at evaluation timestamp")
    actual_move: Union[float, None] = Field(None, description="Actual price movement percentage change")
    correct: Union[bool, None] = Field(None, description="Whether predicted direction aligned with actual outcomes")
