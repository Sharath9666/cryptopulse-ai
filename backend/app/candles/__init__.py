"""
Candle aggregation package initialization.
Exposes schemas, health trackers, and lifecycle managers.
"""

from app.candles.models.candle import Candle
from app.candles.health import candle_health_tracker, CandleEngineHealth
from app.candles.manager import candle_manager

__all__ = [
    "Candle",
    "candle_health_tracker",
    "CandleEngineHealth",
    "candle_manager",
]
