"""
Paper trading diagnostics and health checker.
Aggregates trade statistics, winning rates, and portfolio returns dynamically.
"""

from typing import List
from pydantic import BaseModel, Field
from app.paper_trading.services.portfolio_manager import portfolio_manager


class PaperTradingHealth(BaseModel):
    """
    Representation of the Paper Trading Engine's health indicators.
    """
    total_trades: int = Field(0, description="Total trades created")
    open_trades: int = Field(0, description="Total active open trades")
    closed_trades: int = Field(0, description="Total closed trades")
    winning_trades: int = Field(0, description="Total trades closed in profit")
    losing_trades: int = Field(0, description="Total trades closed in loss")
    current_balance: float = Field(0.0, description="Virtual portfolio valuation in USDT")
    profit_percentage: float = Field(0.0, description="Overall profit return percentage")
    tracked_symbols: List[str] = Field(default_factory=list, description="Symbols traded since start")


class PaperTradingHealthTracker:
    """
    Tracks runtime indicators and matches symbols active in the system.
    """
    def __init__(self) -> None:
        self._tracked_symbols: List[str] = []

    def track_symbols(self, symbol: str) -> None:
        sym = symbol.upper()
        if sym not in self._tracked_symbols:
            self._tracked_symbols.append(sym)

    async def get_health(self) -> PaperTradingHealth:
        """
        Queries the portfolio manager and compiles live stats.
        """
        portfolio = await portfolio_manager.get_portfolio()
        
        open_count = len(portfolio.open_positions)
        closed_count = len(portfolio.closed_trades)
        total_count = open_count + closed_count
        
        winning = sum(1 for t in portfolio.closed_trades if t.profit_loss > 0.0)
        losing = sum(1 for t in portfolio.closed_trades if t.profit_loss < 0.0)
        
        # Calculate current valuation (available balance + principal value of open positions)
        open_value = sum(t.entry_price * t.quantity for t in portfolio.open_positions)
        current_val = portfolio.available_balance + open_value
        
        profit_pct = 0.0
        if portfolio.starting_balance > 0.0:
            profit_pct = ((current_val - portfolio.starting_balance) / portfolio.starting_balance) * 100.0
            
        return PaperTradingHealth(
            total_trades=total_count,
            open_trades=open_count,
            closed_trades=closed_count,
            winning_trades=winning,
            losing_trades=losing,
            current_balance=current_val,
            profit_percentage=profit_pct,
            tracked_symbols=self._tracked_symbols,
        )


# Global tracker instance
paper_trading_health_tracker = PaperTradingHealthTracker()
