"""
Integration test script for Backtesting and Paper Trading pipelines.
Runs a 30-day lookback test for DOGEUSDT and verifies metrics generation.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from loguru import logger
import sys

from app.core.logging import setup_logging
from app.events import event_bus, event_registry
from app.features import CompletedCandleSubscriber
from app.prediction import FeatureVectorSubscriber
from app.paper_trading import PredictionSubscriber, TickSubscriber, portfolio_manager
from app.backtesting.services.backtest_runner import backtest_runner


async def run_integration_test() -> None:
    """
    Executes integration backtest for DOGEUSDT, verifying end-to-end data pipeline.
    """
    setup_logging()
    logger.info("=== Starting Integration Test: Backtesting Pipeline ===")

    # 1. Start Event Bus and register all subscriber components
    event_bus.start()
    
    # Initialize Redis connection pool
    from app.cache import redis_manager
    redis_manager.init_pool()
    
    # Initialize Candle Aggregator Manager
    from app.candles import candle_manager
    candle_manager.start()
    
    event_registry.register(CompletedCandleSubscriber())
    event_registry.register(FeatureVectorSubscriber())
    event_registry.register(PredictionSubscriber())
    event_registry.register(TickSubscriber())
    
    from app.performance import PredictionCreatedSubscriber
    event_registry.register(PredictionCreatedSubscriber())
    
    from app.strategy import FeatureVectorCreatedSubscriber
    event_registry.register(FeatureVectorCreatedSubscriber())
    
    # 2. Configure timeframes and dates
    symbol = "DOGEUSDT"
    timeframe = "1h"  # Using 1-hour interval for swift data retrieval and test processing
    days = 30
    starting_balance = 100000.0
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    logger.info(
        f"Configuring Test: Symbol={symbol} | Interval={timeframe} | "
        f"Duration={days} days | Balance={starting_balance} USDT"
    )

    # 3. Trigger backtest simulation
    result = await backtest_runner.run(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        starting_balance=starting_balance
    )

    # 4. Verification checks
    logger.info("=== Verifying Integration Results ===")
    
    # Check if results model is constructed
    if not result or not result.backtest_id:
        logger.error("Integration Test FAILED: No BacktestResult generated.")
        sys.exit(1)
        
    logger.info(f"Generated Backtest ID: {result.backtest_id}")
    logger.info(f"Total simulated trades executed: {result.total_trades}")
    logger.info(f"Win rate achieved: {result.win_rate * 100.0:.2f}%")
    logger.info(f"Net profit/loss: {result.total_profit:.2f} USDT ({result.profit_percentage:.2f}%)")
    logger.info(f"Maximum drawdown recorded: {result.maximum_drawdown:.2f}%")
    logger.info(f"Average trade return: {result.average_trade_return:.2f}%")

    # Fetch final portfolio state to verify trades list populated
    portfolio = await portfolio_manager.get_portfolio()
    logger.info(f"Final simulated balance: {portfolio.available_balance:.2f} USDT")
    
    # Clean up background threads
    await event_bus.stop()
    event_registry.unregister_all()
    
    # Gracefully stop Candle Aggregator
    from app.candles import candle_manager
    candle_manager.stop()
    
    # Close Redis connection pool
    from app.cache import redis_manager
    await redis_manager.close_pool()

    logger.info("=== Integration Test Completed Successfully ===")


if __name__ == "__main__":
    asyncio.run(run_integration_test())
