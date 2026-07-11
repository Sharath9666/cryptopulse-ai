"""
Backtest engine diagnostics.
Tracks session counts, active runners, and last simulation details.
"""

from typing import Union
from pydantic import BaseModel, Field
from app.backtesting.models.backtest_result import BacktestResult


class BacktestEngineHealth(BaseModel):
    """
    Representation of the Backtest Engine's health indicators.
    """
    completed_backtests: int = Field(0, description="Total completed backtesting sessions count")
    active_backtests: int = Field(0, description="Count of currently running active backtests")
    last_result: Union[BacktestResult, None] = Field(None, description="Metadata results of last completed backtest")


class BacktestHealthTracker:
    """
    Tracks runtime statistics for the Backtesting Engine.
    """
    def __init__(self) -> None:
        self.completed_backtests: int = 0
        self.active_backtests: int = 0
        self.last_result: Union[BacktestResult, None] = None

    def start_backtest(self) -> None:
        self.active_backtests += 1

    def complete_backtest(self, result: BacktestResult) -> None:
        self.active_backtests = max(0, self.active_backtests - 1)
        self.completed_backtests += 1
        self.last_result = result

    def get_health(self) -> BacktestEngineHealth:
        return BacktestEngineHealth(
            completed_backtests=self.completed_backtests,
            active_backtests=self.active_backtests,
            last_result=self.last_result,
        )


# Global tracker instance
backtest_health_tracker = BacktestHealthTracker()
