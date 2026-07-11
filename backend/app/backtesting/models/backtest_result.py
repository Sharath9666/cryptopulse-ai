"""
Backtest result model definitions.
Holds final statistical outputs of a completed backtesting simulation run.
"""

from typing import List, Union
from pydantic import BaseModel, Field


class BacktestResult(BaseModel):
    """
    Representation of quantitative backtest metrics.
    """
    backtest_id: str = Field(..., description="Unique backtest session identifier")
    symbol: str = Field(..., description="Traded symbol (e.g. BTCUSDT)")
    timeframe: str = Field(..., description="Traded timeframe interval")
    total_trades: int = Field(0, description="Total executed simulated trades")
    winning_trades: int = Field(0, description="Count of trades closing in profit")
    losing_trades: int = Field(0, description="Count of trades closing in loss")
    win_rate: float = Field(0.0, description="Win rate percentage ratio (0.0 to 1.0)")
    total_profit: float = Field(0.0, description="Net absolute profit or loss in USDT")
    profit_percentage: float = Field(0.0, description="Net profit percentage return")
    maximum_drawdown: float = Field(0.0, description="Peak-to-trough maximum equity decline percentage")
    average_trade_return: float = Field(0.0, description="Average percentage return per trade")
