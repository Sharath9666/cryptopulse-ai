"""
Development seed script for CryptoPulse AI.

Populates the database with realistic sample data so developers can
immediately explore the application without waiting for the live
Binance feed to populate records.

Usage (run from backend/ directory):
    python -m app.database.seed

Or call programmatically:
    import asyncio
    from app.database.seed import run_seed
    asyncio.run(run_seed())
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_factory
from app.database.models import (
    PredictionRecord,
    TradeRecord,
    BacktestResult,
    MarketCandle,
    PortfolioSnapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _minutes_ago(n: int) -> datetime:
    return _utcnow() - timedelta(minutes=n)


def _hours_ago(n: int) -> datetime:
    return _utcnow() - timedelta(hours=n)


def _days_ago(n: int) -> datetime:
    return _utcnow() - timedelta(days=n)


# ---------------------------------------------------------------------------
# Seed data generators
# ---------------------------------------------------------------------------

def _make_prediction_records() -> list[PredictionRecord]:
    """Generate 10 sample prediction records with varying outcomes."""
    samples = [
        # symbol, direction, confidence, predicted_move, entry, actual, correct
        ("BTCUSDT", "BULLISH", "HIGH", 1.5, 65_000.0, 66_000.0, True),
        ("BTCUSDT", "BULLISH", "MEDIUM", 0.8, 64_800.0, 64_500.0, False),
        ("ETHUSDT", "BULLISH", "HIGH", 2.0, 3_500.0, 3_600.0, True),
        ("ETHUSDT", "BEARISH", "MEDIUM", -1.2, 3_580.0, 3_520.0, True),
        ("DOGEUSDT", "BULLISH", "HIGH", 3.5, 0.145, 0.152, True),
        ("DOGEUSDT", "BEARISH", "LOW", -2.0, 0.150, 0.155, False),
        ("SOLUSDT", "BULLISH", "HIGH", 2.8, 180.0, 185.0, True),
        ("SOLUSDT", "BEARISH", "MEDIUM", -1.5, 182.0, 179.0, True),
        ("XRPUSDT", "BULLISH", "MEDIUM", 1.1, 0.55, 0.56, True),
        ("XRPUSDT", "BEARISH", "LOW", -0.9, 0.56, 0.57, False),
    ]

    records = []
    for i, (symbol, direction, confidence, predicted_move, entry, actual, correct) in enumerate(samples):
        pred_time = _hours_ago(10 - i)
        eval_time = pred_time + timedelta(hours=1)
        actual_move = round((actual - entry) / entry * 100, 4)
        records.append(
            PredictionRecord(
                prediction_id=f"seed-pred-{i+1:04d}",
                symbol=symbol,
                timeframe="1h",
                direction=direction,
                confidence=confidence,
                predicted_move=predicted_move,
                entry_price=entry,
                prediction_time=pred_time,
                evaluation_time=eval_time,
                actual_price=actual,
                actual_move=actual_move,
                correct=correct,
            )
        )
    return records


def _make_trade_records() -> list[TradeRecord]:
    """Generate 8 sample trade records with a mix of open and closed trades."""
    trades = [
        # symbol, direction, entry, exit, qty, pnl, status
        ("BTCUSDT", "LONG",  65_000.0, 66_000.0, 0.1538, 153.8,   "CLOSED"),
        ("BTCUSDT", "LONG",  64_800.0, 64_500.0, 0.1543, -46.3,   "CLOSED"),
        ("ETHUSDT", "LONG",  3_500.0,  3_600.0,  2.857,  285.7,   "CLOSED"),
        ("ETHUSDT", "SHORT", 3_580.0,  3_520.0,  2.793,  167.6,   "CLOSED"),
        ("DOGEUSDT","LONG",  0.145,    0.152,    6896.6, 48.3,    "CLOSED"),
        ("SOLUSDT", "LONG",  180.0,    185.0,    55.6,   278.0,   "CLOSED"),
        ("XRPUSDT", "LONG",  0.55,     None,     1818.2, 0.0,     "OPEN"),
        ("DOGEUSDT","LONG",  0.150,    None,     6666.7, 0.0,     "OPEN"),
    ]

    records = []
    for i, (symbol, direction, entry, exit_p, qty, pnl, status) in enumerate(trades):
        opened = _hours_ago(8 - i)
        closed = (opened + timedelta(hours=1)) if status == "CLOSED" else None
        records.append(
            TradeRecord(
                trade_id=f"seed-trade-{i+1:04d}",
                symbol=symbol,
                direction=direction,
                entry_price=entry,
                exit_price=exit_p,
                quantity=qty,
                profit_loss=pnl,
                status=status,
                opened_at=opened,
                closed_at=closed,
            )
        )
    return records


def _make_backtest_results() -> list[BacktestResult]:
    """Generate 3 sample backtest results."""
    backtests = [
        ("BTCUSDT", "1h", 45, 30, 15, 0.667, 2500.0, 2.5,  8.5,  65.0),
        ("ETHUSDT", "1h", 38, 24, 14, 0.632, 1800.0, 1.8, 12.0,  48.0),
        ("DOGEUSDT","15m",60, 36, 24, 0.600, 1200.0, 1.2, 15.0,  32.0),
    ]
    records = []
    for i, (symbol, tf, total, wins, losses, wr, profit, pct, dd, avg_ret) in enumerate(backtests):
        records.append(
            BacktestResult(
                backtest_id=f"seed-backtest-{i+1:04d}",
                symbol=symbol,
                timeframe=tf,
                total_trades=total,
                winning_trades=wins,
                losing_trades=losses,
                win_rate=wr,
                total_profit=profit,
                profit_percentage=pct,
                maximum_drawdown=dd,
                average_trade_return=avg_ret,
            )
        )
    return records


def _make_market_candles() -> list[MarketCandle]:
    """Generate 24 hourly BTCUSDT candles (last 24h)."""
    records = []
    base_price = 64_500.0
    for i in range(24):
        start = _hours_ago(24 - i)
        end = start + timedelta(hours=1)
        o = base_price + (i * 20)
        h = o + 150
        lo = o - 100
        c = o + (50 * (1 if i % 2 == 0 else -1))
        records.append(
            MarketCandle(
                symbol="BTCUSDT",
                timeframe="1h",
                open=round(o, 2),
                high=round(h, 2),
                low=round(lo, 2),
                close=round(c, 2),
                volume=round(120.0 + i * 5, 2),
                start_time=start,
                end_time=end,
            )
        )
    return records


def _make_portfolio_snapshots() -> list[PortfolioSnapshot]:
    """Generate hourly portfolio snapshots for the last 12 hours."""
    records = []
    balance = 100_000.0
    profit = 0.0
    loss = 0.0
    for i in range(12):
        # Simulate incremental gains/losses
        if i % 3 == 0:
            trade_pnl = 150.0
        elif i % 3 == 1:
            trade_pnl = -50.0
        else:
            trade_pnl = 80.0

        if trade_pnl >= 0:
            profit += trade_pnl
        else:
            loss += abs(trade_pnl)

        balance += trade_pnl
        records.append(
            PortfolioSnapshot(
                timestamp=_hours_ago(12 - i),
                starting_balance=100_000.0,
                available_balance=round(balance, 2),
                total_profit=round(profit, 2),
                total_loss=round(loss, 2),
                open_positions_count=2 if i > 5 else 0,
                closed_trades_count=i,
            )
        )
    return records


# ---------------------------------------------------------------------------
# Main seed runner
# ---------------------------------------------------------------------------

async def run_seed(force: bool = False) -> None:
    """
    Inserts seed data into the database.

    Args:
        force: If True, skips the existing-data check and inserts regardless.
               Use carefully — may cause duplicate key errors if seed IDs collide.
    """
    async with async_session_factory() as session:
        # Guard: skip if data already exists
        if not force:
            from sqlalchemy import select, func
            result = await session.execute(
                select(func.count()).select_from(PredictionRecord)
            )
            count = result.scalar()
            if count and count > 0:
                logger.info(
                    f"Seed skipped — {count} prediction records already present. "
                    "Pass force=True to override."
                )
                return

        logger.info("Seeding database with development data...")

        predictions = _make_prediction_records()
        trades = _make_trade_records()
        backtests = _make_backtest_results()
        candles = _make_market_candles()
        snapshots = _make_portfolio_snapshots()

        session.add_all(predictions)
        session.add_all(trades)
        session.add_all(backtests)
        session.add_all(candles)
        session.add_all(snapshots)

        await session.commit()

        logger.info(
            f"Seed complete: "
            f"{len(predictions)} predictions, "
            f"{len(trades)} trades, "
            f"{len(backtests)} backtests, "
            f"{len(candles)} candles, "
            f"{len(snapshots)} portfolio snapshots."
        )


if __name__ == "__main__":
    asyncio.run(run_seed())
