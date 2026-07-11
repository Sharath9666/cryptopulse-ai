"""
Lifespan event handler for the FastAPI application.
Manages startup and shutdown processes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager to manage the lifecycle of the FastAPI application.
    Executes startup and shutdown logic.
    """
    # 1. Startup Logic
    setup_logging()
    logger.info("=== Starting CryptoPulse AI Backend ===")
    
    # Verify database connectivity
    from app.database.health import verify_db_connection
    await verify_db_connection()
    
    # Initialize Redis connection pool and verify connection
    from app.cache import redis_manager, verify_redis_connection
    redis_manager.init_pool()
    await verify_redis_connection()
    
    # Start the async Event Bus dispatch loop
    from app.events import event_bus
    event_bus.start()
    
    # Start Binance Market Data Engine streams
    from app.market import market_manager
    market_manager.start()
    
    # Start Candle Aggregation Engine
    from app.candles import candle_manager
    candle_manager.start()
    
    # Register Feature Engineering Engine subscribers
    from app.events import event_registry
    from app.features import CompletedCandleSubscriber
    event_registry.register(CompletedCandleSubscriber())
    
    # Register Prediction Engine subscribers
    from app.prediction import FeatureVectorSubscriber
    event_registry.register(FeatureVectorSubscriber())
    
    # Initialize Paper Trading Portfolio
    from app.paper_trading import portfolio_manager, PredictionSubscriber, TickSubscriber
    await portfolio_manager.get_portfolio()
    
    # Register Paper Trading subscribers
    event_registry.register(PredictionSubscriber())
    event_registry.register(TickSubscriber())
    
    # Register Performance Engine subscriber
    from app.performance import PredictionCreatedSubscriber
    event_registry.register(PredictionCreatedSubscriber())
    
    # Register Strategy Optimization Engine subscriber
    from app.strategy import FeatureVectorCreatedSubscriber
    event_registry.register(FeatureVectorCreatedSubscriber())

    # Preload trained ML models for all available symbols
    from app.ml.predictor import ml_predictor
    ml_predictor.preload_all()

    logger.info("Application startup events completed successfully.")

    yield

    # 2. Shutdown Logic
    logger.info("=== Stopping CryptoPulse AI Backend ===")
    
    # Gracefully stop Candle Aggregation Engine
    from app.candles import candle_manager
    candle_manager.stop()
    
    # Gracefully stop Market Data Manager streams
    from app.market import market_manager
    await market_manager.stop()
    
    # Gracefully stop Event Bus dispatch worker
    from app.events import event_bus
    await event_bus.stop()
    
    # Gracefully shut down Redis connection pool
    await redis_manager.close_pool()
    
    logger.info("Application shutdown events completed successfully.")
