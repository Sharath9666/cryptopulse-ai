"""
Paper trading simulated trade schema.
Defines representation of open or closed paper trades.
"""

from datetime import datetime
from typing import Union
import uuid
from pydantic import BaseModel, Field


class Trade(BaseModel):
    """
    Model representing a simulated long trade position.
    """
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique trade identifier")
    symbol: str = Field(..., description="Trading pair symbol (e.g. BTCUSDT)")
    direction: str = Field("LONG", description="Trading direction: 'LONG' only in version 1")
    entry_price: float = Field(..., description="Price at position open")
    exit_price: Union[float, None] = Field(None, description="Price at position close")
    quantity: float = Field(..., description="Simulated volume quantity purchased")
    profit_loss: float = Field(0.0, description="Realized profit/loss value in USDT")
    status: str = Field("OPEN", description="Position status: 'OPEN' or 'CLOSED'")
    opened_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of position entry")
    closed_at: Union[datetime, None] = Field(None, description="Timestamp of position exit")
