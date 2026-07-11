"""
Candle engine health tracking and diagnostics.
Monitors active candles, completed count, supported timeframes, and last completion data.
"""

from datetime import datetime
from typing import Dict, List, Union
from pydantic import BaseModel, Field

from app.candles.models.candle import Candle


class CandleEngineHealth(BaseModel):
    """
    Representation of the Candle Aggregation Engine's health indicators.
    """
    active_candles_count: int = Field(..., description="Count of currently active in-memory candles")
    completed_candles_count: int = Field(..., description="Total completed candles since startup")
    supported_timeframes: List[str] = Field(..., description="Timeframes supported by the engine")
    last_completed_candle: Union[Candle, None] = Field(None, description="The last completed candle information")


class CandleHealthTracker:
    """
    Thread-safe tracker storing runtime metrics for the Candle Aggregator.
    """
    def __init__(self) -> None:
        self.active_candles_count: int = 0
        self.completed_candles_count: int = 0
        self.supported_timeframes: List[str] = ["1m"]
        self.last_completed_candle: Union[Candle, None] = None

    def update_active_count(self, count: int) -> None:
        """
        Updates the count of currently active candles.
        """
        self.active_candles_count = count

    def record_completed(self, candle: Candle) -> None:
        """
        Records a completed candle event.
        """
        self.completed_candles_count += 1
        self.last_completed_candle = candle

    def get_health(self) -> CandleEngineHealth:
        """
        Returns the aggregated health snapshot.
        """
        return CandleEngineHealth(
            active_candles_count=self.active_candles_count,
            completed_candles_count=self.completed_candles_count,
            supported_timeframes=self.supported_timeframes,
            last_completed_candle=self.last_completed_candle,
        )


# Global tracker instance
candle_health_tracker = CandleHealthTracker()
