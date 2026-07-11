"""
Paper trading simulation engine initialization.
Exposes Trade, Portfolio, subscribers, and health checker components.
"""

from app.paper_trading.models.trade import Trade
from app.paper_trading.models.portfolio import Portfolio
from app.paper_trading.health import paper_trading_health_tracker, PaperTradingHealth
from app.paper_trading.subscribers import PredictionSubscriber, TickSubscriber
from app.paper_trading.services.portfolio_manager import portfolio_manager

__all__ = [
    "Trade",
    "Portfolio",
    "paper_trading_health_tracker",
    "PaperTradingHealth",
    "PredictionSubscriber",
    "TickSubscriber",
    "portfolio_manager",
]
