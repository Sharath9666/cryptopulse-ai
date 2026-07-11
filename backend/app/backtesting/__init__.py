"""
Backtesting engine initialization.
Exposes HistoricalCandle, BacktestResult, backtest_runner, and health checkers.
"""

from app.backtesting.models.historical_candle import HistoricalCandle
from app.backtesting.models.backtest_result import BacktestResult
from app.backtesting.services.backtest_runner import backtest_runner, BacktestRunner
from app.backtesting.health import backtest_health_tracker, BacktestEngineHealth

__all__ = [
    "HistoricalCandle",
    "BacktestResult",
    "backtest_runner",
    "BacktestRunner",
    "backtest_health_tracker",
    "BacktestEngineHealth",
]
