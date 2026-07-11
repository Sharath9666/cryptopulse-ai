"""
Paper trading control API endpoints.
Provides endpoints to fetch the state of the simulated portfolio.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import List

from app.paper_trading.services.portfolio_manager import portfolio_manager
from app.paper_trading.models.trade import Trade

router = APIRouter()


class PortfolioResponse(BaseModel):
    balance: float = Field(..., description="Available virtual balance in USDT")
    open_positions: List[Trade] = Field(..., description="List of currently active trades")
    closed_trades: List[Trade] = Field(..., description="List of completed/closed trades")
    profit: float = Field(..., description="Net realized profit or loss in USDT")


@router.get(
    "/portfolio",
    response_model=PortfolioResponse,
    summary="Get paper trading portfolio state"
)
async def get_portfolio_state() -> PortfolioResponse:
    """
    Retrieves the virtual portfolio state from Redis.
    """
    portfolio = await portfolio_manager.get_portfolio()
    
    # Calculate net realized profit
    net_profit = portfolio.total_profit - portfolio.total_loss
    
    return PortfolioResponse(
        balance=portfolio.available_balance,
        open_positions=portfolio.open_positions,
        closed_trades=portfolio.closed_trades,
        profit=net_profit
    )
