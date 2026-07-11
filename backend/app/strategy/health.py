"""
Strategy Engine health indicators.
Tracks signal generation count and active strategy symbol trackers.
"""

from typing import List
from pydantic import BaseModel, Field


class StrategyEngineHealth(BaseModel):
    """
    Representation of the Strategy Engine's health indicators.
    """
    strategies_loaded: int = Field(0, description="Total strategies loaded in engine")
    signals_generated: int = Field(0, description="Count of generated strategy signals")
    symbols_using_strategy: List[str] = Field(default_factory=list, description="Symbols using configured strategy templates")


class StrategyHealthTracker:
    """
    Stateful tracker compiling metrics for the Strategy Engine.
    """
    def __init__(self) -> None:
        self.strategies_loaded: int = 3  # Trend, Momentum, Volatility
        self.signals_generated: int = 0
        self.symbols_using_strategy: List[str] = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SOLUSDT"]

    def increment_signals(self) -> None:
        self.signals_generated += 1

    def get_health(self) -> StrategyEngineHealth:
        return StrategyEngineHealth(
            strategies_loaded=self.strategies_loaded,
            signals_generated=self.signals_generated,
            symbols_using_strategy=self.symbols_using_strategy,
        )


# Global health tracker instance
strategy_health_tracker = StrategyHealthTracker()
