"""
Paper trading portfolio schema.
Tracks available balances, profit/loss metrics, and lists of positions.
"""

from typing import List
from pydantic import BaseModel, Field
from app.paper_trading.models.trade import Trade


class Portfolio(BaseModel):
    """
    Model representing the paper trading simulation virtual portfolio.
    """
    starting_balance: float = Field(100000.0, description="Starting virtual USDT balance")
    available_balance: float = Field(100000.0, description="Current available virtual USDT balance")
    total_profit: float = Field(0.0, description="Sum of positive realized trade profits")
    total_loss: float = Field(0.0, description="Sum of negative realized trade losses")
    open_positions: List[Trade] = Field(default_factory=list, description="List of currently active open trades")
    closed_trades: List[Trade] = Field(default_factory=list, description="List of completed/closed trades")
