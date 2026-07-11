"""
Health check endpoint.
Provides simple API status checks for load balancers or uptime monitoring.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(..., description="Status of the application ('healthy' or 'unhealthy')")
    database: str = Field(..., description="Status of the database connection ('connected' or 'unhealthy')")
    cache: str = Field(..., description="Status of the cache connection ('connected' or 'unhealthy')")
    market_engine: dict = Field(..., description="Health details of the Binance WebSocket Market Data Engine")
    candle_engine: dict = Field(..., description="Health details of the Candle Aggregation Engine")
    event_bus: dict = Field(..., description="Health details of the Internal Event Bus")
    feature_engine: dict = Field(..., description="Health details of the Feature Engineering Engine")
    prediction_engine: dict = Field(..., description="Health details of the Prediction Engine")
    paper_trading: dict = Field(..., description="Health details of the Paper Trading Engine")
    backtesting: dict = Field(..., description="Health details of the Backtesting Engine")
    performance_tracking: dict = Field(..., description="Health details of the Prediction Performance Tracking Engine")
    strategy_engine: dict = Field(..., description="Health details of the Strategy Optimization Engine")
    environment: str = Field(..., description="The current running environment")


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="Perform a health check",
    description="Returns the status of the service to verify that it is running successfully."
)
async def health_check() -> HealthResponse:
    from app.config.settings import settings
    from app.database.health import check_database_health
    from app.cache import check_redis_health
    from app.market.health import market_health_tracker
    from app.candles.health import candle_health_tracker
    from app.events.health import get_event_bus_health
    from app.features.health import feature_health_tracker
    from app.prediction.health import prediction_health_tracker
    from app.paper_trading.health import paper_trading_health_tracker
    from app.backtesting.health import backtest_health_tracker
    from app.performance.health import performance_health_tracker
    from app.strategy.health import strategy_health_tracker
    
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()
    market_health = market_health_tracker.get_health()
    candle_health = candle_health_tracker.get_health()
    eb_health = get_event_bus_health()
    feat_health = feature_health_tracker.get_health()
    pred_health = prediction_health_tracker.get_health()
    paper_health = await paper_trading_health_tracker.get_health()
    backtest_health = backtest_health_tracker.get_health()
    perf_health = performance_health_tracker.get_health()
    strategy_health = strategy_health_tracker.get_health()
    
    overall_healthy = db_healthy and redis_healthy and (market_health.health_status != "unhealthy")
    status_str = "healthy" if overall_healthy else "unhealthy"
    
    db_status = "connected" if db_healthy else "unhealthy"
    redis_status = "connected" if redis_healthy else "unhealthy"
    
    return HealthResponse(
        status=status_str,
        database=db_status,
        cache=redis_status,
        market_engine=market_health.model_dump(),
        candle_engine=candle_health.model_dump(),
        event_bus=eb_health.model_dump(),
        feature_engine=feat_health.model_dump(),
        prediction_engine=pred_health.model_dump(),
        paper_trading=paper_health.model_dump(),
        backtesting=backtest_health.model_dump(),
        performance_tracking=perf_health.model_dump(),
        strategy_engine=strategy_health.model_dump(),
        environment=settings.APP_ENV
    )
