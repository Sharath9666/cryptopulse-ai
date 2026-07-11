"""
SQLAlchemy models for CryptoPulse AI production persistence layer.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import BaseModel


class PredictionRecord(BaseModel):
    """
    Database model representing historical predictions and evaluations.
    """
    __tablename__ = "prediction_records"

    prediction_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    predicted_move: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    prediction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Evaluation fields populated later
    evaluation_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_move: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


class TradeRecord(BaseModel):
    """
    Database model tracking simulated paper trades.
    """
    __tablename__ = "trade_records"

    trade_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), default="LONG", nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    profit_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class BacktestResult(BaseModel):
    """
    Database model representing historical backtest run summaries.
    """
    __tablename__ = "backtest_results"

    backtest_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profit_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    maximum_drawdown: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_trade_return: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class MarketCandle(BaseModel):
    """
    Database model storing historical OHLCV candles.
    """
    __tablename__ = "market_candles"

    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PortfolioSnapshot(BaseModel):
    """
    Database model for saving paper trading portfolio history over time.
    """
    __tablename__ = "portfolio_snapshots"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    starting_balance: Mapped[float] = mapped_column(Float, nullable=False)
    available_balance: Mapped[float] = mapped_column(Float, nullable=False)
    total_profit: Mapped[float] = mapped_column(Float, nullable=False)
    total_loss: Mapped[float] = mapped_column(Float, nullable=False)
    open_positions_count: Mapped[int] = mapped_column(Integer, nullable=False)
    closed_trades_count: Mapped[int] = mapped_column(Integer, nullable=False)
