"""
Backtesting results publisher.
Caches completed backtesting stats results to Redis.
"""

from loguru import logger
from redis.asyncio import Redis

from app.cache.redis import get_redis_client
from app.backtesting.models.backtest_result import BacktestResult


class BacktestPublisher:
    """
    Handles caching of BacktestResult objects in Redis.
    """
    def __init__(self, redis_client: Redis = None) -> None:
        self._redis_client = redis_client

    @property
    def redis(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = get_redis_client()
        return self._redis_client

    async def save_result(self, result: BacktestResult) -> bool:
        """
        Saves BacktestResult in Redis.
        Key structure: backtest:{backtest_id}
        """
        # Try caching to Redis
        from app.config.settings import settings
        if not settings.BACKTEST_SPEED_MODE:
            try:
                redis_key = f"backtest:{result.backtest_id}"
                result_json = result.model_dump_json()
                await self.redis.set(
                    name=redis_key,
                    value=result_json,
                )
                logger.info(f"Cached BacktestResult in Redis: {redis_key}")
            except Exception as e:
                logger.error(f"Failed to cache backtest result {result.backtest_id}: {e}")

        # Persist to PostgreSQL permanent history
        try:
            from app.database.session import async_session_factory
            from app.database.models import BacktestResult as DbBacktestResult
            
            db_result = DbBacktestResult(
                backtest_id=result.backtest_id,
                symbol=result.symbol,
                timeframe=result.timeframe,
                total_trades=result.total_trades,
                winning_trades=result.winning_trades,
                losing_trades=result.losing_trades,
                win_rate=result.win_rate,
                total_profit=result.total_profit,
                profit_percentage=result.profit_percentage,
                maximum_drawdown=result.maximum_drawdown,
                average_trade_return=result.average_trade_return
            )
            async with async_session_factory() as session:
                async with session.begin():
                    session.add(db_result)
            logger.info(f"Persisted BacktestResult {result.backtest_id} to PostgreSQL.")
            return True
        except Exception as e:
            logger.error(f"Failed to persist BacktestResult {result.backtest_id} to PostgreSQL: {e}")
            return False
